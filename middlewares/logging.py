import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.telemetry import telemetry

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
        cmd = None
        if isinstance(event, Message):
            event_desc = f"Message(text={repr(event.text[:30] if event.text else '')})"
            if event.text and event.text.startswith('/'):
                cmd = event.text.split()[0].lower()
        elif isinstance(event, CallbackQuery):
            event_desc = f"CallbackQuery(data={repr(event.data)})"
            if event.data:
                cmd = f"cb:{event.data.split('_')[0]}"

        try:
            result = await handler(event, data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            telemetry.record_update(elapsed_ms, command=cmd)
            logger.info(f"Processed {event_desc} from {user_info} in {elapsed_ms:.2f}ms")
            return result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            telemetry.record_update(elapsed_ms, command=cmd)
            telemetry.record_error()
            logger.error(f"Failed {event_desc} from {user_info} in {elapsed_ms:.2f}ms: {exc}")
            raise exc
