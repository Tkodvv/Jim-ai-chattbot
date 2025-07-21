# Discord Bot with AI Chat Integration

## Overview

This repository contains a Discord bot named "Jim" that integrates with OpenAI's GPT-4o model to provide AI-powered conversations with a natural Gen Z personality. The bot combines Discord.py for chat functionality with a Flask web server for health monitoring and statistics. It uses PostgreSQL for persistent conversation storage and includes memory features to maintain context across interactions. Enhanced with human-like features including typing indicators, reply threading, and natural conversation delays.

## User Preferences

Preferred communication style: Simple, everyday language.
Bot personality: Unfiltered, edgy Gen Z - matches energy, talks back when people are rude, swears naturally, calls out BS.
Database: Local PostgreSQL at postgresql://postgres:1136@localhost:5432/jimbot
Python version: Python 3.13.2 preferred
Startup: start.bat automatically handles PostgreSQL service and database setup

## System Architecture

The application follows a hybrid architecture combining a Discord bot client with a web server:

- **Discord Bot**: Async Python bot using discord.py for real-time chat interactions
- **Web Server**: Flask application providing REST endpoints for monitoring and stats
- **Database Layer**: SQLAlchemy ORM with PostgreSQL for conversation persistence
- **AI Integration**: OpenAI GPT-4o API for natural language generation
- **Concurrent Execution**: Threading model to run both Discord bot and web server simultaneously

## Key Components

### Bot Layer (`bot.py`)
- **DiscordBot Class**: Extends discord.py commands.Bot with custom functionality
- **Message Handling**: Processes incoming Discord messages with spam protection
- **User Tracking**: Maintains interaction timestamps and processing state
- **Database Integration**: Stores conversation history for context awareness
- **Human-like Features**: Typing indicators, reply threading, natural delays (1-3 seconds)
- **Reply System**: Uses Discord's reply feature for better conversation threading

### Web Server (`web_server.py`)
- **Health Monitoring**: `/health` endpoint for system status checks
- **Statistics**: `/stats` endpoint for user and conversation metrics
- **Status Dashboard**: Root endpoint showing bot operational status

### Data Models (`models.py`)
- **Conversation Model**: Simple key-value storage for user conversations
- **Database Factory**: Flask app creation with PostgreSQL configuration
- **Connection Management**: Pool settings for database reliability

### AI Client (`openai_client.py`)
- **OpenAI Integration**: GPT-4o API client for response generation
- **Personality System**: Gen Z-style prompting for authentic conversational tone
- **Context Management**: Conversation memory integration for coherent discussions

### Application Entry (`main.py`)
- **Orchestration**: Coordinates Discord bot and web server startup
- **Threading**: Manages concurrent execution of both services
- **Error Handling**: Graceful startup and error management

## Data Flow

1. **Message Reception**: Discord user sends message to bot
2. **Spam Protection**: Bot checks user interaction timing and processing status
3. **Context Retrieval**: System fetches conversation history from database
4. **AI Processing**: OpenAI API generates response using conversation context and Gen Z personality
5. **Response Delivery**: Bot sends generated response back to Discord channel
6. **Context Storage**: New conversation data is stored in database for future reference

## External Dependencies

### Required Services
- **Discord API**: Bot token and guild permissions required
- **OpenAI API**: GPT-4o access for conversation generation
- **PostgreSQL Database**: Persistent storage for conversation history

### Environment Variables
- `DISCORD_TOKEN`: Discord bot authentication token
- `OPENAI_API_KEY`: OpenAI API access key
- `DATABASE_URL`: Complete PostgreSQL connection string (optional)
- `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGDATABASE`: Individual database connection parameters
- `FLASK_SECRET_KEY`: Flask session security key

### Python Packages
- `discord.py`: Discord API integration
- `Flask`: Web server framework
- `Flask-SQLAlchemy`: Database ORM
- `openai`: OpenAI API client
- `asyncio`: Asynchronous operation support

## Deployment Strategy

The application is designed for containerized deployment with the following characteristics:

- **Port Configuration**: Web server runs on port 5000 with 0.0.0.0 binding
- **Database Flexibility**: Supports both full DATABASE_URL and component-based configuration
- **Environment-Driven**: All sensitive configuration through environment variables
- **Health Monitoring**: Built-in endpoints for deployment health checks
- **Graceful Startup**: Proper initialization order with database creation
- **Error Resilience**: Database connection pooling and ping checks for reliability

The bot can be deployed on platforms like Replit, Railway, or any container-capable hosting service with PostgreSQL database support.