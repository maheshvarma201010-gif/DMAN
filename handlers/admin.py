import psutil
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from core.database import (
    get_all_users_count, ban_user, unban_user, add_admin, is_admin,
    add_helper_bot, remove_helper_bot, get_helper_bots, get_bot_settings, update_bot_settings
)

def register_admin_handlers(app: Client):

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_handler(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        await message.reply_text("⚙️ **Bot Settings**", reply_markup=await get_settings_buttons())

    @app.on_callback_query(filters.regex("^settings$"))
    async def settings_callback(client, callback_query):
        await callback_query.message.edit_text("⚙️ **Bot Settings**", reply_markup=await get_settings_buttons())

    @app.on_callback_query(filters.regex("^toggle_maint$"))
    async def toggle_maint_callback(client, callback_query):
        if not await is_admin(callback_query.from_user.id, OWNER_ID):
            return await callback_query.answer("❌ Admin Only!", show_alert=True)
        
        settings = await get_bot_settings()
        new_state = not settings.get("maint_mode", False)
        await update_bot_settings({"maint_mode": new_state})
        
        await callback_query.answer(f"Maintenance mode {'Enabled' if new_state else 'Disabled'}")
        await callback_query.message.edit_reply_markup(reply_markup=await get_settings_buttons())

    @app.on_message(filters.command("addhelper") & filters.private)
    async def add_helper_handler(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        if len(message.command) < 2:
            return await message.reply_text("❌ Please provide a Helper Bot Token.")
        token = message.command[1]
        await add_helper_bot(token)
        await message.reply_text(f"✅ **Helper Bot added!**")

    @app.on_message(filters.command("removehelper") & filters.private)
    async def remove_helper_handler(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        if len(message.command) < 2:
            return await message.reply_text("❌ Please provide a Helper Bot Token to remove.")
        token = message.command[1]
        await remove_helper_bot(token)
        await message.reply_text(f"🗑 **Helper Bot removed.**")

    @app.on_message(filters.command("status") & filters.private)
    async def status_handler(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        
        # System status
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        users = await get_all_users_count()
        helpers = await get_helper_bots()

        status_text = (
            "📊 **Bot Status**\n\n"
            f"🖥 **CPU:** `{cpu}%`\n"
            f"💾 **RAM:** `{ram}%`\n"
            f"💿 **Disk:** `{disk}%`\n\n"
            f"👥 **Total Users:** `{users}`\n"
            f"🤖 **Active Helpers:** `{len(helpers)}`"
        )
        await message.reply_text(status_text)

    @app.on_callback_query(filters.regex("^bot_status"))
    async def bot_status_callback(client, callback_query):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        users = await get_all_users_count()
        helpers = await get_helper_bots()
        
        status_text = (
            "📊 **Bot Status**\n\n"
            f"🖥 **CPU:** `{cpu}%`\n"
            f"💾 **RAM:** `{ram}%`\n"
            f"👥 **Total Users:** `{users}`\n"
            f"🤖 **Active Helpers:** `{len(helpers)}`"
        )
        await callback_query.message.edit_text(status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_start")]]))

    @app.on_callback_query(filters.regex("^helpers_list"))
    async def helpers_list_callback(client, callback_query):
        helpers = await get_helper_bots()
        if not helpers:
            text = "❌ No active helper bots."
        else:
            text = "🤖 **Active Helper Bots:**\n\n"
            for h in helpers:
                text += f"• `{h['token'][:10]}...` (Active)\n"
        
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_start")]]))

    @app.on_callback_query(filters.regex("^back_to_start"))
    async def back_to_start_callback(client, callback_query):
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
        await callback_query.message.edit_text(
            "👋 **Welcome to FAST MEDIA DOWNLOADER BOT!**\n\n"
            "I am an optimized video/audio processing bot.\n"
            "Use the buttons below to manage the bot.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def get_settings_buttons():
    settings = await get_bot_settings()
    maint_text = "🟢 Maint: OFF" if not settings.get("maint_mode") else "🔴 Maint: ON"
    buttons = [
        [InlineKeyboardButton(maint_text, callback_data="toggle_maint")],
        [InlineKeyboardButton("Back", callback_data="back_to_start")]
    ]
    return InlineKeyboardMarkup(buttons)
