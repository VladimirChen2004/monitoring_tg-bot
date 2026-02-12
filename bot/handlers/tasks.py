from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

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

    lines.append("\nUse /check &lt;task&gt; for detailed status")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("taskinfo"))
async def cmd_taskinfo(message: Message, db_user: User, task_registry: TaskRegistry):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        names = ", ".join(f"<code>{n}</code>" for n in task_registry.names())
        await message.answer(
            f"Usage: /taskinfo &lt;task&gt;\nAvailable: {names}",
            parse_mode="HTML",
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
