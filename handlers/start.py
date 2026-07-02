from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import add_user, is_admin
from config import OWNER_ID

def register_start(app: Client):
    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(client, message):
        # CORE FEATURE: Works only with admin-controlled start
        if not await is_admin(message.from_user.id, OWNER_ID):
            await message.reply_text("⛔ **Access Denied.**\nThis bot is for authorized admins only.")
            return

        # Register admin in DB if they use start
        await add_user(message.from_user.id, message.from_user.username)
        
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
