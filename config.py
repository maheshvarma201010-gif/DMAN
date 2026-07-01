import os
from dotenv import load_dotenv

load_dotenv("config.env")

# Default values and environment variables
API_ID = int(os.getenv("API_ID", 22266643))
API_HASH = os.getenv("API_HASH", "7d0b85b4146034511b8776ed7ff99de4")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7718434227:AAHLp23fUU7QHfXqe-TLkHRDW6G77KyFsrw")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://hemanthbreaker2027:9550399779htr@cluster0.haybbxg.mongodb.net/?appName=Cluster0")
OWNER_ID = int(os.getenv("OWNER_ID", "8614495611"))
AUTH_CHAT_ID = int(os.getenv("AUTH_CHAT_ID", -1004301661870))
HELPER_BOT_TOKENS = os.getenv("HELPER_BOT_TOKENS", "7718434227:AAHLp23fUU7QHfXqe-TLkHRDW6G77KyFsrw").split()
SESSION_STRING = os.getenv("SESSION_STRING", "")

REQUIRED_VARS = ["API_ID", "API_HASH", "BOT_TOKEN", "MONGODB_URI", "OWNER_ID"]

def validate_config():
    missing = []
    for var in REQUIRED_VARS:
        if not globals().get(var) or globals().get(var) == 0:
            missing.append(var)
    return missing
