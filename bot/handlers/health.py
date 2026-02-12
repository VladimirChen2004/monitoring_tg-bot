from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User
from bot.formatters.telegram import format_status_report, format_task_detail
from bot.tasks.registry import TaskRegistry

router = Router()


@router.message(Command("status"))
async def cmd_status(message: Message, db_user: User, task_registry: TaskRegistry):
    reports = await task_registry.run_all_checks()
    text = format_status_report(reports)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f504 Refresh", callback_data="status:refresh")]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "status:refresh")
async def cb_status_refresh(callback: CallbackQuery, task_registry: TaskRegistry):
    reports = await task_registry.run_all_checks()
    text = format_status_report(reports)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f504 Refresh", callback_data="status:refresh")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("Updated")


@router.message(Command("check"))
async def cmd_check(message: Message, db_user: User, task_registry: TaskRegistry):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        names = ", ".join(f"<code>{n}</code>" for n in task_registry.names())
        await message.answer(
            f"Usage: /check &lt;task&gt;\nAvailable: {names}",
            parse_mode="HTML",
        )
        return

    task_name = args[1].strip()
    task = task_registry.get(task_name)
    if not task:
        await message.answer(f"Task <code>{task_name}</code> not found.", parse_mode="HTML")
        return

    report = await task.run_health_checks()
    text = format_task_detail(report)
    await message.answer(text, parse_mode="HTML")
