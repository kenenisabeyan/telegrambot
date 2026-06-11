from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
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
    await state.clear()
    
    welcome_text = (
        f"👋 Welcome, {message.from_user.full_name}!\n\n"
        f"🤖 I'm an Enterprise-Grade Telegram Bot with powerful features:\n\n"
        f"✅ FAQ System\n"
        f"✅ Smart Reminders\n"
        f"✅ AI Chat\n"
        f"✅ Live Weather\n\n"
        f"📌 Quick Start:\n"
        f"• Use the buttons below\n"
        f"• Type /help for all commands\n"
        f"• Type /faq to browse questions\n\n"
        f"Let's get started! 🚀"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
async def cmd_help(message: Message):
    """Handle /help command and Help button"""
    help_text = (
        "📚 Available Commands\n\n"
        "Basic Commands:\n"
        "• /start - Restart the bot\n"
        "• /help - Show this help menu\n"
        "• /cancel - Cancel current operation\n\n"
        
        "Feature Commands:\n"
        "• /faq - Browse FAQ database\n"
        "• /remind - Set a reminder\n"
        "• /ai - Chat with AI\n"
        "• /weather - Get weather\n\n"
        
        "💡 Examples:\n"
        "/remind Call John at 3pm\n"
        "/ai What is Python?\n"
        "/weather London\n\n"
        
        "🔧 Need more help? Contact support."
    )
    
    await message.answer(help_text, reply_markup=get_main_keyboard())

@router.message(F.text == "❌ Cancel")
async def cmd_cancel(message: Message, state: FSMContext):
    """Handle cancel button"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("✅ Operation cancelled. What would you like to do?", reply_markup=get_main_keyboard())
    else:
        await message.answer("❌ No active operation to cancel.", reply_markup=get_main_keyboard())

@router.message(Command("cancel"))
async def cmd_cancel_command(message: Message, state: FSMContext):
    """Handle /cancel command"""
    await cmd_cancel(message, state)

# Handle button presses for FAQ
@router.message(F.text == "❓ FAQ")
async def faq_button(message: Message):
    await cmd_faq(message)

# Handle button presses for Reminder
@router.message(F.text == "⏰ Reminder")
async def reminder_button(message: Message, state: FSMContext):
    await cmd_remind(message, state)

# Handle button presses for AI Chat
@router.message(F.text == "🤖 AI Chat")
async def ai_button(message: Message):
    # Create a fake command message
    message.text = "/ai"
    await cmd_ai(message)

# Handle button presses for Weather
@router.message(F.text == "🌤 Weather")
async def weather_button(message: Message):
    # Create a fake command message
    message.text = "/weather"
    await cmd_weather(message)

# Import the handler functions
from handlers.faq import cmd_faq
from handlers.reminders import cmd_remind
from handlers.ai_chat import cmd_ai
from handlers.weather import cmd_weather