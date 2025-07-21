#!/usr/bin/env python3
"""
Jim - Advanced Discord AI Chatbot
A complete Discord bot with memory, search capabilities, and Gen Z personality
"""

import os
import asyncio
import logging
import threading
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List

import discord
from discord.ext import commands
from openai import OpenAI
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask, jsonify
import aiohttp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class DatabaseManager:
    """Handles PostgreSQL database operations"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            # Construct from individual components
            user = os.getenv('PGUSER', 'postgres')
            password = os.getenv('PGPASSWORD', '')
            host = os.getenv('PGHOST', 'localhost')
            port = os.getenv('PGPORT', '5432')
            database = os.getenv('PGDATABASE', 'discord_bot')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    user_id TEXT,
                    key TEXT,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, key)
                );
            """)
            
            # Create search_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    query TEXT,
                    results TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def get_user_memory(self, user_id: str) -> Dict[str, str]:
        """Get user's conversation memory"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT key, value FROM conversations WHERE user_id = %s",
                (user_id,)
            )
            
            results = cursor.fetchall()
            conn.close()
            
            return {row['key']: row['value'] for row in results}
            
        except Exception as e:
            logger.error(f"Error getting user memory: {e}")
            return {}
    
    def update_user_memory(self, user_id: str, key: str, value: str):
        """Update user's conversation memory"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversations (user_id, key, value, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
            """, (user_id, key, value))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating user memory: {e}")
    
    def store_search_history(self, user_id: str, query: str, results: str):
        """Store search history"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO search_history (user_id, query, results)
                VALUES (%s, %s, %s)
            """, (user_id, query, results))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing search history: {e}")

class AIPersonality:
    """Handles AI personality and response generation"""
    
    # Enhanced unfiltered Gen Z personality prompt
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

    @staticmethod
    async def generate_response(user_message: str, username: str, conversation_memory: Dict[str, str]) -> str:
        """Generate AI response with personality"""
        try:
            # Build context from memory
            context = f"User's name: {username}\n"
            
            if 'recent_messages' in conversation_memory:
                try:
                    recent = json.loads(conversation_memory['recent_messages'])
                    if recent:
                        context += "\nRecent conversation:\n"
                        for msg in recent[-3:]:  # Last 3 exchanges
                            context += f"User: {msg['user']}\nJim: {msg['bot']}\n"
                except:
                    pass
            
            # Add personality traits if stored
            if 'personality_notes' in conversation_memory:
                context += f"\nUser personality notes: {conversation_memory['personality_notes']}\n"
            
            messages = [
                {"role": "system", "content": AIPersonality.SYSTEM_PROMPT},
                {"role": "system", "content": f"Context:\n{context}"},
                {"role": "user", "content": user_message}
            ]
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=250,
                temperature=0.8,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            
            # Unfiltered error responses
            error_responses = [
                "yo my brain just shit the bed, give me a sec",
                "oop my AI's having a stroke, try again",
                "nah my circuits are fucked rn, one sec", 
                "lowkey my brain's being a bitch today 💀",
                "damn something broke, this is annoying af",
                "my bad, tech's being stupid as usual"
            ]
            return random.choice(error_responses)

class GoogleSearcher:
    """Handles Google search functionality"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        self.enabled = bool(self.api_key and self.cse_id)
    
    async def search(self, query: str, num_results: int = 3) -> List[Dict]:
        """Perform Google search"""
        if not self.enabled:
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': num_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    results = []
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', '')
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []

class JimBot(commands.Bot):
    """Main Discord bot class"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize components
        self.db = DatabaseManager()
        self.searcher = GoogleSearcher()
        
        # Track user interactions
        self.user_interactions: Dict[int, datetime] = {}
        self.processing_users: Set[int] = set()
        
        # Response triggers
        self.trigger_words = ['jim', 'bot']
        self.interaction_timeout = 60  # seconds
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info("Tkodv's slave is running")
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="your vibes 🎵"
            )
        )
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot's own messages
        if message.author == self.user:
            return
        
        # Don't respond to DMs
        if isinstance(message.channel, discord.DMChannel):
            return
        
        # Don't respond if user is being processed
        if message.author.id in self.processing_users:
            return
        
        should_respond = False
        user_id = message.author.id
        current_time = datetime.utcnow()
        
        # Check for trigger words
        message_lower = message.content.lower()
        if any(trigger in message_lower for trigger in self.trigger_words):
            should_respond = True
            logger.info(f"Trigger word detected from {message.author.name}")
        
        # Check recent interaction
        if user_id in self.user_interactions:
            last_interaction = self.user_interactions[user_id]
            if current_time - last_interaction <= timedelta(seconds=self.interaction_timeout):
                should_respond = True
                logger.info(f"Recent interaction from {message.author.name}")
        
        if should_respond:
            await self.handle_user_message(message)
        
        # Process commands
        await self.process_commands(message)
    
    async def handle_user_message(self, message):
        """Process and respond to user message"""
        user_id = str(message.author.id)
        self.processing_users.add(message.author.id)
        
        try:
            # Update interaction time
            self.user_interactions[message.author.id] = datetime.utcnow()
            
            # Show typing with natural delay
            async with message.channel.typing():
                typing_delay = random.uniform(1.0, 3.5)
                await asyncio.sleep(typing_delay)
                
                # Get user memory
                conversation_memory = self.db.get_user_memory(user_id)
                
                # Check if message contains search request
                if any(word in message.content.lower() for word in ['search', 'look up', 'find', 'google']):
                    response = await self.handle_search_request(message, conversation_memory)
                else:
                    # Generate AI response
                    response = await AIPersonality.generate_response(
                        message.content,
                        message.author.name,
                        conversation_memory
                    )
                
                # Update conversation memory
                await self.update_conversation_memory(
                    user_id,
                    message.content,
                    response,
                    message.author.name
                )
            
            # Send response with reply
            if response:
                await message.reply(response, mention_author=False)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await message.reply("yo my bad, something went wrong lol")
        
        finally:
            self.processing_users.discard(message.author.id)
    
    async def handle_search_request(self, message, conversation_memory):
        """Handle search requests"""
        if not self.searcher.enabled:
            return "nah I can't search the web rn, my search powers are disabled 😔"
        
        # Extract search query (simple approach)
        content = message.content.lower()
        search_terms = content.replace('jim', '').replace('search', '').replace('look up', '').replace('find', '').replace('google', '').strip()
        
        if not search_terms:
            return "yo what should I search for?"
        
        # Perform search
        results = await self.searcher.search(search_terms)
        
        if not results:
            return f"couldn't find anything for '{search_terms}' rn, my bad"
        
        # Store search history
        self.db.store_search_history(
            str(message.author.id),
            search_terms,
            json.dumps(results)
        )
        
        # Format response
        response = f"found some stuff about '{search_terms}':\n\n"
        for i, result in enumerate(results[:2], 1):
            response += f"{i}. **{result['title']}**\n{result['snippet']}\n{result['link']}\n\n"
        
        return response
    
    async def update_conversation_memory(self, user_id: str, user_message: str, bot_response: str, username: str):
        """Update user's conversation memory"""
        try:
            # Store username
            self.db.update_user_memory(user_id, 'username', username)
            
            # Store last interaction
            self.db.update_user_memory(user_id, 'last_interaction', datetime.utcnow().isoformat())
            
            # Store recent messages
            memory = self.db.get_user_memory(user_id)
            recent_messages = []
            
            if 'recent_messages' in memory:
                try:
                    recent_messages = json.loads(memory['recent_messages'])
                except:
                    recent_messages = []
            
            # Add new exchange
            recent_messages.append({
                'user': user_message,
                'bot': bot_response,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Keep last 10 exchanges
            if len(recent_messages) > 10:
                recent_messages = recent_messages[-10:]
            
            self.db.update_user_memory(user_id, 'recent_messages', json.dumps(recent_messages))
            
        except Exception as e:
            logger.error(f"Error updating conversation memory: {e}")
    
    # Bot Commands
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Ping command"""
        await ctx.send("yo what's good! 🔥")
    
    @commands.command(name='forget')
    async def forget_user(self, ctx):
        """Clear user's memory"""
        try:
            conn = psycopg2.connect(self.db.database_url)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE user_id = %s", (str(ctx.author.id),))
            conn.commit()
            conn.close()
            
            await ctx.send("aight bet, cleared your memory! fresh start fr 🧠✨")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            await ctx.send("my bad, couldn't clear that rn")
    
    @commands.command(name='image')
    async def generate_image(self, ctx, *, prompt):
        """Generate an image using DALL-E"""
        try:
            async with ctx.typing():
                response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                
                embed = discord.Embed(
                    title="Generated Image",
                    description=f"Prompt: {prompt}",
                    color=0x7289da
                )
                embed.set_image(url=response.data[0].url)
                embed.set_footer(text="Generated by DALL-E 3")
                
                responses = [
                    "yo here's your image, hope it's fire 🔥",
                    "made this for you, thoughts?",
                    "DALL-E cooked this up, not bad right?",
                    "here you go, fresh AI art incoming"
                ]
                await ctx.send(random.choice(responses), embed=embed)
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            await ctx.send("damn, image generation broke. my bad")
    
    @commands.command(name='search')
    async def search_web(self, ctx, *, query):
        """Search the web using Google Custom Search"""
        try:
            async with ctx.typing():
                results = await self.searcher.search(query)
                
                if results:
                    embed = discord.Embed(
                        title=f"Search Results: {query}",
                        color=0x4285f4
                    )
                    
                    for i, result in enumerate(results[:3], 1):
                        title = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
                        snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
                        
                        embed.add_field(
                            name=f"{i}. {title}",
                            value=f"{snippet}\n[Link]({result['link']})",
                            inline=False
                        )
                    
                    responses = [
                        "found some shit for you:",
                        "here's what Google says:",
                        "search results coming in hot:",
                        "yo check these out:"
                    ]
                    await ctx.send(random.choice(responses), embed=embed)
                else:
                    await ctx.send(f"couldn't find anything for '{query}', search is being dumb")
                    
        except Exception as e:
            logger.error(f"Error searching: {e}")
            await ctx.send("search broke, Google's probably down or some shit")
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show available commands"""
        embed = discord.Embed(
            title="Jim's Commands 🤖",
            description="yo here's what I can do for you",
            color=0x7289da
        )
        
        embed.add_field(
            name="!ping", 
            value="Check if I'm alive and ready to roast", 
            inline=False
        )
        embed.add_field(
            name="!image <prompt>", 
            value="Generate an image with DALL-E 3", 
            inline=False
        )
        embed.add_field(
            name="!search <query>", 
            value="Search the web for anything", 
            inline=False
        )
        embed.add_field(
            name="!forget", 
            value="Clear your conversation memory", 
            inline=False
        )
        embed.add_field(
            name="!stats", 
            value="Show bot statistics", 
            inline=False
        )
        
        embed.set_footer(text="Just say 'jim' in any message to chat with me!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='stats')
    async def stats(self, ctx):
        """Show bot statistics"""
        try:
            conn = psycopg2.connect(self.db.database_url)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM conversations")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_memories = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM search_history")
            total_searches = cursor.fetchone()[0]
            
            conn.close()
            
            embed = discord.Embed(
                title="Jim's Stats 📊",
                color=0x7289da
            )
            embed.add_field(name="Users", value=total_users, inline=True)
            embed.add_field(name="Memories", value=total_memories, inline=True)
            embed.add_field(name="Searches", value=total_searches, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await ctx.send("couldn't grab stats rn, my bad")

# Flask web server for keeping alive
def create_flask_app():
    """Create Flask app for keeping bot alive"""
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            "status": "Jim Discord Bot is running! 🤖",
            "message": "yo what's good, Tkodv's slave is alive and vibing",
            "version": "2.0.0"
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "message": "all systems go fr 🔥"
        })
    
    @app.route('/ping')
    def ping():
        return jsonify({
            "message": "pong! bot's still breathing 🏓"
        })
    
    return app

def run_web_server():
    """Run Flask server in separate thread"""
    app = create_flask_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    """Main function"""
    # Start web server
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Start Discord bot
    bot = JimBot()
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())