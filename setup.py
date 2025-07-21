#!/usr/bin/env python3
"""
Setup script for Jim Discord Bot
Helps with initial configuration and dependency installation
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version)
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_download.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def setup_env_file():
    """Create .env file from template"""
    if os.path.exists('.env'):
        print("⚠️  .env file already exists, skipping creation")
        return True
    
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your API keys and database credentials")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def check_dependencies():
    """Check if all required packages are available"""
    required_packages = [
        'discord.py',
        'openai',
        'psycopg2',
        'aiohttp',
        'python-dotenv',
        'langchain',
        'faiss-cpu',
        'flask'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        return False
    else:
        print("✅ All required packages are available")
        return True

def main():
    """Main setup function"""
    print("🚀 Jim Discord Bot Setup\n")
    
    if not check_python_version():
        return
    
    print("\n1. Installing dependencies...")
    if not install_dependencies():
        return
    
    print("\n2. Setting up environment file...")
    setup_env_file()
    
    print("\n3. Checking dependencies...")
    if check_dependencies():
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your API keys")
        print("2. Set up your PostgreSQL database")
        print("3. Run: python jim_bot.py")
        print("\n🎉 Jim will be ready to vibe!")
    else:
        print("\n❌ Setup incomplete. Please check dependencies.")

if __name__ == "__main__":
    main()