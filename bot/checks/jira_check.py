import time
from base64 import b64encode

import aiohttp

from bot.checks.base import BaseHealthCheck, CheckStatus, HealthCheckResult


class JiraAPICheck(BaseHealthCheck):

    def __init__(
        self,
        name: str,
        jira_url: str,
        email: str,
        api_token: str,
        project: str = "DOCS",
    ):
        self._name = name
        self.jira_url = jira_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.project = project

    @property
    def name(self) -> str:
        return self._name

    def _auth_header(self) -> dict[str, str]:
        creds = b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        return {"Authorization": f"Basic {creds}", "Accept": "application/json"}

    async def execute(self) -> HealthCheckResult:
        if not self.jira_url or not self.api_token:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNKNOWN,
                message="Jira not configured",
            )

        start = time.monotonic()
        try:
            async with aiohttp.ClientSession(headers=self._auth_header()) as session:
                # Check connectivity
                async with session.get(
                    f"{self.jira_url}/rest/api/3/myself",
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    elapsed = (time.monotonic() - start) * 1000
                    if resp.status != 200:
                        return HealthCheckResult(
                            name=self.name,
                            status=CheckStatus.CRITICAL,
                            message=f"Auth failed: HTTP {resp.status}",
                            response_time_ms=elapsed,
                        )

                # Count active tasks
                jql = f"project={self.project} AND status != Done"
                async with session.get(
                    f"{self.jira_url}/rest/api/3/search",
                    params={"jql": jql, "maxResults": 0},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        total = data.get("total", "?")
                        return HealthCheckResult(
                            name=self.name,
                            status=CheckStatus.OK,
                            message=f"OK ({elapsed:.0f}ms) | {total} active tasks",
                            response_time_ms=elapsed,
                            details={"active_tasks": total},
                        )
                    return HealthCheckResult(
                        name=self.name,
                        status=CheckStatus.OK,
                        message=f"OK ({elapsed:.0f}ms) | task count unavailable",
                        response_time_ms=elapsed,
                    )

        except (aiohttp.ClientError, TimeoutError) as e:
            elapsed = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.CRITICAL,
                message=f"Connection error: {e}",
                response_time_ms=elapsed,
            )
