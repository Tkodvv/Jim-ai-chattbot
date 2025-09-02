"""
Enhanced Memory System for Jim Bot
Handles sophisticated user memory, relationships, and context tracking
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import db, UserProfile, UserMemory, ConversationContext, ChatHistory, UserFact
from sqlalchemy import and_, or_, desc

logger = logging.getLogger(__name__)

class EnhancedMemoryManager:
    """Advanced memory management for Jim Bot"""
    
    def __init__(self, app_context):
        self.app_context = app_context
        
    async def get_or_create_user_profile(self, user_id: str, username: str = None, display_name: str = None) -> UserProfile:
        """Get or create a user profile"""
        try:
            with self.app_context():
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                
                if not profile:
                    profile = UserProfile(
                        user_id=user_id,
                        username=username,
                        display_name=display_name,
                        is_creator=(user_id == "556006898298650662")  # iivxfn (Izaiah)
                    )
                    db.session.add(profile)
                    logger.info(f"Created new user profile for {username or user_id}")
                else:
                    # Update existing profile
                    if username:
                        profile.username = username
                    if display_name:
                        profile.display_name = display_name
                    profile.last_interaction = datetime.utcnow()
                    profile.interaction_count += 1
                
                db.session.commit()
                return profile
                
        except Exception as e:
            logger.error(f"Error getting/creating user profile: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    async def add_user_memory(self, user_id: str, memory_type: str, title: str, content: str, 
                            importance: int = 5, source_message: str = None, tags: List[str] = None) -> bool:
        """Add a new memory about a user"""
        try:
            with self.app_context():
                memory = UserMemory(
                    user_id=user_id,
                    memory_type=memory_type,
                    title=title,
                    content=content,
                    importance=importance,
                    source_message=source_message,
                    tags=json.dumps(tags or [])
                )
                db.session.add(memory)
                db.session.commit()
                logger.info(f"Added memory '{title}' for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding user memory: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    async def get_user_memories(self, user_id: str, memory_type: str = None, limit: int = 20) -> List[UserMemory]:
        """Get memories about a user"""
        try:
            with self.app_context():
                query = UserMemory.query.filter_by(user_id=user_id)
                
                if memory_type:
                    query = query.filter_by(memory_type=memory_type)
                
                memories = query.order_by(desc(UserMemory.importance), desc(UserMemory.last_referenced)).limit(limit).all()
                
                # Update reference count and last_referenced for retrieved memories
                for memory in memories:
                    memory.reference_count += 1
                    memory.last_referenced = datetime.utcnow()
                
                db.session.commit()
                return memories
                
        except Exception as e:
            logger.error(f"Error getting user memories: {e}")
            return []
    
    async def search_memories(self, user_id: str, search_term: str, limit: int = 10) -> List[UserMemory]:
        """Search memories for specific content"""
        try:
            with self.app_context():
                memories = UserMemory.query.filter(
                    and_(
                        UserMemory.user_id == user_id,
                        or_(
                            UserMemory.title.ilike(f'%{search_term}%'),
                            UserMemory.content.ilike(f'%{search_term}%'),
                            UserMemory.tags.ilike(f'%{search_term}%')
                        )
                    )
                ).order_by(desc(UserMemory.importance)).limit(limit).all()
                
                return memories
                
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def update_user_personality(self, user_id: str, personality_notes: str = None, 
                                    communication_style: str = None, mood: str = None) -> bool:
        """Update user's personality information"""
        try:
            with self.app_context():
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                
                if not profile:
                    return False
                
                if personality_notes:
                    profile.personality_notes = personality_notes
                
                if communication_style:
                    profile.communication_style = communication_style
                
                if mood:
                    # Update mood patterns
                    mood_patterns = json.loads(profile.mood_patterns or '{}')
                    current_date = datetime.utcnow().date().isoformat()
                    mood_patterns[current_date] = mood
                    
                    # Keep only last 30 days of mood data
                    cutoff_date = (datetime.utcnow().date() - timedelta(days=30)).isoformat()
                    mood_patterns = {k: v for k, v in mood_patterns.items() if k >= cutoff_date}
                    
                    profile.mood_patterns = json.dumps(mood_patterns)
                
                profile.updated_at = datetime.utcnow()
                db.session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating user personality: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    async def add_interest(self, user_id: str, interest: str, category: str = "general") -> bool:
        """Add an interest to user's profile"""
        try:
            with self.app_context():
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    return False
                
                # Handle different interest categories
                interest_field = {
                    "games": "favorite_games",
                    "music": "favorite_music", 
                    "hobbies": "hobbies",
                    "general": "interests"
                }.get(category, "interests")
                
                current_interests = json.loads(getattr(profile, interest_field) or '[]')
                
                if interest not in current_interests:
                    current_interests.append(interest)
                    setattr(profile, interest_field, json.dumps(current_interests))
                    profile.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Added {category} interest '{interest}' for user {user_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding interest: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    async def update_conversation_context(self, user_id: str, channel_id: str, guild_id: str = None,
                                        topic: str = None, mood: str = None, context_summary: str = None,
                                        user_message: str = None, bot_response: str = None) -> bool:
        """Update conversation context"""
        try:
            with self.app_context():
                context = ConversationContext.query.filter_by(
                    user_id=user_id, 
                    channel_id=channel_id
                ).first()
                
                if not context:
                    context = ConversationContext(
                        user_id=user_id,
                        channel_id=channel_id,
                        guild_id=guild_id,
                        recent_messages='[]'
                    )
                    db.session.add(context)
                
                if topic:
                    context.topic = topic
                if mood:
                    context.mood = mood
                if context_summary:
                    context.context_summary = context_summary
                
                # Update recent messages
                if user_message and bot_response:
                    recent_messages = json.loads(context.recent_messages or '[]')
                    recent_messages.append({
                        'user': user_message,
                        'bot': bot_response,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    # Keep only last 10 exchanges
                    if len(recent_messages) > 10:
                        recent_messages = recent_messages[-10:]
                    
                    context.recent_messages = json.dumps(recent_messages)
                
                context.last_updated = datetime.utcnow()
                db.session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating conversation context: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    async def get_conversation_context(self, user_id: str, channel_id: str) -> Optional[ConversationContext]:
        """Get current conversation context"""
        try:
            with self.app_context():
                context = ConversationContext.query.filter_by(
                    user_id=user_id,
                    channel_id=channel_id
                ).first()
                return context
                
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return None
    
    async def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of what Jim knows about a user"""
        try:
            with self.app_context():
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                memories = UserMemory.query.filter_by(user_id=user_id).order_by(desc(UserMemory.importance)).limit(10).all()
                
                if not profile:
                    return {}
                
                # Parse JSON fields safely
                def safe_json_loads(json_str, default=None):
                    try:
                        return json.loads(json_str) if json_str else (default or [])
                    except:
                        return default or []
                
                summary = {
                    'basic_info': {
                        'username': profile.username,
                        'display_name': profile.display_name,
                        'real_name': profile.real_name,
                        'age': profile.age,
                        'location': profile.location,
                        'timezone': profile.timezone
                    },
                    'interests': {
                        'general': safe_json_loads(profile.interests),
                        'games': safe_json_loads(profile.favorite_games),
                        'music': safe_json_loads(profile.favorite_music),
                        'hobbies': safe_json_loads(profile.hobbies)
                    },
                    'personality': {
                        'notes': profile.personality_notes,
                        'communication_style': profile.communication_style,
                        'mood_patterns': safe_json_loads(profile.mood_patterns, {})
                    },
                    'relationship': {
                        'first_met': profile.first_met.isoformat() if profile.first_met else None,
                        'last_interaction': profile.last_interaction.isoformat() if profile.last_interaction else None,
                        'interaction_count': profile.interaction_count,
                        'trust_level': profile.trust_level,
                        'is_creator': profile.is_creator,
                        'is_friend': profile.is_friend
                    },
                    'recent_memories': [
                        {
                            'type': memory.memory_type,
                            'title': memory.title,
                            'content': memory.content,
                            'importance': memory.importance,
                            'created': memory.created_at.isoformat() if memory.created_at else None
                        }
                        for memory in memories
                    ]
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            return {}
    
    async def analyze_message_for_memory(self, user_id: str, username: str, message: str) -> List[Dict]:
        """Analyze a message for potential memories to store"""
        memories_to_add = []
        
        # Simple keyword-based analysis (can be enhanced with NLP)
        message_lower = message.lower()
        
        # Personal information patterns
        if any(phrase in message_lower for phrase in ['my name is', 'call me', 'i am', "i'm"]):
            if 'my name is' in message_lower:
                name_part = message_lower.split('my name is')[1].strip().split()[0]
                memories_to_add.append({
                    'type': 'personal_info',
                    'title': 'Real Name',
                    'content': f"User's real name is {name_part}",
                    'importance': 8
                })
        
        # Age information
        if any(phrase in message_lower for phrase in ['i am', "i'm", 'years old', 'age']):
            import re
            age_match = re.search(r'(?:i am|i\'m|age)\s*(\d{1,2})', message_lower)
            if age_match:
                age = age_match.group(1)
                memories_to_add.append({
                    'type': 'personal_info',
                    'title': 'Age',
                    'content': f"User is {age} years old",
                    'importance': 7
                })
        
        # Location information
        if any(phrase in message_lower for phrase in ['i live in', 'from', 'located in']):
            memories_to_add.append({
                'type': 'personal_info',
                'title': 'Location Mentioned',
                'content': f"User mentioned location: {message}",
                'importance': 6
            })
        
        # Interests and hobbies
        if any(phrase in message_lower for phrase in ['i like', 'i love', 'i enjoy', 'favorite', 'hobby']):
            memories_to_add.append({
                'type': 'interest',
                'title': 'Interest/Preference',
                'content': f"User expressed interest: {message}",
                'importance': 5
            })
        
        # Emotional state or mood
        if any(phrase in message_lower for phrase in ['i feel', 'i\'m feeling', 'mood', 'sad', 'happy', 'angry', 'excited']):
            memories_to_add.append({
                'type': 'mood',
                'title': 'Emotional State',
                'content': f"User's mood/feeling: {message}",
                'importance': 4
            })
        
        return memories_to_add
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old conversation data to keep database size manageable"""
        try:
            with self.app_context():
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                # Delete old chat history
                old_chats = ChatHistory.query.filter(ChatHistory.timestamp < cutoff_date).delete()
                
                # Delete old conversation contexts
                old_contexts = ConversationContext.query.filter(
                    ConversationContext.last_updated < cutoff_date
                ).delete()
                
                # Delete low-importance old memories
                old_memories = UserMemory.query.filter(
                    and_(
                        UserMemory.created_at < cutoff_date,
                        UserMemory.importance < 5,
                        UserMemory.reference_count < 2
                    )
                ).delete()
                
                db.session.commit()
                logger.info(f"Cleaned up old data: {old_chats} chats, {old_contexts} contexts, {old_memories} memories")
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
