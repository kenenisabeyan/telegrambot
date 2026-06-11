from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

# Temporary FAQ data
FAQ_DATA = {
    "1": {"question": "What is this bot?", "answer": "This is an enterprise-grade Telegram bot with multiple features!"},
    "2": {"question": "How to get help?", "answer": "Use /help command or contact support."},
    "3": {"question": "Is it free?", "answer": "Yes, basic features are free!"},
}

@router.message(Command("faq"))
async def cmd_faq(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=q_data["question"], callback_data=f"faq_{qid}")]
            for qid, q_data in FAQ_DATA.items()
        ]
    )
    await message.answer("❓ Frequently Asked Questions\n\nSelect a question:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("faq_"))
async def faq_callback(callback: CallbackQuery):
    faq_id = callback.data.split("_")[1]
    q_data = FAQ_DATA.get(faq_id)
    
    if q_data:
        answer = f"<b>Q: {q_data['question']}</b>\n\n<i>A: {q_data['answer']}</i>"
    else:
        answer = "FAQ not found."
    
    await callback.answer()
    await callback.message.answer(answer)