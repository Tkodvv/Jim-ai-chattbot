import discord
from discord.ext import commands
from discord import app_commands
from memory_manager import DatabaseManager

memory = DatabaseManager()

class SlashCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Get info about a user")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(title="User Info", color=0x00ffcc)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="Username", value=str(user), inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Joined Discord", value=user.created_at.strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="Joined Server", value=user.joined_at.strftime('%Y-%m-%d') if user.joined_at else "N/A", inline=True)
        embed.set_footer(text="JimBot appreciates your existence fr")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Make Jim say something (only for Oxbir)")
    async def say_slash(self, interaction: discord.Interaction, message: str):
        if interaction.user.id != 364263559263158274:
            await interaction.response.send_message("nah, you ain't got the clearance for that", ephemeral=True)
            return
        await interaction.response.send_message(message)

    @app_commands.command(name="history", description="Get your recent memory")
    async def history(self, interaction: discord.Interaction):
        if str(interaction.user.id) != "364263559263158274":
            await interaction.response.send_message("nah bruh this command ain't for you", ephemeral=True)
            return

        mem = memory.get_user_memory(str(interaction.user.id))
        if not mem:
            await interaction.response.send_message("no memory found bruh")
            return

        msg = "**Memory:**\n"
        for k, v in mem.items():
            msg += f"`{k}`: {v['value']}\n"

        await interaction.response.send_message(msg[:2000])

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashCommands(bot))
