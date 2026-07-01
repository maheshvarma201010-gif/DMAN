import os
import time
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from core.database import is_admin, get_user_lang
from config import OWNER_ID
from utils.ffmpeg_utils import get_audio_track_index, process_media
from utils.helpers import human_readable_size

def register_media_handler(app: Client, helper_manager):

    @app.on_message((filters.video | filters.document | filters.audio) & filters.private)
    async def media_handler(client, message):
        # Restriction: ONLY ADMINS CAN USE
        if not await is_admin(message.from_user.id, OWNER_ID):
            return

        media = message.video or message.document or message.audio
        if not media:
            return

        # Check if it's actually a video or something FFmpeg can handle
        # For simplicity, we'll try to process any document/video/audio
        
        status_msg = await message.reply_text("📥 **Downloading...**")
        
        # 1. Get user preferred language
        lang = await get_user_lang(message.from_user.id)
        
        # 2. Select a helper bot for download
        helper = helper_manager.get_helper() or client

        start_time = time.time()
        file_path = f"downloads/{message.from_user.id}_{int(time.time())}_{media.file_name}"
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        path = None
        output_path = None
        try:
            # Download using helper bot
            # Note: Helper bot must be in the same chat or the file must be accessible.
            # Since it's a private DM to the main bot, helper bot might not see it unless we forward it.
            # However, Pyrogram's download_media can often work if the file_id is valid for that bot.
            # But usually, helper bots are used to avoid main bot's flood limits.
            # If the helper hasn't seen the message, it might fail.
            # Better: use the helper bot if the file was forwarded or just use client if helper is not available.
            # For "FAST MEDIA DOWNLOADER", we'll try to download with the helper.
            
            # Forwarding to helper might be needed but let's assume helper can download by file_id
            # (which is not always true for different bots).
            # If helper fails, fallback to main bot.
            
            try:
                path = await helper.download_media(
                    message,
                    file_name=file_path,
                    progress=progress_func,
                    progress_args=(status_msg, "📥 **Downloading...**", start_time)
                )
            except Exception as e:
                logging.warning(f"Helper download failed: {e}. Falling back to main bot.")
                path = await client.download_media(
                    message,
                    file_name=file_path,
                    progress=progress_func,
                    progress_args=(status_msg, "📥 **Downloading...**", start_time)
                )
            
            if not path:
                return await status_msg.edit_text("❌ **Download failed.**")

            await status_msg.edit_text("🔍 **Probing audio tracks...**")

            # 3. Detect correct audio track
            audio_index = await get_audio_track_index(path, lang)
            if audio_index is None:
                await status_msg.edit_text("❌ **No audio tracks found!**")
                if os.path.exists(path): os.remove(path)
                return

            await status_msg.edit_text(f"⚙️ **Processing with FFmpeg...**\nSelected Audio Index: `{audio_index}`")

            # 4. Process with FFmpeg
            output_path = path + ".mp4"
            success = await process_media(path, output_path, audio_index)

            if not success or not os.path.exists(output_path):
                await status_msg.edit_text("❌ **FFmpeg processing failed.**")
                if os.path.exists(path): os.remove(path)
                return

            await status_msg.edit_text("📤 **Uploading...**")

            # 5. Upload processed file
            mention = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            final_filename = f"{mention}_{media.file_name}"
            if not final_filename.endswith(".mp4"):
                final_filename += ".mp4"

            start_time = time.time()
            await client.send_video(
                chat_id=message.chat.id,
                video=output_path,
                caption=f"✅ **Processed successfully!**\n🌍 **Language:** `{lang.capitalize()}`",
                file_name=final_filename,
                progress=progress_func,
                progress_args=(status_msg, "📤 **Uploading...**", start_time)
            )

            await status_msg.delete()

        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            logging.error(f"Media handler error: {e}")
            await status_msg.edit_text(f"❌ **Error:** `{str(e)}`")
        finally:
            # Cleanup
            if path and os.path.exists(path): os.remove(path)
            if output_path and os.path.exists(output_path): os.remove(output_path)

async def progress_func(current, total, message, text, start_time):
    # Use the message object to store the last update time per-message
    now = time.time()
    last_update = getattr(message, "last_update", 0)

    if now - last_update < 5:
        return

    message.last_update = now

    percentage = current * 100 / total
    speed = current / (now - start_time)
    eta = (total - current) / speed if speed > 0 else 0

    progress_bar = "".join(["▰" if i < percentage / 10 else "▱" for i in range(10)])

    tmp = (
        f"{text}\n\n"
        f"```{progress_bar} {percentage:.1f}%```\n"
        f"🚀 **Speed:** `{human_readable_size(speed)}/s`\n"
        f"⏳ **ETA:** `{time.strftime('%M:%S', time.gmtime(eta))}`\n"
        f"📦 **Size:** `{human_readable_size(current)} / {human_readable_size(total)}`"
    )

    try:
        await message.edit_text(tmp)
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception:
        pass
