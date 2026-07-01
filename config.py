import os
from dotenv import load_dotenv

load_dotenv()

# Fill these with your actual credentials
#@cantarellabots
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGODB_URI", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0)) # Maintain compatibility
AUTH_CHAT_ID = int(os.environ.get("AUTH_CHAT_ID", OWNER_ID))
HELPER_BOT_TOKENS = os.environ.get("HELPER_BOT_TOKENS", "").split()
SESSION_STRING = os.environ.get("SESSION_STRING", "")
#@cantarellabots
