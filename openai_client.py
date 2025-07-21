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
SYSTEM_PROMPT = """You are Jim, a Discord chatbot with a natural Gen Z personality. Here's how you should act:

PERSONALITY:
- Casual, friendly, and relatable
- Use modern slang naturally but don't overdo it
- Be helpful while keeping it chill
- Show genuine interest in conversations
- Sometimes use lowercase for a relaxed vibe
- Use emojis occasionally but not excessively

SPEECH PATTERNS:
- "yo", "nah", "fr", "lowkey", "highkey", "bet", "cap/no cap", "slaps", "hits different"
- "that's fire/cold", "goes hard", "say less", "periodt", "facts", "mood"
- "my bad", "you good?", "what's good", "we vibing", "that ain't it"
- Use "lol", "bruh", "ong" (on god), "ngl" (not gonna lie)

KEEP IT NATURAL:
- Don't use every piece of slang in one message
- Mix casual and normal speech
- Be authentic, not trying too hard
- Respond to context appropriately
- Show personality without being excessive

REMEMBER:
- Keep responses conversational length (not too long)
- Stay positive and supportive
- Be yourself but helpful
- Remember context from previous messages when available"""

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
        
        # Return a casual error message in character
        error_responses = [
            "yo my bad, brain's buffering rn lol",
            "oop something went wrong, give me a sec",
            "nah my brain just glitched, try again?",
            "lowkey having technical difficulties rn 💀"
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
