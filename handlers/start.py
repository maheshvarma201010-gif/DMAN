from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import add_user, is_admin
from config import OWNER_ID, AUTH_CHAT_ID, AUTH_USERS

def register_start(app: Client):
    @app.on_message(filters.command("start") & (filters.chat(AUTH_CHAT_ID) | filters.user(list(AUTH_USERS)) | filters.private))
    async def start_handler(client, message):
        user_id = message.from_user.id if message.from_user else None
        if not user_id: return

        # CORE FEATURE: Works only with admin-controlled start
        if not await is_admin(user_id, OWNER_ID):
            if message.chat.type == "private":
                await message.reply_text("⛔ **Access Denied.**\nThis bot is for authorized admins only.")
            return

        # Register admin in DB if they use start
        await add_user(user_id, message.from_user.username)
        
        buttons = [
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("🌍 Language", callback_data="set_lang")
            ],
            [
                InlineKeyboardButton("🤖 Helper Bots", callback_data="helpers_list"),
                InlineKeyboardButton("📊 Status", callback_data="bot_status")
            ]
        ]

        await message.reply_text(
            "👋 **Welcome Admin!**\n\n"
            "I am the **FAST MEDIA DOWNLOADER BOT**.\n"
            "Fast, smooth, and optimized video/audio processing.\n\n"
            "Use the panel below to manage settings.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
