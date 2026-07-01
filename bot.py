import asyncio
import logging
import os
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, HELPER_BOT_TOKENS
from handlers.media_handler import register_media_handler
from handlers.start import register_start
from handlers.admin import register_admin_handlers
from handlers.language_handler import register_language_handlers
from utils.helpers import HelperManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

app = Client(
    "fast_media_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    # Start Bot
    await app.start()
    
    # Initialize and Start Helper Bots
    helper_manager = HelperManager(HELPER_BOT_TOKENS)
    await helper_manager.start_helpers()
    
    # Register Handlers
    register_start(app)
    register_admin_handlers(app)
    register_language_handlers(app)
    register_media_handler(app, helper_manager)
    
    print("FAST MEDIA DOWNLOADER BOT is running...")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await helper_manager.stop_helpers()
        await app.stop()

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
