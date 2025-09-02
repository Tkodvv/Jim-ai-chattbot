import discord
from discord.ext import commands
from discord import app_commands
import logging
from personality_manager import personality_manager, PersonalityPreset

logger = logging.getLogger(__name__)


class PersonalitySlashCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="personality", description="View Jim's current personality settings")
    async def personality_slash(self, interaction: discord.Interaction):
        """View current personality settings"""
        description = personality_manager.get_personality_description()
        embed = discord.Embed(
            title="🎭 Jim's Personality Settings",
            description=description,
            color=0x00ff00
        )
        embed.add_field(
            name="💡 Commands",
            value=("`/personality_preset <name>` - Change preset\n"
                   "`/personality_set <trait> <value>` - Adjust trait (0-10)\n"
                   "`/personality_presets` - List all presets\n\n"
                   "**Trait Categories:**\n"
                   "🔥 Core: Aggression, Sarcasm, Energy, Profanity\n"
                   "❤️ Social: Helpfulness, Humor, Empathy, Roasting\n"
                   "💬 Communication: Formality, Emoji, Slang\n"
                   "🧠 Behavioral: Attention, Mood, Respect"),
            inline=False
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="personality_preset", description="Change Jim's personality preset")
    @app_commands.describe(preset="Choose a personality preset")
    @app_commands.choices(preset=[
        app_commands.Choice(name="Chill 😎 - Laid-back and peaceful", value="chill"),
        app_commands.Choice(name="Aggressive 🔥 - Confrontational and savage", value="aggressive"),
        app_commands.Choice(name="Wholesome 😇 - Family-friendly and helpful", value="wholesome"),
        app_commands.Choice(name="Sarcastic 😏 - Witty and sarcastic", value="sarcastic"),
        app_commands.Choice(name="Hyped ⚡ - High energy and excited", value="hyped"),
        app_commands.Choice(name="Professional 👔 - Formal and focused", value="professional"),
        app_commands.Choice(name="Gamer 🎮 - Gaming slang and competitive", value="gamer"),
        app_commands.Choice(name="Gen Z 🔥 - Short, snappy, no cap fr", value="genz"),
        app_commands.Choice(name="Helpful 🤝 - Serious answers, focused on helping", value="helpful"),
    ])
    async def personality_preset_slash(self, interaction: discord.Interaction, preset: str):
        """Change personality preset"""
        try:
            preset_enum = PersonalityPreset(preset.lower())
            personality_manager.apply_preset(preset_enum)
            
            embed = discord.Embed(
                title="✅ Personality Updated!",
                description=f"Applied **{preset_enum.value.title()}** preset",
                color=0x00ff00
            )
            embed.add_field(
                name="New Settings",
                value=personality_manager.get_personality_description(),
                inline=False
            )
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid preset selected.", ephemeral=True)
    
    @app_commands.command(name="personality_presets", description="List all available personality presets")
    async def personality_presets_slash(self, interaction: discord.Interaction):
        """List all available personality presets"""
        embed = discord.Embed(
            title="🎭 Available Personality Presets",
            color=0x0099ff
        )
        
        presets_info = {
            'Chill 😎': 'Laid-back, peaceful, low energy',
            'Aggressive 🔥': 'Confrontational, high aggression, savage',
            'Wholesome 😇': 'Family-friendly, helpful, empathetic',
            'Sarcastic 😏': 'Witty, sarcastic, roasting master',
            'Hyped ⚡': 'High energy, excited, lots of emojis',
            'Professional 👔': 'Formal, clean language, focused',
            'Gamer 🎮': 'Gaming slang, competitive, casual',
            'Gen Z 🔥': 'Short, snappy, slang heavy, no cap fr'
        }
        
        for preset, desc in presets_info.items():
            embed.add_field(name=preset, value=desc, inline=True)
        
        embed.add_field(
            name="Usage",
            value="Use `/personality_preset` to apply a preset",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="personality_set", description="Set a specific personality trait")
    @app_commands.describe(
        trait="Choose a personality trait to adjust",
        value="Set the trait value (0-10 scale)"
    )
    @app_commands.choices(trait=[
        # 🔥 Core Personality
        app_commands.Choice(name="🔥 Aggression", value="aggression"),
        app_commands.Choice(name="😏 Sarcasm", value="sarcasm"),
        app_commands.Choice(name="⚡ Energy", value="energy"),
        app_commands.Choice(name="🤬 Profanity", value="profanity"),
        
        # ❤️ Social Traits
        app_commands.Choice(name="🤝 Helpfulness", value="helpfulness"),
        app_commands.Choice(name="😂 Humor", value="humor"),
        app_commands.Choice(name="💗 Empathy", value="empathy"),
        app_commands.Choice(name="🔥 Roasting", value="roasting"),
        
        # 💬 Communication Style
        app_commands.Choice(name="👔 Formality", value="formality"),
        app_commands.Choice(name="😀 Emoji Usage", value="emoji_usage"),
        app_commands.Choice(name="🗣️ Slang Usage", value="slang_usage"),
        
        # 🧠 Behavioral Traits
        app_commands.Choice(name="🎯 Attention Span", value="attention_span"),
        app_commands.Choice(name="😌 Mood Stability", value="mood_stability"),
        app_commands.Choice(name="🙏 Respect Level", value="respect_level"),
    ])
    async def personality_set_slash(self, interaction: discord.Interaction, trait: str, value: int):
        """Set a specific personality trait (0-10)"""
        if not (0 <= value <= 10):
            await interaction.response.send_message("❌ Value must be between 0 and 10", ephemeral=True)
            return
        
        if personality_manager.update_trait(trait.lower(), value):
            embed = discord.Embed(
                title="✅ Trait Updated!",
                description=f"Set **{trait.replace('_', ' ').title()}** to **{value}/10**",
                color=0x00ff00
            )
            embed.add_field(
                name="Current Personality",
                value=personality_manager.get_personality_description(),
                inline=False
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ Invalid trait name: `{trait}`", ephemeral=True)
    
    @app_commands.command(name="personality_reset", description="Reset Jim's personality to default settings")
    async def personality_reset_slash(self, interaction: discord.Interaction):
        """Reset to default personality"""
        personality_manager.apply_preset(PersonalityPreset.CUSTOM)
        embed = discord.Embed(
            title="🔄 Personality Reset",
            description="Reset to default settings",
            color=0xffaa00
        )
        embed.add_field(
            name="Current Settings",
            value=personality_manager.get_personality_description(),
            inline=False
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PersonalitySlashCog(bot))
