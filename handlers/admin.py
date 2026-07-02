import psutil
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler
from config import OWNER_ID
from core.database import (
    get_all_users_count, is_admin, add_helper_bot,
    remove_helper_bot, get_helper_bots, get_bot_settings, update_bot_settings,
    add_session_string, remove_session_string, get_session_strings
)

# In-memory state for registration
pending_add = {} # {user_id: type} where type is 'helper' or 'session'

def register_admin_handlers(app: Client):

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_handler(client, message):
        if not await is_admin(message.from_user.id, OWNER_ID):
            await message.reply_text("⛔ **Access Denied.**")
            return
        await message.reply_text("⚙️ **Admin Control Panel**", reply_markup=await get_settings_buttons())

    @app.on_callback_query(filters.regex("^settings$"))
    async def settings_callback(client, callback_query):
        if not await is_admin(callback_query.from_user.id, OWNER_ID):
            return await callback_query.answer("Admin only!", show_alert=True)
        await callback_query.message.edit_text("⚙️ **Admin Control Panel**", reply_markup=await get_settings_buttons())

    # --- Helper Bot Tokens ---
    @app.on_callback_query(filters.regex("^helpers_mgmt$"))
    async def helpers_mgmt_callback(client, callback_query):
        helpers = await get_helper_bots()
        text = "🤖 **Helper Bot Tokens**\n\n"
        buttons = []
        if not helpers:
            text += "No helper bots added yet."
        else:
            for h in helpers:
                token = h['token']
                display_token = f"{token[:10]}...{token[-5:]}"
                buttons.append([
                    InlineKeyboardButton(f"🤖 {display_token}", callback_data="none"),
                    InlineKeyboardButton("🗑", callback_data=f"del_helper_{token}")
                ])

        buttons.append([InlineKeyboardButton("➕ Add Helper Token", callback_data="add_helper")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])

        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    @app.on_callback_query(filters.regex("^add_helper$"))
    async def add_helper_callback(client, callback_query):
        user_id = callback_query.from_user.id
        pending_add[user_id] = 'helper'
        await callback_query.message.edit_text("📩 **Send the Helper Bot Token now.**",
                                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="helpers_mgmt")]]))

    @app.on_callback_query(filters.regex("^del_helper_"))
    async def del_helper_callback(client, callback_query):
        token = callback_query.data.replace("del_helper_", "")
        await remove_helper_bot(token)
        await callback_query.answer("Helper token removed.")
        await helpers_mgmt_callback(client, callback_query)

    # --- Session Strings ---
    @app.on_callback_query(filters.regex("^sessions_mgmt$"))
    async def sessions_mgmt_callback(client, callback_query):
        sessions = await get_session_strings()
        text = "🔑 **Session Strings**\n\n"
        buttons = []
        if not sessions:
            text += "No session strings added yet."
        else:
            for s in sessions:
                sess = s['session']
                display_sess = f"{sess[:10]}...{sess[-5:]}"
                # Use a hash or ID for deletion in real prod, but here we use prefix for simplicity
                buttons.append([
                    InlineKeyboardButton(f"🔑 {display_sess}", callback_data="none"),
                    InlineKeyboardButton("🗑", callback_data=f"del_sess_{sess[:15]}")
                ])

        buttons.append([InlineKeyboardButton("➕ Add Session String", callback_data="add_sess")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])

        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    @app.on_callback_query(filters.regex("^add_sess$"))
    async def add_sess_callback(client, callback_query):
        user_id = callback_query.from_user.id
        pending_add[user_id] = 'session'
        await callback_query.message.edit_text("📩 **Send the Pyrogram Session String now.**",
                                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="sessions_mgmt")]]))

    @app.on_callback_query(filters.regex("^del_sess_"))
    async def del_sess_callback(client, callback_query):
        prefix = callback_query.data.replace("del_sess_", "")
        sessions = await get_session_strings()
        for s in sessions:
            if s['session'].startswith(prefix):
                await remove_session_string(s['session'])
                break
        await callback_query.answer("Session removed.")
        await sessions_mgmt_callback(client, callback_query)

    # --- Text Handler for Adding ---
    @app.on_message(filters.text & filters.private, group=-1)
    async def admin_text_handler(client, message):
        user_id = message.from_user.id
        if user_id not in pending_add:
            message.continue_propagation()
            return

        mode = pending_add.pop(user_id)
        text = message.text.strip()

        if text.startswith("/"):
            return # Let command handlers handle it

        if mode == 'helper':
            if ":" not in text:
                await message.reply_text("❌ Invalid token format.")
            else:
                await add_helper_bot(text)
                await message.reply_text("✅ **Helper Token Added.**")
        elif mode == 'session':
            await add_session_string(text)
            await message.reply_text("✅ **Session String Added.**")

    # --- Stats ---
    @app.on_callback_query(filters.regex("^stats$"))
    async def stats_callback(client, callback_query):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        users = await get_all_users_count()
        helpers = await get_helper_bots()
        sessions = await get_session_strings()
        
        text = (
            "📊 **Bot Statistics**\n\n"
            f"🖥 **CPU Usage:** `{cpu}%`\n"
            f"💾 **RAM Usage:** `{ram}%`\n"
            f"👥 **Total Users:** `{users}`\n"
            f"🤖 **Helper Bots:** `{len(helpers)}`\n"
            f"🔑 **Sessions:** `{len(sessions)}`"
        )
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings")]]))

    @app.on_callback_query(filters.regex("^toggle_maint$"))
    async def toggle_maint_callback(client, callback_query):
        settings = await get_bot_settings()
        new_val = not settings.get("maint_mode", False)
        await update_bot_settings({"maint_mode": new_val})
        await callback_query.answer(f"Maintenance Mode: {'ON' if new_val else 'OFF'}")
        await settings_callback(client, callback_query)

async def get_settings_buttons():
    settings = await get_bot_settings()
    maint_text = "🟢 Maint: OFF" if not settings.get("maint_mode") else "🔴 Maint: ON"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Helper Bot Tokens", callback_data="helpers_mgmt")],
        [InlineKeyboardButton("🔑 Session Strings", callback_data="sessions_mgmt")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats"), InlineKeyboardButton(maint_text, callback_data="toggle_maint")],
        [InlineKeyboardButton("🔙 Back to Start", callback_data="back_to_start")]
    ])
