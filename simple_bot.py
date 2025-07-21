import os
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Set
import discord
from discord.ext import commands
from models import db, Conversation
from openai_client import generate_response, generate_image_dalle, search_google

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBotClass(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Track user interactions
        self.user_interactions: Dict[int, datetime] = {}
        self.processing_users: Set[int] = set()
        
        # Initialize database
        try:
            with self.app_context():
                db.create_all()
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    def app_context(self):
        """Get Flask app context for database operations"""
        from web_server import app
        return app.app_context()
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info("Tkodv's slave is running")
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # List loaded commands
        logger.info(f"Loaded commands: {[cmd.name for cmd in self.commands]}")
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Don't respond to bot's own messages
        if message.author == self.user:
            return
        
        # Don't respond to DMs
        if isinstance(message.channel, discord.DMChannel):
            return
        
        # Don't respond if user is currently being processed
        if message.author.id in self.processing_users:
            return
        
        should_respond = False
        user_id = message.author.id
        current_time = datetime.utcnow()
        
        # Check if "jim" is mentioned (case insensitive)
        if "jim" in message.content.lower():
            should_respond = True
            logger.info(f"Jim mentioned by {message.author.name}")
        
        # Check if user interacted within last 60 seconds
        if user_id in self.user_interactions:
            last_interaction = self.user_interactions[user_id]
            if current_time - last_interaction <= timedelta(seconds=60):
                should_respond = True
                logger.info(f"Recent interaction from {message.author.name}")
        
        if should_respond:
            # Add user to processing set to prevent spam
            self.processing_users.add(user_id)
            
            try:
                # Update interaction time
                self.user_interactions[user_id] = current_time
                
                # Show typing indicator
                async with message.channel.typing():
                    # Add natural delay
                    typing_delay = random.uniform(1.0, 3.0)
                    await asyncio.sleep(typing_delay)
                    
                    # Get user memory
                    conversation_memory = await self.get_user_memory(user_id)
                    
                    # Generate response
                    response = await generate_response(
                        message.content, 
                        message.author.name, 
                        conversation_memory
                    )
                    
                    # Update user memory
                    await self.update_user_memory(
                        user_id, 
                        message.content, 
                        response,
                        message.author.name
                    )
                
                # Send response with reply
                if response:
                    await message.reply(response, mention_author=False)
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.reply("yo my bad, something went wrong lol")
            
            finally:
                # Remove user from processing set
                self.processing_users.discard(user_id)
        
        # Process commands
        await self.process_commands(message)
    
    async def get_user_memory(self, user_id: int) -> Dict[str, str]:
        """Get user's conversation memory from database"""
        try:
            with self.app_context():
                conversations = Conversation.query.filter_by(user_id=str(user_id)).all()
                return {conv.key: conv.value for conv in conversations}
        except Exception as e:
            logger.error(f"Error getting user memory: {e}")
            return {}
    
    async def update_user_memory(self, user_id: int, user_message: str, bot_response: str, username: str):
        """Update user's conversation memory in database"""
        try:
            with self.app_context():
                import json
                user_id_str = str(user_id)
                
                # Store last interaction
                last_interaction = Conversation.query.filter_by(
                    user_id=user_id_str, key='last_interaction'
                ).first()
                
                if last_interaction:
                    last_interaction.value = datetime.utcnow().isoformat()
                else:
                    last_interaction = Conversation(
                        user_id=user_id_str,
                        key='last_interaction',
                        value=datetime.utcnow().isoformat()
                    )
                    db.session.add(last_interaction)
                
                # Store username
                username_record = Conversation.query.filter_by(
                    user_id=user_id_str, key='username'
                ).first()
                
                if username_record:
                    username_record.value = username
                else:
                    username_record = Conversation(
                        user_id=user_id_str,
                        key='username',
                        value=username
                    )
                    db.session.add(username_record)
                
                # Store recent messages
                recent_messages = Conversation.query.filter_by(
                    user_id=user_id_str, key='recent_messages'
                ).first()
                
                if recent_messages:
                    try:
                        messages = json.loads(recent_messages.value)
                    except:
                        messages = []
                else:
                    messages = []
                    recent_messages = Conversation(
                        user_id=user_id_str,
                        key='recent_messages',
                        value='[]'
                    )
                    db.session.add(recent_messages)
                
                # Add new exchange
                messages.append({
                    'user': user_message,
                    'bot': bot_response,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Keep only last 10 exchanges
                if len(messages) > 10:
                    messages = messages[-10:]
                
                recent_messages.value = json.dumps(messages)
                
                # Commit changes
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating user memory: {e}")
            try:
                db.session.rollback()
            except:
                pass

# Commands
@commands.command(name='ping')
async def ping_cmd(ctx):
    """Simple ping command"""
    responses = [
        "yo what's good! 🔥",
        "pong, bitch! still alive",
        "sup, you need something or just checking?",
        "yeah I'm here, what's up",
        "pong! ready to vibe or roast, your choice"
    ]
    await ctx.send(random.choice(responses))

@commands.command(name='image')
async def image_cmd(ctx, *, prompt):
    """Generate an image using DALL-E"""
    try:
        async with ctx.typing():
            image_result = await generate_image_dalle(prompt)
            
            if image_result and 'url' in image_result:
                embed = discord.Embed(
                    title="Generated Image",
                    description=f"Prompt: {prompt}",
                    color=0x7289da
                )
                embed.set_image(url=image_result['url'])
                embed.set_footer(text="Generated by DALL-E 3")
                
                responses = [
                    "yo here's your image, hope it's fire 🔥",
                    "made this for you, thoughts?",
                    "DALL-E cooked this up, not bad right?",
                    "here you go, fresh AI art incoming"
                ]
                await ctx.send(random.choice(responses), embed=embed)
            else:
                await ctx.send("nah couldn't generate that image, DALL-E's being weird")
                
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await ctx.send("damn, image generation broke. my bad")

@commands.command(name='search')
async def search_cmd(ctx, *, query):
    """Search the web using Google Custom Search"""
    try:
        async with ctx.typing():
            results = await search_google(query)
            
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

@commands.command(name='jimhelp')
async def help_cmd(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="Jim's Commands 🤖",
        description="yo here's what I can do for you",
        color=0x7289da
    )
    
    embed.add_field(name="!ping", value="Check if I'm alive and ready to roast", inline=False)
    embed.add_field(name="!image <prompt>", value="Generate an image with DALL-E 3", inline=False)
    embed.add_field(name="!search <query>", value="Search the web for anything", inline=False)
    embed.add_field(name="!jimhelp", value="Show this help message", inline=False)
    embed.set_footer(text="Just say 'jim' in any message to chat with me!")
    
    await ctx.send(embed=embed)

# Create bot instance and add commands
bot = SimpleBotClass()
bot.add_command(ping_cmd)
bot.add_command(image_cmd)
bot.add_command(search_cmd)
bot.add_command(help_cmd)