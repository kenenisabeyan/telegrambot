from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from datetime import datetime
import json

router = Router()

# Main menu keyboard with web app support
def get_main_keyboard(user_id: int = None):
    """Return the main menu keyboard"""
    buttons = [
        [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="⏰ Reminder")],
        [KeyboardButton(text="🤖 AI Chat"), KeyboardButton(text="🌤 Weather")],
        [KeyboardButton(text="📊 Stats"), KeyboardButton(text="💬 Feedback")],
        [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="❌ Cancel")]
    ]
    
    # Add web app button for premium users
    # buttons.append([KeyboardButton(text="🌐 Open Web App", web_app=WebAppInfo(url="https://your-webapp.com"))])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type a command..."
    )

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with deep linking"""
    await state.clear()
    
    # Handle deep linking (e.g., /start ref_123)
    args = message.text.split()
    referrer = None
    if len(args) > 1:
        referrer = args[1]
        # Save referral to database (implement later)
    
    welcome_text = (
        f"<b>👋 Welcome, {message.from_user.full_name}!</b>\n\n"
        f"<b>🤖 Enterprise Telegram Bot</b>\n"
        f"<i>Your all-in-one productivity assistant</i>\n\n"
        f"<b>✨ Features:</b>\n"
        f"• 📚 <b>FAQ System</b> - Instant answers\n"
        f"• ⏰ <b>Smart Reminders</b> - Never miss tasks\n"
        f"• 🤖 <b>AI Chat</b> - Powered by GPT\n"
        f"• 🌤 <b>Live Weather</b> - Real-time updates\n"
        f"• 📊 <b>Analytics</b> - Track your usage\n"
        f"• 💬 <b>Feedback</b> - Help us improve\n\n"
        f"<b>🚀 Quick Start:</b>\n"
        f"• Click buttons below\n"
        f"• Type /help for all commands\n"
        f"• Visit our website for more info\n\n"
        f"<i>Let's make your day productive! 💪</i>"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    
    # Log user start (implement database logging later)
    print(f"User {message.from_user.id} started bot at {datetime.now()}")

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        "<b>📚 Complete Command Reference</b>\n\n"
        
        "<b>🔹 Basic Commands:</b>\n"
        "• /start - Restart the bot\n"
        "• /help - Show this help\n"
        "• /menu - Show main menu\n"
        "• /cancel - Cancel current operation\n\n"
        
        "<b>🔹 Productivity:</b>\n"
        "• /faq - Browse FAQ database\n"
        "• /remind - Set smart reminder\n"
        "  <code>/remind 10m Call John</code>\n"
        "  <code>/remind tomorrow 9am Meeting</code>\n\n"
        
        "<b>🔹 AI & Information:</b>\n"
        "• /ai - Chat with AI\n"
        "  <code>/ai What is Python?</code>\n"
        "• /weather - Get weather\n"
        "  <code>/weather London</code>\n\n"
        
        "<b>🔹 Utility:</b>\n"
        "• /stats - View your statistics\n"
        "• /feedback - Send feedback\n\n"
        
        "<b>💡 Pro Tips:</b>\n"
        "• Use natural language for reminders\n"
        "• Ask AI to write code, explain concepts\n"
        "• Get weather for any city worldwide\n\n"
        
        "<b>📞 Support:</b>\n"
        "• Email: support@company.com\n"
        "• Telegram: @support_bot\n"
        "• Website: https://company.com\n\n"
        
        "<i>Need more help? Contact our support team 24/7!</i>"
    )
    
    await message.answer(help_text, reply_markup=get_main_keyboard(message.from_user.id))

@router.message(Command("menu"))
@router.message(F.text == "📋 Menu")
async def cmd_menu(message: Message):
    """Show main menu"""
    await message.answer(
        "<b>📋 Main Menu</b>\n\nChoose an option below:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(F.text == "❌ Cancel")
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Handle cancel button/command"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "✅ Operation cancelled successfully.\n\nWhat would you like to do next?",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        await message.answer(
            "❌ No active operation to cancel.\n\nUse the menu below to get started:",
            reply_markup=get_main_keyboard(message.from_user.id)
        )

@router.message(Command("stats"))
@router.message(F.text == "📊 Stats")
async def cmd_stats(message: Message):
    """Show user statistics"""
    # This would pull from database in production
    stats_text = (
        "<b>📊 Your Statistics</b>\n\n"
        f"<b>👤 User:</b> {message.from_user.full_name}\n"
        f"<b>🆔 ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>📅 Joined:</b> {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        "<b>📈 Usage Stats:</b>\n"
        "• Messages sent: 0\n"
        "• Commands used: 0\n"
        "• Reminders set: 0\n"
        "• AI queries: 0\n"
        "• Weather checks: 0\n\n"
        
        "<b>🏆 Achievements:</b>\n"
        "• 🌟 Bot Explorer\n"
        "• 💬 First Message\n\n"
        
        "<i>More stats coming soon with premium features!</i>"
    )
    
    await message.answer(stats_text, reply_markup=get_main_keyboard(message.from_user.id))

@router.message(Command("feedback"))
@router.message(F.text == "💬 Feedback")
async def cmd_feedback(message: Message, state: FSMContext):
    """Collect feedback from users"""
    from aiogram.fsm.state import State, StatesGroup
    
    class FeedbackStates(StatesGroup):
        waiting_for_feedback = State()
    
    await state.set_state(FeedbackStates.waiting_for_feedback)
    await message.answer(
        "<b>💬 Send Feedback</b>\n\n"
        "Please send your feedback, suggestions, or bug report.\n"
        "We value your input!\n\n"
        "<i>Type /cancel to cancel</i>",
        parse_mode="HTML"
    )

@router.message(F.text & ~F.text.startswith("/"))
async def handle_feedback(message: Message, state: FSMContext):
    """Handle feedback input"""
    from handlers.callback import save_feedback
    
    current_state = await state.get_state()
    if current_state and "FeedbackStates" in str(current_state):
        await save_feedback(message.from_user.id, message.text)
        await state.clear()
        await message.answer(
            "<b>✅ Thank you for your feedback!</b>\n\n"
            "We appreciate your input and will use it to improve our bot.\n\n"
            "Is there anything else I can help you with?",
            reply_markup=get_main_keyboard(message.from_user.id),
            parse_mode="HTML"
        )