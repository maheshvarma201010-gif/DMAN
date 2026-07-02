import os
import time
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from core.database import get_user_lang, is_admin, log_file_process
from config import OWNER_ID, AUTH_CHAT_ID, DOWNLOAD_DIR, MAX_WORKERS, AUTH_USERS
from utils.ffmpeg_utils import get_audio_track_index, process_media
from utils.helpers import human_readable_size, fast_download
from core.logger import download_logger as logger

# Global queue dictionary: {user_id: asyncio.Queue}
user_queues = {}
# Global worker dictionary: {user_id: asyncio.Task}
user_workers = {}

async def media_worker(user_id, client, helper_manager):
    """Worker that processes tasks from a specific user's queue."""
    queue = user_queues[user_id]
    while True:
        message = await queue.get()
        try:
            await process_media_task(client, message, helper_manager)
        except Exception as e:
            logger.error(f"Error in media_worker for user {user_id}: {e}")
        finally:
            queue.task_done()

def register_media_handler(app: Client, helper_manager):

    @app.on_message((filters.video | filters.document | filters.audio | filters.video_note) & (filters.chat(AUTH_CHAT_ID) | filters.user(list(AUTH_USERS)) | filters.private))
    async def media_handler(client, message):
        # Access control: only OWNER or AUTH_USERS or AUTH_CHAT
        user_id = message.from_user.id if message.from_user else None

        if not user_id:
            return

        # Check if user is authorized or chat is authorized
        is_auth_chat = message.chat.id == AUTH_CHAT_ID
        is_auth_user = user_id in AUTH_USERS or await is_admin(user_id, OWNER_ID)

        if not (is_auth_chat or is_auth_user):
            return

        media = message.video or message.document or message.audio or message.video_note
        if not media:
            return

        # Initialize queue and worker for user if not exists
        if user_id not in user_queues:
            user_queues[user_id] = asyncio.Queue()
            user_workers[user_id] = asyncio.create_task(media_worker(user_id, client, helper_manager))

        await user_queues[user_id].put(message)

        q_size = user_queues[user_id].qsize()
        if q_size > 1:
            await message.reply_text(f"⏳ **Added to queue.** Position: `{q_size-1}`")
        else:
            # First task starts immediately, but we don't want to spam "Added to queue"
            pass

async def process_media_task(client, message, helper_manager):
    media = message.video or message.document or message.audio or message.video_note
    user_id = message.from_user.id if message.from_user else OWNER_ID

    status_msg = await message.reply_text("📥 **Initializing...**")

    # 1. Get user preference
    lang = await get_user_lang(user_id)

    # 2. Select helper
    helper = helper_manager.get_helper() or client

    orig_filename = getattr(media, 'file_name', None) or (
        "video_note.mp4" if message.video_note else "file.mp4"
    )
    safe_filename = re.sub(r'[^\w\s\.-]', '', orig_filename).strip()
    file_path = os.path.join(DOWNLOAD_DIR, f"{int(time.time())}_{safe_filename}")

    try:
        start_time = time.time()
        await status_msg.edit_text("📥 **Downloading...**")

        path = await fast_download(
            helper,
            message,
            file_path=file_path,
            progress_fn=progress_func,
            progress_args=(status_msg, "📥 **Downloading at max speed...**", start_time)
        )

        if not path:
            return await status_msg.edit_text("❌ Download failed.")

        await status_msg.edit_text("🔍 **Detecting audio tracks...**")
        audio_index, available_langs = await get_audio_track_index(path, lang)

        if audio_index is None:
            avail_text = "\n".join([f"• {l.capitalize()}" for l in available_langs]) if available_langs else "None"
            await status_msg.edit_text(f"❌ **Language `{lang}` not found.**\n\n**Available:**\n{avail_text}")
            if os.path.exists(path): os.remove(path)
            return

        await status_msg.edit_text(f"⚙️ **Processing `{lang}` audio...**")
        output_path = path + ".processed.mp4"
        success = await process_media(path, output_path, audio_index)

        if not success or not os.path.exists(output_path):
            await status_msg.edit_text("❌ FFmpeg processing failed.")
            if os.path.exists(path): os.remove(path)
            return

        await status_msg.edit_text("📤 **Uploading...**")
        mention = f"@{message.from_user.username}" if (message.from_user and message.from_user.username) else str(user_id)
        final_filename = f"{mention} {safe_filename}"
        if not final_filename.lower().endswith(".mp4"):
            final_filename += ".mp4"

        start_time = time.time()
        # Uploading via the main client for reliability, or helper if needed
        await client.send_video(
            chat_id=message.chat.id,
            video=output_path,
            caption=f"✅ **Processed!**\n🌍 **Language:** `{lang.capitalize()}`",
            file_name=final_filename,
            supports_streaming=True,
            progress=progress_func,
            progress_args=(status_msg, "📤 **Uploading...**", start_time)
        )

        await status_msg.delete()
        await log_file_process(user_id, final_filename, "success")

    except FloodWait as e:
        await asyncio.sleep(e.value)
        # Should we re-add to queue? For now just log.
    except Exception as e:
        logger.error(f"Error in process_media_task: {e}")
        await status_msg.edit_text(f"❌ **Error:** `{str(e)}`")
    finally:
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
