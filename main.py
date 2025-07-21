import os
import asyncio
import threading
from simple_bot import bot
from web_server import app

def run_web_server():
    """Run Flask web server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def main():
    """Main function to run the Discord bot and web server"""
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Run the Discord bot
    discord_token = os.getenv('DISCORD_TOKEN', 'your_discord_token_here')
    
    try:
        await bot.start(discord_token)
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
