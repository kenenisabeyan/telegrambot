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

# Import handlers & setup router
from handlers import setup_routers

# Import enterprise middlewares
from middlewares import (
    ThrottlingMiddleware,
    DatabaseMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware,
)
from utils.telemetry import telemetry

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def get_storage():
    """Initialize Redis FSM storage with automated fallback to MemoryStorage."""
    if settings.REDIS_URL:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(settings.REDIS_URL)
            logger.info("⚡ Using Redis FSM Storage")
            return storage
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}. Falling back to MemoryStorage.")
    
    logger.info("💾 Using in-memory FSM storage")
    return MemoryStorage()

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
        BotCommand(command="profile", description="👤 Personal profile & timezone"),
        BotCommand(command="referral", description="🎁 Invite friends & referral program"),
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

def register_middlewares(dp: Dispatcher, db=None):
    """Register enterprise middleware pipeline on Dispatcher"""
    # 1. Performance and request logging
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    # 2. Global exception boundary and error sanitizer
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())

    # 3. Anti-flood and throttling protection
    throttling = ThrottlingMiddleware(
        default_rate=settings.RATE_LIMIT_DEFAULT,
        heavy_rate=settings.RATE_LIMIT_HEAVY
    )
    dp.message.middleware(throttling)
    dp.callback_query.middleware(throttling)

    # 4. Database session injection and auto user profile sync
    if db:
        db_mw = DatabaseMiddleware(db)
        dp.message.middleware(db_mw)
        dp.callback_query.middleware(db_mw)
    
    logger.info("Middlewares registered successfully.")

async def start_webhook_server(bot: Bot, dp: Dispatcher, db=None):
    """Launch production high-concurrency Aiohttp Webhook Server with health checks."""
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    webhook_endpoint = f"{settings.WEBHOOK_URL.rstrip('/')}{settings.WEBHOOK_PATH}"
    logger.info(f"Configuring webhook for {webhook_endpoint}")

    async def webhook_startup(app: web.Application):
        await on_startup(bot, db)
        await bot.set_webhook(
            url=webhook_endpoint,
            secret_token=settings.WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        logger.info(f"Webhook registered successfully with Telegram API: {webhook_endpoint}")

    async def webhook_shutdown(app: web.Application):
        await bot.delete_webhook()
        await on_shutdown(bot, db)
        logger.info("Webhook deleted and resources cleaned up.")

    async def health_endpoint(request: web.Request):
        """Health check endpoint for Docker/Kubernetes container orchestration."""
        is_healthy = await db.is_healthy() if db else True
        snapshot = telemetry.get_metrics_snapshot()
        status_payload = {
            "status": "healthy" if is_healthy else "degraded",
            "bot": "online",
            "database": "connected" if (db and is_healthy) else ("mock" if not db else "error"),
            "telemetry": snapshot,
            "timestamp": datetime.now().isoformat()
        }
        return web.json_response(status_payload, status=200 if is_healthy else 503)

    app = web.Application()
    app.router.add_get("/health", health_endpoint)
    app.on_startup.append(webhook_startup)
    app.on_shutdown.append(webhook_shutdown)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
        db=db
    ).register(app, path=settings.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot, db=db)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.WEBAPP_HOST, port=settings.WEBAPP_PORT)
    await site.start()
    logger.info(f"🚀 Webhook server listening on http://{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}")

    # Keep server running until cancelled
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

async def main():
    """Main function to run the bot in polling or webhook mode"""
    db = None
    if settings.DB_URL:
        from database.models import Database
        db = Database(settings.DB_URL)
        logger.info("Database URL detected in environment variables.")
    else:
        logger.warning("DB_URL is not set. Database functionality will operate in mock fallback mode.")

    storage = await get_storage()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)
    
    # Include master router
    dp.include_router(setup_routers())

    # Register enterprise middlewares
    register_middlewares(dp, db=db)

    # Choose execution mode: Webhook vs Polling
    if settings.WEBHOOK_URL:
        logger.info("Mode: Production Webhook Server")
        await start_webhook_server(bot, dp, db)
    else:
        logger.info("Mode: Resilient Long Polling")
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        try:
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
