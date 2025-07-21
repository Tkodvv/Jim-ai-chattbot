import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Set
import discord
from discord.ext import commands
from models import db, Conversation
from openai_client import generate_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Track user interactions - {user_id: last_interaction_time}
        self.user_interactions: Dict[int, datetime] = {}
        # Track users currently being processed to avoid spam
        self.processing_users: Set[int] = set()
        
        # Initialize database
        with self.app_context():
            db.create_all()
    
    def app_context(self):
        """Get Flask app context for database operations"""
        from web_server import app
        return app.app_context()
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
    
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
        
        # Check if "jim" is mentioned (case insensitive)
        if "jim" in message.content.lower():
            should_respond = True
            logger.info(f"Jim mentioned by {message.author.name}")
        
        # Check if user interacted within last 60 seconds
        user_id = message.author.id
        current_time = datetime.utcnow()
        
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
                
                # Show typing indicator to make it more human-like
                async with message.channel.typing():
                    # Add natural delay to simulate human typing
                    import random
                    typing_delay = random.uniform(1.0, 3.0)  # 1-3 seconds
                    await asyncio.sleep(typing_delay)
                    
                    # Get or create user conversation memory
                    conversation_memory = await self.get_user_memory(user_id)
                    
                    # Generate response
                    response = await generate_response(
                        message.content, 
                        message.author.name, 
                        conversation_memory
                    )
                    
                    # Update user memory with new interaction
                    await self.update_user_memory(
                        user_id, 
                        message.content, 
                        response,
                        message.author.name
                    )
                
                # Send response with reply indicator for better conversation flow
                if response:
                    await message.reply(response, mention_author=False)
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.channel.send("yo my bad, something went wrong lol")
            
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
                
                # Store recent messages (keep last 10 exchanges)
                import json
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

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Simple ping command"""
        await ctx.send("yo what's good! 🔥")
    
    @commands.command(name='forget')
    async def forget_user(self, ctx):
        """Clear user's conversation memory"""
        try:
            with self.app_context():
                user_id_str = str(ctx.author.id)
                Conversation.query.filter_by(user_id=user_id_str).delete()
                db.session.commit()
            
            await ctx.send("aight bet, cleared your memory! fresh start fr 🧠✨")
        except Exception as e:
            logger.error(f"Error clearing user memory: {e}")
            await ctx.send("my bad, couldn't clear that rn")
