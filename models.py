import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# ================== MODELS (unchanged) ==================
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
    message  = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<ChatHistory {self.user_id}: {self.message[:20]}>'

class UserFact(db.Model):
    __tablename__ = 'userfacts'
    id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, nullable=False)
    key     = db.Column(db.String(100), nullable=False)
    value   = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<UserFact {self.user_id} - {self.key}: {self.value[:20]}>'

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
