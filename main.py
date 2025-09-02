import os
import asyncio
import threading
from dotenv import load_dotenv
from simple_bot import bot
from web_server import app

# Load environment variables from .env file
load_dotenv()

def run_web_server():
    """Run Flask web server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def main():
    """Main function to run the Discord bot and web server"""
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Keep-alive ping task for VS Code
    async def keep_alive_ping():
        while True:
            await asyncio.sleep(30)  # Every 30 seconds
            print(f"🔄 Keep-alive: {asyncio.get_event_loop().time():.0f}")
    
    # Start keep-alive task
    keep_alive_task = asyncio.create_task(keep_alive_ping())
    
    # Run the Discord bot
    discord_token = os.getenv('DISCORD_TOKEN', 'your_discord_token_here')
    
    try:
        # Run both the bot and keep-alive concurrently
        await asyncio.gather(
            bot.start(discord_token),
            keep_alive_task
        )
    except Exception as e:
        print(f"Error starting bot: {e}")
        keep_alive_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())

