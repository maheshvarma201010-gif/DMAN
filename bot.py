import asyncio
import os
import sys
import signal
import psutil
from pyrogram import Client, idle
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, BOT_TOKEN, HELPER_BOT_TOKENS, OWNER_ID, validate_config, DOWNLOAD_DIR
from handlers.media_handler import register_media_handler
from handlers.start import register_start
from handlers.admin import register_admin_handlers
from handlers.language_handler import register_language_handlers
from utils.helpers import HelperManager
from core.database import db_instance, get_helper_bots
from core.logger import bot_logger as logger

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

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
    
    # 1. Validate Config
    missing = validate_config()
    if missing:
        logger.error(f"Missing config variables: {', '.join(missing)}")
        release_lock()
        sys.exit(1)

    # 2. Initialize DB
    logger.info("Connecting to Database...")
    if not await db_instance.connect():
        logger.error("DB connection failed. Exiting.")
        release_lock()
        sys.exit(1)

    # 3. Initialize Helper Manager
    helper_manager = HelperManager(HELPER_BOT_TOKENS)

    # 4. Register Handlers
    logger.info("Registering handlers...")
    register_start(app)
    register_admin_handlers(app)
    register_language_handlers(app)
    register_media_handler(app, helper_manager)

    # 5. Start Bot & Helpers
    logger.info("Starting main bot client...")
    try:
        await app.start()

        logger.info("Starting helper manager (bots & sessions)...")
        await helper_manager.start_helpers()

        logger.info("FAST MEDIA DOWNLOADER BOT IS NOW RUNNING!")

        # Notify Owner
        try:
            await app.send_message(OWNER_ID, "🚀 **Bot Started Successfully!**")
        except Exception as e:
            logger.warning(f"Could not notify owner: {e}")

        await idle()
    except Exception as e:
        logger.error(f"Error during runtime: {e}")
    finally:
        # Graceful Shutdown
        logger.info("Shutting down...")
        await helper_manager.stop_helpers()
        if app.is_connected:
            await app.stop()
        release_lock()

if __name__ == "__main__":
    # Create required dirs
    for d in [DOWNLOAD_DIR, "sessions", "temp", "logs"]:
        if not os.path.exists(d):
            os.makedirs(d)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.fatal(f"Unhandled exception: {e}")
        release_lock()
