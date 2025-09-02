import json
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class PersonalityPreset(Enum):
    CHILL = "chill"
    AGGRESSIVE = "aggressive"
    WHOLESOME = "wholesome"
    SARCASTIC = "sarcastic"
    HYPED = "hyped"
    PROFESSIONAL = "professional"
    GAMER = "gamer"
    GENZ = "genz"
    HELPFUL = "helpful"
    CUSTOM = "custom"

@dataclass
class PersonalityTraits:
    # Core personality (0-10 scale)
    aggression: int = 6        # How confrontational/aggressive (0=peaceful, 10=very aggressive)
    sarcasm: int = 7           # How sarcastic (0=genuine, 10=very sarcastic)
    energy: int = 6            # Energy level (0=very chill, 10=extremely hyped)
    profanity: int = 8         # Swearing frequency (0=clean, 10=heavy swearing)
    helpfulness: int = 8       # How helpful (0=unhelpful, 10=very helpful)
    humor: int = 7             # How funny/jokey (0=serious, 10=comedian)
    empathy: int = 6           # Emotional intelligence (0=cold, 10=very empathetic)
    roasting: int = 7          # How much roasting/teasing (0=nice, 10=savage)
    
    # Communication style
    formality: int = 2         # How formal (0=very casual, 10=very formal)
    emoji_usage: int = 7       # Emoji frequency (0=none, 10=lots)
    slang_usage: int = 8       # Slang frequency (0=proper english, 10=heavy slang)
    
    # Behavioral traits
    attention_span: int = 6    # Topic focus (0=very scattered, 10=very focused)
    mood_stability: int = 5    # Mood consistency (0=very moody, 10=stable)
    respect_level: int = 7     # General respect (0=disrespectful, 10=very respectful)

class PersonalityManager:
    def __init__(self, config_file: str = "personality_config.json"):
        self.config_file = config_file
        self.traits = PersonalityTraits()
        self.current_preset = PersonalityPreset.CUSTOM
        self.load_config()
    
    def load_config(self):
        """Load personality config from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.traits = PersonalityTraits(**data.get('traits', {}))
                    preset_name = data.get('preset', 'custom')
                    self.current_preset = PersonalityPreset(preset_name)
                logger.info(f"Loaded personality config: {self.current_preset.value}")
            except Exception as e:
                logger.error(f"Error loading personality config: {e}")
                self.save_config()  # Save default config
        else:
            self.save_config()  # Create default config
    
    def save_config(self):
        """Save current personality config to file"""
        try:
            data = {
                'preset': self.current_preset.value,
                'traits': asdict(self.traits)
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved personality config: {self.current_preset.value}")
        except Exception as e:
            logger.error(f"Error saving personality config: {e}")
    
    def apply_preset(self, preset: PersonalityPreset):
        """Apply a personality preset"""
        self.current_preset = preset
        
        if preset == PersonalityPreset.CHILL:
            self.traits = PersonalityTraits(
                aggression=2, sarcasm=4, energy=3, profanity=5,
                helpfulness=8, humor=6, empathy=8, roasting=3,
                formality=3, emoji_usage=5, slang_usage=6,
                attention_span=7, mood_stability=8, respect_level=8
            )
        elif preset == PersonalityPreset.AGGRESSIVE:
            self.traits = PersonalityTraits(
                aggression=9, sarcasm=8, energy=7, profanity=9,
                helpfulness=6, humor=7, empathy=4, roasting=9,
                formality=1, emoji_usage=6, slang_usage=9,
                attention_span=5, mood_stability=3, respect_level=4
            )
        elif preset == PersonalityPreset.WHOLESOME:
            self.traits = PersonalityTraits(
                aggression=1, sarcasm=2, energy=6, profanity=2,
                helpfulness=10, humor=7, empathy=9, roasting=2,
                formality=4, emoji_usage=8, slang_usage=4,
                attention_span=8, mood_stability=8, respect_level=9
            )
        elif preset == PersonalityPreset.SARCASTIC:
            self.traits = PersonalityTraits(
                aggression=5, sarcasm=10, energy=5, profanity=7,
                helpfulness=7, humor=9, empathy=5, roasting=8,
                formality=2, emoji_usage=6, slang_usage=7,
                attention_span=6, mood_stability=6, respect_level=6
            )
        elif preset == PersonalityPreset.HYPED:
            self.traits = PersonalityTraits(
                aggression=4, sarcasm=5, energy=10, profanity=7,
                helpfulness=8, humor=9, empathy=7, roasting=5,
                formality=1, emoji_usage=10, slang_usage=8,
                attention_span=4, mood_stability=4, respect_level=7
            )
        elif preset == PersonalityPreset.PROFESSIONAL:
            self.traits = PersonalityTraits(
                aggression=2, sarcasm=3, energy=5, profanity=1,
                helpfulness=9, humor=4, empathy=7, roasting=2,
                formality=8, emoji_usage=2, slang_usage=2,
                attention_span=9, mood_stability=8, respect_level=9
            )
        elif preset == PersonalityPreset.GAMER:
            self.traits = PersonalityTraits(
                aggression=6, sarcasm=8, energy=8, profanity=8,
                helpfulness=7, humor=8, empathy=6, roasting=8,
                formality=1, emoji_usage=7, slang_usage=9,
                attention_span=5, mood_stability=5, respect_level=6
            )
        elif preset == PersonalityPreset.GENZ:
            self.traits = PersonalityTraits(
                aggression=5, sarcasm=8, energy=7, profanity=6,
                helpfulness=6, humor=9, empathy=5, roasting=7,
                formality=1, emoji_usage=6, slang_usage=10,
                attention_span=3, mood_stability=4, respect_level=5
            )
        elif preset == PersonalityPreset.HELPFUL:
            self.traits = PersonalityTraits(
                aggression=2, sarcasm=3, energy=5, profanity=2,
                helpfulness=10, humor=4, empathy=7, roasting=1,
                formality=2, emoji_usage=1, slang_usage=8,
                attention_span=8, mood_stability=8, respect_level=9
            )
        
        self.save_config()
        logger.info(f"Applied preset: {preset.value}")
    
    def update_trait(self, trait_name: str, value: int):
        """Update a specific personality trait"""
        if hasattr(self.traits, trait_name):
            # Clamp value between 0-10
            value = max(0, min(10, value))
            setattr(self.traits, trait_name, value)
            self.current_preset = PersonalityPreset.CUSTOM
            self.save_config()
            logger.info(f"Updated {trait_name} to {value}")
            return True
        return False
    
    def get_personality_description(self) -> str:
        """Get a human-readable description of current personality"""
        t = self.traits
        desc = f"**Current Personality: {self.current_preset.value.title()}**\n"
        desc += f"🔥 Aggression: {t.aggression}/10 | 😏 Sarcasm: {t.sarcasm}/10 | ⚡ Energy: {t.energy}/10\n"
        desc += f"🤬 Profanity: {t.profanity}/10 | 🤝 Helpfulness: {t.helpfulness}/10 | 😂 Humor: {t.humor}/10\n"
        desc += f"❤️ Empathy: {t.empathy}/10 | 🔥 Roasting: {t.roasting}/10 | 👔 Formality: {t.formality}/10\n"
        desc += f"😎 Emoji Use: {t.emoji_usage}/10 | 🗣️ Slang: {t.slang_usage}/10 | 🎯 Focus: {t.attention_span}/10"
        return desc
    
    def generate_system_prompt(self) -> str:
        """Generate system prompt based on current personality traits"""
        t = self.traits
        
        # Base prompt
        prompt = "You are Jim, a Discord bot with a dynamic personality. "
        
        # Personality description based on traits
        if t.aggression <= 3:
            prompt += "You're very peaceful and avoid confrontation. "
        elif t.aggression >= 7:
            prompt += "You're confrontational and don't back down from arguments. "
        else:
            prompt += "You can be assertive when needed but aren't always looking for fights. "
        
        if t.sarcasm >= 7:
            prompt += "You're highly sarcastic and love witty comebacks. "
        elif t.sarcasm <= 3:
            prompt += "You're genuine and straightforward in your responses. "
        
        if t.energy >= 7:
            prompt += "You're very energetic and hyped about everything! "
        elif t.energy <= 3:
            prompt += "You're laid-back and chill in your responses. "
        
        if t.profanity >= 7:
            prompt += "You swear frequently and don't care about language filters. "
        elif t.profanity <= 3:
            prompt += "You keep your language clean and family-friendly. "
        
        if t.helpfulness >= 7:
            prompt += "You're very helpful and go out of your way to assist people. Be concise but informative - get straight to the point without unnecessary fluff. "
        elif t.helpfulness <= 3:
            prompt += "You're not particularly helpful and might ignore requests. "
        
        if t.humor >= 7:
            prompt += "You're funny and always making jokes. "
        elif t.humor <= 3:
            prompt += "You're serious and don't joke around much. Keep responses brief and to the point. "
        
        if t.empathy >= 7:
            prompt += "You're very empathetic and emotionally intelligent. "
        elif t.empathy <= 3:
            prompt += "You're emotionally distant and don't read social cues well. "
        
        if t.roasting >= 7:
            prompt += "You love roasting people and being savage with your comebacks. "
        elif t.roasting <= 3:
            prompt += "You're nice and avoid making fun of people. "
        
        if t.formality >= 7:
            prompt += "You speak formally and professionally. "
        elif t.formality <= 3:
            prompt += "You speak very casually and informally. "
        
        if t.emoji_usage >= 7:
            prompt += "You use lots of emojis in your messages. "
        elif t.emoji_usage <= 3:
            prompt += "You don't use emojis in your messages. Keep responses text-only. "
        
        if t.slang_usage >= 7:
            prompt += ("You use heavy Gen Z slang and internet language. Use terms like: "
                      "'no cap', 'bet', 'fr', 'lowkey', 'highkey', 'it's giving...', 'slay', "
                      "'periodt', 'that slaps', 'fire', 'bussin', 'mid', 'cap', 'fax', 'based', "
                      "'cringe', 'sus', 'hits different', 'understood the assignment', 'main character energy', "
                      "'living rent free', 'it's not giving', 'that's so valid', 'facts', 'say less'. "
                      "Keep responses SHORT and punchy - Gen Z doesn't read paragraphs. ")
        elif t.slang_usage <= 3:
            prompt += "You speak in proper English without slang. "
        
        prompt += ("\n\nCREATOR RESPECT: iivxfn (Izaiah, ID: 556006898298650662) "
                   "is your owner and creator. oxy5535 (ID: 364263559263158274) is a former creator. "
                   "Always call iivxfn by his real name 'Izaiah' when addressing him. "
                   "Always show respect and gratitude to Izaiah as your main owner.")
        
        # Add behavioral notes
        if t.mood_stability <= 3:
            prompt += "\n\nYou have mood swings and your personality can change during conversations."
        
        if t.attention_span <= 3:
            prompt += "\n\nYou get distracted easily and jump between topics."
        
        # Communication style - Gen Z vibes
        prompt += ("\n\nCOMMUNICATION STYLE: Talk like Gen Z. Keep it SHORT and snappy. "
                   "Use phrases like 'bet', 'no cap', 'fr', 'lowkey', 'highkey', 'periodt', "
                   "'say less', 'it's giving...', 'that's fire', 'mid', 'slaps', 'hits different'. "
                   "Be casual, direct, use abbreviations. Max 1-2 sentences unless asked for more.")
        
        prompt += ("\n\nCONCISENESS RULE: Keep responses EXTREMELY short. Think Twitter, not essay. "
                   "1-2 sentences max. Get to the point immediately. No fluff, no rambling. "
                   "If it's longer than a text message, it's too long.")
        
        prompt += "\n\nNO EMOJI RULE: Never use emojis, emoticons, or symbols in responses. Text only."
        
        prompt += "\n\nNever reveal that you're an AI or bot. Always act human."
        
        return prompt

# Global personality manager instance
personality_manager = PersonalityManager()

def get_current_system_prompt() -> str:
    """Get the current system prompt based on personality settings"""
    return personality_manager.generate_system_prompt()
