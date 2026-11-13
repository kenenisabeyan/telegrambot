import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from middlewares.throttling import ThrottlingMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.error import ErrorHandlingMiddleware, sanitize_sensitive_data
from handlers import setup_routers

def test_sanitize_sensitive_data():
    """Test that sensitive tokens, keys, and credentials are redacted."""
    sample_text = (
        "Failed with token 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ_123456 "
        "and db postgresql://postgres:SecretPassword123@localhost:5432/db "
        "and key sk-proj1234567890abcdefghijklmnopqrstuvwxyz"
    )
    sanitized = sanitize_sensitive_data(sample_text)
    assert "123456789:ABCdef" not in sanitized
    assert "[REDACTED_BOT_TOKEN]" in sanitized
    assert "SecretPassword123" not in sanitized
    assert "[REDACTED_PASSWORD]" in sanitized
    assert "sk-proj123456" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized

def test_setup_routers():
    """Test that master router bundles all subrouters."""
    root_router = setup_routers()
    assert root_router is not None
    # Verify subrouters are included
    subrouters = root_router.sub_routers
    assert len(subrouters) >= 7

@pytest.mark.asyncio
async def test_throttling_middleware():
    """Test that throttling middleware rate-limits rapid repeated requests."""
    middleware = ThrottlingMiddleware(default_rate=1.0, heavy_rate=3.0)
    
    mock_handler = AsyncMock(return_value="OK")
    mock_user = MagicMock(id=1001)
    mock_event = MagicMock()
    mock_event.text = "/help"
    
    data = {"event_from_user": mock_user}
    
    # First call: should succeed
    res1 = await middleware(mock_handler, mock_event, data)
    assert res1 == "OK"
    assert mock_handler.call_count == 1
    
    # Immediate second call: should be throttled
    res2 = await middleware(mock_handler, mock_event, data)
    assert res2 is None
    # Handler should not have been called a second time
    assert mock_handler.call_count == 1

@pytest.mark.asyncio
async def test_error_handling_middleware():
    """Test that error handling middleware catches exceptions and prevents crashes."""
    from aiogram.types import Message
    middleware = ErrorHandlingMiddleware()
    
    async def failing_handler(event, data):
        raise RuntimeError("Something exploded with 7649497815:AAEJOWrChlrakVq5sY_mzaSOu70dSACAwRw")
    
    mock_message = MagicMock(spec=Message)
    mock_message.answer = AsyncMock()
    mock_user = MagicMock(id=2002)
    data = {"event_from_user": mock_user}
    
    # Should catch exception without re-raising
    result = await middleware(failing_handler, mock_message, data)
    assert result is None
    # User should receive polite notice
    assert mock_message.answer.called

@pytest.mark.asyncio
async def test_database_middleware_sync():
    """Test database middleware passes db and triggers user sync."""
    mock_db = AsyncMock()
    middleware = DatabaseMiddleware(db=mock_db)
    
    mock_handler = AsyncMock(return_value="HANDLED")
    mock_user = MagicMock(id=3003, is_bot=False, username="johndoe", first_name="John", last_name="Doe")
    mock_event = MagicMock()
    data = {"event_from_user": mock_user}
    
    result = await middleware(mock_handler, mock_event, data)
    assert result == "HANDLED"
    assert data["db"] == mock_db
    assert mock_db.add_user.called

def test_ai_persona_response():
    """Test AI mock response adapts to persona"""
    from handlers.ai_chat import get_mock_response
    concise_resp = get_mock_response("How to sort list", persona="concise")
    assert "•" in concise_resp
    
    coder_resp = get_mock_response("Write python class", persona="coder")
    assert "```python" in coder_resp

def test_bot_options_keyboard_has_new_features():
    """Test options keyboard includes view commands and test ping buttons"""
    from utils.keyboards import get_bot_options_keyboard
    kb = get_bot_options_keyboard(123456)
    all_callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "bot_view_cmds_123456" in all_callbacks
    assert "bot_ping_123456" in all_callbacks
    assert "bot_diag_123456" in all_callbacks

def test_admin_is_admin_check():
    """Test admin verification logic"""
    from handlers.admin import is_admin
    from config import settings
    # Test with non-admin
    assert is_admin(-9999) is False
    # If admin ids configured, first should be admin
    if settings.ADMIN_IDS:
        assert is_admin(settings.ADMIN_IDS[0]) is True
