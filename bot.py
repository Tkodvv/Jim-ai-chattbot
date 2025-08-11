from dotenv import load_dotenv
load_dotenv()
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Set
import discord
from discord.ext import commands
from discord import app_commands
from memory_manager import DatabaseManager  # Switched from Postgres to JSON
import os

# NEW: LangChain embeddings setup
from langchain.embeddings import OpenAIEmbeddings
from vector_store import search_similar_texts, add_text_to_vector_store

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    dimensions=1536  # optional for 3-small; remove if using ada-002
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = DatabaseManager()  # JSON memory manager

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(command_prefix='!', intents=intents)

        self.user_interactions: Dict[int, datetime] = {}
        self.processing_users: Set[int] = set()

    async def setup_hook(self):
        try:
            # Load slash command cogs
            await self.load_extension("slash_commands")

            # Global sync
            await self.tree.sync()
            logger.info("✅ Slash commands globally synced.")

            # Also sync to test guild
            await self.tree.sync(guild=discord.Object(id=556006991001288704))
            logger.info("✅ Slash commands also synced to test guild.")
        except Exception as e:
            logger.error(f"❌ Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')

    async def on_message(self, message):
        if message.author == self.user or isinstance(message.channel, discord.DMChannel):
            return

        if message.author.id in self.processing_users:
            return

        should_respond = False
        if "jim" in message.content.lower():
            should_respond = True

        user_id = message.author.id
        current_time = datetime.utcnow()

        if user_id in self.user_interactions:
            last_interaction = self.user_interactions[user_id]
            if current_time - last_interaction <= timedelta(seconds=60):
                should_respond = True

        if should_respond:
            self.processing_users.add(user_id)
            try:
                self.user_interactions[user_id] = current_time
                async with message.channel.typing():
                    import random
                    await asyncio.sleep(random.uniform(1.0, 3.0))

                    conversation_memory = memory.get_user_memory(str(user_id))

                    # NEW: Search for similar past messages
                    try:
                        vector_contexts = search_similar_texts(message.content, k=3)
                        context = "\n".join(vector_contexts)
                    except Exception as e:
                        logger.warning(f"Vector search failed or missing index: {e}")
                        context = ""

                    from openai_client import generate_response
                    response = await generate_response(
                        message.content, message.author.name, context
                    )

                    memory.update_user_memory(str(user_id), "last_message", message.content)
                    memory.update_user_memory(str(user_id), "last_response", response)

                    # NEW: Add to vector memory too
                    try:
                        add_text_to_vector_store([message.content])
                    except Exception as e:
                        logger.warning(f"Failed to add message to vector store: {e}")

                if response:
                    await message.reply(response, mention_author=False)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.channel.send("yo my bad, something went wrong lol")
            finally:
                self.processing_users.discard(user_id)

        await self.process_commands(message)

    @commands.command(name='ping')
    async def ping(self, ctx):
        import random
        responses = [
            "yo what's good! 🔥",
            "pong, bitch! still alive",
            "sup, you need something or just checking?",
            "yeah I'm here, what's up",
            "pong! ready to vibe or roast, your choice"
        ]
        await ctx.send(random.choice(responses))

    @commands.command(name='say')
    async def say(self, ctx, *, message):
        if ctx.author.id != 364263559263158274:
            await ctx.send("nah, you ain't got the clearance for that")
            return
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(name="syncslash")
    async def syncslash(self, ctx):
        if ctx.author.id != 364263559263158274:
            await ctx.send("nah, you ain't got the clearance for that")
            return
        synced = await self.tree.sync(guild=discord.Object(id=556006991001288704))
        await ctx.send(f"Slash commands manually synced: {[cmd.name for cmd in synced]}")

if __name__ == '__main__':
    bot = DiscordBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not found in .env file")
    bot.run(token)
