from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class ReminderStates(StatesGroup):
    waiting_for_reminder = State()

@router.message(Command("remind"))
async def cmd_remind(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "⏰ Set a reminder\n\n"
            "Usage: /remind [message]\n"
            "Example: /remind Call John at 3pm\n\n"
            "Coming soon: Time-based reminders!"
        )
        return
    
    reminder_text = args[1]
    await message.answer(f"✅ Reminder set: '{reminder_text}'\n\n⏰ You'll be notified at the specified time (coming soon in full version!)")