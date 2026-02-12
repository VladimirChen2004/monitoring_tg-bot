from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.models import User

router = Router()

HELP_TEXT = """<b>Server Monitor Bot</b>

<b>Commands:</b>
/status — All tasks status overview
/check &lt;task&gt; — Detailed check for a task
/gpu — GPU usage (nvidia-smi)
/tasks — List registered tasks
/taskinfo &lt;task&gt; — Task details + history
/notify — Manage notification subscriptions

<b>Admin:</b>
/adduser &lt;telegram_id&gt; — Add user
/removeuser &lt;telegram_id&gt; — Remove user
/users — List all users
"""


@router.message(Command("start"))
async def cmd_start(message: Message, db_user: User):
    await message.answer(
        f"Hello, {db_user.full_name}!\n\n{HELP_TEXT}",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User):
    await message.answer(HELP_TEXT, parse_mode="HTML")
