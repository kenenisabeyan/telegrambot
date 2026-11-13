import hashlib
from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from handlers.faq import FAQ_DATA
from handlers.ai_chat import get_mock_response, OPENAI_API_KEY, get_ai_response
from handlers.weather import get_weather_data

router = Router()

def make_result_id(text: str) -> str:
    """Generate deterministic MD5 id for inline results"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

@router.inline_query()
async def inline_query_handler(query: InlineQuery, db=None):
    """Handle inline mode queries across Telegram chats"""
    query_text = query.query.strip().lower()
    results = []

    # 1. Share Bot Card
    share_text = (
        "<b>🤖 Enterprise Telegram Bot</b>\n\n"
        "Your all-in-one assistant featuring:\n"
        "• 🛠️ Dynamic Bot Manager (@BotFather Clone)\n"
        "• ⏰ Natural Language Reminders\n"
        "• 🤖 Multi-Persona AI Chat\n"
        "• 🌤️ Live Global Weather\n\n"
        f"Try it now: @{(await query.bot.get_me()).username}"
    )
    results.append(
        InlineQueryResultArticle(
            id=make_result_id("share_bot"),
            title="🚀 Share Enterprise Bot",
            description="Share this productivity platform with friends or groups",
            input_message_content=InputTextMessageContent(
                message_text=share_text,
                parse_mode="HTML"
            )
        )
    )

    # 2. FAQ Inline Search
    matched_faqs = []
    for cat, items in FAQ_DATA.items():
        for item in items:
            if not query_text or query_text in item["q"].lower() or query_text in item["a"].lower():
                matched_faqs.append(item)

    for faq in matched_faqs[:5]:
        faq_content = (
            f"<b>📚 FAQ: {faq['q']}</b>\n\n"
            f"{faq['a']}\n\n"
            f"<i>Shared via @{(await query.bot.get_me()).username}</i>"
        )
        results.append(
            InlineQueryResultArticle(
                id=make_result_id(f"faq_{faq['id']}"),
                title=f"❓ {faq['q']}",
                description=faq['a'][:60] + "...",
                input_message_content=InputTextMessageContent(
                    message_text=faq_content,
                    parse_mode="HTML"
                )
            )
        )

    # 3. AI Query Inline Card
    if query_text.startswith("ai ") or len(query_text) > 5:
        prompt = query_text.replace("ai ", "", 1) if query_text.startswith("ai ") else query_text
        if OPENAI_API_KEY:
            try:
                ai_reply = await get_ai_response(prompt, query.from_user.id, context=False)
            except Exception:
                ai_reply = get_mock_response(prompt, persona="assistant")
        else:
            ai_reply = get_mock_response(prompt, persona="assistant")

        ai_msg = (
            f"<b>🤖 AI Answer:</b>\n"
            f"<i>Prompt: {prompt}</i>\n\n"
            f"{ai_reply}\n\n"
            f"<i>Generated via @{(await query.bot.get_me()).username}</i>"
        )
        results.append(
            InlineQueryResultArticle(
                id=make_result_id(f"ai_{prompt}"),
                title=f"🤖 AI Answer: '{prompt[:30]}'",
                description="Instant AI completion for your query",
                input_message_content=InputTextMessageContent(
                    message_text=ai_msg,
                    parse_mode="HTML"
                )
            )
        )

    # 4. Weather Query Inline Card
    if query_text.startswith(("weather ", "w ")):
        city = query_text.replace("weather ", "").replace("w ", "").strip()
        if city:
            weather = await get_weather_data(city)
            if weather:
                w_msg = (
                    f"<b>🌤 Weather in {weather['city']}, {weather['country']}:</b>\n\n"
                    f"• <b>Temperature:</b> {weather['temp']}°C (Feels like {weather['feels_like']}°C)\n"
                    f"• <b>Condition:</b> {weather['description'].capitalize()}\n"
                    f"• <b>Humidity:</b> {weather['humidity']}%\n"
                    f"• <b>Wind:</b> {weather['wind_speed']} m/s\n\n"
                    f"<i>Shared via @{(await query.bot.get_me()).username}</i>"
                )
                results.append(
                    InlineQueryResultArticle(
                        id=make_result_id(f"weather_{city}"),
                        title=f"🌤 Weather for {weather['city']}",
                        description=f"{weather['temp']}°C, {weather['description']}",
                        input_message_content=InputTextMessageContent(
                            message_text=w_msg,
                            parse_mode="HTML"
                        )
                    )
                )

    await query.answer(results, cache_time=30, is_personal=True)
