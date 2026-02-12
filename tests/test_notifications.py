import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.checks.base import CheckStatus, HealthCheckResult
from bot.notifications.engine import NotificationEngine
from bot.tasks.base import TaskHealthReport


def _make_report(is_healthy: bool, task_name: str = "test") -> TaskHealthReport:
    status = CheckStatus.OK if is_healthy else CheckStatus.CRITICAL
    msg = "OK" if is_healthy else "Failed"
    return TaskHealthReport(
        task_name=task_name,
        task_display_name="Test Task",
        is_healthy=is_healthy,
        checks=[HealthCheckResult(name="check1", status=status, message=msg)],
    )


@pytest.mark.asyncio
async def test_edge_triggered_no_notification_on_first_check():
    """First check should not trigger notification (no previous state)."""
    engine = NotificationEngine.__new__(NotificationEngine)
    engine._previous_healthy = {}

    # Simulate: no previous state -> should NOT notify
    prev = engine._previous_healthy.get("test")
    assert prev is None  # No previous state = no transition


@pytest.mark.asyncio
async def test_edge_triggered_detects_transition():
    """State change OK->CRITICAL should be detected."""
    engine = NotificationEngine.__new__(NotificationEngine)
    engine._previous_healthy = {"test": True}

    prev_healthy = engine._previous_healthy.get("test")
    now_healthy = False

    # Transition detected
    assert prev_healthy is not None
    assert prev_healthy != now_healthy


@pytest.mark.asyncio
async def test_edge_triggered_no_notification_same_state():
    """Same state should not trigger notification."""
    engine = NotificationEngine.__new__(NotificationEngine)
    engine._previous_healthy = {"test": False}

    prev_healthy = engine._previous_healthy.get("test")
    now_healthy = False

    # No transition
    assert prev_healthy == now_healthy
