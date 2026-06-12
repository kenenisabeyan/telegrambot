import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

DB_URL = os.getenv("DB_URL")
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

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
