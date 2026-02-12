from bot.checks.base import CheckStatus, HealthCheckResult
from bot.tasks.base import TaskHealthReport

STATUS_ICONS = {
    CheckStatus.OK: "\u2705",
    CheckStatus.WARNING: "\u26a0\ufe0f",
    CheckStatus.CRITICAL: "\u274c",
    CheckStatus.UNKNOWN: "\u2753",
}


def format_check_line(check: HealthCheckResult) -> str:
    icon = STATUS_ICONS.get(check.status, "?")
    time_str = f" ({check.response_time_ms:.0f}ms)" if check.response_time_ms else ""
    return f"{icon} <b>{check.name}</b>{time_str}\n    {check.message}"


def format_status_report(reports: dict[str, TaskHealthReport]) -> str:
    if not reports:
        return "No tasks registered."

    lines = ["<b>Server Status</b>", "\u2500" * 20]

    for report in reports.values():
        icon = "\u2705" if report.is_healthy else "\u274c"
        lines.append(f"\n{icon} <b>{report.task_display_name}</b>")
        for check in report.checks:
            lines.append(format_check_line(check))

    return "\n".join(lines)


def format_task_detail(report: TaskHealthReport) -> str:
    icon = "\u2705" if report.is_healthy else "\u274c"
    lines = [
        f"{icon} <b>{report.task_display_name}</b>",
        f"<i>{report.summary}</i>",
        "",
    ]
    for check in report.checks:
        lines.append(format_check_line(check))

    lines.append(f"\n<i>Checked at: {report.timestamp[:19]}</i>")
    return "\n".join(lines)


def format_gpu_report(check: HealthCheckResult) -> str:
    if check.status == CheckStatus.UNKNOWN:
        return f"\u2753 <b>GPU</b>\n{check.message}"

    gpus = check.details.get("gpus", [])
    if not gpus:
        return f"<b>GPU Status</b>\n{check.message}"

    lines = ["<b>GPU Status</b>", "\u2550" * 20]
    for g in gpus:
        util = g.get("utilization")
        temp = g.get("temperature")
        mem_used = g.get("memory_used")
        mem_total = g.get("memory_total")

        if util is not None:
            bar_filled = util // 10
            bar = "\u2588" * bar_filled + "\u2591" * (10 - bar_filled)
            util_line = f"  Utilization: {util}%  [{bar}]"
        else:
            util_line = "  Utilization: N/A"

        if mem_used is not None and mem_total is not None:
            mem_pct = mem_used / mem_total * 100
            mem_line = f"  Memory:      {mem_used} / {mem_total} MB ({mem_pct:.0f}%)"
        else:
            mem_line = "  Memory:      unified (shared with CPU)"

        temp_line = f"  Temperature: {temp}\u00b0C" if temp is not None else "  Temperature: N/A"

        lines.extend([
            f"\n<b>GPU{g['index']}: {g['name']}</b>",
            util_line,
            mem_line,
            temp_line,
        ])

    return "\n".join(lines)


def format_alert(task_name: str, report: TaskHealthReport) -> str:
    failed = [c for c in report.checks if c.status in (CheckStatus.CRITICAL, CheckStatus.WARNING)]
    ok = [c for c in report.checks if c.status == CheckStatus.OK]

    lines = [f"\u26a0\ufe0f <b>{report.task_display_name}</b>", ""]
    for check in failed:
        icon = STATUS_ICONS[check.status]
        lines.append(f"{icon} <b>{check.name}</b> \u2014 {check.message}")

    if ok:
        ok_names = ", ".join(c.name for c in ok)
        lines.append(f"\nRemaining checks OK: {ok_names}")

    return "\n".join(lines)


def format_recovery(task_name: str, report: TaskHealthReport) -> str:
    return f"\u2705 <b>{report.task_display_name}</b>\n\nAll systems restored."


def format_user_list(users) -> str:
    if not users:
        return "No users registered."

    lines = ["<b>Users</b>", ""]
    for u in users:
        admin = " [admin]" if u.is_admin else ""
        active = "" if u.is_active else " (inactive)"
        name = f"@{u.username}" if u.username else u.full_name
        lines.append(f"\u2022 <code>{u.id}</code> {name}{admin}{active}")

    return "\n".join(lines)
