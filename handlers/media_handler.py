import os
import time
import asyncio
import logging
import re
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from core.database import get_user_lang, is_admin, log_file_process
from config import OWNER_ID, AUTH_CHAT_ID
from utils.ffmpeg_utils import get_audio_track_index, process_media
from utils.helpers import human_readable_size

logger = logging.getLogger(__name__)

def register_media_handler(app: Client, helper_manager):

    @app.on_message((filters.video | filters.document | filters.audio) & (filters.chat(AUTH_CHAT_ID) | filters.user(OWNER_ID)))
    async def media_handler(client, message):
        # Admin check for forward/file processing outside AUTH_CHAT_ID if needed
        # But per requirements: Works only with admin-controlled start.
        # Here we assume AUTH_CHAT_ID is where users interact or it's DM with admin.

        media = message.video or message.document or message.audio
        if not media:
            return

        # Core requirement: Fast processing, optimized
        status_msg = await message.reply_text("📥 **Initializing download...**")
        
        # 1. Get user preference
        user_id = message.from_user.id if message.from_user else OWNER_ID
        lang = await get_user_lang(user_id)
        
        # 2. Select helper for download
        helper = helper_manager.get_helper() or client

        orig_filename = media.file_name or "video.mp4"
        # Sanitize for shell
        safe_filename = re.sub(r'[^\w\s\.-]', '', orig_filename).strip()
        file_path = f"downloads/{int(time.time())}_{safe_filename}"

        try:
            start_time = time.time()
            # ASYNC DOWNLOAD PIPELINE
            path = await helper.download_media(
                message,
                file_name=file_path,
                progress=progress_func,
                progress_args=(status_msg, "📥 **Downloading at max speed...**", start_time)
            )

            if not path:
                return await status_msg.edit_text("❌ Download failed.")

            await status_msg.edit_text("🔍 **Detecting audio tracks...**")

            # 3. Detect correct audio track
            audio_index = await get_audio_track_index(path, lang)
            if audio_index is None:
                await status_msg.edit_text("❌ No audio tracks found in this file.")
                if os.path.exists(path): os.remove(path)
                return

            await status_msg.edit_text(f"⚙️ **FFmpeg: Mapping `{lang}` audio...**")

            # 4. FFmpeg processing
            output_path = path + ".processed.mp4"
            success = await process_media(path, output_path, audio_index)

            if not success or not os.path.exists(output_path):
                await status_msg.edit_text("❌ FFmpeg processing failed.")
                if os.path.exists(path): os.remove(path)
                return

            await status_msg.edit_text("📤 **Uploading processed file...**")

            # 5. Upload with specific filename format: {mention}_{original_filename}.mp4
            mention = f"@{message.from_user.username}" if (message.from_user and message.from_user.username) else str(user_id)
            final_filename = f"{mention}_{safe_filename}"
            if not final_filename.lower().endswith(".mp4"):
                final_filename += ".mp4"

            start_time = time.time()
            await client.send_video(
                chat_id=message.chat.id,
                video=output_path,
                caption=f"✅ **Processed successfully!**\n🌍 **Language:** `{lang.capitalize()}`",
                file_name=final_filename,
                supports_streaming=True,
                progress=progress_func,
                progress_args=(status_msg, "📤 **Uploading...**", start_time)
            )

            await status_msg.delete()
            await log_file_process(user_id, final_filename, "success")

        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.error(f"Error in media_handler: {e}")
            await status_msg.edit_text(f"❌ **Error:** `{str(e)}`")
        finally:
            # Cleanup
            if 'path' in locals() and os.path.exists(path):
                os.remove(path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)

async def progress_func(current, total, message, text, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        progress_bar = "".join(["▰" if i < percentage / 10 else "▱" for i in range(10)])

        status = (
            f"{text}\n\n"
            f"```{progress_bar} {percentage:.1f}%```\n"
            f"🚀 **Speed:** `{human_readable_size(speed)}/s`\n"
            f"⏳ **ETA:** `{time.strftime('%M:%S', time.gmtime(eta))}`\n"
            f"📦 **Size:** `{human_readable_size(current)} / {human_readable_size(total)}`"
        )
        try:
            await message.edit_text(status)
        except:
            pass
