"""
🎤 JimBot Voice Test Guide

The FFmpeg issue has been fixed! Here's how to test Jim's voice features:

## Quick Test Steps:
1. Join a voice channel in your Discord server
2. Type `/join` in any text channel - Jim will join your voice channel
3. Type `!voice hello everyone!` - Jim should speak in voice
4. Type any message with "jim" in it - Jim will respond in both text and voice

## Available Voice Commands:
- `!voice <text>` - Make Jim speak any text
- `/speak <text> [voice]` - Slash command with voice options
- `/join` - Join your voice channel  
- `/leave` - Leave voice channel
- `/chat_mode` - Toggle auto-voice responses

## Voice Options (use with /speak):
- nova (default) - Female, bright and energetic
- onyx - Male, deep and authoritative
- echo - Male, clear and professional  
- fable - Female, warm and engaging
- shimmer - Female, soft and calming
- alloy - Balanced and neutral

## Examples:
- `/speak Hello everyone! voice:onyx`
- `!voice yo what's up!`
- "hey jim, how are you doing?" (auto voice response)

## Troubleshooting:
- Make sure you're in the same voice channel as Jim
- Check that Jim has connected successfully with `/join`
- Use `!voice test` to verify voice is working

The bot is currently running with voice support enabled!
"""

print(__doc__)
