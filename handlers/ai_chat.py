from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("ai"))
async def cmd_ai(message: Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "🤖 AI Chat\n\n"
            "Usage: /ai [your question]\n"
            "Example: /ai What is machine learning?\n\n"
            "Full AI integration coming soon with OpenAI API!"
        )
        return
    
    question = args[1]
    await message.answer(f"🤖 Processing your question: '{question}'\n\n✨ Full AI features will be available after API configuration!")