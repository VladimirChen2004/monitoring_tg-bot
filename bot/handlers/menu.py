from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.checks.gpu_check import GPUCheck
from bot.db.models import User
from bot.formatters.telegram import format_gpu_report, format_status_report
from bot.tasks.registry import TaskRegistry

router = Router()


@router.callback_query(F.data == "menu:status")
async def cb_menu_status(callback: CallbackQuery, db_user: User, task_registry: TaskRegistry):
    from bot.handlers.health import _status_keyboard

    reports = await task_registry.run_all_checks()
    text = format_status_report(reports)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=_status_keyboard(task_registry))
    await callback.answer()


@router.callback_query(F.data == "menu:gpu")
async def cb_menu_gpu(callback: CallbackQuery, db_user: User):
    check = GPUCheck()
    result = await check.execute()
    text = format_gpu_report(result)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_menu_help(callback: CallbackQuery, db_user: User):
    from bot.handlers.start import HELP_TEXT

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f4ca Status", callback_data="menu:status"),
            InlineKeyboardButton(text="\u2699\ufe0f GPU", callback_data="menu:gpu"),
        ],
        [
            InlineKeyboardButton(text="\U0001f514 Notify", callback_data="menu:notify"),
        ],
    ])
    await callback.message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "menu:notify")
async def cb_menu_notify(
    callback: CallbackQuery, db_user: User, session, task_registry: TaskRegistry
):
    from bot.handlers.notifications import _build_notify_keyboard

    keyboard = await _build_notify_keyboard(session, db_user.id, task_registry)
    await callback.message.answer(
        "<b>Настройки уведомлений</b>\n\n"
        "\U0001f514 = включено, \U0001f515 = выключено\n"
        "Нажмите, чтобы переключить:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    await callback.answer()
