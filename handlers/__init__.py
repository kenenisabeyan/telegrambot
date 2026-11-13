from aiogram import Router

from . import start
from . import faq
from . import reminders
from . import ai_chat
from . import weather
from . import admin
from . import callback
from . import bot_manager
from . import inline

def setup_routers() -> Router:
    """Master router consolidating all domain handlers in priority order."""
    root_router = Router(name="root_router")
    root_router.include_router(start.router)
    root_router.include_router(faq.router)
    root_router.include_router(reminders.router)
    root_router.include_router(ai_chat.router)
    root_router.include_router(weather.router)
    root_router.include_router(admin.router)
    root_router.include_router(callback.router)
    root_router.include_router(bot_manager.router)
    root_router.include_router(inline.router)
    return root_router

__all__ = [
    'start',
    'faq',
    'reminders',
    'ai_chat',
    'weather',
    'admin',
    'callback',
    'bot_manager',
    'inline',
    'setup_routers',
]
