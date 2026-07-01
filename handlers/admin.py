import psutil
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from core.database import (
    get_all_users_count, is_admin, add_helper_bot,
    remove_helper_bot, get_helper_bots, get_bot_settings, update_bot_settings
)

def register_admin_handlers(app: Client):

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_handler(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        await message.reply_text("⚙️ **Admin Control Panel**", reply_markup=await get_settings_buttons())

    @app.on_callback_query(filters.regex("^settings$"))
    async def settings_callback(client, callback_query):
        if not await is_admin(callback_query.from_user.id, OWNER_ID):
            return await callback_query.answer("Admin only!")
        await callback_query.message.edit_text("⚙️ **Admin Control Panel**", reply_markup=await get_settings_buttons())

    @app.on_message(filters.command("addhelper") & filters.private)
    async def add_helper_command(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        if len(message.command) < 2:
            return await message.reply_text("Usage: `/addhelper <token>`")
        token = message.command[1]
        await add_helper_bot(token)
        await message.reply_text("✅ Helper bot token added to database.")

    @app.on_message(filters.command("removehelper") & filters.private)
    async def remove_helper_command(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        if len(message.command) < 2:
            return await message.reply_text("Usage: `/removehelper <token>`")
        token = message.command[1]
        await remove_helper_bot(token)
        await message.reply_text("🗑 Helper bot token removed.")

    @app.on_message(filters.command("status") & filters.private)
    async def status_command(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            return
        await message.reply_text(await get_status_text())

    @app.on_callback_query(filters.regex("^bot_status$"))
    async def bot_status_callback(client, callback_query):
        await callback_query.message.edit_text(
            await get_status_text(),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_start")]])
        )

    @app.on_callback_query(filters.regex("^helpers_list$"))
    async def helpers_list_callback(client, callback_query):
        helpers = await get_helper_bots()
        text = "🤖 **Active Helper Bots:**\n\n"
        if not helpers:
            text += "None found in DB."
        else:
            for h in helpers:
                text += f"• `{h['token'][:15]}...` (Active)\n"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_start")]])
        )

    @app.on_callback_query(filters.regex("^back_to_start$"))
    async def back_to_start_callback(client, callback_query):
        # Trigger the start panel again
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
            "👋 **Welcome Admin!**\n\nPanel refreshed.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def get_status_text():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    users = await get_all_users_count()
    helpers = await get_helper_bots()
    return (
        "📊 **Bot Health & Workers**\n\n"
        f"🖥 **CPU:** `{cpu}%`\n"
        f"💾 **RAM:** `{ram}%`\n"
        f"👥 **Users:** `{users}`\n"
        f"🤖 **Helpers:** `{len(helpers)}`"
    )

async def get_settings_buttons():
    settings = await get_bot_settings()
    maint_text = "🟢 Maint: OFF" if not settings.get("maint_mode") else "🔴 Maint: ON"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(maint_text, callback_data="toggle_maint")],
        [InlineKeyboardButton("Back", callback_data="back_to_start")]
    ])
