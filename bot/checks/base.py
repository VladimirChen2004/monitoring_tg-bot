from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    name: str
    status: CheckStatus
    message: str
    response_time_ms: float = 0.0
    details: dict = field(default_factory=dict)


class BaseHealthCheck(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def execute(self) -> HealthCheckResult: ...
