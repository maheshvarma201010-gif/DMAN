import asyncio
import logging
from pyrogram import Client
from config import API_ID, API_HASH

logger = logging.getLogger(__name__)

class HelperManager:
    def __init__(self, bot_tokens):
        self.tokens = bot_tokens
        self.helpers = []
        self._current = 0

    async def start_helpers(self):
        """Initializes and starts all helper bots."""
        if not self.tokens:
            logger.info("No helper bot tokens provided.")
            return

        for i, token in enumerate(self.tokens):
            try:
                # Use in_memory sessions for helpers to avoid session file clutter
                helper = Client(
                    f"helper_{i}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    in_memory=True
                )
                await helper.start()
                self.helpers.append(helper)
                logger.info(f"Helper bot {i} started successfully.")
            except Exception as e:
                logger.error(f"Failed to start helper bot {i}: {e}")

    async def stop_helpers(self):
        """Stops all running helper bots."""
        for helper in self.helpers:
            try:
                await helper.stop()
            except Exception:
                pass
        logger.info("All helper bots stopped.")

    def get_helper(self):
        """Returns the next helper bot in a round-robin fashion."""
        if not self.helpers:
            return None

        helper = self.helpers[self._current]
        self._current = (self._current + 1) % len(self.helpers)
        return helper

def human_readable_size(size, decimal_places=2):
    """Converts bytes to a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
