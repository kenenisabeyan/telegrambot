import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

# Configure standard streams for UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import configuration
from config import settings

# Import all handlers
from handlers import start, faq, reminders, ai_chat, weather, admin, callback, bot_manager  # noqa: E402

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
        BotCommand(command="newbot", description="🤖 Register/add a new bot"),
        BotCommand(command="mybots", description="📋 List and manage your bots"),
        BotCommand(command="setname", description="✍️ Set bot display name"),
        BotCommand(command="setdescription", description="📝 Set bot description"),
        BotCommand(command="setabouttext", description="ℹ️ Set bot short description (about text)"),
        BotCommand(command="setuserpic", description="🖼️ Set bot profile picture"),
        BotCommand(command="setcommands", description="📜 Set bot command list"),
        BotCommand(command="deletebot", description="❌ Delete a bot from the manager"),
        BotCommand(command="cancel", description="❌ Cancel current operation"),
        BotCommand(command="stats", description="📊 Bot statistics"),
        BotCommand(command="feedback", description="💬 Send feedback"),
        BotCommand(command="admin", description="🔐 Admin panel"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")

async def on_startup(bot: Bot, db=None):
    """Actions to perform when bot starts"""
    logger.info("🚀 Bot is starting up...")
    await set_bot_commands(bot)
    
    if db:
        try:
            logger.info("Connecting to PostgreSQL database...")
            await db.connect()
            logger.info("PostgreSQL database connected and tables verified.")
            
            # Reschedule active reminders
            active_reminders = await db.get_active_reminders()
            logger.info(f"Loaded {len(active_reminders)} active reminders to reschedule.")
            from handlers.reminders import send_reminder
            for reminder in active_reminders:
                asyncio.create_task(send_reminder(
                    bot=bot,
                    chat_id=reminder['user_id'],
                    reminder_id=reminder['id'],
                    message_text=reminder['message'],
                    remind_time=reminder['remind_time'],
                    db=db
                ))
        except Exception as e:
            logger.error(f"Failed to connect to database or reschedule reminders: {e}")
    
    # Send notification to admins
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✅ Bot started successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception:
            pass
    
    logger.info("✨ Bot is ready to serve!")

async def on_shutdown(bot: Bot, db=None):
    """Actions to perform when bot shuts down"""
    logger.info("🛑 Bot is shutting down...")
    
    if db and db.pool:
        try:
            logger.info("Closing database connection pool...")
            await db.pool.close()
            logger.info("Database connection pool closed successfully.")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")
            
    # Notify admins
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"⚠️ Bot is shutting down at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception:
            pass
    
    await bot.session.close()
    logger.info("✅ Bot shutdown complete")

async def main():
    """Main function to run the bot"""
    db = None
    if settings.DB_URL:
        from database.models import Database
        db = Database(settings.DB_URL)
        logger.info("Database URL found in environment variables.")
    else:
        logger.warning("DB_URL is not set in environment variables. Database functionality will use mock fallbacks.")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
    dp.include_router(bot_manager.router)
    
    # Start polling
    try:
        logger.info("🔄 Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), db=db)
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
