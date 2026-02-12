import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.checks.base import CheckStatus
from bot.config import Settings
from bot.db.queries import get_task_subscribers, is_in_cooldown, log_notification, save_health_log
from bot.formatters.telegram import format_alert, format_recovery
from bot.tasks.base import TaskHealthReport
from bot.tasks.registry import TaskRegistry

logger = logging.getLogger(__name__)


class NotificationEngine:

    def __init__(
        self,
        bot: Bot,
        registry: TaskRegistry,
        session_factory: async_sessionmaker[AsyncSession],
        config: Settings,
    ):
        self.bot = bot
        self.registry = registry
        self.session_factory = session_factory
        self.config = config
        self._task: asyncio.Task | None = None
        # Track previous state for edge-triggered notifications
        self._previous_healthy: dict[str, bool] = {}

    async def start(self):
        self._task = asyncio.create_task(self._loop())
        logger.info("Notification engine started (interval=%ds)", self.config.health_check_interval)

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Notification engine stopped")

    async def _loop(self):
        # Wait a bit before first check to let bot initialize
        await asyncio.sleep(5)

        while True:
            try:
                await self._run_checks_and_notify()
            except Exception:
                logger.exception("Monitoring loop error")
            await asyncio.sleep(self.config.health_check_interval)

    async def _run_checks_and_notify(self):
        reports = await self.registry.run_all_checks()

        async with self.session_factory() as session:
            for task_name, report in reports.items():
                # Save health logs
                for check in report.checks:
                    await save_health_log(
                        session,
                        task_name=task_name,
                        check_name=check.name,
                        status=check.status.value,
                        message=check.message,
                        response_time_ms=check.response_time_ms,
                    )

                # Detect state transition
                prev_healthy = self._previous_healthy.get(task_name)
                now_healthy = report.is_healthy

                if prev_healthy is not None and prev_healthy != now_healthy:
                    await self._send_notifications(session, task_name, report, now_healthy)

                self._previous_healthy[task_name] = now_healthy

    async def _send_notifications(
        self,
        session: AsyncSession,
        task_name: str,
        report: TaskHealthReport,
        is_healthy: bool,
    ):
        subscribers = await get_task_subscribers(session, task_name)
        if not subscribers:
            return

        if is_healthy:
            text = format_recovery(task_name, report)
            status = "recovery"
        else:
            text = format_alert(task_name, report)
            status = "alert"

        for user_id in subscribers:
            if await is_in_cooldown(session, user_id, task_name, self.config.notification_cooldown):
                continue

            try:
                await self.bot.send_message(user_id, text, parse_mode="HTML")
                await log_notification(
                    session,
                    user_id=user_id,
                    task_name=task_name,
                    status=status,
                    message=text[:500],
                )
                logger.info("Sent %s to user %d for task %s", status, user_id, task_name)
            except Exception:
                logger.exception("Failed to send notification to user %d", user_id)
