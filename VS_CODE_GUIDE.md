# 🤖 JimBot - VS Code Quick Start Guide

## Quick Run & Debug Setup

### 🚀 F5 Quick Start
Press **F5** to instantly run JimBot with debugging enabled!

### ⌨️ Keyboard Shortcuts
- **F5** - Start JimBot with debugger
- **Ctrl+F5** - Run JimBot without debugger  
- **Shift+F5** - Stop debugging
- **F6** - Restart JimBot (kills and restarts)
- **F7** - Check bot status
- **Ctrl+Shift+K** - Kill all Python processes

### 🎯 Debug Configurations Available
1. **🤖 Run JimBot** - Standard bot execution
2. **🔧 Debug JimBot** - Full debugging with breakpoints
3. **🧪 Test Bot Components** - Test individual components
4. **🔍 Debug Voice System** - Debug voice features specifically

### 📋 Quick Tasks (Ctrl+Shift+P → Tasks: Run Task)
- **🤖 Start JimBot** - Launch the bot
- **🔧 Install Dependencies** - Install required packages
- **🧹 Kill All Python Processes** - Emergency stop
- **🔄 Restart JimBot** - Full restart sequence
- **📋 Check Bot Status** - Verify bot is running

### 🔧 Development Features
- **Auto-save** - Files save automatically
- **Python IntelliSense** - Code completion and error detection
- **Environment Variables** - Automatically loads .env file
- **Integrated Terminal** - Run commands within VS Code
- **Problem Detection** - Shows Python errors in real-time

### 🎮 How to Use
1. Open this project in VS Code
2. Make sure your `.env` file has your Discord and OpenAI tokens
3. Press **F5** to start the bot
4. Check the integrated terminal for bot status
5. Set breakpoints in your code for debugging

### 🐛 Debugging Tips
- Set breakpoints by clicking left of line numbers
- Use the Debug Console to run Python commands while paused
- Watch variables in the Debug sidebar
- Step through code with F10 (step over) and F11 (step into)

### 📁 Project Structure
```
Jim-ai-chattbot/
├── .vscode/
│   ├── launch.json      # F5 debug configurations
│   ├── tasks.json       # Build and run tasks
│   ├── settings.json    # VS Code settings
│   └── keybindings.json # Custom keyboard shortcuts
├── main.py              # Bot entry point
├── simple_bot.py        # Main bot logic
├── voice_system.py      # Voice features
├── openai_client.py     # AI integration
└── .env                 # Environment variables
```

Happy coding! 🎉
