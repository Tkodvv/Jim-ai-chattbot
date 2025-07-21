#!/bin/bash

echo "Starting Jim Discord Bot..."
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create a .env file with your API keys and database configuration."
    echo "You can copy .env.example and fill in your values."
    exit 1
fi

# Check for Python 3.13, fallback to python3, then python
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found! Please install Python 3.13"
    exit 1
fi

echo "Using $PYTHON_CMD"
echo

# Install dependencies if needed
echo "Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements_download.txt

echo
echo "Starting Jim Bot..."
echo "Press Ctrl+C to stop the bot"
echo

# Run the bot
$PYTHON_CMD main.py

echo
echo "Bot stopped."