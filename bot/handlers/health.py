from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User
from bot.formatters.telegram import format_status_report, format_task_detail
from bot.tasks.registry import TaskRegistry

router = Router()


def _status_keyboard(task_registry: TaskRegistry) -> InlineKeyboardMarkup:
    rows = []
    for task in task_registry.all():
        rows.append([InlineKeyboardButton(
            text=f"\U0001f50d {task.display_name}",
            callback_data=f"check:task:{task.name}",
        )])
    rows.append([InlineKeyboardButton(text="\U0001f504 Refresh", callback_data="status:refresh")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("status"))
async def cmd_status(message: Message, db_user: User, task_registry: TaskRegistry):
    reports = await task_registry.run_all_checks()
    text = format_status_report(reports)
    await message.answer(text, parse_mode="HTML", reply_markup=_status_keyboard(task_registry))


@router.callback_query(F.data == "status:refresh")
async def cb_status_refresh(callback: CallbackQuery, task_registry: TaskRegistry):
    reports = await task_registry.run_all_checks()
    text = format_status_report(reports)
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=_status_keyboard(task_registry),
    )
    await callback.answer("Updated")


@router.message(Command("check"))
async def cmd_check(message: Message, db_user: User, task_registry: TaskRegistry):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        rows = []
        for task in task_registry.all():
            rows.append([InlineKeyboardButton(
                text=f"\U0001f50d {task.display_name}",
                callback_data=f"check:task:{task.name}",
            )])
        await message.answer(
            "<b>Выберите задачу для проверки:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        return

    task_name = args[1].strip()
    task = task_registry.get(task_name)
    if not task:
        await message.answer(f"Task <code>{task_name}</code> not found.", parse_mode="HTML")
        return

    report = await task.run_health_checks()
    text = format_task_detail(report)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f504 Refresh", callback_data=f"check:task:{task_name}"),
            InlineKeyboardButton(text="\U0001f4ca Status", callback_data="menu:status"),
        ],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("check:task:"))
async def cb_check_task(callback: CallbackQuery, task_registry: TaskRegistry):
    task_name = callback.data.split(":", 2)[2]
    task = task_registry.get(task_name)
    if not task:
        await callback.answer("Task not found", show_alert=True)
        return

    report = await task.run_health_checks()
    text = format_task_detail(report)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f504 Refresh", callback_data=f"check:task:{task_name}"),
            InlineKeyboardButton(text="\U0001f4ca Status", callback_data="menu:status"),
        ],
    ])
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()
