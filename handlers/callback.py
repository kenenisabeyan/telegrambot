from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

router = Router()

async def save_feedback(user_id: int, feedback_text: str):
    """Save user feedback (implement with database)"""
    print(f"Feedback from {user_id}: {feedback_text}")
    # Save to database here

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu"""
    from handlers.start import get_main_keyboard
    
    await callback.message.edit_text(
        "<b>📋 Main Menu</b>\n\nChoose an option below:",
        reply_markup=get_main_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )
    await callback.answer()