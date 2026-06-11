import asyncio
import logging
import sys
from os import getenv
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all handlers
from handlers import start, faq, reminders, ai_chat, weather, admin, callback

# Configure logging
logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Get configuration
TOKEN = getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

# Use Memory storage
storage = MemoryStorage()
logger.info("Using Memory storage")

async def set_bot_commands(bot: Bot):
    """Set bot commands for menu"""
    commands = [
        BotCommand(command="start", description="🚀 Start the bot"),
        BotCommand(command="help", description="❓ Get help"),
        BotCommand(command="menu", description="📋 Show main menu"),
        BotCommand(command="faq", description="📚 Frequently asked questions"),
        BotCommand(command="remind", description="⏰ Set a reminder"),
        BotCommand(command="ai", description="🤖 Chat with AI"),
        BotCommand(command="weather", description="🌤 Get weather forecast"),
        BotCommand(command="cancel", description="❌ Cancel current operation"),
        BotCommand(command="stats", description="📊 Bot statistics"),
        BotCommand(command="feedback", description="💬 Send feedback"),
        BotCommand(command="admin", description="🔐 Admin panel"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")

async def on_startup(bot: Bot):
    """Actions to perform when bot starts"""
    logger.info("🚀 Bot is starting up...")
    await set_bot_commands(bot)
    
    # Send notification to admins
    admin_ids = getenv("ADMIN_IDS", "").split(",")
    for admin_id in admin_ids:
        if admin_id.strip():
            try:
                await bot.send_message(
                    int(admin_id),
                    f"✅ Bot started successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except:
                pass
    
    logger.info("✨ Bot is ready to serve!")

async def on_shutdown(bot: Bot):
    """Actions to perform when bot shuts down"""
    logger.info("🛑 Bot is shutting down...")
    
    # Notify admins
    admin_ids = getenv("ADMIN_IDS", "").split(",")
    for admin_id in admin_ids:
        if admin_id.strip():
            try:
                await bot.send_message(
                    int(admin_id),
                    f"⚠️ Bot is shutting down at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except:
                pass
    
    await bot.session.close()
    logger.info("✅ Bot shutdown complete")

async def main():
    """Main function to run the bot"""
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)
    
    # Register startup/shutdown events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Include all routers
    dp.include_router(start.router)
    dp.include_router(faq.router)
    dp.include_router(reminders.router)
    dp.include_router(ai_chat.router)
    dp.include_router(weather.router)
    dp.include_router(admin.router)
    dp.include_router(callback.router)
    
    # Start polling
    try:
        logger.info("🔄 Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Error while polling: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹ Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)