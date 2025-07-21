# Jim - Advanced Discord AI Chatbot

A complete Discord bot with AI personality, memory, search capabilities, and human-like conversation features.

## 🚀 Features

✅ **AI-Powered Conversations**: Uses OpenAI's GPT-4o with authentic Gen Z personality  
✅ **User Memory**: PostgreSQL database stores conversation history and user preferences  
✅ **Smart Triggers**: Responds when mentioned or after recent interactions (60s window)  
✅ **Google Search**: Integrated web search capabilities (optional)  
✅ **Human-like Behavior**: Typing indicators, reply threading, natural delays  
✅ **Web Server**: Keep-alive server for cloud hosting (Replit, Railway, etc.)  
✅ **Advanced Commands**: Stats, memory management, and more  

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Discord Bot Token
- OpenAI API Key

### Setup Steps

1. **Clone or Download**
   ```bash
   git clone <your-repo-url>
   cd jim-discord-bot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or if using the complete bot file:
   ```bash
   pip install discord.py openai psycopg2-binary aiohttp python-dotenv langchain faiss-cpu flask
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your credentials:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql://username:password@host:port/database
   GOOGLE_API_KEY=your_google_api_key_here  # Optional
   GOOGLE_CSE_ID=your_search_engine_id_here  # Optional
   ```

4. **Database Setup**
   
   The bot will automatically create required tables:
   - `conversations` - User memory storage
   - `search_history` - Search history tracking

5. **Discord Bot Setup**
   
   1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
   2. Create new application
   3. Go to "Bot" section
   4. Create bot and copy token
   5. Enable "Message Content Intent"
   6. Invite bot to your server with appropriate permissions

6. **Run the Bot**
   ```bash
   python jim_bot.py
   ```

## 🛠️ Configuration

### Required Environment Variables
- `DISCORD_TOKEN` - Your Discord bot token
- `OPENAI_API_KEY` - Your OpenAI API key  
- `DATABASE_URL` - PostgreSQL connection string

### Optional Environment Variables
- `GOOGLE_API_KEY` - Google Custom Search API key
- `GOOGLE_CSE_ID` - Google Custom Search Engine ID
- `FLASK_SECRET_KEY` - Flask session key
- `DEBUG` - Enable debug mode (default: True)
- `PORT` - Web server port (default: 5000)

### Database Configuration
You can use either:
1. Full `DATABASE_URL` connection string, or
2. Individual components: `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGDATABASE`

## 💬 Usage

### Basic Interaction
- Mention "jim" in any message to get a response
- After first interaction, Jim will respond for 60 seconds without needing to mention his name
- Jim uses Discord's reply feature for better conversation threading

### Commands
- `!ping` - Check if bot is responsive
- `!forget` - Clear your conversation memory
- `!stats` - View bot statistics

### Search Feature
Say things like:
- "jim search for python tutorials"
- "jim look up weather today"
- "jim find information about AI"

## 🏗️ Architecture

### Core Components
- **JimBot Class**: Main Discord bot with message handling
- **DatabaseManager**: PostgreSQL operations and memory management
- **AIPersonality**: OpenAI integration with Gen Z personality
- **GoogleSearcher**: Web search capabilities
- **Flask Server**: Keep-alive web server

### Database Schema
```sql
CREATE TABLE conversations (
    user_id TEXT,
    key TEXT,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, key)
);

CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    query TEXT,
    results TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🌐 Deployment

### Replit
1. Upload all files to Replit
2. Set environment variables in Secrets tab
3. Run `python jim_bot.py`

### Railway/Heroku
1. Add PostgreSQL addon
2. Set environment variables
3. Deploy with `python jim_bot.py` as start command

### VPS/Local
1. Install PostgreSQL
2. Create database and user
3. Set environment variables
4. Run with process manager like systemd or pm2

## 🎯 Personality Features

Jim has an authentic Gen Z personality that:
- Uses natural slang without overdoing it
- Responds contextually to conversations
- Remembers past interactions
- Shows typing indicators
- Uses reply threading
- Maintains conversation flow with 60-second interaction windows

## 🔧 Customization

### Modify Personality
Edit the `SYSTEM_PROMPT` in `AIPersonality` class to change Jim's personality.

### Add Commands
Add new commands by creating methods with `@commands.command()` decorator in the `JimBot` class.

### Extend Memory
Add new memory types by modifying the `update_conversation_memory` method.

## 📊 Monitoring

- Web server runs on port 5000 (configurable)
- Health check endpoint: `/health`
- Status endpoint: `/`
- Ping endpoint: `/ping`

## 🐛 Troubleshooting

### Common Issues
1. **Bot won't start**: Check if `DISCORD_TOKEN` is set correctly
2. **No AI responses**: Verify `OPENAI_API_KEY` is valid
3. **Database errors**: Ensure PostgreSQL is running and accessible
4. **Search not working**: Google API keys are optional, search will be disabled without them

### Debug Mode
Set `DEBUG=True` in `.env` for detailed logging.

## 📝 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

**Jim is ready to vibe with your Discord community! 🎵**