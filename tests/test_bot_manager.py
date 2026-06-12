import re
import pytest
from handlers.bot_manager import (
    router,
    db_add_bot,
    db_get_bots,
    db_get_bot,
    db_update_bot,
    db_delete_bot,
    MOCK_MANAGED_BOTS,
    BotManagerStates
)

def test_bot_manager_imports():
    """Test that the bot manager module can be imported and has expected components"""
    assert router is not None
    assert BotManagerStates is not None

def test_bot_manager_routes_registered():
    """Test that routes are registered with the router"""
    # The router should have a list of message and callback query handlers registered
    message_handlers = router.message.handlers
    callback_handlers = router.callback_query.handlers
    
    assert len(message_handlers) > 0
    assert len(callback_handlers) > 0

@pytest.mark.asyncio
async def test_mock_database_operations():
    """Test CRUD operations on the mock database fallback"""
    user_id = 99999
    token = "123456789:AAFgfgfg-fgfgfgf_fgfgfgfgfgfgf"
    bot_id = 123456789
    username = "test_bot"
    name = "Test Bot"
    
    # Reset mock db for user
    if user_id in MOCK_MANAGED_BOTS:
        del MOCK_MANAGED_BOTS[user_id]
        
    # 1. Add bot
    await db_add_bot(user_id, token, bot_id, username, name, db=None)
    bots = await db_get_bots(user_id, db=None)
    assert len(bots) == 1
    assert bots[0]['username'] == username
    assert bots[0]['token'] == token
    
    # 2. Get bot
    bot = await db_get_bot(user_id, bot_id, db=None)
    assert bot is not None
    assert bot['name'] == name
    
    # 3. Update bot fields
    await db_update_bot(user_id, bot_id, db=None, name="Updated Name", description="Updated Description")
    bot = await db_get_bot(user_id, bot_id, db=None)
    assert bot['name'] == "Updated Name"
    assert bot['description'] == "Updated Description"
    
    # 4. Delete bot
    await db_delete_bot(user_id, bot_id, db=None)
    bots = await db_get_bots(user_id, db=None)
    assert len(bots) == 0

def test_token_regex_validation():
    """Test token regex matching logic used in bot manager"""
    token_pattern = r"^\d+:[A-Za-z0-9_-]{30,50}$"
    
    # Valid tokens
    valid_tokens = [
        "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "7649497815:AAEJOWrChlrakVq5sY_mzaSOu70dSACAwRw",
        "1234567890:BCDFGHJKLMNPQRSTVWXYZ1234567890abcde"
    ]
    
    # Invalid tokens
    invalid_tokens = [
        "invalid_token",
        "123456:short",
        "abc:AAEJOWrChlrakVq5sY_mzaSOu70dSACAwRw",
        "123456:AAEJOWrChlrakVq5sY_mzaSOu70dSACAwRw extra",
    ]
    
    for t in valid_tokens:
        assert re.match(token_pattern, t) is not None
        
    for t in invalid_tokens:
        assert re.match(token_pattern, t) is None
