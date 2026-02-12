import time

import aiohttp

from bot.checks.base import BaseHealthCheck, CheckStatus, HealthCheckResult


class HTTPHealthCheck(BaseHealthCheck):

    def __init__(
        self,
        name: str,
        url: str,
        timeout: float = 10.0,
        expected_status: int = 200,
    ):
        self._name = name
        self.url = url
        self.timeout = timeout
        self.expected_status = expected_status

    @property
    def name(self) -> str:
        return self._name

    async def execute(self) -> HealthCheckResult:
        start = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    elapsed = (time.monotonic() - start) * 1000
                    body = await resp.text()

                    if resp.status == self.expected_status:
                        return HealthCheckResult(
                            name=self.name,
                            status=CheckStatus.OK,
                            message=f"{resp.status} OK ({elapsed:.0f}ms)",
                            response_time_ms=elapsed,
                            details={"body_preview": body[:200]},
                        )
                    return HealthCheckResult(
                        name=self.name,
                        status=CheckStatus.CRITICAL,
                        message=f"HTTP {resp.status} ({elapsed:.0f}ms)",
                        response_time_ms=elapsed,
                    )
        except aiohttp.ClientError as e:
            elapsed = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.CRITICAL,
                message=f"Connection error: {e}",
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
