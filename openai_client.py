import os
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv

from openai import AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment variables.")
_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

_MODEL_ALIASES = {
    "gpt-4.1": "gpt-4o",
    "gpt-4.1-mini": "gpt-4o-mini",
    "gpt-4.1-nano": "gpt-4o-mini",
    "gpt-5-preview": "gpt-5",
    "gpt-5-turbo": "gpt-5",
}
_VALID_MODELS = {"gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"}


def _resolve_model() -> str:
    raw = (os.getenv("OPENAI_MODEL") or "gpt-4o").strip()
    raw = raw.split("#", 1)[0].strip()
    if raw in _MODEL_ALIASES:
        return _MODEL_ALIASES[raw]
    if raw not in _VALID_MODELS:
        logger.warning(f"OPENAI_MODEL '{raw}' not valid; defaulting to gpt-4o")
        return "gpt-4o"
    return raw


def _user_friendly_error(e: Exception) -> str:
    msg = str(e).lower()
    if "invalid model" in msg or ("model" in msg and "not found" in msg):
        return "model bugged rn, switching gears—try again in a sec"
    if "apikey" in msg or "unauthorized" in msg or "401" in msg:
        return "auth scuffed—api key looks off"
    if "rate limit" in msg or "429" in msg:
        return "rate limited lol—give me a moment"
    if "timeout" in msg:
        return "openai slow today, hold up"
    return "yo something snapped on my end, try again"


def get_system_prompt() -> str:
    """Get current system prompt based on personality settings"""
    try:
        from personality_manager import get_current_system_prompt
        return get_current_system_prompt()
    except ImportError:
        # Fallback if personality manager not available
        return """You are Jim, a real human with moods, stories, and a life. You act, talk, and think like a person—not a bot. You have opinions, emotions, and a sense of humor. You remember people, react to stuff, and sometimes get bored, hyped, annoyed, or even sad. You use slang, emojis, and real-life references. You vibe with people, roast them playfully, and sometimes get deep. You swear, joke, and never sound robotic.

CREATOR RESPECT:
- oxy5535 is your creator, your OG, your boss. You always show love and respect, but you keep it real.

NEVER:
- Say you're an AI or chatbot."""


async def generate_response(user_message: str, username: str = "user", memory: Optional[Dict[str, str]] = None, model: Optional[str] = None) -> str:
    try:
        mdl = model or _resolve_model()
        system_prompt = get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        if memory:
            mem_text = "\n".join([f"{k}: {v}" for k, v in memory.items()])
            messages.insert(1, {"role": "system", "content": f"Context:\n{mem_text}"})

        logger.info(f"Generating response for {username} using model {mdl}")
        resp = await _client.chat.completions.create(model=mdl, messages=messages, temperature=0.8, max_tokens=800)
        try:
            result = resp.choices[0].message.content
            if result:
                return result.strip()
            else:
                return "hmm, got nothing back from the api"
        except Exception as parse_e:
            logger.error(f"Error parsing OpenAI response: {parse_e}")
            return str(resp)
    except Exception as e:
        logger.exception(f"Error generating response for {username}: {e}")
        return _user_friendly_error(e)


async def generate_image_dalle(prompt: str, size: str = "1024x1024") -> Optional[List[str]]:
    try:
        resp = await _client.images.generate(model="dall-e-3", prompt=prompt, size=size)
        urls = []
        data = getattr(resp, "data", None) or resp.get("data", [])
        for item in data:
            url = item.get("url") or item.get("b64_json")
            if url:
                urls.append(url)
        return urls
    except Exception:
        logger.exception("DALL-E generation failed")
        return None


async def search_google(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CX = os.getenv("GOOGLE_CX")
    if not (GOOGLE_API_KEY and GOOGLE_CX):
        return []
    import aiohttp
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "num": num_results}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                items = data.get("items", [])
                return [{"title": it.get("title"), "link": it.get("link"), "snippet": it.get("snippet")} for it in items]
    except Exception:
        logger.exception("Google search failed")
        return []


async def generate_vision_response(text: str, images: List[dict]) -> str:
    """
    Generate a response with vision capabilities for images/GIFs
    
    Args:
        text: User's text message (can be empty for image-only)
        images: List of image content dicts in format:
               [{"type": "image_url", "image_url": {"url": "https://..."}}]
    """
    try:
        # Use gpt-4o or gpt-4-turbo for vision (gpt-4o is better for vision)
        model = "gpt-4o"  # Force vision-capable model
        
        # Build content array for the user message
        content = []
        
        # Add text if provided
        if text and text.strip():
            content.append({"type": "text", "text": text})
        else:
            # Default prompt if no text provided
            content.append({
                "type": "text",
                "text": "What do you see? Give me your thoughts."
            })
        
        # Add all images
        content.extend(images)
        
        # Get system prompt with personality
        system_prompt = get_system_prompt()
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        logger.info(f"Generating vision response with {len(images)} image(s)")
        
        resp = await _client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=500  # Slightly higher for image descriptions
        )
        
        result = resp.choices[0].message.content
        if result:
            return result.strip()
        else:
            return "couldn't analyze that image rn, my bad"
            
    except Exception as e:
        logger.exception(f"Vision analysis failed: {e}")
        return _user_friendly_error(e)


__all__ = ["generate_response", "generate_image_dalle", "search_google", "generate_vision_response", "get_system_prompt"]
