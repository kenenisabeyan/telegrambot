from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

router = Router()

async def save_feedback(user_id: int, feedback_text: str):
    """Save user feedback to database"""
    # In production, save to database
    print(f"📝 Feedback from user {user_id}: {feedback_text}")
    
    # You can also save to a file
    with open(f"logs/feedback_{datetime.now().strftime('%Y%m%d')}.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | User: {user_id} | {feedback_text}\n")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu"""
    from handlers.start import get_main_keyboard
    
    await callback.message.edit_text(
        "<b>📋 Main Menu</b>\n\nChoose an option below:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "close_menu")
async def close_menu(callback: CallbackQuery):
    """Close the current menu"""
    await callback.message.delete()
    await callback.answer("Menu closed!")