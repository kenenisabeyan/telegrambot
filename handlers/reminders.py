from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import re
import asyncio
import json

router = Router()

# Store reminders in memory (use database in production)
user_reminders = {}

class ReminderStates(StatesGroup):
    waiting_for_time = State()
    waiting_for_message = State()

def parse_natural_time(text: str) -> timedelta | None:
    """Parse natural language time expressions"""
    text = text.lower().strip()
    
    # Patterns for different time units
    patterns = {
        'seconds': r'(\d+)\s*seconds?',
        'minutes': r'(\d+)\s*minutes?',
        'hours': r'(\d+)\s*hours?',
        'days': r'(\d+)\s*days?',
        'weeks': r'(\d+)\s*weeks?',
    }
    
    for unit, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = int(match.group(1))
            if unit == 'seconds':
                return timedelta(seconds=value)
            elif unit == 'minutes':
                return timedelta(minutes=value)
            elif unit == 'hours':
                return timedelta(hours=value)
            elif unit == 'days':
                return timedelta(days=value)
            elif unit == 'weeks':
                return timedelta(weeks=value)
    
    # Handle shorthand (10m, 2h, 1d)
    shorthand = re.search(r'(\d+)([mhdw])', text)
    if shorthand:
        value = int(shorthand.group(1))
        unit = shorthand.group(2)
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
    
    return None

def parse_datetime(text: str) -> datetime | None:
    """Parse absolute datetime expressions"""
    text = text.lower()
    
    # Today at time
    today_match = re.search(r'today at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    if today_match:
        hour = int(today_match.group(1))
        minute = int(today_match.group(2)) if today_match.group(2) else 0
        ampm = today_match.group(3)
        
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        
        now = datetime.now()
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reminder_time < now:
            reminder_time += timedelta(days=1)
        return reminder_time
    
    # Tomorrow at time
    tomorrow_match = re.search(r'tomorrow at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    if tomorrow_match:
        hour = int(tomorrow_match.group(1))
        minute = int(tomorrow_match.group(2)) if tomorrow_match.group(2) else 0
        ampm = tomorrow_match.group(3)
        
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return None

async def send_reminder(bot, chat_id: int, reminder_id: str, message_text: str):
    """Background task to send reminder"""
    reminder = user_reminders.get(reminder_id)
    if not reminder:
        return
    
    # Wait until the reminder time
    now = datetime.now()
    wait_time = (reminder['time'] - now).total_seconds()
    
    if wait_time > 0:
        await asyncio.sleep(wait_time)
    
    # Send the reminder
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Mark as Done", callback_data=f"remind_done_{reminder_id}"),
             InlineKeyboardButton(text="⏰ Snooze 5m", callback_data=f"remind_snooze_{reminder_id}")],
            [InlineKeyboardButton(text="❌ Delete", callback_data=f"remind_delete_{reminder_id}")]
        ]
    )
    
    await bot.send_message(
        chat_id,
        f"<b>⏰ REMINDER!</b>\n\n"
        f"<b>📝 Message:</b> {message_text}\n"
        f"<b>🕐 Scheduled:</b> {reminder['time'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"<i>What would you like to do?</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Remove from active reminders (or mark as sent)
    if reminder_id in user_reminders:
        del user_reminders[reminder_id]

@router.message(Command("remind"))
async def cmd_remind(message: Message, state: FSMContext):
    """Handle /remind command"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        # Show reminder setup guide
        await message.answer(
            "<b>⏰ Set a Reminder</b>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/remind 10m Call John</code>\n"
            "• <code>/remind 2h Team meeting</code>\n"
            "• <code>/remind tomorrow 9am Doctor appointment</code>\n"
            "• <code>/remind today at 3pm Submit report</code>\n\n"
            "<b>Time formats:</b>\n"
            "• <code>10s, 5m, 2h, 3d, 1w</code>\n"
            "• <code>today at 3pm</code>\n"
            "• <code>tomorrow at 9am</code>\n\n"
            "<i>Or just send /remind and I'll guide you step by step!</i>",
            parse_mode="HTML"
        )
        await state.set_state(ReminderStates.waiting_for_message)
        return
    
    full_text = args[1]
    await process_reminder(message, full_text, state)

async def process_reminder(message: Message, text: str, state: FSMContext):
    """Process reminder creation"""
    # Parse time and message
    # Try to extract time from beginning
    time_match = re.match(r'^(\d+[mhdws]|today at|tomorrow at)\s+(.+)', text, re.IGNORECASE)
    
    if not time_match:
        # Try natural language
        time_part = None
        message_part = text
        
        # Check for natural time expressions
        for word in ['minutes', 'minute', 'mins', 'min', 'hours', 'hour', 'days', 'day', 'weeks', 'week']:
            if word in text.lower():
                idx = text.lower().find(word) + len(word)
                time_part = text[:idx]
                message_part = text[idx:].strip()
                break
        
        if not time_part:
            await message.answer(
                "❌ Couldn't understand the time format.\n\n"
                "Please use formats like:\n"
                "• <code>/remind 10m Call John</code>\n"
                "• <code>/remind tomorrow at 9am Meeting</code>\n\n"
                "Or send /remind for interactive setup.",
                parse_mode="HTML"
            )
            return
    else:
        time_part = time_match.group(1)
        message_part = time_match.group(2)
    
    # Parse the time
    reminder_time = None
    delta = parse_natural_time(time_part)
    
    if delta:
        reminder_time = datetime.now() + delta
    else:
        reminder_time = parse_datetime(time_part)
    
    if not reminder_time:
        await message.answer(
            "❌ Invalid time format.\n\n"
            "Try:\n"
            "• <code>/remind 10m Task</code> (10 minutes)\n"
            "• <code>/remind 2h Meeting</code> (2 hours)\n"
            "• <code>/remind tomorrow at 9am Wake up</code>",
            parse_mode="HTML"
        )
        return
    
    # Create reminder
    reminder_id = f"{message.chat.id}_{len(user_reminders) + 1}_{int(reminder_time.timestamp())}"
    
    user_reminders[reminder_id] = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "message": message_part,
        "time": reminder_time,
        "created_at": datetime.now()
    }
    
    # Schedule the reminder
    asyncio.create_task(send_reminder(message.bot, message.chat.id, reminder_id, message_part))
    
    # Format time difference
    time_diff = reminder_time - datetime.now()
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    time_str = []
    if time_diff.days > 0:
        time_str.append(f"{time_diff.days} day(s)")
    if hours > 0:
        time_str.append(f"{hours} hour(s)")
    if minutes > 0:
        time_str.append(f"{minutes} minute(s)")
    
    await message.answer(
        f"<b>✅ Reminder Set!</b>\n\n"
        f"<b>📝 Message:</b> {message_part}\n"
        f"<b>⏰ Time:</b> {reminder_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"<b>⌛ In:</b> {' '.join(time_str)}\n\n"
        f"<i>I'll remind you at the specified time! 🔔</i>",
        parse_mode="HTML"
    )

@router.message(ReminderStates.waiting_for_message)
async def get_reminder_message(message: Message, state: FSMContext):
    """Get reminder message from user"""
    await state.update_data(message_text=message.text)
    await state.set_state(ReminderStates.waiting_for_time)
    await message.answer(
        "<b>⏰ When should I remind you?</b>\n\n"
        "Send me the time (e.g., '10m', '2h', 'tomorrow at 9am'):",
        parse_mode="HTML"
    )

@router.message(ReminderStates.waiting_for_time)
async def get_reminder_time(message: Message, state: FSMContext):
    """Get reminder time from user"""
    data = await state.get_data()
    reminder_text = data.get('message_text')
    
    full_text = f"{message.text} {reminder_text}"
    await process_reminder(message, full_text, state)
    await state.clear()

@router.callback_query(F.data.startswith("remind_done_"))
async def reminder_done(callback: CallbackQuery):
    """Mark reminder as done"""
    reminder_id = callback.data.split("_")[2]
    
    if reminder_id in user_reminders:
        del user_reminders[reminder_id]
        await callback.answer("✅ Reminder completed!")
        await callback.message.edit_text("✅ Reminder marked as done.")
    else:
        await callback.answer("Reminder already processed!")

@router.callback_query(F.data.startswith("remind_snooze_"))
async def reminder_snooze(callback: CallbackQuery):
    """Snooze reminder for 5 minutes"""
    reminder_id = callback.data.split("_")[2]
    
    if reminder_id in user_reminders:
        # Update time
        user_reminders[reminder_id]['time'] += timedelta(minutes=5)
        
        # Reschedule
        asyncio.create_task(send_reminder(
            callback.bot,
            user_reminders[reminder_id]['chat_id'],
            reminder_id,
            user_reminders[reminder_id]['message']
        ))
        
        await callback.answer("⏰ Snoozed for 5 minutes!")
        await callback.message.edit_text("⏰ Reminder snoozed for 5 minutes.")
    else:
        await callback.answer("Reminder already processed!")

@router.callback_query(F.data.startswith("remind_delete_"))
async def reminder_delete(callback: CallbackQuery):
    """Delete reminder"""
    reminder_id = callback.data.split("_")[2]
    
    if reminder_id in user_reminders:
        del user_reminders[reminder_id]
        await callback.answer("❌ Reminder deleted!")
        await callback.message.edit_text("❌ Reminder has been deleted.")
    else:
        await callback.answer("Reminder already processed!")

@router.message(Command("list_reminders"))
async def list_reminders(message: Message):
    """List all active reminders for user"""
    user_reminder_list = [
        (rid, r) for rid, r in user_reminders.items()
        if r['user_id'] == message.from_user.id
    ]
    
    if not user_reminder_list:
        await message.answer("📭 You have no active reminders.")
        return
    
    reminder_text = "<b>📋 Your Active Reminders:</b>\n\n"
    for i, (rid, reminder) in enumerate(user_reminder_list, 1):
        reminder_text += (
            f"{i}. <b>{reminder['message']}</b>\n"
            f"   🕐 {reminder['time'].strftime('%Y-%m-%d %H:%M')}\n"
            f"   📅 Created: {reminder['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    await message.answer(reminder_text, parse_mode="HTML")