import os
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional
import discord
from discord.ext import commands
from dotenv import load_dotenv
from models import db, Conversation, UserProfile, create_app
from enhanced_memory import EnhancedMemoryManager
from openai_client import generate_response, generate_image_dalle, search_google

# try optional vision helper; we'll fall back if it's not implemented yet
try:
    from openai_client import generate_vision_response  # async (text:str, images:list[dict]) -> str
    HAS_VISION = True
except Exception:
    HAS_VISION = False

# Load environment variables from .env file
load_dotenv()

# ---- feature flags ----
ENABLE_JIM_MOD_CMDS = os.getenv("JIM_ENABLE_MOD_CMDS", "false").lower() in {"1","true","yes","y"}

# ---- creator/master settings ----
CREATOR_USER_ID = 556006898298650662  # Jim's owner - iivxfn (Izaiah)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- helpers for image detection ----
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".ico", ".jfif")
IMAGE_DOMAINS = ("tenor.com", "giphy.com", "imgur.com", "discord.com", "discordapp.com", "media.discordapp.net")

class SimpleBotClass(commands.Bot):
    # Creator information
    CREATOR_USER_ID = 556006898298650662  # iivxfn (Izaiah)
    CREATOR_USERNAME = "yoda"
    
    # memory guardrails
    MAX_USERS_TRACKED = 500
    INTERACTION_TTL_SECONDS = 3600
    MAX_USER_TEXT = 3000
    MAX_RECENT_EXCHANGES = 6

    # recent conversation window (seconds) – images only respond within this or if addressed directly
    RECENT_WINDOW_SECONDS = int(os.getenv("JIM_RECENT_WINDOW", "60"))

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.voice_states = True  # Enable voice state tracking
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Track user interactions
        self.user_interactions: Dict[int, datetime] = {}
        self.processing_users: Set[int] = set()
        
        # Initialize enhanced memory system
        self.memory_manager = None
        
        # Initialize database
        try:
            with self.app_context():
                db.create_all()
                # Initialize memory manager after database is ready
                self.memory_manager = EnhancedMemoryManager(self.app_context)
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
        logger.info(f"Loaded commands: {[cmd.name for cmd in self.commands]}")

        # Load voice system
        try:
            await self.load_extension("voice_system")
            logger.info("Voice system loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load voice system: {e}")
        
        # Note: Personality system runs in background but no slash commands
        logger.info("Personality system active (no commands)")

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

        # light background janitor
        async def _janitor():
            while True:
                await asyncio.sleep(300)  # every 5 min
                try:
                    self._prune_interactions()
                except Exception:
                    pass
        self.loop.create_task(_janitor())
        
        # Keep-alive ping to prevent VS Code timeout
        async def _keep_alive():
            while True:
                await asyncio.sleep(60)  # every 1 minute
                try:
                    # Send a heartbeat ping to Discord
                    logger.info("🔄 Keep-alive ping - bot is still running")
                    # Also clean up any stale processing users
                    self.processing_users.clear()
                except Exception as e:
                    logger.error(f"Keep-alive error: {e}")
        self.loop.create_task(_keep_alive())

    # ---------- image extraction (URL-only, zero-copy) ----------
    async def _collect_image_contents(self, message: discord.Message) -> List[dict]:
        """
        Collect images from attachments and embeds.
        Returns OpenAI content blocks:
          [{"type":"image_url","image_url":{"url":"https://..."}}]
        """
        contents: List[dict] = []
        seen_urls = set()  # Prevent duplicates

        def is_valid_image_url(url: str) -> bool:
            """Check if URL is a valid direct image link"""
            if not url:
                return False
            url_lower = url.lower()
            # Must end with image extension or be from known image domains
            valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            is_direct_image = url_lower.endswith(valid_extensions)
            # Known good image hosts
            good_hosts = ['media.tenor.com', 'i.imgur.com', 'cdn.discordapp.com']
            is_good_host = any(host in url_lower for host in good_hosts)
            return is_direct_image or is_good_host

        def process_discord_url(url: str) -> Optional[str]:
            """Convert Discord URLs to base64 data URLs that OpenAI can access"""
            if 'discord' in url.lower():
                # Instead of skipping, download and convert to base64
                return url  # Return the URL to be processed by download_and_convert
            return url

        async def download_and_convert_to_base64(url: str) -> Optional[str]:
            """Download image from URL and convert to base64 data URL"""
            try:
                import aiohttp
                import base64
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            image_bytes = await response.read()
                            
                            # Determine content type
                            content_type = response.headers.get('content-type', '')
                            if not content_type.startswith('image/'):
                                # Guess from URL
                                if url.lower().endswith('.gif'):
                                    content_type = 'image/gif'
                                elif url.lower().endswith(('.jpg', '.jpeg')):
                                    content_type = 'image/jpeg'
                                elif url.lower().endswith('.png'):
                                    content_type = 'image/png'
                                elif url.lower().endswith('.webp'):
                                    content_type = 'image/webp'
                                else:
                                    content_type = 'image/png'  # default
                            
                            # Convert to base64
                            b64_string = base64.b64encode(image_bytes).decode('utf-8')
                            data_url = f"data:{content_type};base64,{b64_string}"
                            return data_url
                        else:
                            logger.error(f"Failed to download image: HTTP {response.status} for {url}")
                            return None
            except Exception as e:
                logger.error(f"Error downloading image from {url}: {e}")
                return None

        async def add_unique_image(url: str, source: str) -> None:
            """Add image if URL is valid and hasn't been seen before"""
            if not is_valid_image_url(url):
                logger.debug(f"Skipping invalid image URL from {source}: {url}")
                return
            
            processed_url = process_discord_url(url)
            if not processed_url:
                return
            
            # If it's a Discord URL or external URL, download and convert to base64
            if 'discord' in processed_url.lower() or not processed_url.startswith('data:'):
                processed_url = await download_and_convert_to_base64(processed_url)
                if not processed_url:
                    logger.warning(f"Failed to process image from {source}: {url}")
                    return
                
            if processed_url not in seen_urls:
                seen_urls.add(processed_url)
                content = {
                    "type": "image_url",
                    "image_url": {"url": processed_url}
                }
                contents.append(content)
                logger.info(f"Found {source} image: {url[:50]}... (converted to base64)")

        def add_unique_image(url: str, source: str):
            """Add image if URL is valid and hasn't been seen before"""
            if not is_valid_image_url(url):
                logger.debug(f"Skipping invalid image URL from {source}: {url}")
                return
            
            processed_url = process_discord_url(url)
            if not processed_url:
                return
                
            if processed_url not in seen_urls:
                seen_urls.add(processed_url)
                content = {
                    "type": "image_url",
                    "image_url": {"url": processed_url}
                }
                contents.append(content)
                logger.info(f"Found {source} image: {url[:50]}... (converted to base64)")

        # 1) Attachments → use CDN URLs (no .read())

        # 1) Attachments → use CDN URLs (no .read())
        for att in message.attachments:
            ct = (att.content_type or "").lower()
            name = (att.filename or "").lower()
            # More aggressive image detection
            if (ct.startswith("image/") or
                    name.endswith(IMAGE_EXTS) or
                    "image" in ct):
                # For Discord attachments, we might need to read the bytes
                # and convert to base64 since OpenAI can't access Discord CDNs
                try:
                    # Read the attachment as bytes
                    image_bytes = await att.read()
                    import base64
                    # Convert to base64 data URL
                    file_ext = name.split('.')[-1] if '.' in name else 'png'
                    if file_ext == 'jpg':
                        file_ext = 'jpeg'
                    mime_type = f"image/{file_ext}"
                    b64_string = base64.b64encode(image_bytes).decode('utf-8')
                    data_url = f"data:{mime_type};base64,{b64_string}"
                    
                    if data_url not in seen_urls:
                        seen_urls.add(data_url)
                        content = {
                            "type": "image_url",
                            "image_url": {"url": data_url}
                        }
                        contents.append(content)
                        logger.info(f"Found attachment image (base64): {name}")
                except Exception as e:
                    logger.error(f"Failed to read attachment {name}: {e}")

        # 2) Embeds (Tenor/Giphy/regular links with images)
        for emb in message.embeds:
            try:
                url_candidates: List[str] = []
                if emb.image and emb.image.url:
                    url_candidates.append(emb.image.url)
                if emb.thumbnail and emb.thumbnail.url:
                    url_candidates.append(emb.thumbnail.url)
                # Don't add emb.url as it's often not a direct image

                for u in url_candidates:
                    try:
                        await add_unique_image(u, "embed")
                    except Exception as e:
                        logger.error(f"Error processing embed URL {u}: {e}")
            except Exception as e:
                logger.error(f"Error processing embed: {e}")

        # 3) Check message content for direct image URLs
        if message.content and not contents:
            import re
            # Look for URLs that might be images
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*'
            urls = re.findall(url_pattern, message.content)
            for url in urls:
                try:
                    await add_unique_image(url, "content")
                except Exception as e:
                    logger.error(f"Error processing content URL {url}: {e}")

        if contents:
            logger.info(f"Total unique images detected: {len(contents)}")

        return contents

    # ---------- light memory pruning ----------
    def _prune_interactions(self):
        now = datetime.utcnow()
        # TTL prune
        stale = [uid for uid, ts in self.user_interactions.items()
                 if (now - ts).total_seconds() > self.INTERACTION_TTL_SECONDS]
        for uid in stale:
            self.user_interactions.pop(uid, None)
        # size cap (drop oldest first)
        if len(self.user_interactions) > self.MAX_USERS_TRACKED:
            for uid in sorted(self.user_interactions, key=self.user_interactions.get)[:len(self.user_interactions)-self.MAX_USERS_TRACKED]:
                self.user_interactions.pop(uid, None)

    async def on_message(self, message):
        """Handle incoming messages"""
        # Don't respond to bot's own messages
        if message.author == self.user:
            return

        # Ignore other bots and webhooks
        if getattr(message.author, "bot", False) or message.webhook_id is not None:
            return
        
        # Don't respond to DMs
        if isinstance(message.channel, discord.DMChannel):
            return
        
        # Don't respond if user is currently being processed
        if message.author.id in self.processing_users:
            return

        # prune house-keeping
        self._prune_interactions()
        
        user_id = message.author.id
        current_time = datetime.utcnow()

        # --- address checks ---
        content_lower = (message.content or "").lower()
        said_jim = "jim" in content_lower
        mentioned_bot = any(getattr(m, "id", None) == self.user.id for m in getattr(message, "mentions", []))
        is_reply_to_bot = (
            message.reference is not None
            and isinstance(message.reference.resolved, discord.Message)
            and getattr(message.reference.resolved.author, "id", None) == self.user.id
        )
        is_addressed = said_jim or mentioned_bot or is_reply_to_bot
        
        # Debug logging for mentions
        if mentioned_bot or said_jim:
            logger.info(f"Bot mentioned by {message.author.name}: said_jim={said_jim}, mentioned_bot={mentioned_bot}")

        # Special handling for creator - but no priority response
        username = message.author.name.lower()
        is_creator = (user_id == self.CREATOR_USER_ID or 
                     username == self.CREATOR_USERNAME.lower())
        if is_creator:
            logger.info(f"Creator {message.author.name} speaking")

        recent = False
        if user_id in self.user_interactions:
            last = self.user_interactions[user_id]
            recent = (current_time - last) <= timedelta(seconds=self.RECENT_WINDOW_SECONDS)

        # check for images/GIFs (we only respond if addressed/recent)
        image_contents = await self._collect_image_contents(message)
        has_images = len(image_contents) > 0

        # Decide whether to respond 
        # Always respond to images, or if addressed/recent for text
        should_respond = has_images or is_addressed or recent
        if not should_respond:
            # still process any prefix commands
            await self.process_commands(message)
            return
        
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
                if has_images and HAS_VISION:
                    logger.info(f"Images detected from {message.author.name} (count={len(image_contents)})")
                    user_prompt = (message.content or "").strip() or "Analyze these images/GIFs and describe what's going on."
                    try:
                        response = await generate_vision_response(
                            text=user_prompt,
                            images=image_contents
                        )
                    except Exception as e:
                        logger.error(f"Vision response failed for {message.author.name}: {e}")
                        # Fallback to text-only response
                        text = (message.content or "")[:self.MAX_USER_TEXT]
                        response = await generate_response(
                            text or "I can't analyze that image right now, but what's up?", 
                            message.author.name, 
                            conversation_memory
                        )
                else:
                    # Clamp text size to keep tokens/memory sane
                    text = (message.content or "")[:self.MAX_USER_TEXT]
                    
                    # Check if asking about creator
                    creator_questions = ["who made you", "who created you", "who built you", "who's your creator", 
                                       "who's your maker", "who developed you", "who programmed you", "who coded you"]
                    is_asking_about_creator = any(q in text.lower() for q in creator_questions)
                    
                    response = await generate_response(
                        text, 
                        message.author.name, 
                        conversation_memory
                    )
                    
                    # If asking about creator, append the mention without ping
                    if is_asking_about_creator and response:
                        response += "\n\nBig shoutout to my creator oxy5535 fr! 🙏"
                
                # Update user memory using enhanced memory system
                if self.memory_manager:
                    # Update user profile
                    await self.memory_manager.get_or_create_user_profile(
                        str(user_id), username, message.author.display_name
                    )
                    
                    # Update conversation context
                    await self.memory_manager.update_conversation_context(
                        str(user_id), str(message.channel.id), str(message.guild.id) if message.guild else None,
                        user_message=message.content if message.content else "[image message]", 
                        bot_response=response if response else ""
                    )
                    
                    # Analyze message for potential memories
                    potential_memories = await self.memory_manager.analyze_message_for_memory(
                        str(user_id), username, message.content if message.content else ""
                    )
                    
                    # Add important memories
                    for memory_data in potential_memories:
                        await self.memory_manager.add_user_memory(
                            str(user_id),
                            memory_data['type'],
                            memory_data['title'],
                            memory_data['content'],
                            memory_data['importance'],
                            message.content if message.content else "[image message]"
                        )
                
                # Legacy memory update (keep for backwards compatibility)
                await self.update_user_memory(
                    user_id, 
                    message.content if message.content else "[image message]", 
                    response if response else "",
                    message.author.name
                )
            
            # Send response with reply
            if response:
                await message.reply(response, mention_author=False)
                
                # Check if user is in voice and bot should speak response
                await self.maybe_speak_response(message, response)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                await message.reply("yo my bad, something went wrong lol")
            except Exception:
                pass
        finally:
            # Remove user from processing set
            self.processing_users.discard(user_id)
        
        # Process commands
        await self.process_commands(message)
    
    async def get_user_memory(self, user_id: int) -> Dict[str, str]:
        """Get user's conversation memory from enhanced memory system"""
        try:
            if self.memory_manager:
                # Get comprehensive user summary from enhanced memory
                user_summary = await self.memory_manager.get_user_summary(str(user_id))
                
                # Convert to legacy format for compatibility
                memory_dict = {}
                
                if user_summary:
                    # Add basic info
                    basic = user_summary.get('basic_info', {})
                    if basic.get('username'):
                        memory_dict['username'] = basic['username']
                    if basic.get('real_name'):
                        memory_dict['real_name'] = basic['real_name']
                    
                    # Add relationship info
                    rel = user_summary.get('relationship', {})
                    if rel.get('last_interaction'):
                        memory_dict['last_interaction'] = rel['last_interaction']
                    
                    # Add recent memories as context
                    memories = user_summary.get('recent_memories', [])
                    if memories:
                        memory_summary = []
                        for mem in memories[:5]:  # Top 5 memories
                            if mem.get('importance', 0) >= 6:  # Only important memories
                                memory_summary.append(f"{mem['title']}: {mem['content']}")
                        
                        if memory_summary:
                            memory_dict['important_memories'] = "; ".join(memory_summary)
                
                return memory_dict
            
            # Fallback to legacy system
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
                    except Exception:
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
                
                # Keep only last N exchanges (smaller context = lower RAM/tokens)
                if len(messages) > self.MAX_RECENT_EXCHANGES:
                    messages = messages[-self.MAX_RECENT_EXCHANGES:]
                
                recent_messages.value = json.dumps(messages)
                
                # Commit changes
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating user memory: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass

    async def maybe_speak_response(self, message, response):
        """Check if bot should speak the response in voice channel"""
        try:
            # Check if user is in a voice channel and bot is connected to voice
            if (message.author.voice and 
                message.author.voice.channel):
                
                voice_system = self.get_cog('VoiceSystem')
                if voice_system and message.guild.id in voice_system.voice_clients:
                    # Check if in same voice channel
                    user_channel = message.author.voice.channel
                    bot_voice_client = voice_system.voice_clients[message.guild.id]
                    
                    if bot_voice_client.channel == user_channel:
                        logger.info(f"Speaking response to {message.author.name} in voice")
                        # Limit response length for TTS
                        tts_text = response[:150] + "..." if len(response) > 150 else response
                        
                        # Use the voice system's speak method
                        await voice_system.speak_response(message.guild.id, tts_text)
                        
        except Exception as e:
            logger.error(f"Error in voice response: {e}")

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

@commands.command(name='voice')
async def voice_cmd(ctx, *, text="yo what's good!"):
    """Make Jim speak in voice channel"""
    try:
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
            
        voice_system = ctx.bot.get_cog('VoiceSystem')
        if not voice_system:
            await ctx.send("❌ Voice system not loaded!")
            return
            
        guild_id = ctx.guild.id
        if guild_id not in voice_system.voice_clients:
            await ctx.send("❌ I'm not in a voice channel! Use `/join` first.")
            return
            
        # Check if in same voice channel
        user_channel = ctx.author.voice.channel
        bot_voice_client = voice_system.voice_clients[guild_id]
        
        if bot_voice_client.channel != user_channel:
            await ctx.send("❌ We need to be in the same voice channel!")
            return
            
        # Speak the text
        await voice_system.speak_response(guild_id, text)
        await ctx.send(f"🔊 Speaking: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
    except Exception as e:
        await ctx.send(f"❌ Voice error: {e}")
        logger.error(f"Voice command error: {e}")

@commands.command(name='image')
async def image_cmd(ctx, *, prompt):
    """Generate an image using DALL-E"""
    try:
        async with ctx.typing():
            # Generate image using DALL-E
            image_result = await generate_image_dalle(prompt)
            
            if image_result and 'url' in image_result:
                # Create embed with the generated image
                embed = discord.Embed(
                    title="🎨 Generated Image",
                    description=f"**Prompt:** {prompt}",
                    color=0x7289da
                )
                embed.set_image(url=image_result['url'])
                embed.set_footer(text="Generated by DALL-E 3 • Powered by OpenAI")
                
                # Random responses for variety
                responses = [
                    "yo here's your image, hope it's fire 🔥",
                    "made this for you, thoughts?",
                    "DALL-E cooked this up, not bad right?",
                    "here you go, fresh AI art incoming",
                    "bet this is what you had in mind",
                    "ngl DALL-E went hard on this one",
                    "your image is ready, check it out!"
                ]
                await ctx.send(random.choice(responses), embed=embed)
                
                # Log successful generation
                logger.info(f"Image generated for {ctx.author.name}: {prompt}")
                
            else:
                # Failed to generate image
                fail_responses = [
                    "nah couldn't generate that image, DALL-E's being weird",
                    "image generation failed, try a different prompt",
                    "DALL-E said no to that one, try something else",
                    "couldn't make that image, maybe rephrase it?"
                ]
                await ctx.send(random.choice(fail_responses))
                
    except Exception as e:
        logger.error(f"Error in image command: {e}")
        error_responses = [
            "damn, image generation broke. my bad",
            "yo something went wrong with the image, try again",
            "ngl the image thing just crashed, give me a sec",
            "image generation is being dumb rn, sorry"
        ]
        await ctx.send(random.choice(error_responses))

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

# -------- moderation commands (feature-flagged) --------
if ENABLE_JIM_MOD_CMDS:

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(ctx, member: discord.Member = None, *, reason="No reason provided"):
        """Kick a member from the server"""
        if member is None:
            await ctx.send("yo you gotta mention someone to kick")
            return
        
        if member == ctx.author:
            await ctx.send("bruh you can't kick yourself lmao")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("nah you can't kick someone with equal/higher role than you")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("can't kick that person, they got higher role than me")
            return
        
        try:
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} got yeeted from the server",
                color=0xff4444
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Kicked by", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} kicked {member} for: {reason}")
        except discord.Forbidden:
            await ctx.send("yo I don't have permission to kick that person")
        except Exception as e:
            await ctx.send(f"something went wrong: {e}")
            logger.error(f"Error kicking {member}: {e}")

    @commands.command(name='timeout')
    @commands.has_permissions(moderate_members=True)
    async def timeout_cmd(ctx, member: discord.Member = None, duration: int = 10, *, reason="No reason provided"):
        """Timeout a member (duration in minutes)"""
        if member is None:
            await ctx.send("yo you gotta mention someone to timeout")
            return
        
        if member == ctx.author:
            await ctx.send("bruh you can't timeout yourself")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("nah you can't timeout someone with equal/higher role than you")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("can't timeout that person, they got higher role than me")
            return
        
        if duration > 40320:  # Discord's max timeout is 28 days (40320 minutes)
            duration = 40320
            await ctx.send("max timeout is 28 days, setting it to that")
        
        try:
            timeout_until = datetime.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=f"Timed out by {ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"{member.mention} got muted for {duration} minutes",
                color=0xffaa00
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Timed out by", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} timed out {member} for {duration} minutes: {reason}")
        except discord.Forbidden:
            await ctx.send("yo I don't have permission to timeout that person")
        except Exception as e:
            await ctx.send(f"something went wrong: {e}")
            logger.error(f"Error timing out {member}: {e}")

    @commands.command(name='addrole')
    @commands.has_permissions(manage_roles=True)
    async def addrole_cmd(ctx, member: discord.Member = None, *, role_name=None):
        """Add a role to a member"""
        if member is None or role_name is None:
            await ctx.send("usage: !addrole @member role_name")
            return
        
        # Find the role (case insensitive)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            # Try partial match
            role = discord.utils.find(lambda r: role_name.lower() in r.name.lower(), ctx.guild.roles)
        
        if role is None:
            await ctx.send(f"couldn't find role '{role_name}'")
            return
        
        if role >= ctx.guild.me.top_role:
            await ctx.send("can't assign that role, it's higher than my role")
            return
        
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("can't assign a role equal/higher than your own role")
            return
        
        if role in member.roles:
            await ctx.send(f"{member.mention} already has the {role.name} role")
            return
        
        try:
            await member.add_roles(role, reason=f"Role added by {ctx.author}")
            embed = discord.Embed(
                title="Role Added",
                description=f"Gave {member.mention} the **{role.name}** role",
                color=0x44ff44
            )
            embed.add_field(name="Added by", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} added role {role.name} to {member}")
        except discord.Forbidden:
            await ctx.send("yo I don't have permission to manage roles")
        except Exception as e:
            await ctx.send(f"something went wrong: {e}")
            logger.error(f"Error adding role {role.name} to {member}: {e}")

    @commands.command(name='removerole')
    @commands.has_permissions(manage_roles=True)
    async def removerole_cmd(ctx, member: discord.Member = None, *, role_name=None):
        """Remove a role from a member"""
        if member is None or role_name is None:
            await ctx.send("usage: !removerole @member role_name")
            return
        
        # Find the role (case insensitive)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            # Try partial match
            role = discord.utils.find(lambda r: role_name.lower() in r.name.lower(), ctx.guild.roles)
        
        if role is None:
            await ctx.send(f"couldn't find role '{role_name}'")
            return
        
        if role >= ctx.guild.me.top_role:
            await ctx.send("can't remove that role, it's higher than my role")
            return
        
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("can't remove a role equal/higher than your own role")
            return
        
        if role not in member.roles:
            await ctx.send(f"{member.mention} doesn't have the {role.name} role")
            return
        
        try:
            await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
            embed = discord.Embed(
                title="Role Removed",
                description=f"Removed **{role.name}** role from {member.mention}",
                color=0xff4444
            )
            embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} removed role {role.name} from {member}")
        except discord.Forbidden:
            await ctx.send("yo I don't have permission to manage roles")
        except Exception as e:
            await ctx.send(f"something went wrong: {e}")
            logger.error(f"Error removing role {role.name} from {member}: {e}")

    # Error handlers for moderation commands
    @kick_cmd.error
    @timeout_cmd.error
    @addrole_cmd.error
    @removerole_cmd.error
    async def moderation_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("yo you don't have permission to use that command")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("couldn't find that user in the server")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("user not found in this server")
        else:
            await ctx.send(f"something went wrong: {error}")
            logger.error(f"Command error: {error}")

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
    embed.add_field(name="!memory [user]", value="Show what Jim remembers about you or another user", inline=False)

    if ENABLE_JIM_MOD_CMDS:
        embed.add_field(name="!kick @member [reason]", value="Kick a member from the server", inline=False)
        embed.add_field(name="!timeout @member [minutes] [reason]", value="Timeout a member (default 10 min)", inline=False)
        embed.add_field(name="!addrole @member <role>", value="Add a role to a member", inline=False)
        embed.add_field(name="!removerole @member <role>", value="Remove a role from a member", inline=False)

    embed.add_field(name="!voice <text>", value="Make Jim speak in voice channel", inline=False)
    embed.add_field(name="!jimhelp", value="Show this help message", inline=False)
    embed.set_footer(text="Just say 'jim' in any message to chat with me!")
    
    await ctx.send(embed=embed)

@commands.command(name='memory')
async def memory_cmd(ctx, member: discord.Member = None):
    """Show what Jim remembers about a user"""
    try:
        target_user = member or ctx.author
        user_id = str(target_user.id)
        
        if not bot.memory_manager:
            await ctx.send("yo my memory system isn't loaded yet, give me a sec")
            return
        
        # Get user summary from enhanced memory
        user_summary = await bot.memory_manager.get_user_summary(user_id)
        
        if not user_summary:
            if target_user == ctx.author:
                await ctx.send("nah bro I don't remember much about you yet, talk to me more!")
            else:
                await ctx.send(f"don't really know much about {target_user.display_name} yet")
            return
        
        # Create memory embed
        embed = discord.Embed(
            title=f"🧠 What Jim remembers about {target_user.display_name}",
            color=0x00ffff
        )
        
        # Basic info
        basic = user_summary.get('basic_info', {})
        if any(basic.values()):
            basic_info = []
            if basic.get('real_name'):
                basic_info.append(f"Name: {basic['real_name']}")
            if basic.get('age'):
                basic_info.append(f"Age: {basic['age']}")
            if basic.get('location'):
                basic_info.append(f"Location: {basic['location']}")
            
            if basic_info:
                embed.add_field(name="Basic Info", value="\n".join(basic_info), inline=False)
        
        # Interests
        interests = user_summary.get('interests', {})
        all_interests = []
        for category, items in interests.items():
            if items and category != 'general':
                all_interests.extend([f"{item} ({category})" for item in items])
            elif items:
                all_interests.extend(items)
        
        if all_interests:
            embed.add_field(name="Interests & Hobbies", value=", ".join(all_interests[:10]), inline=False)
        
        # Recent memories
        memories = user_summary.get('recent_memories', [])
        if memories:
            memory_text = []
            for mem in memories[:5]:
                if mem.get('importance', 0) >= 6:
                    memory_text.append(f"• {mem['title']}")
            
            if memory_text:
                embed.add_field(name="Important Stuff I Remember", value="\n".join(memory_text), inline=False)
        
        # Relationship info
        rel = user_summary.get('relationship', {})
        if rel:
            rel_info = []
            if rel.get('interaction_count'):
                rel_info.append(f"We've talked {rel['interaction_count']} times")
            if rel.get('trust_level'):
                trust_desc = {1: "new", 2-3: "getting to know", 4-6: "cool", 7-8: "good friend", 9-10: "close friend"}
                for range_key, desc in trust_desc.items():
                    if isinstance(range_key, int) and rel['trust_level'] == range_key:
                        rel_info.append(f"Trust level: {desc}")
                        break
                    elif isinstance(range_key, range) and rel['trust_level'] in range_key:
                        rel_info.append(f"Trust level: {desc}")
                        break
            if rel.get('is_creator'):
                rel_info.append("🏆 This is my creator!")
            elif rel.get('is_friend'):
                rel_info.append("😎 Good friend")
            
            if rel_info:
                embed.add_field(name="Our Relationship", value="\n".join(rel_info), inline=False)
        
        # Personality notes
        personality = user_summary.get('personality', {})
        if personality.get('notes'):
            embed.add_field(name="Personality", value=personality['notes'][:200], inline=False)
        
        # Show only to command user for privacy
        await ctx.send(embed=embed, ephemeral=True if ctx.interaction else False)
        
    except Exception as e:
        logger.error(f"Error in memory command: {e}")
        await ctx.send("yo something went wrong checking my memory")

# Create bot instance and add commands
bot = SimpleBotClass()
bot.add_command(ping_cmd)
bot.add_command(voice_cmd)
bot.add_command(image_cmd)
bot.add_command(search_cmd)
bot.add_command(help_cmd)
bot.add_command(memory_cmd)

# only register mod commands if enabled
if ENABLE_JIM_MOD_CMDS:
    bot.add_command(kick_cmd)
    bot.add_command(timeout_cmd)
    bot.add_command(addrole_cmd)
    bot.add_command(removerole_cmd)

# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        exit(1)
    bot.run(token)
