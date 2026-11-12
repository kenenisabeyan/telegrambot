import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger("bot.events")

class LoggingMiddleware(BaseMiddleware):
    """
    Performance monitoring and structured logging middleware.
    Tracks update execution duration, originating user, and action payloads.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.perf_counter()
        user = data.get("event_from_user")
        user_info = f"user_id={user.id}" if user else "anonymous"

        event_desc = "unknown"
        if isinstance(event, Message):
            event_desc = f"Message(text={repr(event.text[:30] if event.text else '')})"
        elif isinstance(event, CallbackQuery):
            event_desc = f"CallbackQuery(data={repr(event.data)})"

        try:
            result = await handler(event, data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Processed {event_desc} from {user_info} in {elapsed_ms:.2f}ms")
            return result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Failed {event_desc} from {user_info} in {elapsed_ms:.2f}ms: {exc}")
            raise exc
