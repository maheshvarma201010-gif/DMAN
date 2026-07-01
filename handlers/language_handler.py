from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import set_user_lang, get_user_lang, is_admin
from config import OWNER_ID

def register_language_handlers(app: Client):
    @app.on_message(filters.command("language") & filters.private)
    async def language_command(client, message):
        # Open to all users as requested
        if len(message.command) > 1:
            lang = message.command[1].lower()
            await set_user_lang(message.from_user.id, lang)
            await message.reply_text(f"✅ **Language set to:** `{lang.capitalize()}`")
        else:
            current_lang = await get_user_lang(message.from_user.id)
            await message.reply_text(
                f"🌍 **Current Language:** `{current_lang.capitalize()}`\n\n"
                "Use `/language <name>` to change it or use the buttons below.",
                reply_markup=get_language_buttons()
            )

    @app.on_callback_query(filters.regex("^set_lang"))
    async def set_lang_callback(client, callback_query):
        # Open to all users as requested
        await callback_query.message.edit_text(
            "🌍 **Select your preferred audio language:**",
            reply_markup=get_language_buttons()
        )

    @app.on_callback_query(filters.regex("^lang_"))
    async def lang_select_callback(client, callback_query):
        # Open to all users as requested
        lang = callback_query.data.split("_")[1]
        await set_user_lang(callback_query.from_user.id, lang)
        await callback_query.answer(f"Language set to {lang.capitalize()}", show_alert=True)
        await callback_query.message.edit_text(f"✅ **Language set to:** `{lang.capitalize()}`")

def get_language_buttons():
    languages = ["Telugu", "Tamil", "Hindi", "English", "Malayalam", "Kannada"]
    buttons = []
    for i in range(0, len(languages), 2):
        row = [
            InlineKeyboardButton(languages[i], callback_data=f"lang_{languages[i].lower()}"),
        ]
        if i + 1 < len(languages):
            row.append(InlineKeyboardButton(languages[i+1], callback_data=f"lang_{languages[i+1].lower()}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)
