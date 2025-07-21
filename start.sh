#!/bin/bash

echo "Starting Jim Discord Bot with PostgreSQL..."
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create a .env file with your API keys and database configuration."
    echo "You can copy .env.example and fill in your values."
    exit 1
fi

# Check for Python 3.13.2, fallback to python3.13, then python3, then python
if command -v python3.13.2 &> /dev/null; then
    PYTHON_CMD="python3.13.2"
elif command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found! Please install Python 3.13.2"
    exit 1
fi

echo "Using $PYTHON_CMD"
echo

# Start PostgreSQL service (varies by system)
echo "Starting PostgreSQL service..."
if command -v systemctl &> /dev/null; then
    # SystemD (Ubuntu 16+, CentOS 7+, etc.)
    sudo systemctl start postgresql
    if [ $? -eq 0 ]; then
        echo "PostgreSQL service started successfully."
    else
        echo "WARNING: Could not start PostgreSQL via systemctl."
    fi
elif command -v service &> /dev/null; then
    # SysV Init (older systems)
    sudo service postgresql start
    if [ $? -eq 0 ]; then
        echo "PostgreSQL service started successfully."
    else
        echo "WARNING: Could not start PostgreSQL via service."
    fi
elif command -v brew &> /dev/null; then
    # macOS with Homebrew
    brew services start postgresql
    if [ $? -eq 0 ]; then
        echo "PostgreSQL service started successfully."
    else
        echo "WARNING: Could not start PostgreSQL via brew."
    fi
else
    echo "WARNING: Could not determine how to start PostgreSQL on this system."
    echo "Please ensure PostgreSQL is running manually."
fi

# Wait a moment for PostgreSQL to fully start
sleep 3

# Setup database and test connection
echo "Setting up database..."
$PYTHON_CMD setup_database.py

if [ $? -ne 0 ]; then
    echo
    echo "Database setup failed. Continuing anyway..."
    echo "Make sure PostgreSQL is running and DATABASE_URL is correct."
    echo
fi

# Install dependencies if needed
echo "Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements_download.txt

echo
echo "Starting Jim Bot..."
echo "Press Ctrl+C to stop the bot"
echo

# Function to cleanup on exit
cleanup() {
    echo
    echo "Bot stopped."
    echo "Stopping PostgreSQL service..."
    
    if command -v systemctl &> /dev/null; then
        sudo systemctl stop postgresql
    elif command -v service &> /dev/null; then
        sudo service postgresql stop
    elif command -v brew &> /dev/null; then
        brew services stop postgresql
    fi
    
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Run the bot
$PYTHON_CMD main.py

cleanup