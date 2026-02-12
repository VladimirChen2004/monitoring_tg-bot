from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User
from bot.db.queries import get_user_prefs, toggle_notification
from bot.tasks.registry import TaskRegistry

router = Router()


async def _build_notify_keyboard(
    session, user_id: int, task_registry: TaskRegistry
) -> InlineKeyboardMarkup:
    prefs = {p.task_name: p.is_enabled for p in await get_user_prefs(session, user_id)}

    buttons = []
    for task in task_registry.all():
        enabled = prefs.get(task.name, False)
        icon = "\u2705" if enabled else "\u274c"
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {task.display_name}",
                callback_data=f"notify:toggle:{task.name}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("notify"))
async def cmd_notify(
    message: Message, db_user: User, session, task_registry: TaskRegistry
):
    keyboard = await _build_notify_keyboard(session, db_user.id, task_registry)
    await message.answer(
        "<b>Notification Settings</b>\n\nTap to toggle notifications per task:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("notify:toggle:"))
async def cb_notify_toggle(
    callback: CallbackQuery, db_user: User, session, task_registry: TaskRegistry
):
    task_name = callback.data.split(":", 2)[2]
    new_state = await toggle_notification(session, callback.from_user.id, task_name)
    state_text = "ON" if new_state else "OFF"
    await callback.answer(f"{task_name}: {state_text}")

    keyboard = await _build_notify_keyboard(session, callback.from_user.id, task_registry)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
