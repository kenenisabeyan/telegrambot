import os
import glob
import html
import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.keyboards import get_admin_keyboard
from config import settings

router = Router()

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in settings.ADMIN_IDS

class BroadcastStates(StatesGroup):
    waiting_for_message = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message, db=None):
    """Admin panel (restricted)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Access denied. Admin only.")
        return
    
    if db:
        await db.log_command(message.from_user.id, "admin")
        
    await message.answer(
        "<b>🔐 Admin Control Center</b>\n\n"
        "Welcome to the system administration dashboard.\n"
        "Select an administrative module below:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, db=None):
    """Show bot statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    
    if db:
        stats = await db.get_admin_stats()
    else:
        stats = {
            "users": 1,
            "active_today": 1,
            "commands_used": 15,
            "reminders_set": 2,
            "ai_queries": 4,
            "weather_checks": 3
        }
    
    stats_text = (
        "<b>📊 System Performance & Statistics</b>\n\n"
        f"• <b>Total Registered Users:</b> {stats['users']}\n"
        f"• <b>Daily Active Users (DAU):</b> {stats['active_today']}\n"
        f"• <b>Total Commands Executed:</b> {stats['commands_used']}\n"
        f"• <b>Active Reminders:</b> {stats['reminders_set']}\n"
        f"• <b>AI Queries Handled:</b> {stats['ai_queries']}\n"
        f"• <b>Weather Forecast Checks:</b> {stats['weather_checks']}\n\n"
        f"<i>Metrics updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_telemetry")
async def callback_admin_telemetry(callback: CallbackQuery):
    """Display real-time performance and telemetry metrics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return

    from utils.telemetry import telemetry
    m = telemetry.get_metrics_snapshot()
    
    telemetry_text = (
        "<b>📈 Real-Time Engine Telemetry</b>\n\n"
        f"• <b>Uptime:</b> <code>{m['uptime']}</code>\n"
        f"• <b>Total Updates Handled:</b> <code>{m['total_updates']}</code>\n"
        f"• <b>Error Boundary Events:</b> <code>{m['total_errors']}</code>\n"
        f"• <b>Average Latency:</b> <code>{m['avg_latency_ms']} ms</code>\n"
        f"• <b>P95 Latency:</b> <code>{m['p95_latency_ms']} ms</code>\n"
        f"• <b>Process RSS Memory:</b> <code>{m['memory_rss_mb']} MB</code>\n"
        f"• <b>Python Version:</b> <code>{m['python_version']}</code>\n"
        f"• <b>Platform OS:</b> <code>{m['platform']}</code>\n\n"
        f"<i>Snapshot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh Metrics", callback_data="admin_telemetry")],
            [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel_back")]
        ]
    )
    await callback.message.edit_text(telemetry_text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast process"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text(
        "<b>📢 Mass Notification Broadcast</b>\n\n"
        "Send the message content you wish to broadcast to all registered users.\n\n"
        "• Supports HTML formatting (<b>bold</b>, <i>italic</i>, <code>code</code>, links).\n"
        "• Send /cancel to abort at any time.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(BroadcastStates.waiting_for_message)
async def send_broadcast_preview(message: Message, state: FSMContext):
    """Show broadcast preview before execution"""
    if not is_admin(message.from_user.id):
        return
    
    broadcast_text = message.text
    await state.update_data(broadcast_message=broadcast_text)
    
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Yes, Send to All", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Abort", callback_data="broadcast_cancel")
            ]
        ]
    )
    
    await message.answer(
        f"<b>📢 Broadcast Preview:</b>\n\n{broadcast_text}\n\n"
        f"⚠️ Are you sure you want to dispatch this message to all active users?",
        reply_markup=confirm_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, db=None):
    """Execute live broadcast delivery across all registered users"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get('broadcast_message')
    if not broadcast_text:
        await callback.answer("No broadcast text found.", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("⏳ <b>Dispatching broadcast...</b>\nPlease wait.", parse_mode="HTML")
    
    user_ids = []
    if db:
        try:
            user_ids = await db.get_all_user_ids()
        except Exception:
            user_ids = [callback.from_user.id]
    else:
        user_ids = [callback.from_user.id]

    # Include admins in test delivery if not present
    for aid in settings.ADMIN_IDS:
        if aid not in user_ids:
            user_ids.append(aid)

    success_count = 0
    fail_count = 0

    for uid in user_ids:
        try:
            await callback.bot.send_message(uid, broadcast_text, parse_mode="HTML")
            success_count += 1
            await asyncio.sleep(0.05)  # Throttle to avoid Telegram broadcast limits
        except Exception:
            fail_count += 1

    summary = (
        f"<b>📢 Broadcast Completed!</b>\n\n"
        f"• <b>Total Targeted:</b> {len(user_ids)}\n"
        f"• <b>Successfully Delivered:</b> {success_count}\n"
        f"• <b>Failed / Blocked:</b> {fail_count}\n\n"
        f"<i>Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    
    await callback.message.edit_text(summary, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await state.clear()
    await callback.answer("Broadcast finished!", show_alert=True)

@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast"""
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.", reply_markup=get_admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery, db=None):
    """Inspect registered users"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    
    if db:
        users = await db.get_recent_users(limit=10)
    else:
        users = [
            {
                "user_id": callback.from_user.id,
                "username": callback.from_user.username or "none",
                "first_name": callback.from_user.first_name or "Admin",
                "last_active": datetime.now()
            }
        ]

    users_text = "<b>👥 Registered Users (Latest 10)</b>\n\n"
    if not users:
        users_text += "<i>No users found in database.</i>\n"
    else:
        for idx, u in enumerate(users, start=1):
            name = u.get("first_name", "User")
            username = f"@{u['username']}" if u.get("username") else "No username"
            uid = u.get("user_id")
            active = u.get("last_active")
            active_str = active.strftime("%Y-%m-%d %H:%M") if active else "Recently"
            users_text += f"{idx}. <b>{name}</b> ({username})\n   ID: <code>{uid}</code> | Active: {active_str}\n\n"

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_users")],
            [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel_back")]
        ]
    )
    await callback.message.edit_text(users_text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    """Display real-time system logs"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return

    # Find today's log or latest log file
    log_files = sorted(glob.glob("logs/bot_*.log"), reverse=True)
    if not log_files or not os.path.exists(log_files[0]):
        log_snippet = "No log files found in logs/ directory."
    else:
        try:
            with open(log_files[0], "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                log_snippet = "".join(lines[-20:]) if lines else "Log file is currently empty."
        except Exception as e:
            log_snippet = f"Error reading log file: {e}"

    safe_logs = html.escape(log_snippet)
    
    logs_text = (
        f"<b>📝 System Runtime Logs</b>\n"
        f"<i>Showing latest 20 entries:</i>\n\n"
        f"<pre><code>{safe_logs}</code></pre>"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh Logs", callback_data="admin_logs")],
            [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel_back")]
        ]
    )
    await callback.message.edit_text(logs_text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery, db=None):
    """Display active system configuration"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return

    db_status = "🟢 Connected (PostgreSQL)" if (db and db.pool) else "🟡 In-Memory Mock"
    redis_status = "🟢 Connected" if settings.REDIS_URL else "⚪ Memory Fallback"
    openai_status = "🟢 Active" if settings.OPENAI_API_KEY else "⚪ Mock Intelligence"
    weather_status = "🟢 Active" if settings.OPENWEATHER_API_KEY else "⚪ Mock Weather"
    mode = f"🌐 Webhook ({settings.WEBHOOK_URL})" if settings.WEBHOOK_URL else "🔄 Long Polling"

    settings_text = (
        "<b>⚙️ Active System Settings</b>\n\n"
        f"• <b>Runtime Mode:</b> {mode}\n"
        f"• <b>Log Level:</b> <code>{settings.LOG_LEVEL}</code>\n"
        f"• <b>Database:</b> {db_status}\n"
        f"• <b>FSM Storage:</b> {redis_status}\n"
        f"• <b>OpenAI API:</b> {openai_status}\n"
        f"• <b>OpenWeather API:</b> {weather_status}\n"
        f"• <b>Default Cooldown:</b> <code>{settings.RATE_LIMIT_DEFAULT}s</code>\n"
        f"• <b>Heavy Cooldown:</b> <code>{settings.RATE_LIMIT_HEAVY}s</code>\n"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel_back")]
        ]
    )
    await callback.message.edit_text(settings_text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_export")
async def callback_admin_export(callback: CallbackQuery, db=None):
    """Export system state and metrics snapshot as a downloadable JSON file"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
        
    await callback.answer("Preparing export package...", show_alert=False)
    
    import json
    from aiogram.types import BufferedInputFile
    from utils.telemetry import telemetry
    
    stats = await db.get_admin_stats() if db else {"users": 1, "commands": 0}
    recent_users = await db.get_recent_users(limit=25) if db else []
    for u in recent_users:
        for k, v in u.items():
            if isinstance(v, datetime):
                u[k] = v.isoformat()
                
    export_payload = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "exported_by": callback.from_user.id,
            "system_version": "Enterprise 2.0"
        },
        "statistics": stats,
        "telemetry": telemetry.get_metrics_snapshot(),
        "recent_users": recent_users
    }
    
    json_bytes = json.dumps(export_payload, indent=2, ensure_ascii=False).encode("utf-8")
    filename = f"telemetry_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    file_doc = BufferedInputFile(json_bytes, filename=filename)
    await callback.message.answer_document(
        file_doc,
        caption=(
            f"<b>💾 Audit Data Export Generated</b>\n"
            f"• <b>Records Captured:</b> {len(recent_users)} users\n"
            f"• <b>Timestamp:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_panel_back")
async def admin_panel_back(callback: CallbackQuery):
    """Return to admin panel home"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
        
    await callback.message.edit_text(
        "<b>🔐 Admin Control Center</b>\n\n"
        "Welcome to the system administration dashboard.\n"
        "Select an administrative module below:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
