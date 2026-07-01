import asyncio
import logging
from pyrogram import Client
from config import API_ID, API_HASH

class HelperManager:
    def __init__(self, bot_tokens):
        self.tokens = bot_tokens
        self.helpers = []
        self._current = 0

    async def start_helpers(self):
        for i, token in enumerate(self.tokens):
            try:
                helper = Client(
                    f"helper_{i}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    in_memory=True
                )
                await helper.start()
                self.helpers.append(helper)
                logging.info(f"Helper {i} started successfully.")
            except Exception as e:
                logging.error(f"Failed to start helper {i}: {e}")

    async def stop_helpers(self):
        for helper in self.helpers:
            await helper.stop()

    def get_helper(self):
        if not self.helpers:
            return None
        helper = self.helpers[self._current]
        self._current = (self._current + 1) % len(self.helpers)
        return helper

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
