# Jim Discord Bot - Complete Package

## 📁 Package Contents

This complete Discord bot package includes all the files you need to run Jim locally or deploy him anywhere:

### Core Files
- **`jim_bot.py`** - Complete standalone bot with all features
- **`.env.example`** - Environment variables template
- **`requirements_download.txt`** - Python dependencies
- **`README.md`** - Complete setup and usage guide

### Setup & Deployment
- **`setup.py`** - Automated setup script
- **`run.sh`** - Quick start script for Unix/Linux
- **`PACKAGE_INFO.md`** - This file

## 🚀 Quick Start

1. **Download all files** to your local machine
2. **Run setup**: `python setup.py`
3. **Edit `.env`** with your API keys
4. **Start bot**: `python jim_bot.py` or `./run.sh`

## 🔥 What You Get

✅ **Complete Discord Bot** - Ready to run, no additional coding needed  
✅ **Advanced AI Personality** - Authentic Gen Z conversation style  
✅ **User Memory System** - PostgreSQL database with conversation history  
✅ **Smart Response Logic** - Responds to mentions + 60s interaction window  
✅ **Human-like Features** - Typing indicators, replies, natural delays  
✅ **Google Search Integration** - Optional web search capabilities  
✅ **Web Server** - Keep-alive server for cloud hosting  
✅ **Commands & Stats** - Built-in bot management commands  

## 🎯 Key Features

### Memory System
- Stores user conversations in PostgreSQL
- Remembers usernames and interaction history
- Maintains context across conversations
- Conversation memory with 10-message history

### AI Personality
- Uses OpenAI GPT-4o for responses
- Natural Gen Z speaking style
- Context-aware conversations
- Authentic slang usage without overdoing it

### Human-like Behavior
- Shows typing indicators (1-3.5 second delays)
- Uses Discord reply threading
- Responds to trigger words ("jim", "bot")
- 60-second interaction windows for continuous conversation

### Search Capabilities
- Integrated Google Custom Search
- Stores search history in database
- Natural language search requests
- Returns formatted results with links

### Deployment Ready
- Flask web server for keep-alive functionality
- Environment variable configuration
- Error handling and logging
- Database auto-initialization

## 🛠️ Requirements

- **Python 3.8+**
- **PostgreSQL database**
- **Discord Bot Token**
- **OpenAI API Key**
- **Google API Keys** (optional, for search)

## 📱 Discord Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Bot section
3. Copy bot token to `.env` file
4. Enable "Message Content Intent"
5. Invite bot with appropriate permissions

## 💾 Database Schema

The bot automatically creates these tables:

```sql
-- User conversation memory
CREATE TABLE conversations (
    user_id TEXT,
    key TEXT,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, key)
);

-- Search history tracking
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    query TEXT,
    results TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎮 Bot Commands

- `!ping` - Test bot responsiveness
- `!forget` - Clear your conversation memory  
- `!stats` - View bot usage statistics

## 🌍 Deployment Options

### Local Development
```bash
python jim_bot.py
```

### Replit
1. Upload all files
2. Set secrets in environment
3. Run bot

### Railway/Heroku
1. Add PostgreSQL addon
2. Set environment variables
3. Deploy with Python buildpack

### VPS/Cloud
1. Install PostgreSQL
2. Set up environment
3. Run with process manager (pm2, systemd)

## 🔧 Customization

### Personality Changes
Edit the `SYSTEM_PROMPT` in the `AIPersonality` class to modify Jim's speaking style and behavior.

### Add Commands
Create new methods in the `JimBot` class with `@commands.command()` decorator.

### Memory Extensions
Modify `update_conversation_memory()` to store additional user data.

### Search Providers
Replace `GoogleSearcher` class to use different search APIs.

## 📊 Monitoring

- Web server runs on port 5000
- Health endpoint: `http://localhost:5000/health`
- Status page: `http://localhost:5000/`
- Debug logs show all interactions

## 🎵 Ready to Vibe!

Jim is now ready to bring authentic Gen Z energy to your Discord server. He'll remember conversations, search the web, and chat naturally with your community.

**"Tkodv's slave is running" - Jim is ready! 🔥**