from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from utils.keyboards import get_main_keyboard

router = Router()

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db=None):
    """Handle /start command with deep linking"""
    await state.clear()
    
    # Handle deep linking (e.g., /start ref_123)
    args = message.text.split()
    _referrer = None
    if len(args) > 1:
        _referrer = args[1]
    
    if db:
        await db.add_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        await db.log_command(message.from_user.id, "start")
    
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

@router.message(Command("help"))
@router.message(F.text == "Help")
async def cmd_help(message: Message, db=None):
    """Handle /help command"""
    if db:
        await db.log_command(message.from_user.id, "help")
        
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
@router.message(F.text == "Menu")
async def cmd_menu(message: Message, db=None):
    """Show main menu"""
    if db:
        await db.log_command(message.from_user.id, "menu")
    await message.answer(
        "<b>📋 Main Menu</b>\n\nChoose an option below:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(F.text == "Cancel")
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, db=None):
    """Handle cancel button/command"""
    if db:
        await db.log_command(message.from_user.id, "cancel")
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
@router.message(F.text == "Stats")
async def cmd_stats(message: Message, db=None):
    """Show user statistics"""
    if db:
        await db.log_command(message.from_user.id, "stats")
        stats = await db.get_user_stats(message.from_user.id)
        joined_str = stats["joined_at"].strftime('%Y-%m-%d')
        commands_count = stats["commands_count"]
        reminders_count = stats["reminders_count"]
        ai_count = stats["ai_count"]
        weather_count = stats["weather_count"]
    else:
        joined_str = datetime.now().strftime('%Y-%m-%d')
        commands_count = 0
        reminders_count = 0
        ai_count = 0
        weather_count = 0

    stats_text = (
        "<b>📊 Your Statistics</b>\n\n"
        f"<b>👤 User:</b> {message.from_user.full_name}\n"
        f"<b>🆔 ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>📅 Joined:</b> {joined_str}\n\n"
        
        "<b>📈 Usage Stats:</b>\n"
        f"• Commands used: {commands_count}\n"
        f"• Reminders set: {reminders_count}\n"
        f"• AI queries: {ai_count}\n"
        f"• Weather checks: {weather_count}\n\n"
        
        "<b>🏆 Achievements:</b>\n"
        "• 🌟 Bot Explorer\n"
        "• 💬 First Message\n\n"
        
        "<i>More stats coming soon with premium features!</i>"
    )
    
    await message.answer(stats_text, reply_markup=get_main_keyboard(message.from_user.id))

@router.message(Command("feedback"))
@router.message(F.text == "Feedback")
async def cmd_feedback(message: Message, state: FSMContext, db=None):
    """Collect feedback from users"""
    if db:
        await db.log_command(message.from_user.id, "feedback")
        
    await state.set_state(FeedbackStates.waiting_for_feedback)
    await message.answer(
        "<b>💬 Send Feedback</b>\n\n"
        "Please send your feedback, suggestions, or bug report.\n"
        "We value your input!\n\n"
        "<i>Type /cancel to cancel</i>",
        parse_mode="HTML"
    )

@router.message(FeedbackStates.waiting_for_feedback)
async def handle_feedback(message: Message, state: FSMContext, db=None):
    """Handle feedback input"""
    from handlers.callback import save_feedback
    
    await save_feedback(message.from_user.id, message.text, db=db)
    await state.clear()
    await message.answer(
        "<b>✅ Thank you for your feedback!</b>\n\n"
        "We appreciate your input and will use it to improve our bot.\n\n"
        "Is there anything else I can help you with?",
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="HTML"
    )