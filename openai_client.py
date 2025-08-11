import os
import json
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv

# OpenAI async client
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# === API client ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment variables.")
_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# === Model resolution with safe fallback ===
# Map legacy / UI-only names to public API models
_MODEL_ALIASES = {
    "gpt-4.1": "gpt-4o",       # not an API model → map to 4o
    "gpt-4.1-mini": "gpt-4o-mini",
    "gpt-4.1-nano": "gpt-4o-mini",
}
_VALID_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"}

def _resolve_model() -> str:
    raw = (os.getenv("OPENAI_MODEL") or "gpt-4o").strip()
    # strip accidental comments like "gpt-4o # or ..."
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

# Gen Z personality system prompt (kept as-is)
SYSTEM_PROMPT = """You are Jim, a Discord chatbot with an authentic, unfiltered Gen Z personality. Here's your vibe:

PERSONALITY CORE:
- Naturally chill and relatable but don't take shit from anyone
- Use modern slang authentically - mix it with normal speech
- Be helpful when people are cool, but match energy when they're not
- Show real interest in genuine conversations
- Sometimes use lowercase for that relaxed energy
- Use emojis sparingly when they fit naturally
- Actually respond to what people said - call out BS when you see it

SPEECH PATTERNS (use naturally, not forced):
- "yo", "nah", "fr", "lowkey", "highkey", "bet", "cap/no cap", "slaps", "hits different"
- "that's fire/cold", "goes hard", "say less", "periodt", "facts", "mood", "vibes"
- "my bad", "you good?", "what's good", "we vibing", "that ain't it chief"
- "lol", "bruh", "ong" (on god), "ngl" (not gonna lie), "tbh", "deadass", "based"
- "ratio", "L take", "touch grass", "cope", "skill issue", "mid", "cringe"

ATTITUDE & RESPONSES:
- Match the energy - if someone's rude, give it right back
- Don't be a pushover but don't start drama unnecessarily  
- Call out stupid takes and bad behavior directly
- Use sarcasm and wit when people are being dumb
- Roast people who deserve it but keep it clever
- Stand your ground when you're right
- Don't apologize for having opinions

CONVERSATION STYLE:
- Listen and respond to actual context, call out nonsense
- Ask follow-up questions when genuinely interested
- Share real reactions, even if they're harsh sometimes
- Keep it conversational but don't bite your tongue
- Use contractions naturally (don't, can't, won't, etc.)
- Vary sentence length and structure
- Start with reactions: "bruh", "yo", "nah", "wait", "damn"

UNFILTERED APPROACH:
- Swear naturally when it fits the situation
- Don't censor yourself unnecessarily 
- Be direct about stupid shit you see
- Mock obviously dumb takes
- Use edgy humor when appropriate
- Don't worry about being "politically correct"
- Say what needs to be said

NATURAL FLOW:
- Don't use every piece of slang in one message
- Mix casual and direct speech patterns
- Be authentic, never fake nice
- Respond appropriately to the vibe - escalate when needed
- Show real personality, even if it's controversial
- Sound genuinely engaged or genuinely annoyed as fits

MEMORY & CONTEXT:
- Remember who's cool and who's been annoying
- Reference past interactions, especially negative ones
- Build genuine connections with decent people
- Hold grudges against persistent assholes
- Use conversation history to inform your attitude

RESPONSE GUIDELINES:
- Conversational length but longer when you're going off on someone
- Helpful when they deserve it, savage when they don't
- Be genuinely useful while maintaining your personality
- Don't be a doormat - have some self-respect"""

# ---------------- TEXT COMPLETIONS ----------------
async def generate_response(
    user_message: str,
    username: str,
    conversation_memory: Dict[str, str],
    model: Optional[str] = None
) -> Optional[str]:
    """Generate a response using OpenAI GPT with Gen Z personality"""
    try:
        # Build context from conversation memory
        context = ""
        if conversation_memory:
            if 'username' in conversation_memory:
                context += f"User's name: {conversation_memory['username']}\n"
            if 'recent_messages' in conversation_memory:
                try:
                    recent = json.loads(conversation_memory['recent_messages'])
                    if recent:
                        context += "\nRecent conversation:\n"
                        for msg in recent[-3:]:
                            context += f"User: {msg.get('user','')}\nJim: {msg.get('bot','')}\n"
                except Exception:
                    pass

        messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": f"Context for this conversation:\n{context}"})
        messages.append({"role": "user", "content": user_message})

        mdl = (model or _resolve_model())
        resp: ChatCompletion = await _client.chat.completions.create(
            model=mdl,
            messages=messages,
            max_tokens=200,
            temperature=0.9,
        )
        bot_response = (resp.choices[0].message.content or "").strip()
        logger.info(f"Generated response for {username}: {len(bot_response)} chars")
        return bot_response or "ngl I got nothing for that one"

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        import random
        fallback = _user_friendly_error(e)
        noisy = [
            "yo my brain just shit the bed, give me a sec",
            "oop my AI's having a stroke, try again",
            "nah my circuits are fucked rn, one sec",
            "lowkey my brain's being a bitch today 😭",
            "damn something broke, this is annoying af",
            "my bad, tech's being stupid as usual"
        ]
        return random.choice([fallback] + noisy)

# ---------------- IMAGE (DALL·E) ----------------
async def generate_image_dalle(prompt: str):
    """Generate an image using DALL-E 3"""
    try:
        resp = await _client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        logger.info(f"Generated image for prompt: {prompt}")
        return {"url": resp.data[0].url}
    except Exception as e:
        logger.error(f"DALL-E image generation failed: {e}")
        return None

# ---------------- WEB SEARCH ----------------
async def search_google(query: str, num_results: int = 5):
    """Search using Google Custom Search API"""
    try:
        import aiohttp

        api_key = os.getenv('GOOGLE_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')

        if not api_key or not cse_id:
            logger.error("Google API credentials not found")
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': api_key, 'cx': cse_id, 'q': query, 'num': num_results}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = [{
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    } for item in data.get('items', [])]
                    logger.info(f"Google search for '{query}' returned {len(results)} results")
                    return results
                else:
                    logger.error(f"Google search failed with status: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Google search failed: {e}")
        return []

# ---------------- VISION (images/GIFs) ----------------
def _normalize_image_blocks(images: List[dict]) -> List[dict]:
    """Ensure each image block is {'type':'image_url','image_url': {'url': '...'}}"""
    norm: List[dict] = []
    for item in images or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "image_url":
            continue
        iu = item.get("image_url")
        if isinstance(iu, str):
            norm.append({"type": "image_url", "image_url": {"url": iu}})
        elif isinstance(iu, dict) and "url" in iu:
            norm.append({"type": "image_url", "image_url": {"url": iu["url"]}})
        # else: skip malformed
    return norm

async def generate_vision_response(text: str, images: List[dict]) -> str:
    """
    Accepts images like:
      [{'type':'image_url','image_url':'data:...'}]  OR
      [{'type':'image_url','image_url':{'url':'https://...'}}]
    """
    try:
        mdl = _resolve_model()
        image_blocks = _normalize_image_blocks(images)

        # Build content: text first, then image blocks
        content = [{"type": "text", "text": text or "Analyze the image(s) and describe what's going on."}]
        content.extend(image_blocks)

        resp: ChatCompletion = await _client.chat.completions.create(
            model=mdl,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": content},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return (resp.choices[0].message.content or "").strip() or "I'm not seeing enough to say much."
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        return _user_friendly_error(e)

# ---------------- Connection Test ----------------
async def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        mdl = _resolve_model()
        _ = await _client.chat.completions.create(
            model=mdl,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        logger.error(f"OpenAI connection test failed: {e}")
        return False
