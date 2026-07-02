from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import set_user_lang, get_user_lang, is_admin
from config import OWNER_ID, AUTH_CHAT_ID, AUTH_USERS

def register_language_handlers(app: Client):
    @app.on_message(filters.command("language") & (filters.chat(AUTH_CHAT_ID) | filters.user(list(AUTH_USERS)) | filters.private))
    async def language_command(client, message):
        # Language selection is open to users who can access the bot
        user_id = message.from_user.id if message.from_user else None
        if not user_id: return

        is_auth_chat = message.chat.id == AUTH_CHAT_ID
        is_auth_user = user_id in AUTH_USERS or await is_admin(user_id, OWNER_ID)
        if not (is_auth_chat or is_auth_user):
            return

        if len(message.command) > 1:
            lang = " ".join(message.command[1:]).lower()
            await set_user_lang(user_id, lang)
            await message.reply_text(f"✅ **Language set to:** `{lang.capitalize()}`")
        else:
            current_lang = await get_user_lang(user_id)
            await message.reply_text(
                f"🌍 **Current Preferred Language:** `{current_lang.capitalize()}`\n\n"
                "Select a language below or use `/language <name>` to automatically extract it from videos:",
                reply_markup=get_language_buttons()
            )

    @app.on_callback_query(filters.regex("^set_lang$"))
    async def set_lang_callback(client, callback_query):
        await callback_query.message.edit_text(
            "🌍 **Select your preferred audio language:**",
            reply_markup=get_language_buttons()
        )

    @app.on_callback_query(filters.regex("^lang_"))
    async def lang_select_callback(client, callback_query):
        lang = callback_query.data.split("_")[1]
        await set_user_lang(callback_query.from_user.id, lang)
        await callback_query.answer(f"Language set to {lang.capitalize()}")
        await callback_query.message.edit_text(f"✅ **Language set to:** `{lang.capitalize()}`")

def get_language_buttons():
    languages = ["Telugu", "Tamil", "Hindi", "English", "Japanese", "Malayalam"]
    buttons = []
    for i in range(0, len(languages), 2):
        row = [
            InlineKeyboardButton(languages[i], callback_data=f"lang_{languages[i].lower()}"),
        ]
        if i + 1 < len(languages):
            row.append(InlineKeyboardButton(languages[i+1], callback_data=f"lang_{languages[i+1].lower()}"))
        buttons.append(row)

    # Back button should go to start only for admin
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_start")])
    return InlineKeyboardMarkup(buttons)
