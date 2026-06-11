from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Main menu keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="⏰ Reminder")],
            [KeyboardButton(text="🤖 AI Chat"), KeyboardButton(text="🌤 Weather")],
            [KeyboardButton(text="ℹ️ Help")]
        ],
        resize_keyboard=True
    )

def get_faq_keyboard():
    """FAQ inline keyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Question 1", callback_data="faq_1")],
            [InlineKeyboardButton(text="Question 2", callback_data="faq_2")],
            [InlineKeyboardButton(text="Contact Support", callback_data="faq_support")]
        ]
    )