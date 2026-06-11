import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

# You can also hardcode it temporarily for testing (not recommended for production)
# TOKEN = "YOUR_BOT_TOKEN_HERE"

# Verify token exists
if not TOKEN:
    raise ValueError("No BOT_TOKEN found. Please add it to .env file")