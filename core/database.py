import dns.resolver
import asyncio
import socket
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI
from pymongo.errors import ServerSelectionTimeoutError
from core.logger import db_logger as logger

# Fix for Termux/Colab DNS
def setup_dns():
    try:
        socket.gethostbyname("google.com")
        logger.info("System DNS is working correctly.")
    except Exception:
        logger.warning("System DNS failed. Applying custom resolver fallback...")
        try:
            resolver = dns.resolver.Resolver(configure=False)
            resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
            dns.resolver.default_resolver = resolver
            logger.info("Custom DNS resolver configured.")
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
        self.sessions_db = None
        self.settings_db = None
        self.files_db = None

    async def connect(self, retries=5, delay=5):
        async with self._lock:
            if self.db is not None:
                return True
            if not MONGODB_URI:
                logger.error("MONGODB_URI is empty.")
                return False

            for i in range(retries):
                try:
                    logger.info(f"Connecting to MongoDB (Attempt {i+1}/{retries})...")
                    self.client = AsyncIOMotorClient(
                        MONGODB_URI,
                        serverSelectionTimeoutMS=10000,
                        connectTimeoutMS=20000
                    )
                    await self.client.admin.command('ping')
                    self.db = self.client.fast_media_bot
                    self.users_db = self.db.users
                    self.admins_db = self.db.admins
                    self.helpers_db = self.db.helpers
                    self.sessions_db = self.db.sessions
                    self.settings_db = self.db.settings
                    self.files_db = self.db.files
                    logger.info("Successfully connected to MongoDB.")
                    return True
                except Exception as e:
                    logger.error(f"MongoDB connection attempt {i+1} failed: {e}")
                    if i < retries - 1:
                        await asyncio.sleep(delay)
            return False

db_instance = Database()

async def ensure_db():
    if db_instance.db is None:
        success = await db_instance.connect()
        if not success:
            raise Exception("Database connection failed.")

# --- USER METHODS ---
async def add_user(user_id, username):
    await ensure_db()
    await db_instance.users_db.update_one(
        {"user_id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

async def get_all_users_count():
    await ensure_db()
    return await db_instance.users_db.count_documents({})

async def set_user_lang(user_id, lang):
    await ensure_db()
    await db_instance.users_db.update_one(
        {"user_id": user_id},
        {"$set": {"language_pref": lang}},
        upsert=True
    )

async def get_user_lang(user_id):
    await ensure_db()
    user = await db_instance.users_db.find_one({"user_id": user_id})
    return user.get("language_pref", "english") if user else "english"

# --- ADMIN METHODS ---
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
    await ensure_db()
    admin = await db_instance.admins_db.find_one({"user_id": user_id})
    return bool(admin)

# --- HELPER BOT METHODS ---
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
    return await db_instance.helpers_db.find().to_list(length=100)

async def add_session_string(session_string):
    await ensure_db()
    await db_instance.sessions_db.update_one(
        {"session": session_string},
        {"$set": {"active": True}},
        upsert=True
    )

async def remove_session_string(session_string):
    await ensure_db()
    await db_instance.sessions_db.delete_one({"session": session_string})

async def get_session_strings():
    await ensure_db()
    return await db_instance.sessions_db.find().to_list(length=100)

# --- SETTINGS METHODS ---
async def get_bot_settings():
    await ensure_db()
    settings = await db_instance.settings_db.find_one({"id": "bot_settings"})
    return settings or {"id": "bot_settings", "maint_mode": False}

async def update_bot_settings(settings_dict):
    await ensure_db()
    await db_instance.settings_db.update_one(
        {"id": "bot_settings"},
        {"$set": settings_dict},
        upsert=True
    )

# --- LOGS / METADATA ---
async def log_file_process(user_id, file_name, status):
    await ensure_db()
    await db_instance.files_db.insert_one({
        "user_id": user_id,
        "file_name": file_name,
        "status": status,
        "timestamp": asyncio.get_event_loop().time() # Simple timestamp
    })
