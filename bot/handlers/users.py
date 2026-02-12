from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.models import User
from bot.db.queries import create_user, deactivate_user, get_all_users, get_user
from bot.formatters.telegram import format_user_list

router = Router()


@router.message(Command("adduser"))
async def cmd_adduser(message: Message, db_user: User, session):
    if not db_user.is_admin:
        await message.answer("Only admins can add users.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /adduser &lt;telegram_id&gt;", parse_mode="HTML")
        return

    try:
        new_user_id = int(args[1].strip())
    except ValueError:
        await message.answer("Telegram ID must be a number.")
        return

    existing = await get_user(session, new_user_id)
    if existing:
        await message.answer(f"User <code>{new_user_id}</code> already exists.", parse_mode="HTML")
        return

    await create_user(
        session,
        user_id=new_user_id,
        full_name=f"User {new_user_id}",
        added_by=db_user.id,
    )
    await message.answer(
        f"User <code>{new_user_id}</code> added. They can now use the bot.",
        parse_mode="HTML",
    )


@router.message(Command("removeuser"))
async def cmd_removeuser(message: Message, db_user: User, session):
    if not db_user.is_admin:
        await message.answer("Only admins can remove users.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /removeuser &lt;telegram_id&gt;", parse_mode="HTML")
        return

    try:
        target_id = int(args[1].strip())
    except ValueError:
        await message.answer("Telegram ID must be a number.")
        return

    if target_id == db_user.id:
        await message.answer("You cannot remove yourself.")
        return

    removed = await deactivate_user(session, target_id)
    if removed:
        await message.answer(f"User <code>{target_id}</code> removed.", parse_mode="HTML")
    else:
        await message.answer("User not found.")


@router.message(Command("users"))
async def cmd_users(message: Message, db_user: User, session):
    if not db_user.is_admin:
        await message.answer("Only admins can view users.")
        return

    users = await get_all_users(session)
    await message.answer(format_user_list(users), parse_mode="HTML")
