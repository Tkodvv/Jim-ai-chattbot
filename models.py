import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import Text, String, Integer, DateTime, JSON, Boolean

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# ================== MODELS ==================
class Conversation(db.Model):
    __tablename__ = 'conversations'
    user_id = db.Column(db.Text, primary_key=True, nullable=False)
    key     = db.Column(db.Text, primary_key=True, nullable=False)
    value   = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Conversation {self.user_id}:{self.key}>'

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id  = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    message  = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    channel_id = db.Column(db.Text, nullable=True)
    guild_id = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<ChatHistory {self.user_id}: {self.message[:20]}>'

class UserFact(db.Model):
    __tablename__ = 'userfacts'
    id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, nullable=False)
    key     = db.Column(db.String(100), nullable=False)
    value   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserFact {self.user_id} - {self.key}: {self.value[:20]}>'

class UserProfile(db.Model):
    """Enhanced user profile with detailed information Jim remembers"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    display_name = db.Column(db.String(100), nullable=True)
    
    # Personal info Jim learns
    real_name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    
    # Preferences and interests
    interests = db.Column(db.Text, nullable=True)  # JSON array of interests
    favorite_games = db.Column(db.Text, nullable=True)  # JSON array
    favorite_music = db.Column(db.Text, nullable=True)  # JSON array
    hobbies = db.Column(db.Text, nullable=True)  # JSON array
    
    # Personality traits Jim notices
    personality_notes = db.Column(db.Text, nullable=True)
    communication_style = db.Column(db.String(100), nullable=True)  # casual, formal, funny, etc.
    mood_patterns = db.Column(db.Text, nullable=True)  # JSON with mood tracking
    
    # Relationship with Jim
    first_met = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    interaction_count = db.Column(db.Integer, default=0)
    trust_level = db.Column(db.Integer, default=1)  # 1-10 scale
    
    # Special relationships
    is_creator = db.Column(db.Boolean, default=False)
    is_friend = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserProfile {self.username or self.user_id}>'

class UserMemory(db.Model):
    """Specific memories Jim has about users"""
    __tablename__ = 'user_memories'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, nullable=False)
    memory_type = db.Column(db.String(50), nullable=False)  # fact, story, preference, etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    importance = db.Column(db.Integer, default=5)  # 1-10 scale
    source_message = db.Column(db.Text, nullable=True)  # original message that created this memory
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags for searching
    is_confirmed = db.Column(db.Boolean, default=False)  # whether user confirmed this is accurate
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_referenced = db.Column(db.DateTime, default=datetime.utcnow)
    reference_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<UserMemory {self.title}>'

class ConversationContext(db.Model):
    """Context for ongoing conversations"""
    __tablename__ = 'conversation_contexts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, nullable=False)
    channel_id = db.Column(db.Text, nullable=False)
    guild_id = db.Column(db.Text, nullable=True)
    
    # Current conversation state
    topic = db.Column(db.String(200), nullable=True)
    mood = db.Column(db.String(50), nullable=True)
    context_summary = db.Column(db.Text, nullable=True)
    
    # Recent messages (JSON array)
    recent_messages = db.Column(db.Text, nullable=True)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ConversationContext {self.user_id}:{self.topic}>'

# ================== APP/DB INIT ==================
def _normalize_db_url(url: str) -> str:
    """Fix scheme, add sslmode=require for non-local Postgres if missing."""
    if not url:
        return url

    # Heroku/Neon sometimes provide postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Only enforce SSL on remote Postgres (not localhost, not sqlite)
    if url.startswith("postgresql://"):
        # split out host to decide if remote
        # crude parse without urllib to avoid edge deps
        try:
            after_scheme = url[len("postgresql://"):]
            creds_host = after_scheme.split("@", 1)[-1]  # host[:port]/db?...
            host_port_and_rest = creds_host.split("/", 1)[0]
            host_only = host_port_and_rest.split(":", 1)[0]
        except Exception:
            host_only = ""

        is_local = host_only in ("localhost", "127.0.0.1", "::1", "")
        if not is_local and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"

    return url

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "jim_discord_bot_secret")

    database_url = os.environ.get("DATABASE_URL", "").strip()

    # Fallback build from PG* envs if DATABASE_URL missing
    if not database_url:
        pg_user = os.environ.get("PGUSER", "postgres")
        pg_password = os.environ.get("PGPASSWORD", "password")
        pg_host = os.environ.get("PGHOST", "localhost")
        pg_port = os.environ.get("PGPORT", "5432")
        pg_database = os.environ.get("PGDATABASE", "discord_bot")
        database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

    database_url = _normalize_db_url(database_url)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Lean pool to save RAM on Koyeb
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,
        "max_overflow": 0,
        "pool_recycle": 1800,   # recycle every 30 min
        "pool_pre_ping": True,  # validate connections
        "pool_timeout": 30,     # don't hang forever
    }

    db.init_app(app)

    # Create tables on boot
    with app.app_context():
        db.create_all()

    return app
