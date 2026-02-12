import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.db.queries import create_user, get_user

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Injects async DB session into handler data."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session
            return await handler(event, data)


class AuthMiddleware(BaseMiddleware):
    """Checks if user is authorized. Auto-registers initial admin on first use."""

    def __init__(self, settings: Settings):
        self.initial_admin_id = settings.initial_admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        db_user = await get_user(session, user.id)

        if db_user is None:
            if user.id == self.initial_admin_id:
                db_user = await create_user(
                    session,
                    user_id=user.id,
                    full_name=user.full_name or "Admin",
                    username=user.username,
                    is_admin=True,
                )
                logger.info("Auto-registered initial admin: %s (%d)", user.full_name, user.id)
            else:
                if isinstance(event, Update) and event.message:
                    await event.message.answer(
                        "Access denied. Ask an admin to add you.\n"
                        f"Your Telegram ID: <code>{user.id}</code>",
                        parse_mode="HTML",
                    )
                return

        data["db_user"] = db_user
        return await handler(event, data)
