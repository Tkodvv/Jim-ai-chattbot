import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiohttp
import io
import os
import tempfile
import logging
from typing import Optional
from openai import AsyncOpenAI
from openai_client import generate_response

logger = logging.getLogger(__name__)

class VoiceRecorder:
    """Simple voice recorder for Discord voice channels"""
    def __init__(self, voice_system):
        self.voice_system = voice_system
        self.recording = False
        self.audio_buffer = []
        
    def start_recording(self):
        self.recording = True
        self.audio_buffer = []
        
    def stop_recording(self):
        self.recording = False
        return b''.join(self.audio_buffer)
        
    def write(self, data):
        if self.recording:
            self.audio_buffer.append(data)

class VoiceSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.voice_clients = {}  # guild_id -> voice_client
        self.listening_channels = {}  # guild_id -> channel_id where bot is listening
        self.conversation_mode = {}  # guild_id -> bool (natural conversation mode)
        self.voice_activity = {}  # guild_id -> last activity timestamp
        
        # TTS Voice options
        self.tts_voices = {
            'alloy': 'Balanced and neutral',
            'echo': 'Male, clear and professional', 
            'fable': 'Female, warm and engaging',
            'onyx': 'Male, deep and authoritative',
            'nova': 'Female, bright and energetic',
            'shimmer': 'Female, soft and calming'
        }
        
    async def generate_speech(self, text: str, voice: str = "nova") -> bytes:
        """Generate speech using OpenAI TTS API"""
        try:
            response = await self.openai_client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=voice,
                input=text,
                speed=1.0
            )
            return response.content
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            raise

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            with open(temp_file_path, "rb") as audio_file:
                response = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            os.unlink(temp_file_path)
            return response.text
            
        except Exception as e:
            logger.error(f"Speech transcription error: {e}")
            raise

    async def handle_voice_conversation(self, user, transcribed_text, guild_id):
        """Handle natural voice conversation"""
        try:
            # Get user memory for context
            user_memory = await self.bot.get_user_memory(user.id)
            
            # Generate response using the same system as text chat
            response = await generate_response(
                transcribed_text, 
                user.display_name, 
                user_memory
            )
            
            # Update user memory
            await self.bot.update_user_memory(
                user.id,
                transcribed_text,
                response,
                user.display_name
            )
            
            if response:
                # Send to text channel only (silent mode - no TTS response)
                if guild_id in self.listening_channels:
                    channel = self.bot.get_channel(self.listening_channels[guild_id])
                    if channel:
                        embed = discord.Embed(
                            title="🎤 Voice Conversation (Silent)",
                            color=0x00ffff
                        )
                        embed.add_field(name=f"{user.display_name} said:", value=transcribed_text, inline=False)
                        embed.add_field(name="Jim replied:", value=response, inline=False)
                        await channel.send(embed=embed)
                        
        except Exception as e:
            logger.error(f"Error in voice conversation: {e}")

    async def speak_response(self, guild_id, text, voice="nova"):
        """Speak a response in the voice channel"""
        try:
            if guild_id not in self.voice_clients:
                return
                
            # Limit text length for TTS
            tts_text = text[:300] + "..." if len(text) > 300 else text
            
            # Generate speech
            audio_data = await self.generate_speech(tts_text, voice)
            
            # Use FFmpeg path from environment or fallback to system path
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
            
            # Create audio source with specific FFmpeg path
            audio_source = discord.FFmpegPCMAudio(
                io.BytesIO(audio_data),
                pipe=True,
                before_options='-f mp3',
                executable=ffmpeg_path
            )
            
            voice_client = self.voice_clients[guild_id]
            
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)  # Brief pause
                
            voice_client.play(audio_source)
            
        except Exception as e:
            logger.error(f"Error speaking response: {e}")

    @app_commands.command(name="join", description="Join your voice channel")
    async def join_voice(self, interaction: discord.Interaction):
        """Join the user's voice channel"""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        
        try:
            if interaction.guild.id in self.voice_clients:
                await self.voice_clients[interaction.guild.id].disconnect()
                
            voice_client = await channel.connect()
            self.voice_clients[interaction.guild.id] = voice_client
            
            embed = discord.Embed(
                title="🎤 Voice Connected",
                description=f"Successfully joined **{channel.name}**",
                color=0x00ff00
            )
            embed.add_field(name="Available Commands", value="`/speak`, `/chat_mode`, `/listen`, `/voice_help`, `/leave`", inline=False)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to join voice channel: {str(e)}", ephemeral=True)

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave_voice(self, interaction: discord.Interaction):
        """Leave the voice channel"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
            return
            
        try:
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
            
            if guild_id in self.listening_channels:
                del self.listening_channels[guild_id]
                
            embed = discord.Embed(
                title="👋 Voice Disconnected",
                description="Successfully left the voice channel",
                color=0xff9900
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error leaving voice channel: {str(e)}", ephemeral=True)

    @app_commands.command(name="chat_mode", description="Toggle natural voice conversation mode")
    async def toggle_chat_mode(self, interaction: discord.Interaction):
        """Toggle natural conversation mode where Jim listens and responds to voice naturally"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ I need to be in a voice channel! Use `/join` first.", ephemeral=True)
            return
            
        # Toggle conversation mode
        if guild_id in self.conversation_mode and self.conversation_mode[guild_id]:
            # Turn off chat mode
            self.conversation_mode[guild_id] = False
            if guild_id in self.listening_channels:
                del self.listening_channels[guild_id]
                
            embed = discord.Embed(
                title="💬 Chat Mode OFF",
                description="Natural voice conversation disabled",
                color=0xff4444
            )
            embed.add_field(name="Status", value="Jim will no longer automatically respond to voice", inline=False)
        else:
            # Turn on chat mode
            self.conversation_mode[guild_id] = True
            self.listening_channels[guild_id] = interaction.channel_id
            
            embed = discord.Embed(
                title="🗣️ Chat Mode ON (Silent)",
                description="Natural voice conversation enabled - text responses only!",
                color=0x00ff00
            )
            embed.add_field(
                name="How it works", 
                value="• Say 'Jim' or 'Hey Jim' to get his attention\n• He'll listen and respond in text only\n• No voice responses - silent mode\n• Say 'stop listening' to pause", 
                inline=False
            )
            embed.add_field(
                name="Pro Tips", 
                value="• Speak clearly for best recognition\n• Jim responds in text, not voice\n• He remembers your conversation context", 
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="speak", description="Make Jim speak text in voice channel")
    @app_commands.describe(
        text="Text for Jim to speak",
        voice="Voice style to use"
    )
    async def speak_text(self, interaction: discord.Interaction, text: str, 
                        voice: Optional[str] = "nova"):
        """Text-to-speech in voice channel"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ I need to be in a voice channel! Use `/join` first.", ephemeral=True)
            return
            
        if voice not in self.tts_voices:
            voice = "nova"
            
        await interaction.response.defer()
        
        try:
            # Generate speech
            audio_data = await self.generate_speech(text, voice)
            
            # Use FFmpeg path from environment or fallback to system path
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
            
            # Create audio source with specific FFmpeg path
            audio_source = discord.FFmpegPCMAudio(
                io.BytesIO(audio_data),
                pipe=True,
                before_options='-f mp3',
                executable=ffmpeg_path
            )
            
            voice_client = self.voice_clients[guild_id]
            
            if voice_client.is_playing():
                voice_client.stop()
                
            voice_client.play(audio_source)
            
            embed = discord.Embed(
                title="🔊 Speaking",
                description=f"**Text:** {text[:100]}{'...' if len(text) > 100 else ''}",
                color=0x00ffff
            )
            embed.add_field(name="Voice", value=f"{voice} - {self.tts_voices[voice]}", inline=True)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            await interaction.followup.send(f"❌ Failed to generate speech: {str(e)}", ephemeral=True)

    @app_commands.command(name="listen", description="Start/stop listening for voice commands")
    async def toggle_listening(self, interaction: discord.Interaction):
        """Toggle voice listening mode"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ I need to be in a voice channel! Use `/join` first.", ephemeral=True)
            return
            
        if guild_id in self.listening_channels:
            # Stop listening
            del self.listening_channels[guild_id]
            embed = discord.Embed(
                title="🔇 Stopped Listening",
                description="Voice command listening disabled",
                color=0xff0000
            )
        else:
            # Start listening
            self.listening_channels[guild_id] = interaction.channel_id
            embed = discord.Embed(
                title="🎤 Now Listening (Silent Mode)",
                description="Speak in voice chat and I'll transcribe and respond in text only!\nSay 'stop listening' to disable.",
                color=0x00ff00
            )
            embed.add_field(name="How it works", value="I'll listen to voice, transcribe it, and respond only in text (no voice)", inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="voice_help", description="Show voice commands and features")
    async def voice_help(self, interaction: discord.Interaction):
        """Show voice system help"""
        embed = discord.Embed(
            title="🎤 Jim's Voice System Help",
            description="Advanced voice features powered by OpenAI",
            color=0x7289da
        )
        
        embed.add_field(
            name="🔗 Connection Commands",
            value="`/join` - Join your voice channel\n`/leave` - Leave voice channel",
            inline=False
        )
        
        embed.add_field(
            name="�️ Conversation Commands",
            value="`/chat_mode` - Toggle natural voice chat\n`/speak <text> [voice]` - Text-to-speech\n`/listen` - Toggle voice transcription", 
            inline=False
        )
        
        voice_list = "\n".join([f"`{voice}` - {desc}" for voice, desc in self.tts_voices.items()])
        embed.add_field(
            name="🎭 Available Voices",
            value=voice_list,
            inline=False
        )
        
        embed.add_field(
            name="✨ Chat Mode Features",
            value="• Say 'Jim' or 'Hey Jim' to start talking\n• Natural conversation flow\n• Remembers context\n• Responds in voice automatically\n• High-quality AI voice responses",
            inline=False
        )
        
        embed.set_footer(text="Powered by OpenAI TTS-1-HD and Whisper models")
        await interaction.response.send_message(embed=embed)

    # Auto-complete for voice parameter
    @speak_text.autocomplete('voice')
    async def voice_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for voice selection"""
        return [
            app_commands.Choice(name=f"{voice} - {desc}", value=voice)
            for voice, desc in self.tts_voices.items()
            if current.lower() in voice.lower() or current.lower() in desc.lower()
        ][:25]

    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates - simulate voice conversation triggers"""
        # Note: Discord.py doesn't support direct voice recording due to Discord API limitations
        # This is a placeholder for voice activity detection
        pass

    @app_commands.command(name="voice_test", description="Test voice conversation (simulates hearing 'Hey Jim')")
    async def test_voice_conversation(self, interaction: discord.Interaction, message: str = "Hey Jim, how are you?"):
        """Test the voice conversation system"""
        guild_id = interaction.guild.id
        
        if guild_id not in self.voice_clients:
            await interaction.response.send_message("❌ I need to be in a voice channel! Use `/join` first.", ephemeral=True)
            return
            
        if guild_id not in self.conversation_mode or not self.conversation_mode[guild_id]:
            await interaction.response.send_message("❌ Chat mode is not enabled! Use `/chat_mode` first.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Simulate hearing the message
            await self.handle_voice_conversation(interaction.user, message, guild_id)
            
            embed = discord.Embed(
                title="🎤 Voice Test Complete",
                description=f"Simulated hearing: '{message}'",
                color=0x00ffff
            )
            embed.add_field(name="Note", value="This simulates what would happen when someone says this in voice chat", inline=False)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Test failed: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceSystem(bot))
