from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def get_main_keyboard(user_id: int = None, is_premium: bool = False):
    """Main menu keyboard"""
    buttons = [
        [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="⏰ Reminder")],
        [KeyboardButton(text="🤖 AI Chat"), KeyboardButton(text="🌤 Weather")],
        [KeyboardButton(text="📊 Stats"), KeyboardButton(text="💬 Feedback")],
        [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="❌ Cancel")]
    ]
    if is_premium:
        buttons.append([KeyboardButton(text="🌐 Open Web App", web_app=WebAppInfo(url="https://your-webapp.com"))])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type a command..."
    )

def get_admin_keyboard():
    """Admin panel keyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Bot Stats", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton(text="📝 Logs", callback_data="admin_logs")],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="admin_settings")],
            [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_to_menu")]
        ]
    )

def get_weather_keyboard(city: str = None):
    """Weather inline keyboard"""
    buttons = []
    if city:
        buttons.append([InlineKeyboardButton(text="📅 Forecast", callback_data=f"forecast_{city}")])
        buttons.append([InlineKeyboardButton(text="🔄 Refresh", callback_data=f"refresh_{city}")])
    buttons.append([InlineKeyboardButton(text="📍 My Location", callback_data="weather_location")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reminder_keyboard(reminder_id: str):
    """Reminder action keyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Done", callback_data=f"remind_done_{reminder_id}"),
                InlineKeyboardButton(text="⏰ Snooze", callback_data=f"remind_snooze_{reminder_id}")
            ],
            [InlineKeyboardButton(text="❌ Delete", callback_data=f"remind_delete_{reminder_id}")]
        ]
    )