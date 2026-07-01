import asyncio
import logging
import os
import sys
import signal
import psutil
from pyrogram import Client, idle
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, BOT_TOKEN, HELPER_BOT_TOKENS, OWNER_ID, validate_config
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
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if psutil.pid_exists(old_pid):
                logger.error(f"Another instance of the bot (PID {old_pid}) is already running.")
                sys.exit(1)
            else:
                logger.warning(f"Orphaned lock file found (PID {old_pid} not running). Overwriting...")
        except Exception:
            logger.warning("Corrupted lock file found. Overwriting...")

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def release_lock():
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass

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
        logger.info("Initializing Database connection...")
        db_connected = await db_instance.connect()
        if not db_connected:
            logger.error("Could not connect to MongoDB. Exiting.")
            release_lock()
            sys.exit(1)

        # Initialize Helper Manager
        helper_manager = HelperManager(HELPER_BOT_TOKENS)

        # Register Handlers
        logger.info("Registering handlers...")
        register_start(app)
        register_admin_handlers(app)
        register_language_handlers(app)
        register_media_handler(app, helper_manager)

        # Global Debug Handler
        @app.on_message(group=-1)
        async def debug_handler(client, message):
            logger.info(f"Received message from {message.from_user.id if message.from_user else 'Unknown'} in chat {message.chat.id}")

        # Start Bot
        logger.info("Starting main bot client...")
        while True:
            try:
                await app.start()
                break
            except FloodWait as e:
                logger.warning(f"FloodWait during app.start: {e.value} seconds. Sleeping...")
                await asyncio.sleep(e.value)
            except Exception as e:
                logger.error(f"Failed to start bot: {e}")
                release_lock()
                sys.exit(1)

        # Start Helper Bots
        logger.info("Starting helper bots...")
        await helper_manager.start_helpers()

        logger.info("FAST MEDIA DOWNLOADER BOT IS NOW RUNNING!")

        # Notify Owner
        try:
            await app.send_message(OWNER_ID, "🚀 **FAST MEDIA DOWNLOADER BOT has started!**")
        except Exception as e:
            logger.warning(f"Could not notify owner: {e}")

        # Keep running
        await idle()

    except Exception as e:
        logger.error(f"Critical unhandled exception: {e}", exc_info=True)
    finally:
        logger.info("Shutting down gracefully...")
        if 'helper_manager' in locals():
            await helper_manager.stop_helpers()
        if app.is_connected:
            await app.stop()
        release_lock()

def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, exiting...")
    # sys.exit(0) might not trigger finally in asyncio.run, so we handle it within main or by stopping the loop

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
