from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User
from bot.tasks.registry import TaskRegistry

router = Router()


@router.message(Command("tasks"))
async def cmd_tasks(message: Message, db_user: User, task_registry: TaskRegistry):
    tasks = task_registry.all()
    if not tasks:
        await message.answer("No tasks registered.")
        return

    lines = ["<b>Registered Tasks</b>", ""]
    for t in tasks:
        lines.append(f"\u2022 <code>{t.name}</code> — {t.display_name}")
        lines.append(f"  <i>{t.description}</i>")

    rows = []
    for t in tasks:
        rows.append([InlineKeyboardButton(
            text=f"\U0001f50d {t.display_name}",
            callback_data=f"check:task:{t.name}",
        )])

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.message(Command("taskinfo"))
async def cmd_taskinfo(message: Message, db_user: User, task_registry: TaskRegistry):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        rows = []
        for task in task_registry.all():
            rows.append([InlineKeyboardButton(
                text=task.display_name,
                callback_data=f"taskinfo:{task.name}",
            )])
        await message.answer(
            "<b>Выберите задачу:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        return

    task_name = args[1].strip()
    task = task_registry.get(task_name)
    if not task:
        await message.answer(f"Task <code>{task_name}</code> not found.", parse_mode="HTML")
        return

    lines = [
        f"<b>{task.display_name}</b>",
        f"Name: <code>{task.name}</code>",
        f"Description: {task.description}",
    ]
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.callback_query(F.data.startswith("taskinfo:"))
async def cb_taskinfo(callback: CallbackQuery, task_registry: TaskRegistry):
    task_name = callback.data.split(":", 1)[1]
    task = task_registry.get(task_name)
    if not task:
        await callback.answer("Task not found", show_alert=True)
        return

    lines = [
        f"<b>{task.display_name}</b>",
        f"Name: <code>{task.name}</code>",
        f"Description: {task.description}",
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f50d Check", callback_data=f"check:task:{task.name}")],
    ])
    try:
        await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        await callback.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()
