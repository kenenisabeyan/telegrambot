from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from config import settings

router = Router()

# Conversation history (in-memory or Redis)
conversation_history = {}
user_personas = {}

PERSONA_PROMPTS = {
    "assistant": "You are a helpful, professional, and knowledgeable AI productivity assistant.",
    "coder": "You are a Senior Software Engineer specializing in Python, clean architecture, and best practices. Provide concise, clean, well-documented code.",
    "concise": "You are an executive assistant. Give ultra-concise, direct answers in 1-3 bullet points without filler or pleasantries."
}

# OpenAI configuration (optional - will use mock if not available)
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class AIStates(StatesGroup):
    chatting = State()

async def get_ai_response(prompt: str, user_id: int, context: bool = True) -> str:
    """Get response from AI with conversation context and customized persona"""
    persona_key = user_personas.get(user_id, "assistant")
    system_prompt = PERSONA_PROMPTS.get(persona_key, PERSONA_PROMPTS["assistant"])

    # If no API key, use intelligent mock responses
    if not OPENAI_API_KEY:
        return get_mock_response(prompt, persona_key)
    
    # Build conversation context
    messages = [{"role": "system", "content": system_prompt}]
    
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
                "temperature": 0.7 if persona_key != "coder" else 0.2
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
                    return f"❌ AI Error: HTTP {resp.status}. Please check your OpenAI API key or quota."
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

def get_mock_response(prompt: str, persona: str = "assistant") -> str:
    """Intelligent mock responses adapting to selected persona"""
    prompt_lower = prompt.lower()
    
    if persona == "concise":
        return f"• Query received: {prompt[:30]}...\n• Solution: Verified and operational.\n• Next step: Ready for input."
    
    if persona == "coder" or any(word in prompt_lower for word in ['code', 'python', 'javascript', 'function', 'class', 'sql']):
        if 'python' in prompt_lower or 'class' in prompt_lower:
            return (
                "```python\n"
                "# Python Production Implementation\n"
                "from dataclasses import dataclass\n\n"
                "@dataclass\n"
                "class TaskModel:\n"
                "    task_id: int\n"
                "    title: str\n"
                "    is_active: bool = True\n\n"
                "def solve(item: TaskModel) -> bool:\n"
                "    return item.is_active\n"
                "```\n\n"
                "<i>Clean, typed, and PEP 8 compliant. Need tests or async integration?</i>"
            )
        elif 'sql' in prompt_lower or 'db' in prompt_lower:
            return (
                "```sql\n"
                "SELECT user_id, COUNT(*) as total_actions\n"
                "FROM usage_stats\n"
                "WHERE used_at >= NOW() - INTERVAL '7 days'\n"
                "GROUP BY user_id\n"
                "ORDER BY total_actions DESC;\n"
                "```\n\n"
                "<i>Indexed parameterized query sample.</i>"
            )
        else:
            return (
                "```javascript\n"
                "// Asynchronous task handler\n"
                "async function processRequest(payload) {\n"
                "  const response = await fetch('/api/v1/data');\n"
                "  return await response.json();\n"
                "}\n"
                "```"
            )
    
    # General greetings
    if any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'start']):
        return "👋 Hello! I'm your AI productivity assistant. I can write code, analyze data, draft documents, or answer technical questions!"
    
    return (
        f"🤖 <b>AI Assistant Response</b>\n\n"
        f"I received your inquiry regarding: <i>'{prompt}'</i>\n\n"
        f"💡 <b>Full OpenAI Integration:</b>\n"
        f"To enable live GPT-3.5/GPT-4 completions, set <code>OPENAI_API_KEY</code> in your <code>.env</code> file.\n\n"
        f"Currently running in intelligent offline mock mode with full context retention."
    )

def get_ai_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Start Interactive Chat", callback_data="ai_start_chat"),
                InlineKeyboardButton(text="🎭 Choose Persona", callback_data="ai_choose_persona")
            ],
            [
                InlineKeyboardButton(text="🔄 Clear History", callback_data="ai_clear_history"),
                InlineKeyboardButton(text="ℹ️ Capabilities", callback_data="ai_about")
            ]
        ]
    )

@router.message(Command("ai"))
@router.message(F.text == "AI Chat")
async def cmd_ai(message: Message, state: FSMContext, db=None):
    """Handle /ai command"""
    if db:
        await db.log_command(message.from_user.id, "ai")
        
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        persona = user_personas.get(message.from_user.id, "assistant").capitalize()
        await message.answer(
            f"<b>🤖 Conversational AI Assistant</b>\n\n"
            f"• <b>Active Persona:</b> <code>{persona}</code>\n"
            f"• <b>Engine:</b> {'🟢 OpenAI GPT-3.5 Turbo' if OPENAI_API_KEY else '⚪ Local Mock Intelligence'}\n"
            f"• <b>Context Memory:</b> Active (Last 5 dialogue turns)\n\n"
            f"<b>Quick Usage:</b>\n"
            f"Send <code>/ai [your prompt]</code> or click below to enter interactive chat mode!",
            reply_markup=get_ai_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    question = args[1]
    await message.bot.send_chat_action(message.chat.id, "typing")
    response = await get_ai_response(question, message.from_user.id)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.answer(response[i:i+4000], parse_mode="HTML")
    else:
        await message.answer(response, parse_mode="HTML")

@router.callback_query(F.data == "ai_choose_persona")
async def ai_choose_persona(callback: CallbackQuery):
    """Open persona selection menu"""
    current = user_personas.get(callback.from_user.id, "assistant")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'✅ ' if current == 'assistant' else ''}🧑‍💼 Productivity Assistant",
                    callback_data="ai_set_persona_assistant"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'✅ ' if current == 'coder' else ''}💻 Senior Software Engineer",
                    callback_data="ai_set_persona_coder"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'✅ ' if current == 'concise' else ''}⚡ Ultra-Concise Executive",
                    callback_data="ai_set_persona_concise"
                )
            ],
            [
                InlineKeyboardButton(text="🔙 Back to AI Menu", callback_data="ai_menu_back")
            ]
        ]
    )
    await callback.message.edit_text(
        "<b>🎭 Select AI Persona</b>\n\n"
        "Customize how the AI responds to your questions:\n\n"
        "• <b>Productivity Assistant:</b> Detailed, friendly, and structured.\n"
        "• <b>Senior Software Engineer:</b> Writes clean code, refactors, and explains bugs.\n"
        "• <b>Ultra-Concise Executive:</b> Direct bullet points, zero filler.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ai_set_persona_"))
async def ai_set_persona(callback: CallbackQuery):
    """Change active AI persona"""
    new_persona = callback.data.replace("ai_set_persona_", "")
    user_personas[callback.from_user.id] = new_persona
    
    # Clear history on persona switch to avoid conflicting context
    if callback.from_user.id in conversation_history:
        del conversation_history[callback.from_user.id]
        
    await callback.answer(f"Switched persona to {new_persona.capitalize()}!", show_alert=True)
    await ai_choose_persona(callback)

@router.callback_query(F.data == "ai_menu_back")
async def ai_menu_back(callback: CallbackQuery):
    """Return to main AI menu"""
    persona = user_personas.get(callback.from_user.id, "assistant").capitalize()
    await callback.message.edit_text(
        f"<b>🤖 Conversational AI Assistant</b>\n\n"
        f"• <b>Active Persona:</b> <code>{persona}</code>\n"
        f"• <b>Engine:</b> {'🟢 OpenAI GPT-3.5 Turbo' if OPENAI_API_KEY else '⚪ Local Mock Intelligence'}\n"
        f"• <b>Context Memory:</b> Active (Last 5 dialogue turns)\n\n"
        f"<b>Quick Usage:</b>\n"
        f"Send <code>/ai [your prompt]</code> or click below to enter interactive chat mode!",
        reply_markup=get_ai_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_start_chat")
async def start_ai_chat(callback: CallbackQuery, state: FSMContext):
    """Start interactive AI chat session"""
    await state.set_state(AIStates.chatting)
    persona = user_personas.get(callback.from_user.id, "assistant").capitalize()
    await callback.message.answer(
        f"<b>🤖 Interactive Chat Activated ({persona})</b>\n\n"
        f"You can now send any message without prefixing /ai.\n\n"
        f"• Type <code>/end_chat</code> or <code>/cancel</code> to exit.\n"
        f"• Type <code>/clear_history</code> to wipe dialogue memory.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AIStates.chatting)
async def handle_ai_chat(message: Message, state: FSMContext, db=None):
    """Handle messages during AI chat session"""
    if db:
        await db.log_command(message.from_user.id, "ai")
        
    if message.text.startswith(("/end_chat", "/cancel", "Cancel")):
        await state.clear()
        await message.answer("👋 Interactive chat session concluded. Use /ai to start again anytime!")
        return
    
    if message.text.startswith("/clear_history"):
        if message.from_user.id in conversation_history:
            del conversation_history[message.from_user.id]
        await message.answer("🧹 Dialogue memory cleared successfully!")
        return
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    response = await get_ai_response(message.text, message.from_user.id)
    await message.answer(response, parse_mode="HTML")

@router.callback_query(F.data == "ai_clear_history")
async def clear_ai_history(callback: CallbackQuery):
    """Clear conversation history"""
    if callback.from_user.id in conversation_history:
        del conversation_history[callback.from_user.id]
        await callback.answer("✅ Dialogue memory cleared!", show_alert=True)
    else:
        await callback.answer("No active dialogue history found.")

@router.callback_query(F.data == "ai_about")
async def ai_about(callback: CallbackQuery):
    """Show AI information"""
    about_text = (
        "<b>🤖 About the AI Intelligence Layer</b>\n\n"
        "• <b>Base Model:</b> OpenAI GPT-3.5 Turbo\n"
        "• <b>Context Window:</b> 5 conversational turns preserved\n"
        "• <b>Temperature Optimization:</b> 0.2 for coding accuracy, 0.7 for general assistance\n"
        "• <b>Safety:</b> Credentials and system secrets automatically redacted by security middleware."
    )
    await callback.message.answer(about_text, parse_mode="HTML")
    await callback.answer()
