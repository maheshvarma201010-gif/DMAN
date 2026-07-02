import os
from dotenv import load_dotenv

load_dotenv("config.env")

# Core Telegram API Credentials
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Database
MONGODB_URI = os.getenv("MONGODB_URI", "")

# Access Control
OWNER_ID = int(os.getenv("OWNER_ID", 0))
AUTH_USERS = set(int(x) for x in os.getenv("AUTH_USERS", "").split() if x.isdigit())
AUTH_USERS.add(OWNER_ID)
AUTH_CHAT_ID = int(os.getenv("AUTH_CHAT_ID", OWNER_ID))

# Credentials
HELPER_BOT_TOKENS = os.getenv("HELPER_BOT_TOKENS", "").split()
SESSION_STRINGS = os.getenv("SESSION_STRINGS", "").split()

# Logging & Monitoring
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", 0))

# Performance & Storage
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
TEMP_DIR = os.getenv("TEMP_DIR", "temp")

REQUIRED_VARS = ["API_ID", "API_HASH", "BOT_TOKEN", "MONGODB_URI", "OWNER_ID"]

def validate_config():
    missing = []
    for var in REQUIRED_VARS:
        val = globals().get(var)
        if not val or val == 0:
            missing.append(var)
    return missing
