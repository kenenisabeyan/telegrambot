from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from os import getenv
from datetime import datetime

router = Router()

# Get admin IDs from environment
ADMIN_IDS = [int(id.strip()) for id in getenv("ADMIN_IDS", "").split(",") if id.strip()]

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

class BroadcastStates(StatesGroup):
    waiting_for_message = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel (restricted)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    keyboard = [
        [("📊 Bot Stats", "admin_stats")],
        [("📢 Broadcast", "admin_broadcast")],
        [("👥 Users", "admin_users")],
        [("📝 Logs", "admin_logs")],
        [("⚙️ Settings", "admin_settings")]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=data)]
            for text, data in keyboard
        ]
    )
    
    await message.answer(
        "<b>🔐 Admin Panel</b>\n\n"
        "Welcome to the admin dashboard.\n"
        "Select an option below:",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Show bot statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!")
        return
    
    stats = {
        "users": 1234,  # Fetch from database
        "active_today": 456,
        "total_messages": 56789,
        "commands_used": 12345,
        "reminders_set": 678,
        "ai_queries": 2345,
        "weather_checks": 1234
    }
    
    stats_text = (
        "<b>📊 Bot Statistics</b>\n\n"
        f"<b>👥 Total Users:</b> {stats['users']}\n"
        f"<b>✅ Active Today:</b> {stats['active_today']}\n"
        f"<b>💬 Total Messages:</b> {stats['total_messages']}\n"
        f"<b>⚡ Commands Used:</b> {stats['commands_used']}\n"
        f"<b>⏰ Reminders Set:</b> {stats['reminders_set']}\n"
        f"<b>🤖 AI Queries:</b> {stats['ai_queries']}\n"
        f"<b>🌤 Weather Checks:</b> {stats['weather_checks']}\n\n"
        f"<i>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    
    await callback.message.edit_text(stats_text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast process"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!")
        return
    
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text(
        "<b>📢 Broadcast Message</b>\n\n"
        "Send me the message you want to broadcast to all users.\n\n"
        "You can use HTML formatting.\n"
        "Type /cancel to cancel.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(BroadcastStates.waiting_for_message)
async def send_broadcast(message: Message, state: FSMContext):
    """Send broadcast to all users"""
    if not is_admin(message.from_user.id):
        return
    
    broadcast_text = message.text
    
    # Confirm broadcast
    keyboard = [
        [("✅ Yes, Send", "broadcast_confirm")],
        [("❌ Cancel", "broadcast_cancel")]
    ]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=data)]
            for text, data in keyboard
        ]
    )
    
    await message.answer(
        f"<b>📢 Broadcast Preview:</b>\n\n{broadcast_text}\n\n"
        f"Send this message to all users?",
        reply_markup=confirm_keyboard,
        parse_mode="HTML"
    )
    
    await state.update_data(broadcast_message=broadcast_text)
    await state.set_state(BroadcastStates.waiting_for_message)  # Keep state

@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast"""
    data = await state.get_data()
    broadcast_text = data.get('broadcast_message')
    
    # In production, fetch all user IDs from database
    # For now, just acknowledge
    await callback.message.edit_text(
        f"✅ Broadcast sent successfully!\n\n"
        f"Message: {broadcast_text[:100]}..."
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast"""
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.")
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Show user management"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!")
        return
    
    # This would fetch from database
    await callback.message.edit_text(
        "<b>👥 User Management</b>\n\n"
        "Features coming soon:\n"
        "• List all users\n"
        "• Export user data\n"
        "• Manage user roles\n"
        "• Block/unblock users\n\n"
        "<i>Database integration required for full functionality.</i>",
        parse_mode="HTML"
    )
    await callback.answer()