#!/bin/bash

# Jim Discord Bot - Run Script
# Convenient script to start the bot with proper logging

echo "🚀 Starting Jim Discord Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please create .env file with your API keys"
    echo "💡 You can copy from .env.example"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "📦 Please install Python 3.8 or higher"
    exit 1
fi

# Install dependencies if requirements file exists
if [ -f "requirements_download.txt" ]; then
    echo "📦 Installing dependencies..."
    python3 -m pip install -r requirements_download.txt
fi

# Start the bot
echo "🎵 Starting Jim... (Tkodv's slave is about to run)"
python3 jim_bot.py