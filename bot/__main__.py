import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import get_settings
from bot.db.engine import create_engine, create_session_factory, init_db
from bot.handlers import gpu, health, menu, notifications, start, tasks, users
from bot.middlewares.auth import AuthMiddleware, DatabaseMiddleware
from bot.notifications.engine import NotificationEngine
from bot.tasks.documentation import DocumentationPipelineTask
from bot.tasks.registry import TaskRegistry


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    settings = get_settings()

    # Ensure data directory exists for SQLite
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Database
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    await init_db(engine)
    logger.info("Database initialized")

    # Task registry
    registry = TaskRegistry()
    registry.register(DocumentationPipelineTask(settings))
    logger.info("Registered %d task(s): %s", len(registry.all()), registry.names())

    # Bot & Dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Middlewares
    dp.update.outer_middleware(DatabaseMiddleware(session_factory))
    dp.update.outer_middleware(AuthMiddleware(settings))

    # Inject task_registry into handler data
    dp["task_registry"] = registry

    # Routers
    dp.include_router(start.router)
    dp.include_router(users.router)
    dp.include_router(tasks.router)
    dp.include_router(health.router)
    dp.include_router(gpu.router)
    dp.include_router(notifications.router)
    dp.include_router(menu.router)

    # Notification engine
    notification_engine = NotificationEngine(bot, registry, session_factory, settings)

    async def on_startup():
        await notification_engine.start()
        await bot.set_my_commands([
            BotCommand(command="status", description="Статус сервера"),
            BotCommand(command="check", description="Проверить задачу"),
            BotCommand(command="gpu", description="Состояние GPU"),
            BotCommand(command="help", description="Все команды"),
        ])
        me = await bot.get_me()
        logger.info("Bot started: @%s", me.username)

    async def on_shutdown():
        await notification_engine.stop()
        await engine.dispose()
        logger.info("Bot stopped")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
