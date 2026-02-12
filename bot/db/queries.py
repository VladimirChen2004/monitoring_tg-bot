from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import HealthLog, NotificationLog, NotificationPreference, User


# ── Users ────────────────────────────────────────────────────────────────────

async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    user_id: int,
    full_name: str,
    username: str | None = None,
    is_admin: bool = False,
    added_by: int | None = None,
) -> User:
    user = User(
        id=user_id,
        full_name=full_name,
        username=username,
        is_admin=is_admin,
        added_by=added_by,
    )
    session.add(user)
    await session.commit()
    return user


async def deactivate_user(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        update(User).where(User.id == user_id).values(is_active=False)
    )
    await session.commit()
    return result.rowcount > 0


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).where(User.is_active == True).order_by(User.created_at))
    return list(result.scalars().all())


# ── Notification preferences ─────────────────────────────────────────────────

async def get_notification_pref(
    session: AsyncSession, user_id: int, task_name: str
) -> NotificationPreference | None:
    result = await session.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.task_name == task_name,
        )
    )
    return result.scalar_one_or_none()


async def get_user_prefs(session: AsyncSession, user_id: int) -> list[NotificationPreference]:
    result = await session.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    return list(result.scalars().all())


async def toggle_notification(
    session: AsyncSession, user_id: int, task_name: str
) -> bool:
    """Toggle notification for user+task. Returns new is_enabled state."""
    pref = await get_notification_pref(session, user_id, task_name)
    if pref is None:
        pref = NotificationPreference(
            user_id=user_id, task_name=task_name, is_enabled=True
        )
        session.add(pref)
        await session.commit()
        return True
    pref.is_enabled = not pref.is_enabled
    pref.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return pref.is_enabled


async def get_task_subscribers(session: AsyncSession, task_name: str) -> list[int]:
    """Get user IDs subscribed to notifications for a task."""
    result = await session.execute(
        select(NotificationPreference.user_id).where(
            NotificationPreference.task_name == task_name,
            NotificationPreference.is_enabled == True,
        )
    )
    return list(result.scalars().all())


# ── Health logs ──────────────────────────────────────────────────────────────

async def save_health_log(
    session: AsyncSession,
    task_name: str,
    check_name: str,
    status: str,
    message: str | None = None,
    response_time_ms: float | None = None,
):
    log = HealthLog(
        task_name=task_name,
        check_name=check_name,
        status=status,
        message=message,
        response_time_ms=response_time_ms,
    )
    session.add(log)
    await session.commit()


async def get_recent_health_logs(
    session: AsyncSession, task_name: str, limit: int = 20
) -> list[HealthLog]:
    result = await session.execute(
        select(HealthLog)
        .where(HealthLog.task_name == task_name)
        .order_by(HealthLog.checked_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Notification log ─────────────────────────────────────────────────────────

async def log_notification(
    session: AsyncSession,
    user_id: int,
    task_name: str,
    status: str,
    message: str | None = None,
    check_name: str | None = None,
):
    entry = NotificationLog(
        user_id=user_id,
        task_name=task_name,
        check_name=check_name,
        status=status,
        message=message,
    )
    session.add(entry)
    await session.commit()


async def is_in_cooldown(
    session: AsyncSession, user_id: int, task_name: str, cooldown_seconds: int
) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=cooldown_seconds)
    result = await session.execute(
        select(NotificationLog)
        .where(
            NotificationLog.user_id == user_id,
            NotificationLog.task_name == task_name,
            NotificationLog.sent_at >= cutoff,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None
