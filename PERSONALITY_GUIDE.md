"""
🎭 JimBot Tweakable Personality System Demo

This shows how you can customize Jim's personality on the fly!

## Available Commands:

### Basic Usage:
!p                     - View current personality settings
!p presets             - List all available personality presets  
!p preset <name>       - Apply a personality preset

### Advanced Tweaking:
!p set <trait> <value> - Set individual traits (0-10 scale)

## Available Personality Presets:

### 😎 Chill 
- Low aggression, peaceful responses
- Laid-back energy, helpful attitude
- Clean language, empathetic

### 🔥 Aggressive  
- High aggression and roasting
- Confrontational, savage comebacks
- Heavy profanity, competitive

### 😇 Wholesome
- Family-friendly, very helpful  
- High empathy, supportive
- Clean language, positive vibes

### 😏 Sarcastic
- Maximum sarcasm and wit
- Roasting master, clever comebacks
- Moderate profanity

### ⚡ Hyped
- Maximum energy and excitement
- Lots of emojis, enthusiastic
- High humor, party vibes

### 👔 Professional  
- Formal communication style
- Clean language, focused
- Helpful but serious

### 🎮 Gamer
- Gaming slang and references
- Competitive attitude
- Casual but energetic

## Individual Traits (0-10 scale):

Core Personality:
- aggression: How confrontational (0=peaceful, 10=aggressive)
- sarcasm: Sarcasm level (0=genuine, 10=very sarcastic)  
- energy: Energy level (0=chill, 10=hyped)
- profanity: Swearing frequency (0=clean, 10=heavy)
- helpfulness: How helpful (0=unhelpful, 10=very helpful)
- humor: Comedy level (0=serious, 10=comedian)
- empathy: Emotional intelligence (0=cold, 10=empathetic)
- roasting: Teasing/roasting (0=nice, 10=savage)

Communication Style:
- formality: Language style (0=casual, 10=formal)
- emoji_usage: Emoji frequency (0=none, 10=lots)
- slang_usage: Slang frequency (0=proper, 10=heavy slang)

Behavioral:
- attention_span: Topic focus (0=scattered, 10=focused)
- mood_stability: Mood consistency (0=moody, 10=stable)
- respect_level: General respect (0=rude, 10=respectful)

## Examples:

```
!p preset aggressive    # Makes Jim savage and confrontational
!p preset wholesome     # Makes Jim family-friendly and helpful
!p set sarcasm 10       # Maximum sarcasm mode
!p set energy 10        # Maximum hype energy
!p set profanity 0      # Clean language only
!p                      # View current settings
```

## How It Works:

The personality system dynamically generates Jim's system prompt based on your settings.
When you change a trait or preset, Jim's responses immediately reflect the new personality!

Each trait influences how Jim responds:
- High aggression = more confrontational responses
- High sarcasm = witty, sarcastic comebacks  
- High energy = excited, enthusiastic responses
- High profanity = more swearing and casual language
- High empathy = more understanding and supportive

## Tips:

1. Try different presets to find your preferred Jim vibe
2. Mix and match traits for custom personalities
3. Settings are saved automatically and persist between restarts
4. You can reset to defaults with `!p reset`
5. All users can view settings but only admins can change them

Have fun customizing Jim's personality! 🚀
"""
