from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json

router = Router()

# Complete FAQ Database
FAQ_CATEGORIES = {
    "general": "📚 General",
    "account": "👤 Account",
    "billing": "💰 Billing",
    "technical": "🔧 Technical",
    "features": "✨ Features"
}

FAQ_DATA = {
    "general": [
        {"id": "g1", "q": "What is this bot?", "a": "This is an enterprise-grade Telegram bot with AI, reminders, weather, and more!"},
        {"id": "g2", "q": "Is it free?", "a": "Basic features are free! Premium features available with subscription."},
        {"id": "g3", "q": "How to get started?", "a": "Just send /start and use the buttons or commands!"},
    ],
    "account": [
        {"id": "a1", "q": "How to change username?", "a": "Your username is managed by Telegram, not the bot."},
        {"id": "a2", "q": "Can I delete my data?", "a": "Yes! Send /delete_my_data to remove all your information."},
        {"id": "a3", "q": "Is my data secure?", "a": "Yes! We use encryption and follow GDPR guidelines."},
    ],
    "billing": [
        {"id": "b1", "q": "Premium subscription cost?", "a": "Premium is $9.99/month or $99.99/year."},
        {"id": "b2", "q": "Payment methods?", "a": "We accept credit cards, PayPal, and cryptocurrency."},
        {"id": "b3", "q": "Refund policy?", "a": "30-day money-back guarantee!"},
    ],
    "technical": [
        {"id": "t1", "q": "Bot not responding?", "a": "Try restarting the bot with /start or contact support."},
        {"id": "t2", "q": "Commands not working?", "a": "Make sure to type commands exactly as shown in /help."},
        {"id": "t3", "q": "How to report bugs?", "a": "Use /feedback command to report issues."},
    ],
    "features": [
        {"id": "f1", "q": "AI capabilities?", "a": "Can answer questions, write code, translate, and more!"},
        {"id": "f2", "q": "Reminder features?", "a": "Set reminders with natural language like 'remind me in 10 minutes'."},
        {"id": "f3", "q": "Weather accuracy?", "a": "Real-time data from OpenWeatherMap, updated every hour."},
    ]
}

class FAQStates(StatesGroup):
    searching = State()

@router.message(Command("faq"))
async def cmd_faq(message: Message):
    """Show FAQ categories"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat_name, callback_data=f"faq_cat_{cat_key}")]
            for cat_key, cat_name in FAQ_CATEGORIES.items()
        ] + [
            [InlineKeyboardButton(text="🔍 Search FAQ", callback_data="faq_search"),
             InlineKeyboardButton(text="📞 Contact Support", callback_data="faq_contact")],
            [InlineKeyboardButton(text="⭐ Premium FAQ", callback_data="faq_premium")]
        ]
    )
    
    await message.answer(
        "<b>❓ Frequently Asked Questions</b>\n\n"
        "Select a category to browse FAQs:\n"
        "Or use the buttons below for more options.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("faq_cat_"))
async def show_category(callback: CallbackQuery):
    """Show FAQs for selected category"""
    category = callback.data.split("_")[2]
    faqs = FAQ_DATA.get(category, [])
    
    if not faqs:
        await callback.answer("No FAQs in this category yet!")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{faq['q'][:50]}...", callback_data=f"faq_ans_{faq['id']}")]
            for faq in faqs[:5]  # Show first 5
        ] + [
            [InlineKeyboardButton(text="🔙 Back to Categories", callback_data="faq_back")]
        ]
    )
    
    await callback.message.edit_text(
        f"<b>📚 {FAQ_CATEGORIES[category]}</b>\n\nSelect a question:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("faq_ans_"))
async def show_answer(callback: CallbackQuery):
    """Show answer for selected FAQ"""
    faq_id = callback.data.split("_")[2]
    
    # Find the FAQ
    answer = None
    question = None
    for category, faqs in FAQ_DATA.items():
        for faq in faqs:
            if faq["id"] == faq_id:
                question = faq["q"]
                answer = faq["a"]
                break
        if answer:
            break
    
    if answer:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👍 Helpful", callback_data=f"faq_helpful_{faq_id}"),
                 InlineKeyboardButton(text="👎 Not Helpful", callback_data=f"faq_nothelpful_{faq_id}")],
                [InlineKeyboardButton(text="🔙 Back to Category", callback_data="faq_back")]
            ]
        )
        
        await callback.message.edit_text(
            f"<b>❓ Question:</b>\n{question}\n\n"
            f"<b>✅ Answer:</b>\n{answer}\n\n"
            f"<i>Was this answer helpful?</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.answer("Answer not found!")
    
    await callback.answer()

@router.callback_query(F.data == "faq_back")
async def back_to_categories(callback: CallbackQuery):
    """Go back to categories"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat_name, callback_data=f"faq_cat_{cat_key}")]
            for cat_key, cat_name in FAQ_CATEGORIES.items()
        ] + [
            [InlineKeyboardButton(text="🔍 Search FAQ", callback_data="faq_search"),
             InlineKeyboardButton(text="📞 Contact Support", callback_data="faq_contact")]
        ]
    )
    
    await callback.message.edit_text(
        "<b>❓ Frequently Asked Questions</b>\n\nSelect a category:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "faq_search")
async def search_faq_prompt(callback: CallbackQuery, state: FSMContext):
    """Prompt user to search FAQs"""
    await state.set_state(FAQStates.searching)
    await callback.message.edit_text(
        "<b>🔍 Search FAQs</b>\n\n"
        "Send me a keyword or question to search for.\n\n"
        "<i>Example: 'payment', 'account', 'weather'</i>\n\n"
        "Type /cancel to cancel search.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(FAQStates.searching)
async def perform_search(message: Message, state: FSMContext):
    """Search FAQs based on user input"""
    query = message.text.lower()
    results = []
    
    for category, faqs in FAQ_DATA.items():
        for faq in faqs:
            if query in faq["q"].lower() or query in faq["a"].lower():
                results.append(faq)
    
    if results:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{r['q'][:50]}...", callback_data=f"faq_ans_{r['id']}")]
                for r in results[:5]
            ] + [
                [InlineKeyboardButton(text="🔍 New Search", callback_data="faq_search")]
            ]
        )
        
        await message.answer(
            f"<b>🔍 Search Results for '{query}':</b>\n\nFound {len(results)} results.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"<b>❌ No results found for '{query}'</b>\n\n"
            "Try different keywords or contact support.",
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "faq_contact")
async def contact_support(callback: CallbackQuery):
    """Show contact information"""
    await callback.message.edit_text(
        "<b>📞 Contact Support</b>\n\n"
        "<b>📧 Email:</b> support@company.com\n"
        "<b>💬 Telegram:</b> @support_bot\n"
        "<b>🌐 Website:</b> https://company.com/support\n"
        "<b>📱 Phone:</b> +1 (555) 123-4567\n\n"
        "<b>⏰ Support Hours:</b>\n"
        "Monday-Friday: 9 AM - 6 PM EST\n"
        "Saturday: 10 AM - 4 PM EST\n"
        "Sunday: Closed\n\n"
        "<i>Emergency support available 24/7 for premium users.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("faq_helpful_"))
async def helpful_feedback(callback: CallbackQuery):
    """Record helpful feedback"""
    faq_id = callback.data.split("_")[2]
    # Save to database
    await callback.answer("Thanks for your feedback! 👍")
    await callback.message.delete()

@router.callback_query(F.data.startswith("faq_nothelpful_"))
async def nothelpful_feedback(callback: CallbackQuery):
    """Record not helpful feedback"""
    faq_id = callback.data.split("_")[2]
    # Save to database and suggest improvements
    await callback.answer("Sorry about that! We'll improve this answer.")
    await callback.message.delete()