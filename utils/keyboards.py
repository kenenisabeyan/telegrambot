from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def get_main_keyboard(user_id: int = None, is_premium: bool = False):
    """Main menu keyboard"""
    buttons = [
        [KeyboardButton(text="Bot Manager"), KeyboardButton(text="AI Chat")],
        [KeyboardButton(text="FAQ"), KeyboardButton(text="Reminder")],
        [KeyboardButton(text="Weather"), KeyboardButton(text="Stats")],
        [KeyboardButton(text="Feedback"), KeyboardButton(text="Help")],
        [KeyboardButton(text="Cancel")]
    ]
    if is_premium:
        buttons.append([KeyboardButton(text="🌐 Open Web App", web_app=WebAppInfo(url="https://your-webapp.com"))])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type a command..."
    )

def get_my_bots_keyboard(bots: list):
    """List of user's managed bots"""
    inline_keyboard = []
    for bot in bots:
        inline_keyboard.append([
            InlineKeyboardButton(text=f"🤖 @{bot['username']}", callback_data=f"bot_select_{bot['bot_id']}")
        ])
    inline_keyboard.append([
        InlineKeyboardButton(text="➕ Register New Bot", callback_data="bot_register_new")
    ])
    inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_to_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_bot_options_keyboard(bot_id: int):
    """Options to manage/edit a specific bot"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Edit Name", callback_data=f"bot_edit_name_{bot_id}"),
                InlineKeyboardButton(text="📝 Edit Description", callback_data=f"bot_edit_desc_{bot_id}")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Edit About Text", callback_data=f"bot_edit_about_{bot_id}"),
                InlineKeyboardButton(text="📜 Edit Commands", callback_data=f"bot_edit_cmds_{bot_id}")
            ],
            [
                InlineKeyboardButton(text="🖼️ Edit Profile Pic", callback_data=f"bot_edit_pic_{bot_id}"),
                InlineKeyboardButton(text="🔑 Get Token", callback_data=f"bot_show_token_{bot_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Delete Bot", callback_data=f"bot_delete_{bot_id}"),
                InlineKeyboardButton(text="🔙 Back to List", callback_data=f"bot_list_back")
            ]
        ]
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