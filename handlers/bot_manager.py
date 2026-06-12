import os
import re
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from utils.keyboards import get_main_keyboard, get_my_bots_keyboard, get_bot_options_keyboard

logger = logging.getLogger(__name__)
router = Router()

# In-memory database fallback
MOCK_MANAGED_BOTS = {}

async def db_add_bot(user_id: int, token: str, bot_id: int, username: str, name: str, db=None):
    if db:
        await db.add_managed_bot(user_id, token, bot_id, username, name)
    else:
        if user_id not in MOCK_MANAGED_BOTS:
            MOCK_MANAGED_BOTS[user_id] = []
        # Check conflict
        MOCK_MANAGED_BOTS[user_id] = [b for b in MOCK_MANAGED_BOTS[user_id] if b['token'] != token]
        MOCK_MANAGED_BOTS[user_id].append({
            "owner_id": user_id,
            "token": token,
            "bot_id": bot_id,
            "username": username,
            "name": name,
            "description": None,
            "about_text": None,
            "commands": None
        })

async def db_get_bots(user_id: int, db=None) -> list:
    if db:
        return await db.get_user_managed_bots(user_id)
    else:
        return MOCK_MANAGED_BOTS.get(user_id, [])

async def db_get_bot(user_id: int, bot_id: int, db=None) -> dict:
    if db:
        return await db.get_managed_bot(user_id, bot_id)
    else:
        for b in MOCK_MANAGED_BOTS.get(user_id, []):
            if b['bot_id'] == bot_id:
                return b
        return None

async def db_update_bot(user_id: int, bot_id: int, db=None, **fields):
    if db:
        await db.update_managed_bot_fields(user_id, bot_id, **fields)
    else:
        for b in MOCK_MANAGED_BOTS.get(user_id, []):
            if b['bot_id'] == bot_id:
                b.update(fields)
                break

async def db_delete_bot(user_id: int, bot_id: int, db=None):
    if db:
        await db.delete_managed_bot(user_id, bot_id)
    else:
        if user_id in MOCK_MANAGED_BOTS:
            MOCK_MANAGED_BOTS[user_id] = [b for b in MOCK_MANAGED_BOTS[user_id] if b['bot_id'] != bot_id]

async def call_bot_api(token: str, method_name: str, *args, **kwargs):
    """Execute a Telegram Bot API method using a temporary Bot instance and close the session."""
    temp_bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        method = getattr(temp_bot, method_name)
        return await method(*args, **kwargs)
    finally:
        await temp_bot.session.close()

class BotManagerStates(StatesGroup):
    waiting_for_token = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_about_text = State()
    waiting_for_commands = State()
    waiting_for_photo = State()

@router.message(Command("bot_manager"))
@router.message(F.text == "Bot Manager")
async def cmd_bot_manager(message: Message, state: FSMContext, db=None):
    await state.clear()
    if db:
        await db.log_command(message.from_user.id, "bot_manager")
    
    bots = await db_get_bots(message.from_user.id, db)
    
    if not bots:
        welcome_text = (
            "<b>🤖 Bot Manager Dashboard</b>\n\n"
            "You don't have any bots registered in the manager yet.\n\n"
            "To get started, we need your Bot Token from @BotFather.\n"
            "Please follow these steps:\n"
            "1. Open @BotFather and create a new bot (using <code>/newbot</code>).\n"
            "2. Copy the HTTP API token provided.\n"
            "3. Send the token here."
        )
        await message.answer(welcome_text, reply_markup=get_my_bots_keyboard(bots), parse_mode="HTML")
    else:
        await message.answer(
            "<b>🤖 Managed Bots List</b>\n\n"
            "Select a bot to configure or register a new one:",
            reply_markup=get_my_bots_keyboard(bots),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "bot_register_new")
async def callback_register_new(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotManagerStates.waiting_for_token)
    await callback.message.edit_text(
        "<b>➕ Register a New Bot</b>\n\n"
        "Please send me the HTTP API token of your bot (e.g. <code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>).\n\n"
        "<i>Type /cancel to abort.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("newbot"))
async def cmd_newbot(message: Message, state: FSMContext):
    await state.set_state(BotManagerStates.waiting_for_token)
    await message.answer(
        "<b>➕ Register a New Bot</b>\n\n"
        "Please send me the HTTP API token of your bot (e.g. <code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>).\n\n"
        "<i>Type /cancel to abort.</i>",
        parse_mode="HTML"
    )

@router.message(BotManagerStates.waiting_for_token)
async def process_token_input(message: Message, state: FSMContext, db=None):
    token = message.text.strip()
    
    # Regex validation for token format
    if not re.match(r"^\d+:[A-Za-z0-9_-]{30,50}$", token):
        await message.answer(
            "❌ Invalid token format. A valid token looks like <code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>.\n\n"
            "Please try again or type /cancel."
        )
        return
    
    await message.answer("🔄 Validating token with Telegram API...")
    
    try:
        bot_info = await call_bot_api(token, "get_me")
        
        await db_add_bot(
            user_id=message.from_user.id,
            token=token,
            bot_id=bot_info.id,
            username=bot_info.username,
            name=bot_info.first_name,
            db=db
        )
        
        await state.clear()
        success_text = (
            f"<b>🎉 Success!</b>\n\n"
            f"Bot has been registered successfully.\n"
            f"• <b>Name:</b> {bot_info.first_name}\n"
            f"• <b>Username:</b> @{bot_info.username}\n"
            f"• <b>ID:</b> <code>{bot_info.id}</code>\n\n"
            f"You can now manage its settings using `/mybots`!"
        )
        await message.answer(success_text, reply_markup=get_main_keyboard(message.from_user.id), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Failed to validate bot token: {e}")
        await message.answer(
            f"❌ Failed to connect to bot. Verification failed.\n"
            f"Error details: <code>{str(e)}</code>\n\n"
            f"Please make sure the token is correct and not revoked, and try again."
        )

@router.message(Command("mybots"))
async def cmd_mybots(message: Message, db=None):
    bots = await db_get_bots(message.from_user.id, db)
    if not bots:
        await message.answer(
            "📭 You don't have any registered bots.\nUse `/newbot` to register one!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        await message.answer(
            "<b>🤖 Your Managed Bots</b>\n\nSelect a bot to configure settings:",
            reply_markup=get_my_bots_keyboard(bots),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("bot_select_"))
async def callback_select_bot(callback: CallbackQuery, db=None):
    bot_id = int(callback.data.split("_")[2])
    bot_data = await db_get_bot(callback.from_user.id, bot_id, db)
    
    if not bot_data:
        await callback.answer("Bot not found!", show_alert=True)
        return
    
    try:
        me = await call_bot_api(bot_data['token'], "get_me")
        if me.first_name != bot_data['name']:
            await db_update_bot(callback.from_user.id, bot_id, db, name=me.first_name)
            bot_data['name'] = me.first_name
    except Exception:
        pass

    menu_text = (
        f"<b>🤖 Bot Configuration: @{bot_data['username']}</b>\n\n"
        f"• <b>Name:</b> {bot_data['name']}\n"
        f"• <b>Username:</b> @{bot_data['username']}\n"
        f"• <b>ID:</b> <code>{bot_id}</code>\n"
        f"• <b>Status:</b> ✅ Active & Connected\n\n"
        f"Select an option below to update your bot's properties:"
    )
    
    await callback.message.edit_text(menu_text, reply_markup=get_bot_options_keyboard(bot_id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "bot_list_back")
@router.callback_query(F.data == "bot_edit_back")
async def callback_list_back(callback: CallbackQuery, db=None):
    bots = await db_get_bots(callback.from_user.id, db)
    await callback.message.edit_text(
        "<b>🤖 Your Managed Bots</b>\n\nSelect a bot to configure settings:",
        reply_markup=get_my_bots_keyboard(bots),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "bot_list_back")
async def callback_bot_list_back(callback: CallbackQuery, db=None):
    bots = await db_get_bots(callback.from_user.id, db)
    await callback.message.edit_text(
        "<b>🤖 Your Managed Bots</b>\n\nSelect a bot to configure settings:",
        reply_markup=get_my_bots_keyboard(bots),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("bot_delete_"))
async def callback_delete_bot(callback: CallbackQuery, db=None):
    bot_id = int(callback.data.split("_")[2])
    bot_data = await db_get_bot(callback.from_user.id, bot_id, db)
    
    if not bot_data:
        await callback.answer("Bot not found!", show_alert=True)
        return
        
    await db_delete_bot(callback.from_user.id, bot_id, db)
    await callback.answer(f"Deleted @{bot_data['username']}", show_alert=True)
    
    bots = await db_get_bots(callback.from_user.id, db)
    await callback.message.edit_text(
        "<b>🤖 Your Managed Bots</b>\n\nSelect a bot to configure settings:",
        reply_markup=get_my_bots_keyboard(bots),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("bot_show_token_"))
async def callback_show_token(callback: CallbackQuery, db=None):
    bot_id = int(callback.data.split("_")[3])
    bot_data = await db_get_bot(callback.from_user.id, bot_id, db)
    
    if not bot_data:
        await callback.answer("Bot not found!", show_alert=True)
        return
    
    token_text = (
        f"<b>🔑 Token for @{bot_data['username']}</b>\n\n"
        f"<code>{bot_data['token']}</code>\n\n"
        f"⚠️ <i>Do not share this token with anyone!</i>"
    )
    
    await callback.message.answer(token_text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("bot_edit_"))
async def callback_edit_property(callback: CallbackQuery, state: FSMContext, db=None):
    parts = callback.data.split("_")
    action = parts[2]
    bot_id = int(parts[3])
    
    bot_data = await db_get_bot(callback.from_user.id, bot_id, db)
    if not bot_data:
        await callback.answer("Bot not found!", show_alert=True)
        return
        
    await state.update_data(managing_bot_id=bot_id, managing_bot_token=bot_data['token'])
    
    if action == "name":
        await state.set_state(BotManagerStates.waiting_for_name)
        prompt = (
            f"<b>✍️ Edit Name for @{bot_data['username']}</b>\n\n"
            f"Current name: <b>{bot_data['name']}</b>\n\n"
            f"Please send the new display name for your bot.\n"
            f"<i>Type /cancel to abort.</i>"
        )
    elif action == "desc":
        await state.set_state(BotManagerStates.waiting_for_description)
        prompt = (
            f"<b>📝 Edit Description for @{bot_data['username']}</b>\n\n"
            f"Please send the new description for your bot. This is shown when a user opens the chat.\n"
            f"<i>Type /cancel to abort.</i>"
        )
    elif action == "about":
        await state.set_state(BotManagerStates.waiting_for_about_text)
        prompt = (
            f"<b>ℹ️ Edit About Text for @{bot_data['username']}</b>\n\n"
            f"Please send the new about text (short description). This is shown on the bot's profile.\n"
            f"<i>Type /cancel to abort.</i>"
        )
    elif action == "cmds":
        await state.set_state(BotManagerStates.waiting_for_commands)
        prompt = (
            f"<b>📜 Edit Commands for @{bot_data['username']}</b>\n\n"
            f"Please send the list of commands in the following format:\n"
            f"<code>command1 - description1\ncommand2 - description2</code>\n\n"
            f"Example:\n"
            f"<code>start - Start the bot\nhelp - Get help info</code>\n"
            f"<i>Type /cancel to abort.</i>"
        )
    elif action == "pic":
        await state.set_state(BotManagerStates.waiting_for_photo)
        prompt = (
            f"<b>🖼️ Edit Profile Picture for @{bot_data['username']}</b>\n\n"
            f"Please send/upload a photo to set as the bot's profile picture.\n"
            f"<i>Type /cancel to abort.</i>"
        )
    elif action == "back":
        # Handled by bot_list_back
        await callback.answer()
        return
    else:
        await callback.answer("Invalid operation")
        return
        
    await callback.message.answer(prompt, parse_mode="HTML")
    await callback.answer()

@router.message(BotManagerStates.waiting_for_name)
async def process_name_input(message: Message, state: FSMContext, db=None):
    data = await state.get_data()
    bot_id = data.get("managing_bot_id")
    token = data.get("managing_bot_token")
    new_name = message.text.strip()
    
    await message.answer("🔄 Updating display name on Telegram...")
    try:
        await call_bot_api(token, "set_my_name", name=new_name)
        await db_update_bot(message.from_user.id, bot_id, db, name=new_name)
        await state.clear()
        await message.answer(f"✅ Bot display name updated successfully to: <b>{new_name}</b>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Failed to update name. Error: <code>{str(e)}</code>", parse_mode="HTML")

@router.message(BotManagerStates.waiting_for_description)
async def process_desc_input(message: Message, state: FSMContext, db=None):
    data = await state.get_data()
    bot_id = data.get("managing_bot_id")
    token = data.get("managing_bot_token")
    new_desc = message.text.strip()
    
    await message.answer("🔄 Updating description on Telegram...")
    try:
        await call_bot_api(token, "set_my_description", description=new_desc)
        await db_update_bot(message.from_user.id, bot_id, db, description=new_desc)
        await state.clear()
        await message.answer("✅ Bot description updated successfully!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Failed to update description. Error: <code>{str(e)}</code>", parse_mode="HTML")

@router.message(BotManagerStates.waiting_for_about_text)
async def process_about_input(message: Message, state: FSMContext, db=None):
    data = await state.get_data()
    bot_id = data.get("managing_bot_id")
    token = data.get("managing_bot_token")
    new_about = message.text.strip()
    
    await message.answer("🔄 Updating about text on Telegram...")
    try:
        await call_bot_api(token, "set_my_short_description", short_description=new_about)
        await db_update_bot(message.from_user.id, bot_id, db, about_text=new_about)
        await state.clear()
        await message.answer("✅ Bot about text updated successfully!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Failed to update about text. Error: <code>{str(e)}</code>", parse_mode="HTML")

@router.message(BotManagerStates.waiting_for_commands)
async def process_cmds_input(message: Message, state: FSMContext, db=None):
    data = await state.get_data()
    bot_id = data.get("managing_bot_id")
    token = data.get("managing_bot_token")
    lines = message.text.strip().split("\n")
    
    from aiogram.types import BotCommand
    commands = []
    for line in lines:
        match = re.match(r"^([a-z0-9_]{1,32})\s*-\s*(.+)$", line.strip(), re.IGNORECASE)
        if match:
            commands.append(BotCommand(command=match.group(1).lower(), description=match.group(2)))
        else:
            await message.answer(
                f"❌ Invalid format for line: <code>{line}</code>\n"
                f"Please ensure it matches: <code>command - description</code>"
            )
            return
            
    await message.answer("🔄 Setting commands list on Telegram...")
    try:
        await call_bot_api(token, "set_my_commands", commands=commands)
        await state.clear()
        await message.answer("✅ Bot commands updated successfully!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Failed to update commands. Error: <code>{str(e)}</code>", parse_mode="HTML")

@router.message(BotManagerStates.waiting_for_photo)
async def process_photo_input(message: Message, state: FSMContext, db=None):
    if not message.photo:
        await message.answer("❌ Please send a valid photo (image file).")
        return
        
    data = await state.get_data()
    bot_id = data.get("managing_bot_id")
    token = data.get("managing_bot_token")
    
    photo = message.photo[-1]
    await message.answer("🔄 Downloading photo and updating profile picture...")
    
    try:
        file_info = await message.bot.get_file(photo.file_id)
        temp_dir = "logs"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"temp_photo_{message.from_user.id}.jpg")
        
        await message.bot.download_file(file_info.file_path, temp_file_path)
        
        from aiogram.types import FSInputFile
        photo_input = FSInputFile(temp_file_path)
        
        await call_bot_api(token, "set_my_profile_photo", photo=photo_input)
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        await state.clear()
        await message.answer("✅ Bot profile picture updated successfully!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Failed to update profile picture. Error: <code>{str(e)}</code>", parse_mode="HTML")

async def resolve_bot_for_action(message: Message, action: str, state: FSMContext, db=None):
    bots = await db_get_bots(message.from_user.id, db)
    if not bots:
        await message.answer("📭 You don't have any registered bots. Use `/newbot` to register one!")
        return
        
    if len(bots) == 1:
        bot_data = bots[0]
        bot_id = bot_data['bot_id']
        await state.update_data(managing_bot_id=bot_id, managing_bot_token=bot_data['token'])
        
        if action == "setname":
            await state.set_state(BotManagerStates.waiting_for_name)
            await message.answer(f"<b>✍️ Edit Name for @{bot_data['username']}</b>\n\nCurrent name: <b>{bot_data['name']}</b>\n\nPlease send the new display name.", parse_mode="HTML")
        elif action == "setdescription":
            await state.set_state(BotManagerStates.waiting_for_description)
            await message.answer(f"<b>📝 Edit Description for @{bot_data['username']}</b>\n\nPlease send the new description text.", parse_mode="HTML")
        elif action == "setabouttext":
            await state.set_state(BotManagerStates.waiting_for_about_text)
            await message.answer(f"<b>ℹ️ Edit About Text for @{bot_data['username']}</b>\n\nPlease send the new about text (short description).", parse_mode="HTML")
        elif action == "setcommands":
            await state.set_state(BotManagerStates.waiting_for_commands)
            await message.answer(f"<b>📜 Edit Commands for @{bot_data['username']}</b>\n\nPlease send the commands list.", parse_mode="HTML")
        elif action == "setuserpic":
            await state.set_state(BotManagerStates.waiting_for_photo)
            await message.answer(f"<b>🖼️ Edit Profile Picture for @{bot_data['username']}</b>\n\nPlease send/upload a photo.", parse_mode="HTML")
        elif action == "deletebot":
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            confirm_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🗑 Yes, Delete", callback_data=f"bot_delete_{bot_id}"),
                        InlineKeyboardButton(text="❌ Cancel", callback_data=f"bot_select_{bot_id}")
                    ]
                ]
            )
            await message.answer(f"⚠️ <b>Are you sure you want to delete @{bot_data['username']}?</b>", reply_markup=confirm_keyboard, parse_mode="HTML")
    else:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        inline_keyboard = []
        for bot in bots:
            inline_keyboard.append([
                InlineKeyboardButton(text=f"🤖 @{bot['username']}", callback_data=f"shortcut_{action}_{bot['bot_id']}")
            ])
        await message.answer(
            f"<b>🔍 Select Bot</b>\n\nWhich bot do you want to perform <code>/{action}</code> on?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("shortcut_"))
async def callback_shortcut_bot(callback: CallbackQuery, state: FSMContext, db=None):
    parts = callback.data.split("_")
    action = parts[1]
    bot_id = int(parts[2])
    
    bot_data = await db_get_bot(callback.from_user.id, bot_id, db)
    if not bot_data:
        await callback.answer("Bot not found!", show_alert=True)
        return
        
    await state.update_data(managing_bot_id=bot_id, managing_bot_token=bot_data['token'])
    
    if action == "setname":
        await state.set_state(BotManagerStates.waiting_for_name)
        await callback.message.edit_text(f"<b>✍️ Edit Name for @{bot_data['username']}</b>\n\nCurrent name: <b>{bot_data['name']}</b>\n\nPlease send the new display name.", parse_mode="HTML")
    elif action == "setdescription":
        await state.set_state(BotManagerStates.waiting_for_description)
        await callback.message.edit_text(f"<b>📝 Edit Description for @{bot_data['username']}</b>\n\nPlease send the new description text.", parse_mode="HTML")
    elif action == "setabouttext":
        await state.set_state(BotManagerStates.waiting_for_about_text)
        await callback.message.edit_text(f"<b>ℹ️ Edit About Text for @{bot_data['username']}</b>\n\nPlease send the new about text (short description).", parse_mode="HTML")
    elif action == "setcommands":
        await state.set_state(BotManagerStates.waiting_for_commands)
        await callback.message.edit_text(f"<b>📜 Edit Commands for @{bot_data['username']}</b>\n\nPlease send the commands list.", parse_mode="HTML")
    elif action == "setuserpic":
        await state.set_state(BotManagerStates.waiting_for_photo)
        await callback.message.edit_text(f"<b>🖼️ Edit Profile Picture for @{bot_data['username']}</b>\n\nPlease send/upload a photo.", parse_mode="HTML")
    elif action == "deletebot":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🗑 Yes, Delete", callback_data=f"bot_delete_{bot_id}"),
                    InlineKeyboardButton(text="❌ Cancel", callback_data=f"bot_select_{bot_id}")
                ]
            ]
        )
        await callback.message.edit_text(f"⚠️ <b>Are you sure you want to delete @{bot_data['username']}?</b>", reply_markup=confirm_keyboard, parse_mode="HTML")
        
    await callback.answer()

@router.message(Command("setname"))
async def cmd_setname(message: Message, state: FSMContext, db=None):
    await resolve_bot_for_action(message, "setname", state, db)

@router.message(Command("setdescription"))
async def cmd_setdescription(message: Message, state: FSMContext, db=None):
    await resolve_bot_for_action(message, "setdescription", state, db)

@router.message(Command("setabouttext"))
async def cmd_setabouttext(message: Message, state: FSMContext, db=None):
    await resolve_bot_for_action(message, "setabouttext", state, db)

@router.message(Command("setcommands"))
async def cmd_setcommands(message: Message, state: FSMContext, db=None):
    await resolve_bot_for_action(message, "setcommands", state, db)

@router.message(Command("setuserpic"))
async def cmd_setuserpic(message: Message, state: FSMContext, db=None):
    await resolve_bot_for_action(message, "setuserpic", state, db)

@router.message(Command("deletebot"))
async def cmd_deletebot(message: Message, state: FSMContext, db=None):
    await resolve_bot_for_action(message, "deletebot", state, db)
