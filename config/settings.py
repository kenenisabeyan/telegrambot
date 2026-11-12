import os
import re
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

# Storage & Database
DB_URL = os.getenv("DB_URL")
REDIS_URL = os.getenv("REDIS_URL")

# External APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Admin IDs parsed as a list of integers
ADMIN_IDS = []
admin_ids_raw = os.getenv("ADMIN_IDS", "")
for admin_id_str in admin_ids_raw.split(","):
    if admin_id_str.strip():
        try:
            ADMIN_IDS.append(int(admin_id_str.strip()))
        except ValueError:
            pass

# Logging Level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Webhook Production Settings (Optional)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8080"))

# Rate Limiting / Anti-flood Settings
RATE_LIMIT_DEFAULT = float(os.getenv("RATE_LIMIT_DEFAULT", "0.6"))
RATE_LIMIT_HEAVY = float(os.getenv("RATE_LIMIT_HEAVY", "2.0"))
