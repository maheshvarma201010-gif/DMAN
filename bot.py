import asyncio
import logging
import os
import sys
import signal
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, HELPER_BOT_TOKENS, validate_config
from handlers.media_handler import register_media_handler
from handlers.start import register_start
from handlers.admin import register_admin_handlers
from handlers.language_handler import register_language_handlers
from utils.helpers import HelperManager
from core.database import db_instance

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOCK_FILE = "bot.lock"

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        logger.error("Another instance of the bot is already running (bot.lock exists).")
        sys.exit(1)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

app = Client(
    "fast_media_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="sessions"
)

async def main():
    acquire_lock()
    
    # Validate config
    missing_vars = validate_config()
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your config.env file.")
        release_lock()
        sys.exit(1)

    try:
        # Initialize Database
        db_connected = await db_instance.connect()
        if not db_connected:
            logger.error("Could not connect to MongoDB. Exiting.")
            release_lock()
            sys.exit(1)

        # Start Bot
        logger.info("Starting main bot...")
        await app.start()

        # Initialize and Start Helper Bots
        helper_manager = HelperManager(HELPER_BOT_TOKENS)
        await helper_manager.start_helpers()

        # Register Handlers
        register_start(app)
        register_admin_handlers(app)
        register_language_handlers(app)
        register_media_handler(app, helper_manager)

        logger.info("FAST MEDIA DOWNLOADER BOT is running...")

        # Keep running
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
    finally:
        logger.info("Shutting down...")
        if 'helper_manager' in locals():
            await helper_manager.stop_helpers()
        if app.is_connected:
            await app.stop()
        release_lock()

def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, exiting...")
    sys.exit(0)

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    if not os.path.exists("sessions"):
        os.makedirs("sessions")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
