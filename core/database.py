import dns.resolver
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

# Fix for Termux: dnspython needs a resolver configuration
try:
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
except Exception:
    pass

#@cantarellabots
if not MONGO_URI:
    raise ValueError("MONGODB_URI is not set in environment variables.")

client = AsyncIOMotorClient(MONGO_URI)
db = client.fast_media_bot
#@cantarellabots
users_db = db.users
admins_db = db.admins
helpers_db = db.helpers
settings_db = db.settings

async def add_user(user_id, username):
    await users_db.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "banned": False}},
        upsert=True
    )

async def is_banned(user_id):
    user = await users_db.find_one({"user_id": user_id})
    return user.get("banned", False) if user else False

async def ban_user(user_id):
    await users_db.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True}},
        upsert=True
    )

async def unban_user(user_id):
    await users_db.update_one(
        {"user_id": user_id},
        {"$set": {"banned": False}}
    )

async def get_all_users_count():
    return await users_db.count_documents({})

async def add_admin(user_id):
    await admins_db.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": True}},
        upsert=True
    )

async def is_admin(user_id, owner_id):
    if user_id == owner_id:
        return True
    admin = await admins_db.find_one({"user_id": user_id})
    return bool(admin)

# New Functions for FAST MEDIA DOWNLOADER BOT

async def set_user_lang(user_id, lang):
    await users_db.update_one(
        {"user_id": user_id},
        {"$set": {"language_pref": lang}},
        upsert=True
    )

async def get_user_lang(user_id):
    user = await users_db.find_one({"user_id": user_id})
    return user.get("language_pref", "english") if user else "english"

async def add_helper_bot(token):
    await helpers_db.update_one(
        {"token": token},
        {"$set": {"active": True}},
        upsert=True
    )

async def remove_helper_bot(token):
    await helpers_db.delete_one({"token": token})

async def get_helper_bots():
    return await helpers_db.find({"active": True}).to_list(length=100)

async def get_bot_settings():
    settings = await settings_db.find_one({"id": "bot_settings"})
    if not settings:
        return {"id": "bot_settings", "maint_mode": False}
    return settings

async def update_bot_settings(settings_dict):
    await settings_db.update_one(
        {"id": "bot_settings"},
        {"$set": settings_dict},
        upsert=True
    )
