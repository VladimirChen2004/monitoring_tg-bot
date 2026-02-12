import asyncio
import time

from bot.checks.base import BaseHealthCheck, CheckStatus, HealthCheckResult


class SubprocessCheck(BaseHealthCheck):

    def __init__(
        self,
        name: str,
        command: list[str],
        timeout: float = 30.0,
        expected_returncode: int = 0,
    ):
        self._name = name
        self.command = command
        self.timeout = timeout
        self.expected_returncode = expected_returncode

    @property
    def name(self) -> str:
        return self._name

    async def execute(self) -> HealthCheckResult:
        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout
            )
            elapsed = (time.monotonic() - start) * 1000

            if proc.returncode == self.expected_returncode:
                output = stdout.decode().strip()
                return HealthCheckResult(
                    name=self.name,
                    status=CheckStatus.OK,
                    message=output[:200] or "OK",
                    response_time_ms=elapsed,
                )
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.CRITICAL,
                message=f"Exit code {proc.returncode}: {stderr.decode().strip()[:200]}",
                response_time_ms=elapsed,
            )
        except TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.CRITICAL,
                message=f"Timeout after {self.timeout}s",
                response_time_ms=elapsed,
            )
        except FileNotFoundError:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.CRITICAL,
                message=f"Command not found: {self.command[0]}",
            )
