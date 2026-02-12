from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from bot.checks.base import CheckStatus, HealthCheckResult


@dataclass
class TaskHealthReport:
    task_name: str
    task_display_name: str
    is_healthy: bool
    checks: list[HealthCheckResult]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    summary: str = ""

    def __post_init__(self):
        if not self.summary:
            failed = [c for c in self.checks if c.status not in (CheckStatus.OK, CheckStatus.UNKNOWN)]
            if failed:
                self.summary = f"{len(failed)} check(s) failed: " + ", ".join(c.name for c in failed)
            else:
                self.summary = "All systems operational"


class BaseTask(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique slug: 'documentation'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description for /taskinfo."""

    @abstractmethod
    async def run_health_checks(self) -> TaskHealthReport:
        """Run all health checks and return aggregated report."""
