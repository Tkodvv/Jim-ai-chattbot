import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Conversation(db.Model):
    __tablename__ = 'conversations'

    user_id = db.Column(db.Text, primary_key=True, nullable=False)
    key = db.Column(db.Text, primary_key=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Conversation {self.user_id}:{self.key}>'

# ✅ Optional memory table (if you want history tracking beyond key/value)
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<ChatHistory {self.user_id}: {self.message[:20]}>'

# ✅ Long-term user facts
class UserFact(db.Model):
    __tablename__ = 'userfacts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Text, nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<UserFact {self.user_id} - {self.key}: {self.value[:20]}>'

# Create Flask app for database initialization
def create_app():
    app = Flask(__name__)

    # Setup secret key
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "jim_discord_bot_secret")

    # Configure database
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Fallback construction from individual components
        pg_user = os.environ.get("PGUSER", "postgres")
        pg_password = os.environ.get("PGPASSWORD", "password")
        pg_host = os.environ.get("PGHOST", "localhost")
        pg_port = os.environ.get("PGPORT", "5432")
        pg_database = os.environ.get("PGDATABASE", "discord_bot")
        database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database with app
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app
