import logging

from bot.checks.base import CheckStatus, HealthCheckResult
from bot.checks.file_check import FileCheck
from bot.checks.gpu_check import GPUCheck
from bot.checks.http_check import HTTPHealthCheck
from bot.checks.jira_check import JiraAPICheck
from bot.checks.subprocess_check import SubprocessCheck
from bot.config import Settings
from bot.tasks.base import BaseTask, TaskHealthReport

logger = logging.getLogger(__name__)


class DocumentationPipelineTask(BaseTask):

    def __init__(self, config: Settings):
        self._checks = []

        # 1. vLLM API
        self._checks.append(
            HTTPHealthCheck(
                name="vLLM API",
                url=f"{config.vllm_api_url}/models",
                timeout=10.0,
            )
        )

        # 2. Jira API
        if config.jira_url and config.jira_api_token:
            self._checks.append(
                JiraAPICheck(
                    name="Jira API",
                    jira_url=config.jira_url,
                    email=config.jira_email,
                    api_token=config.jira_api_token,
                    project=config.jira_project,
                )
            )

        # 3. Claude CLI
        self._checks.append(
            SubprocessCheck(
                name="Claude CLI",
                command=["claude", "--version"],
                timeout=15.0,
            )
        )

        # 4. Cycle Runner lock
        if config.cycle_runner_lock_path:
            self._checks.append(
                FileCheck(
                    name="Cycle Runner",
                    path=config.cycle_runner_lock_path,
                    max_age_seconds=4 * 3600,
                )
            )

        # 5. GPU
        self._checks.append(GPUCheck(name="GPU"))

    @property
    def name(self) -> str:
        return "documentation"

    @property
    def display_name(self) -> str:
        return "Documentation Pipeline"

    @property
    def description(self) -> str:
        return "vLLM, Jira, Claude CLI, Cycle Runner, GPU"

    async def run_health_checks(self) -> TaskHealthReport:
        results: list[HealthCheckResult] = []
        for check in self._checks:
            try:
                result = await check.execute()
            except Exception as e:
                logger.exception("Check %s failed unexpectedly", check.name)
                result = HealthCheckResult(
                    name=check.name,
                    status=CheckStatus.UNKNOWN,
                    message=f"Error: {str(e)[:100]}",
                )
            results.append(result)

        is_healthy = all(
            r.status in (CheckStatus.OK, CheckStatus.UNKNOWN) for r in results
        )

        return TaskHealthReport(
            task_name=self.name,
            task_display_name=self.display_name,
            is_healthy=is_healthy,
            checks=results,
        )
