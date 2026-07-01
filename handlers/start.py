from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import add_user, is_admin
from config import OWNER_ID, AUTH_CHAT_ID

def register_start(app: Client):
    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(client, message):
        # Restriction: ONLY ADMINS CAN USE
        if not await is_admin(message.from_user.id, OWNER_ID):
            # Ignore or silent reject as per requirements
            return

        # Register user in DB
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
            "👋 **Welcome to FAST MEDIA DOWNLOADER BOT!**\n\n"
            "I am an optimized video/audio processing bot.\n"
            "Use the buttons below to manage the bot.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
