import time
from pathlib import Path

from bot.checks.base import BaseHealthCheck, CheckStatus, HealthCheckResult


class FileCheck(BaseHealthCheck):

    def __init__(
        self,
        name: str,
        path: str,
        max_age_seconds: int | None = None,
    ):
        self._name = name
        self.path = Path(path)
        self.max_age_seconds = max_age_seconds

    @property
    def name(self) -> str:
        return self._name

    async def execute(self) -> HealthCheckResult:
        if not self.path.exists():
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.OK,
                message="Not running (no lock file)",
                details={"exists": False},
            )

        stat = self.path.stat()
        age_seconds = time.time() - stat.st_mtime

        if self.max_age_seconds and age_seconds > self.max_age_seconds:
            hours = age_seconds / 3600
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                message=f"Stale lock ({hours:.1f}h old)",
                details={"exists": True, "age_seconds": age_seconds, "stale": True},
            )

        minutes = age_seconds / 60
        return HealthCheckResult(
            name=self.name,
            status=CheckStatus.OK,
            message=f"Running (lock {minutes:.0f}m old)",
            details={"exists": True, "age_seconds": age_seconds, "stale": False},
        )
