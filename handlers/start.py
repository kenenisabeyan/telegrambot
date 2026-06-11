from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

router = Router()

# Create main menu keyboard
def get_main_keyboard():
    """Return the main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="⏰ Reminder")],
            [KeyboardButton(text="🤖 AI Chat"), KeyboardButton(text="🌤 Weather")],
            [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="❌ Cancel")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type a command..."
    )
    return keyboard

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()  # Clear any active states
    
    welcome_text = (
        f"<b>👋 Welcome, {message.from_user.full_name}!</b>\n\n"
        f"🤖 I'm an <b>Enterprise-Grade Telegram Bot</b> with powerful features:\n\n"
        f"✅ <b>FAQ System</b> - Browse answers to common questions\n"
        f"✅ <b>Smart Reminders</b> - Never miss important tasks\n"
        f"✅ <b>AI Chat</b> - Powered by advanced AI\n"
        f"✅ <b>Live Weather</b> - Real-time weather updates\n\n"
        f"📌 <b>Quick Start:</b>\n"
        f"• Use the buttons below\n"
        f"• Type /help for all commands\n"
        f"• Type /faq to browse questions\n\n"
        f"<i>Let's get started!</i> 🚀"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
async def cmd_help(message: Message):
    """Handle /help command and Help button"""
    help_text = (
        "<b>📚 Available Commands</b>\n\n"
        "<b>Basic Commands:</b>\n"
        "• /start - Restart the bot\n"
        "• /help - Show this help menu\n"
        "• /cancel - Cancel current operation\n\n"
        
        "<b>Feature Commands:</b>\n"
        "• /faq - Browse FAQ database\n"
        "• /remind - Set a reminder (e.g., /remind 10m Call John)\n"
        "• /ai - Chat with AI (e.g., /ai What is Python?)\n"
        "• /weather - Get weather (e.g., /weather London)\n\n"
        
        "<b>💡 Examples:</b>\n"
        "<code>/remind 30m Team meeting</code>\n"
        "<code>/ai Write a Python function to sort a list</code>\n"
        "<code>/weather Tokyo</code>\n\n"
        
        "<b>🔧 Need more help?</b>\n"
        "Contact: support@company.com"
    )
    
    await message.answer(help_text, reply_markup=get_main_keyboard())

@router.message(F.text == "❌ Cancel")
async def cmd_cancel(message: Message, state: FSMContext):
    """Handle cancel button"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "✅ Operation cancelled. What would you like to do?",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "❌ No active operation to cancel.",
            reply_markup=get_main_keyboard()
        )

@router.message(Command("cancel"))
async def cmd_cancel_command(message: Message, state: FSMContext):
    """Handle /cancel command"""
    await cmd_cancel(message, state)