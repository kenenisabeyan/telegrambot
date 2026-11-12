import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)

class ThrottlingMiddleware(BaseMiddleware):
    """
    Anti-flood / Rate limiting middleware.
    Prevents flood attacks and Telegram 429 Too Many Requests errors.
    """
    def __init__(self, default_rate: float = 0.6, heavy_rate: float = 2.0):
        super().__init__()
        self.default_rate = default_rate
        self.heavy_rate = heavy_rate
        self.user_timestamps: Dict[int, float] = {}
        self.user_warned: Dict[int, float] = {}

    def _get_rate_limit(self, event: TelegramObject) -> float:
        if isinstance(event, Message) and event.text:
            text = event.text.lower().strip()
            # Heavy operations like AI or Weather get higher cooldown
            if text.startswith(('/ai', '/weather', 'ai chat', 'weather')):
                return self.heavy_rate
        return self.default_rate

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        user_id = user.id
        now = time.monotonic()
        rate_limit = self._get_rate_limit(event)

        last_time = self.user_timestamps.get(user_id, 0.0)
        time_passed = now - last_time

        if time_passed < rate_limit:
            # User is sending updates too quickly
            last_warning = self.user_warned.get(user_id, 0.0)
            # Only warn the user at most once every 3 seconds to avoid double-spamming
            if now - last_warning > 3.0:
                self.user_warned[user_id] = now
                warning_text = "⏳ <b>Slow down!</b> Please wait a moment before sending another request."
                if isinstance(event, Message):
                    await event.answer(warning_text, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⏳ Please wait a moment...", show_alert=False)
            
            logger.debug(f"Throttled request from user {user_id} (passed: {time_passed:.2f}s, required: {rate_limit:.2f}s)")
            return None

        self.user_timestamps[user_id] = now
        return await handler(event, data)
