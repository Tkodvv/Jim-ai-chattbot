import discord
from discord.ext import commands
import logging
from personality_manager import personality_manager, PersonalityPreset

logger = logging.getLogger(__name__)

class PersonalityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name='personality', aliases=['p'], invoke_without_command=True)
    async def personality(self, ctx):
        """View current personality settings"""
        description = personality_manager.get_personality_description()
        embed = discord.Embed(
            title="🎭 Jim's Personality Settings",
            description=description,
            color=0x00ff00
        )
        embed.add_field(
            name="💡 Commands",
            value="`!p preset <name>` - Change preset\n`!p set <trait> <value>` - Adjust trait\n`!p presets` - List all presets",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @personality.command(name='preset')
    async def set_preset(self, ctx, preset_name: str = None):
        """Change personality preset"""
        if not preset_name:
            await ctx.send("❌ Please specify a preset name. Use `!p presets` to see available options.")
            return
        
        try:
            preset = PersonalityPreset(preset_name.lower())
            personality_manager.apply_preset(preset)
            
            embed = discord.Embed(
                title="✅ Personality Updated!",
                description=f"Applied **{preset.value.title()}** preset",
                color=0x00ff00
            )
            embed.add_field(
                name="New Settings",
                value=personality_manager.get_personality_description(),
                inline=False
            )
            await ctx.send(embed=embed)
            
        except ValueError:
            valid_presets = [p.value for p in PersonalityPreset]
            await ctx.send(f"❌ Invalid preset. Valid options: {', '.join(valid_presets)}")
    
    @personality.command(name='presets')
    async def list_presets(self, ctx):
        """List all available personality presets"""
        embed = discord.Embed(
            title="🎭 Available Personality Presets",
            color=0x0099ff
        )
        
        presets_info = {
            'chill': '😎 Laid-back, peaceful, low energy',
            'aggressive': '🔥 Confrontational, high aggression, savage',
            'wholesome': '😇 Family-friendly, helpful, empathetic',
            'sarcastic': '😏 Witty, sarcastic, roasting master',
            'hyped': '⚡ High energy, excited, lots of emojis',
            'professional': '👔 Formal, clean language, focused',
            'gamer': '🎮 Gaming slang, competitive, casual'
        }
        
        for preset, desc in presets_info.items():
            embed.add_field(name=preset.title(), value=desc, inline=True)
        
        embed.add_field(
            name="Usage",
            value="`!p preset <name>` to apply a preset",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @personality.command(name='set')
    async def set_trait(self, ctx, trait: str = None, value: int = None):
        """Set a specific personality trait (0-10)"""
        if not trait or value is None:
            traits_list = [
                "aggression", "sarcasm", "energy", "profanity",
                "helpfulness", "humor", "empathy", "roasting",
                "formality", "emoji_usage", "slang_usage",
                "attention_span", "mood_stability", "respect_level"
            ]
            embed = discord.Embed(
                title="🎛️ Personality Traits",
                description="Use `!p set <trait> <value>` where value is 0-10",
                color=0x0099ff
            )
            embed.add_field(
                name="Available Traits",
                value="\n".join([f"• {trait}" for trait in traits_list]),
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        if not (0 <= value <= 10):
            await ctx.send("❌ Value must be between 0 and 10")
            return
        
        if personality_manager.update_trait(trait.lower(), value):
            embed = discord.Embed(
                title="✅ Trait Updated!",
                description=f"Set **{trait}** to **{value}/10**",
                color=0x00ff00
            )
            embed.add_field(
                name="Current Personality",
                value=personality_manager.get_personality_description(),
                inline=False
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Invalid trait name: `{trait}`")
    
    @personality.command(name='reset')
    async def reset_personality(self, ctx):
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
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PersonalityCog(bot))
