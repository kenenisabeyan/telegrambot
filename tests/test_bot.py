import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_bot_imports():
    """Test that all modules import correctly"""
    try:
        # Test each module individually
        from handlers import start
        from handlers import faq
        from handlers import reminders
        from handlers import ai_chat
        from handlers import weather
        from handlers import admin
        from handlers import callback
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"

def test_env_file_exists():
    """Test that .env file exists"""
    env_path = Path(__file__).parent.parent / ".env"
    assert env_path.exists(), ".env file not found"

def test_token_configured():
    """Test that token is configured"""
    from dotenv import load_dotenv
    
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    token = os.getenv("BOT_TOKEN")
    
    # Check if token exists and is not the placeholder
    if token and token != "your_bot_token_from_botfather" and len(token) > 10:
        assert True
    else:
        assert False, "BOT_TOKEN not configured correctly in .env file"

def test_handlers_exist():
    """Test that all handler files exist"""
    handlers_dir = Path(__file__).parent.parent / "handlers"
    
    required_handlers = [
        "start.py",
        "faq.py", 
        "reminders.py",
        "ai_chat.py",
        "weather.py",
        "admin.py",
        "callback.py"
    ]
    
    for handler in required_handlers:
        handler_path = handlers_dir / handler
        assert handler_path.exists(), f"Handler {handler} not found"python bot.py
        