import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

logger = logging.getLogger(__name__)

class DatabaseMiddleware(BaseMiddleware):
    """
    Dependency injection & automatic user registration middleware.
    Ensures `db` is consistently passed to handlers and keeps user activity synchronized.
    """
    def __init__(self, db=None):
        super().__init__()
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        db = data.get("db") or self.db
        if db:
            data["db"] = db
            
            # Automatically synchronize active user profile with database
            user: User = data.get("event_from_user")
            if user and not user.is_bot:
                try:
                    await db.add_user(
                        user_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name
                    )
                except Exception as e:
                    logger.debug(f"User sync skipped in DatabaseMiddleware: {e}")

        return await handler(event, data)
