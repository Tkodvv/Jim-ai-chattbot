import os
import asyncio
import logging
import random
import base64
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional
import discord
from discord.ext import commands
from dotenv import load_dotenv
from models import db, Conversation
from openai_client import generate_response, generate_image_dalle, search_google

# try optional vision helper; we'll fall back if it's not implemented yet
try:
    from openai_client import generate_vision_response  # async (text:str, images:list[dict]) -> str
    HAS_VISION = True
except Exception:
    HAS_VISION = False

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- helpers for image detection/packing ----
IMAGE_MIME_PREFIXES = ("image/",)
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")

def _guess_mime_from_name(name: str) -> str:
    low = name.lower()
    if low.endswith(".png"): return "image/png"
    if low.endswith(".jpg") or low.endswith(".jpeg"): return "image/jpeg"
    if low.endswith(".webp"): return "image/webp"
    if low.endswith(".gif"): return "image/gif"
    if low.endswith(".bmp"): return "image/bmp"
    return "application/octet-stream"

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

    # ---------- new: image extraction ----------
    async def _collect_image_contents(self, message: discord.Message) -> List[dict]:
        """
        Collect images from attachments and embeds.
        Returns a list of OpenAI 'content' blocks: [{"type":"image_url","image_url": "..."}]
        For attachments we send data URLs (base64). For embeds we pass the remote URL directly.
        """
        contents: List[dict] = []

        # 1) Attachments
        for att in message.attachments:
            # Some bots/users upload non-images; filter
            ct = att.content_type or _guess_mime_from_name(att.filename or "")
            if ct.startswith(IMAGE_MIME_PREFIXES):
                try:
                    data = await att.read()
                    # Build data URL; default to filename-based mime when content_type missing
                    mime = ct if ct.startswith("image/") else _guess_mime_from_name(att.filename or "")
                    b64 = base64.b64encode(data).decode("utf-8")
                    contents.append({
                        "type": "image_url",
                        "image_url": f"data:{mime};base64,{b64}"
                    })
                except Exception as e:
                    logger.warning(f"Failed reading attachment {att.filename}: {e}")

        # 2) Embeds (Tenor/Giphy/regular links with images)
        for emb in message.embeds:
            try:
                url_candidates: List[str] = []
                if emb.image and emb.image.url:
                    url_candidates.append(emb.image.url)
                if emb.thumbnail and emb.thumbnail.url:
                    url_candidates.append(emb.thumbnail.url)
                if emb.url:
                    url_candidates.append(emb.url)

                for url in url_candidates:
                    u = str(url)
                    if any(u.lower().endswith(ext) for ext in IMAGE_EXTS):
                        contents.append({"type": "image_url", "image_url": u})
            except Exception:
                pass

        return contents

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

        # NEW: check for images/GIFs
        image_contents = await self._collect_image_contents(message)
        has_images = len(image_contents) > 0
        
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

        # If images present, respond even without mention/recent chat
        if has_images:
            should_respond = True
            logger.info(f"Images detected from {message.author.name} (count={len(image_contents)})")
        
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
                    if has_images and HAS_VISION:
                        # Prefer explicit user prompt if present; otherwise a default analysis request
                        user_prompt = message.content.strip() or "Analyze these images/GIFs and describe what's going on."
                        response = await generate_vision_response(
                            text=user_prompt,
                            images=image_contents  # list of {"type":"image_url","image_url": ...}
                        )
                    else:
                        # Fallback to text-only
                        response = await generate_response(
                            message.content, 
                            message.author.name, 
                            conversation_memory
                        )
                    
                    # Update user memory
                    await self.update_user_memory(
                        user_id, 
                        message.content if message.content else "[image message]", 
                        response if response else "",
                        message.author.name
                    )
                
                # Send response with reply
                if response:
                    await message.reply(response, mention_author=False)
                    
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

# NEW MODERATION COMMANDS
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
    embed.add_field(name="!kick @member [reason]", value="Kick a member from the server", inline=False)
    embed.add_field(name="!timeout @member [minutes] [reason]", value="Timeout a member (default 10 min)", inline=False)
    embed.add_field(name="!addrole @member <role>", value="Add a role to a member", inline=False)
    embed.add_field(name="!removerole @member <role>", value="Remove a role from a member", inline=False)
    embed.add_field(name="!jimhelp", value="Show this help message", inline=False)
    embed.set_footer(text="Just say 'jim' in any message to chat with me!")
    
    await ctx.send(embed=embed)

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

# Create bot instance and add commands
bot = SimpleBotClass()
bot.add_command(ping_cmd)
bot.add_command(image_cmd)
bot.add_command(search_cmd)
bot.add_command(kick_cmd)
bot.add_command(timeout_cmd)
bot.add_command(addrole_cmd)
bot.add_command(removerole_cmd)
bot.add_command(help_cmd)
