import os
from dotenv import load_dotenv

load_dotenv("config.env")

# Default values and environment variables
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGODB_URI = os.getenv("MONGODB_URI", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
AUTH_CHAT_ID = int(os.getenv("AUTH_CHAT_ID", OWNER_ID))
HELPER_BOT_TOKENS = os.getenv("HELPER_BOT_TOKENS", "").split()
SESSION_STRING = os.getenv("SESSION_STRING", "")

REQUIRED_VARS = ["API_ID", "API_HASH", "BOT_TOKEN", "MONGODB_URI"]

def validate_config():
    missing = []
    for var in REQUIRED_VARS:
        if not globals().get(var) or globals().get(var) == 0:
            missing.append(var)
    return missing
