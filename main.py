import asyncio
import os
from dotenv import load_dotenv
import uvicorn
from threading import Thread

from bot.bot import DiscordBot
from web.app import create_web_app
from crawler.crawler import DataCrawler
from config.settings import Settings

load_dotenv()

async def run_bot():
    """Run the Discord bot"""
    bot = DiscordBot()
    await bot.start()

def run_web():
    """Run the web interface"""
    app = create_web_app()
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

async def run_crawler():
    """Run the data crawler"""
    crawler = DataCrawler()
    await crawler.start()

def main():
    """Main application entry point"""
    settings = Settings()
    
    # Start web interface in a separate thread
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Create event loop for bot and crawler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run bot and crawler concurrently
    loop.run_until_complete(asyncio.gather(
        run_bot(),
        run_crawler()
    ))

if __name__ == "__main__":
    main()