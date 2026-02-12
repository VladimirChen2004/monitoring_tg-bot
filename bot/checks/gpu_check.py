import asyncio

from bot.checks.base import BaseHealthCheck, CheckStatus, HealthCheckResult


class GPUCheck(BaseHealthCheck):

    def __init__(self, name: str = "GPU Status", warning_util: int = 90, warning_temp: int = 80):
        self._name = name
        self.warning_util = warning_util
        self.warning_temp = warning_temp

    @property
    def name(self) -> str:
        return self._name

    async def execute(self) -> HealthCheckResult:
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        except FileNotFoundError:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNKNOWN,
                message="nvidia-smi not found",
            )
        except TimeoutError:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.CRITICAL,
                message="nvidia-smi timeout",
            )

        if proc.returncode != 0:
            # Fallback: try plain nvidia-smi (DGX Spark unified memory may differ)
            return await self._fallback_check(stderr.decode().strip())

        gpus = []
        for line in stdout.decode().strip().split("\n"):
            parts = [x.strip() for x in line.split(",")]
            if len(parts) < 6:
                continue
            try:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "utilization": int(parts[2]),
                    "memory_used": int(parts[3]),
                    "memory_total": int(parts[4]),
                    "temperature": int(parts[5]),
                })
            except (ValueError, IndexError):
                continue

        if not gpus:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNKNOWN,
                message="No GPU data parsed",
            )

        max_util = max(g["utilization"] for g in gpus)
        max_temp = max(g["temperature"] for g in gpus)

        if max_temp > self.warning_temp + 10 or max_util > 95:
            status = CheckStatus.CRITICAL
        elif max_temp > self.warning_temp or max_util > self.warning_util:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK

        lines = []
        for g in gpus:
            mem_pct = (g["memory_used"] / g["memory_total"] * 100) if g["memory_total"] else 0
            lines.append(
                f"GPU{g['index']}: {g['utilization']}% | "
                f"{g['memory_used']}/{g['memory_total']}MB ({mem_pct:.0f}%) | "
                f"{g['temperature']}°C"
            )

        return HealthCheckResult(
            name=self.name,
            status=status,
            message="\n".join(lines),
            details={"gpus": gpus},
        )

    async def _fallback_check(self, error_msg: str) -> HealthCheckResult:
        """Fallback: run plain nvidia-smi and parse output."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            if proc.returncode == 0:
                output = stdout.decode().strip()
                # Extract basic info from nvidia-smi text output
                return HealthCheckResult(
                    name=self.name,
                    status=CheckStatus.OK,
                    message=output[:500],
                    details={"fallback": True},
                )
        except Exception:
            pass

        return HealthCheckResult(
            name=self.name,
            status=CheckStatus.CRITICAL,
            message=f"nvidia-smi error: {error_msg[:200]}",
        )
