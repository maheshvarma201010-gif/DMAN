import asyncio
import math
import os
import time
from pyrogram import Client, utils
from pyrogram.raw import functions, types
from config import API_ID, API_HASH, SESSION_STRINGS
from core.database import get_helper_bots, get_session_strings
from core.logger import bot_logger as logger

class HelperManager:
    def __init__(self, bot_tokens):
        self.tokens = bot_tokens
        self.helpers = []
        self.user_clients = []
        self._bot_idx = 0

    async def start_helpers(self, main_bot_token=None):
        """Initializes and starts all helper bots and session strings."""
        db_helpers = await get_helper_bots()
        db_tokens = [h['token'] for h in db_helpers]
        all_tokens = list(set(self.tokens + db_tokens))

        for i, token in enumerate(all_tokens):
            if token == main_bot_token:
                logger.info(f"Skipping helper bot {i} as it matches the main bot token.")
                continue
            if not token: continue
            try:
                helper = Client(
                    f"helper_bot_{i}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    in_memory=True
                )
                await helper.start()
                self.helpers.append(helper)
                logger.info(f"Helper bot {i} started.")
            except Exception as e:
                logger.error(f"Failed to start helper bot {i}: {e}")

        db_sessions = await get_session_strings()
        db_strs = [s['session'] for s in db_sessions]
        all_sessions = list(set(SESSION_STRINGS + db_strs))

        for i, session in enumerate(all_sessions):
            if not session: continue
            try:
                u_client = Client(
                    f"user_client_{i}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=session,
                    in_memory=True
                )
                await u_client.start()
                self.user_clients.append(u_client)
                logger.info(f"User client {i} started.")
            except Exception as e:
                logger.error(f"Failed to start user client {i}: {e}")

    async def stop_helpers(self):
        """Stops all running helper bots and user clients."""
        for client in self.helpers + self.user_clients:
            try:
                await client.stop()
            except Exception:
                pass
        logger.info("All auxiliary clients stopped.")

    def get_helper(self):
        """Returns the next available helper client in round-robin."""
        all_clients = self.helpers + self.user_clients
        if not all_clients:
            return None

        client = all_clients[self._bot_idx % len(all_clients)]
        self._bot_idx += 1
        return client

async def fast_download(client: Client, message, file_path, progress_fn, progress_args):
    """
    Standard Pyrogram download_media is used here.
    While parallel chunking for a single file is complex,
    latest Pyrogram with TgCrypto and multiple helper clients (HelperManager)
    provides excellent performance for concurrent tasks.
    """
    return await client.download_media(
        message,
        file_name=file_path,
        progress=progress_fn,
        progress_args=progress_args
    )

def human_readable_size(size, decimal_places=2):
    """Converts bytes to a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
