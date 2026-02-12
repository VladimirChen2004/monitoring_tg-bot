from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.checks.gpu_check import GPUCheck
from bot.db.models import User
from bot.formatters.telegram import format_gpu_report

router = Router()


@router.message(Command("gpu"))
async def cmd_gpu(message: Message, db_user: User):
    check = GPUCheck()
    result = await check.execute()
    text = format_gpu_report(result)
    await message.answer(text, parse_mode="HTML")
