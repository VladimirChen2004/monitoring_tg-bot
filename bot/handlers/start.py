from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User

router = Router()

HELP_TEXT = """\
<b>Server Monitor Bot</b>

<b>Мониторинг:</b>
/status — Статус всех задач
/check — Детальная проверка задачи
/gpu — Состояние GPU (nvidia-smi)

<b>Задачи и настройки:</b>
/tasks — Список задач
/taskinfo — Информация о задаче
/notify — Управление уведомлениями

<b>Админ:</b>
/adduser &lt;telegram_id&gt; — Добавить пользователя
/removeuser &lt;telegram_id&gt; — Удалить пользователя
/users — Список пользователей"""


def _quick_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f4ca Status", callback_data="menu:status"),
            InlineKeyboardButton(text="\u2699\ufe0f GPU", callback_data="menu:gpu"),
        ],
        [
            InlineKeyboardButton(text="\U0001f514 Notify", callback_data="menu:notify"),
            InlineKeyboardButton(text="\U0001f4cb Commands", callback_data="menu:help"),
        ],
    ])


@router.message(Command("start"))
async def cmd_start(message: Message, db_user: User):
    await message.answer(
        f"Hello, <b>{db_user.full_name}</b>!\n\n"
        "<b>Server Monitor Bot</b> — мониторинг инфраструктуры.",
        parse_mode="HTML",
        reply_markup=_quick_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User):
    await message.answer(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="\U0001f4ca Status", callback_data="menu:status"),
                InlineKeyboardButton(text="\u2699\ufe0f GPU", callback_data="menu:gpu"),
            ],
            [
                InlineKeyboardButton(text="\U0001f514 Notify", callback_data="menu:notify"),
            ],
        ]),
    )
