import dns.resolver
import logging
import asyncio
import socket
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Fix for Termux/Colab DNS: dnspython needs a resolver configuration
def setup_dns():
    try:
        # Check if we can resolve google.com normally first
        socket.gethostbyname("google.com")
        logger.info("System DNS is working correctly.")
    except Exception:
        logger.warning("System DNS failed. Applying custom resolver fallback...")
        try:
            resolver = dns.resolver.Resolver(configure=False)
            resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
            dns.resolver.default_resolver = resolver
            logger.info("Custom DNS resolver configured (8.8.8.8, 1.1.1.1).")
        except Exception as e:
            logger.error(f"Failed to setup custom DNS: {e}")

setup_dns()

class Database:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.client = None
        self.db = None
        self.users_db = None
        self.admins_db = None
        self.helpers_db = None
        self.settings_db = None

    async def connect(self, retries=5, delay=5):
        async with self._lock:
            if self.db:
                return True
            if not MONGODB_URI:
                logger.error("MONGODB_URI is empty. DB features will not work.")
                return False

            # Simplified URI for better compatibility if srv fails
            uri = MONGODB_URI

            for i in range(retries):
                try:
                    logger.info(f"Connecting to MongoDB (Attempt {i+1}/{retries})...")
                    self.client = AsyncIOMotorClient(
                        uri,
                        serverSelectionTimeoutMS=10000,
                        connectTimeoutMS=20000,
                        retryWrites=True
                    )
                    # Test connection
                    await self.client.admin.command('ping')
                    self.db = self.client.fast_media_bot
                    self.users_db = self.db.users
                    self.admins_db = self.db.admins
                    self.helpers_db = self.db.helpers
                    self.settings_db = self.db.settings
                    logger.info("Successfully connected to MongoDB.")
                    return True
                except Exception as e:
                    logger.error(f"MongoDB connection attempt {i+1} failed: {e}")
                    if i < retries - 1:
                        await asyncio.sleep(delay)
            return False

db_instance = Database()

# Helper to ensure DB is connected before use
async def ensure_db():
    if not db_instance.db:
        success = await db_instance.connect()
        if not success:
            raise Exception("Database connection failed after multiple retries.")

async def add_user(user_id, username):
    await ensure_db()
    try:
        await db_instance.users_db.update_one(
            {"user_id": user_id},
            {"$set": {"username": username, "banned": False}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"DB Error (add_user): {e}")

async def is_banned(user_id):
    await ensure_db()
    try:
        user = await db_instance.users_db.find_one({"user_id": user_id})
        return user.get("banned", False) if user else False
    except Exception:
        return False

async def ban_user(user_id):
    await ensure_db()
    await db_instance.users_db.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True}},
        upsert=True
    )

async def unban_user(user_id):
    await ensure_db()
    await db_instance.users_db.update_one(
        {"user_id": user_id},
        {"$set": {"banned": False}}
    )

async def get_all_users_count():
    await ensure_db()
    return await db_instance.users_db.count_documents({})

async def add_admin(user_id):
    await ensure_db()
    await db_instance.admins_db.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": True}},
        upsert=True
    )

async def is_admin(user_id, owner_id):
    if user_id == owner_id:
        return True
    try:
        await ensure_db()
        admin = await db_instance.admins_db.find_one({"user_id": user_id})
        return bool(admin)
    except Exception:
        return False

async def set_user_lang(user_id, lang):
    await ensure_db()
    try:
        await db_instance.users_db.update_one(
            {"user_id": user_id},
            {"$set": {"language_pref": lang}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"DB Error (set_user_lang): {e}")

async def get_user_lang(user_id):
    try:
        await ensure_db()
        user = await db_instance.users_db.find_one({"user_id": user_id})
        return user.get("language_pref", "english") if user else "english"
    except Exception:
        return "english"

async def add_helper_bot(token):
    await ensure_db()
    await db_instance.helpers_db.update_one(
        {"token": token},
        {"$set": {"active": True}},
        upsert=True
    )

async def remove_helper_bot(token):
    await ensure_db()
    await db_instance.helpers_db.delete_one({"token": token})

async def get_helper_bots():
    await ensure_db()
    try:
        return await db_instance.helpers_db.find({"active": True}).to_list(length=100)
    except Exception:
        return []

async def get_bot_settings():
    try:
        await ensure_db()
        settings = await db_instance.settings_db.find_one({"id": "bot_settings"})
        if not settings:
            return {"id": "bot_settings", "maint_mode": False}
        return settings
    except Exception:
        return {"id": "bot_settings", "maint_mode": False}

async def update_bot_settings(settings_dict):
    await ensure_db()
    await db_instance.settings_db.update_one(
        {"id": "bot_settings"},
        {"$set": settings_dict},
        upsert=True
    )
