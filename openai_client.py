import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

# Gen Z personality system prompt
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

async def generate_response(user_message: str, username: str, conversation_memory: Dict[str, str]) -> Optional[str]:
    """Generate a response using OpenAI GPT-4o with Gen Z personality"""
    
    try:
        # Build context from conversation memory
        context = ""
        if conversation_memory:
            # Add username context
            if 'username' in conversation_memory:
                context += f"User's name: {conversation_memory['username']}\n"
            
            # Add recent conversation context
            if 'recent_messages' in conversation_memory:
                try:
                    recent = json.loads(conversation_memory['recent_messages'])
                    if recent:
                        context += "\nRecent conversation:\n"
                        for msg in recent[-3:]:  # Last 3 exchanges for context
                            context += f"User: {msg['user']}\nJim: {msg['bot']}\n"
                except:
                    pass
        
        # Construct the prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"Context for this conversation:\n{context}"
            })
        
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        # Generate response
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=200,  # Keep responses conversational length
            temperature=0.8,  # Add some personality variance
        )
        
        bot_response = response.choices[0].message.content.strip()
        
        # Log successful generation
        logger.info(f"Generated response for {username}: {len(bot_response)} chars")
        
        return bot_response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        
        # Return an unfiltered error message in character
        error_responses = [
            "yo my brain just shit the bed, give me a sec",
            "oop my AI's having a stroke, try again",
            "nah my circuits are fucked rn, one sec",
            "lowkey my brain's being a bitch today 💀",
            "damn something broke, this is annoying af",
            "my bad, tech's being stupid as usual"
        ]
        
        import random
        return random.choice(error_responses)

async def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        logger.error(f"OpenAI connection test failed: {e}")
        return False
