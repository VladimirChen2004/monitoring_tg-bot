import asyncio

from bot.checks.base import BaseHealthCheck, CheckStatus, HealthCheckResult


def _parse_int(val: str) -> int | None:
    """Parse int from nvidia-smi output, handling [N/A] for unified memory."""
    val = val.strip().strip("[]")
    if val in ("N/A", ""):
        return None
    return int(val)


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
                    "utilization": _parse_int(parts[2]),
                    "memory_used": _parse_int(parts[3]),
                    "memory_total": _parse_int(parts[4]),
                    "temperature": _parse_int(parts[5]),
                })
            except (ValueError, IndexError):
                continue

        if not gpus:
            return HealthCheckResult(
                name=self.name,
                status=CheckStatus.UNKNOWN,
                message="No GPU data parsed",
            )

        utils = [g["utilization"] for g in gpus if g["utilization"] is not None]
        temps = [g["temperature"] for g in gpus if g["temperature"] is not None]
        max_util = max(utils) if utils else 0
        max_temp = max(temps) if temps else 0

        # For inference servers, high utilization is normal.
        # Only temperature is a real concern.
        if max_temp > self.warning_temp + 10:
            status = CheckStatus.CRITICAL
        elif max_temp > self.warning_temp:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK

        lines = []
        for g in gpus:
            util_str = f"{g['utilization']}%" if g["utilization"] is not None else "N/A"
            temp_str = f"{g['temperature']}°C" if g["temperature"] is not None else "N/A"
            if g["memory_used"] is not None and g["memory_total"] is not None:
                mem_pct = g["memory_used"] / g["memory_total"] * 100
                mem_str = f"{g['memory_used']}/{g['memory_total']}MB ({mem_pct:.0f}%)"
            elif g["memory_used"] is not None:
                mem_str = f"{g['memory_used']}MB"
            else:
                mem_str = "unified memory"
            lines.append(f"GPU{g['index']}: {util_str} | {mem_str} | {temp_str}")

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
