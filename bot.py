import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import handlers (we'll create these next)
from handlers import start, faq, reminders, ai_chat, weather

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Get bot token
TOKEN = getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

async def set_bot_commands(bot: Bot):
    """Set bot commands for menu"""
    commands = [
        BotCommand(command="start", description="🚀 Start the bot"),
        BotCommand(command="help", description="❓ Get help"),
        BotCommand(command="faq", description="📚 Frequently asked questions"),
        BotCommand(command="remind", description="⏰ Set a reminder"),
        BotCommand(command="ai", description="🤖 Chat with AI"),
        BotCommand(command="weather", description="🌤 Get weather forecast"),
        BotCommand(command="cancel", description="❌ Cancel current operation"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")

async def on_startup(bot: Bot):
    """Actions to perform when bot starts"""
    logger.info("Bot is starting up...")
    await set_bot_commands(bot)
    logger.info(f"Bot is ready!")

async def on_shutdown(bot: Bot):
    """Actions to perform when bot shuts down"""
    logger.info("Bot is shutting down...")
    await bot.session.close()
    logger.info("Bot shutdown complete")

async def main():
    """Main function to run the bot"""
    # Initialize bot and dispatcher (remove parse_mode from here)
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register startup/shutdown events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Include all handlers
    dp.include_router(start.router)
    dp.include_router(faq.router)
    dp.include_router(reminders.router)
    dp.include_router(ai_chat.router)
    dp.include_router(weather.router)
    
    # Start polling
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error while polling: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)