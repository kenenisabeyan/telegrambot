from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from config import settings

router = Router()

# Conversation history (use Redis in production)
conversation_history = {}

# OpenAI configuration (optional - will use mock if not available)
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class AIStates(StatesGroup):
    chatting = State()

async def get_ai_response(prompt: str, user_id: int, context: bool = True) -> str:
    """Get response from AI with conversation context"""
    
    # If no API key, use intelligent mock responses
    if not OPENAI_API_KEY:
        return get_mock_response(prompt)
    
    # Build conversation context
    messages = []
    if context and user_id in conversation_history:
        # Get last 5 messages for context
        history = conversation_history[user_id][-5:]
        messages.extend(history)
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            async with session.post(OPENAI_API_URL, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response = result["choices"][0]["message"]["content"]
                    
                    # Save to history
                    if user_id not in conversation_history:
                        conversation_history[user_id] = []
                    conversation_history[user_id].append({"role": "user", "content": prompt})
                    conversation_history[user_id].append({"role": "assistant", "content": response})
                    
                    # Limit history length
                    if len(conversation_history[user_id]) > 20:
                        conversation_history[user_id] = conversation_history[user_id][-20:]
                    
                    return response
                else:
                    return f"❌ AI Error: {resp.status}. Check API configuration."
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_mock_response(prompt: str) -> str:
    """Intelligent mock responses for when no API key is available"""
    prompt_lower = prompt.lower()
    
    # Code-related queries
    if any(word in prompt_lower for word in ['code', 'python', 'javascript', 'function']):
        if 'python' in prompt_lower:
            return "```python\n# Here's a Python example:\ndef hello_world():\n    print('Hello, World!')\n\nhello_world()\n```\n\nThis is a simple function. Want to learn more specific concepts?"
        elif 'javascript' in prompt_lower:
            return "```javascript\n// JavaScript example:\nfunction greet(name) {\n    console.log(`Hello, ${name}!`);\n}\n\ngreet('User');\n```\n\nNeed help with specific JavaScript concepts?"
    
    # General questions
    if 'hello' in prompt_lower or 'hi' in prompt_lower:
        return "👋 Hello! How can I assist you today? I can help with coding, answer questions, or just chat!"
    
    if 'help' in prompt_lower:
        return "🤖 I'm your AI assistant! I can:\n• Answer questions\n• Write and explain code\n• Help with problem-solving\n• Have general conversations\n\nWhat would you like help with?"
    
    if 'weather' in prompt_lower:
        return "🌤 For weather information, use the /weather command followed by a city name!\nExample: /weather London"
    
    if 'remind' in prompt_lower:
        return "⏰ To set a reminder, use the /remind command!\nExample: /remind 10m Call John"
    
    # Default response
    return (
        f"🤖 I'm your AI assistant! I received: '{prompt}'\n\n"
        f"💡 To use the full OpenAI integration:\n"
        f"1. Get an API key from https://platform.openai.com\n"
        f"2. Add it to your .env file: OPENAI_API_KEY=your_key\n"
        f"3. Restart the bot\n\n"
        f"Meanwhile, I can still help with basic responses! What specific topic interests you?"
    )

@router.message(Command("ai"))
@router.message(F.text == "AI Chat")
async def cmd_ai(message: Message, state: FSMContext, db=None):
    """Handle /ai command"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Start Chat", callback_data="ai_start_chat")],
                [InlineKeyboardButton(text="🔄 Clear History", callback_data="ai_clear_history")],
                [InlineKeyboardButton(text="ℹ️ About", callback_data="ai_about")]
            ]
        )
        
        await message.answer(
            "<b>🤖 AI Chat Assistant</b>\n\n"
            "Send <code>/ai [your question]</code> to chat with AI!\n\n"
            "<b>Examples:</b>\n"
            "• <code>/ai What is machine learning?</code>\n"
            "• <code>/ai Write a Python function to sort a list</code>\n"
            "• <code>/ai Explain quantum computing in simple terms</code>\n\n"
            "<b>Features:</b>\n"
            "• 💬 Conversation memory (remembers context)\n"
            "• 📝 Code generation and explanation\n"
            "• 🔍 Research assistance\n"
            "• 🌐 Multi-language support\n\n"
            f"<i>OpenAI integration: {'✅ Active' if OPENAI_API_KEY else '❌ Inactive (mock mode)'}</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    question = args[1]
    
    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Get AI response
    response = await get_ai_response(question, message.from_user.id)
    
    # Split long responses
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.answer(response[i:i+4000], parse_mode="HTML")
    else:
        await message.answer(response, parse_mode="HTML")

@router.callback_query(F.data == "ai_start_chat")
async def start_ai_chat(callback: CallbackQuery, state: FSMContext):
    """Start interactive AI chat session"""
    await state.set_state(AIStates.chatting)
    await callback.message.answer(
        "<b>🤖 AI Chat Session Started!</b>\n\n"
        "You can now chat with me directly. Just send any message!\n\n"
        "Commands:\n"
        "• /end_chat - End the session\n"
        "• /clear_history - Clear conversation history\n\n"
        "<i>Start chatting now! 💬</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AIStates.chatting)
async def handle_ai_chat(message: Message, state: FSMContext, db=None):
    """Handle messages during AI chat session"""
    if db:
        await db.log_command(message.from_user.id, "ai")
    if message.text.startswith("/end_chat"):
        await state.clear()
        await message.answer("👋 AI Chat session ended. Use /ai to start again!")
        return
    
    if message.text.startswith("/clear_history"):
        if message.from_user.id in conversation_history:
            del conversation_history[message.from_user.id]
        await message.answer("🧹 Conversation history cleared!")
        return
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    response = await get_ai_response(message.text, message.from_user.id)
    await message.answer(response, parse_mode="HTML")

@router.callback_query(F.data == "ai_clear_history")
async def clear_ai_history(callback: CallbackQuery):
    """Clear conversation history"""
    if callback.from_user.id in conversation_history:
        del conversation_history[callback.from_user.id]
        await callback.answer("✅ History cleared!")
        await callback.message.answer("🧹 Your conversation history has been cleared.")
    else:
        await callback.answer("No history to clear!")

@router.callback_query(F.data == "ai_about")
async def ai_about(callback: CallbackQuery):
    """Show AI information"""
    about_text = (
        "<b>🤖 About AI Assistant</b>\n\n"
        "<b>Powered by:</b> OpenAI GPT-3.5 Turbo\n"
        "<b>Capabilities:</b>\n"
        "• Natural language understanding\n"
        "• Code generation in multiple languages\n"
        "• Mathematical calculations\n"
        "• Translation between languages\n"
        "• Creative writing\n"
        "• Research assistance\n\n"
        "<b>Limitations:</b>\n"
        "• Knowledge cutoff: 2021\n"
        "• Cannot access real-time data\n"
        "• May occasionally produce incorrect information\n\n"
        "<b>Privacy:</b>\n"
        "Conversations are stored temporarily and not shared.\n\n"
        "<i>For real-time data (weather, news), use specific commands!</i>"
    )
    await callback.message.answer(about_text, parse_mode="HTML")
    await callback.answer()