import re
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger("bot.error_boundary")

def sanitize_sensitive_data(text: str) -> str:
    """Mask tokens, passwords, and API keys from error outputs."""
    if not text:
        return text
    # Mask bot tokens (e.g., 123456789:AAFg...)
    text = re.sub(r'\d{6,12}:[A-Za-z0-9_-]{30,50}', '[REDACTED_BOT_TOKEN]', text)
    # Mask DB credentials (e.g., postgresql://user:pass@host)
    text = re.sub(r'(postgresql:\/\/[^:]+:)[^@]+(@)', r'\1[REDACTED_PASSWORD]\2', text)
    # Mask OpenAI / API keys (e.g., sk-...)
    text = re.sub(r'sk-[A-Za-z0-9_-]{20,}', '[REDACTED_API_KEY]', text)
    return text

class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Exception boundary middleware.
    Safely captures unhandled exceptions, sanitizes sensitive data, and responds gracefully to users.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            raw_err = str(e)
            safe_err = sanitize_sensitive_data(raw_err)
            user = data.get("event_from_user")
            user_id = user.id if user else "Unknown"
            
            logger.error(f"Unhandled exception for user {user_id}: {safe_err}", exc_info=True)
            
            friendly_msg = (
                "⚠️ <b>An unexpected error occurred.</b>\n"
                "Our engineering team has been notified. Please try again in a few moments."
            )
            
            try:
                if isinstance(event, Message):
                    await event.answer(friendly_msg, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ An error occurred. Please try again.", show_alert=True)
            except Exception as notify_err:
                logger.debug(f"Could not deliver error notification to user: {notify_err}")
                
            return None
