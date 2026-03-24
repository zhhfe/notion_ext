"""钉钉日报消息格式化。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import Reminder, TodayTask, WeekTask

_WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
_SECTION_SEP = "\n--------------------\n"


def _parse_iso(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def _to_hm(iso: Optional[str]) -> str:
    if not iso:
        return ""
    dt = _parse_iso(iso)
    return dt.strftime("%H:%M") if dt else ""


def _ymd_to_weekday(ymd: Optional[str]) -> str:
    if not ymd:
        return ""
    try:
        d = datetime.strptime(ymd, "%Y-%m-%d")
        return _WEEKDAY_CN[d.weekday()]
    except (ValueError, TypeError):
        return ""


def _weekday_range(start_ymd: Optional[str], end_ymd: Optional[str]) -> str:
    a = _ymd_to_weekday(start_ymd)
    b = _ymd_to_weekday(end_ymd)
    if not a and not b:
        return ""
    if not b or a == b:
        return f" ({a})"
    return f" ({a}-{b})"


def _progress_pct(done: int, total: int) -> int:
    return round(done / total * 100) if total > 0 else 0


def _start_ts(iso: Optional[str]) -> float:
    """ISO 时间 → 时间戳，解析失败返回 inf（排到最后）。"""
    if not iso:
        return float("inf")
    dt = _parse_iso(iso)
    return dt.timestamp() if dt else float("inf")


def _sort_incomplete_first(items, *, is_done, sort_key):
    """未完成在前、已完成在后；同组内按 sort_key 升序。"""
    return sorted(items, key=lambda it: (is_done(it), sort_key(it)))


# ── 三段格式化 ────────────────────────────────────────────


def format_today(items: list[TodayTask]) -> str:
    if not items:
        return "今日 todo，进度【0%】：\n暂无"

    done_count = sum(1 for it in items if it.done)
    pct = _progress_pct(done_count, len(items))

    sorted_items = _sort_incomplete_first(
        items,
        is_done=lambda it: it.done,
        sort_key=lambda it: _start_ts(it.time_start),
    )

    lines = []
    for it in sorted_items:
        mark = "✅" if it.done else "⬜"
        start_hm = _to_hm(it.time_start)
        end_hm = _to_hm(it.time_end)
        if start_hm and end_hm:
            time_str = f" ({start_hm} - {end_hm})"
        elif start_hm:
            time_str = f" ({start_hm})"
        else:
            time_str = ""
        lines.append(f"{mark} {it.name}.{time_str}")

    return f"今日 todo，进度【{pct}%】：\n" + "\n".join(lines)


def format_week_tasks(items: list[WeekTask]) -> str:
    if not items:
        return "本周 todo，进度【0%】：\n暂无"

    done_count = sum(1 for it in items if it.done)
    pct = _progress_pct(done_count, len(items))

    sorted_items = _sort_incomplete_first(
        items,
        is_done=lambda it: it.done,
        sort_key=lambda it: it.start_date or "\xff",
    )

    lines = []
    for it in sorted_items:
        mark = "✅" if it.done else "⬜"
        range_str = _weekday_range(it.start_date, it.end_date) if it.start_date else ""
        lines.append(f"{mark} {it.task_name}{range_str}")

    return f"本周 todo，进度【{pct}%】：\n" + "\n".join(lines)


def format_reminders(reminders: list[Reminder]) -> str:
    pending = [r for r in reminders if not r.completed]
    n = len(pending)
    if n == 0:
        return "待办 todo（未完成 0 条）：\n暂无"
    lines = [f"⬜ {r.name}." for r in pending]
    return f"待办 todo（未完成 {n} 条）：\n" + "\n".join(lines)


def format_daily_digest(
    today_items: list[TodayTask],
    week_items: list[WeekTask],
    reminders: list[Reminder],
) -> str:
    """三段合并：今日 + 本周 + 提醒事项。"""
    return _SECTION_SEP.join([
        format_today(today_items),
        format_week_tasks(week_items),
        format_reminders(reminders),
    ])


# ── 当前进行中任务 ────────────────────────────────────────


def get_running_todo_lines(
    items: list[TodayTask],
    now: Optional[datetime] = None,
) -> list[str]:
    """找出当前正在进行的任务，返回描述行列表。"""
    now = now or datetime.now()
    now_ts = now.timestamp()
    lines = []
    for it in items:
        if not it.time_start or not it.time_end:
            continue
        start = _parse_iso(it.time_start)
        end = _parse_iso(it.time_end)
        if not start or not end:
            continue
        if not (start.timestamp() <= now_ts < end.timestamp()):
            continue
        left_min = max(0, round((end.timestamp() - now_ts) / 60))
        start_hm = _to_hm(it.time_start)
        end_hm = _to_hm(it.time_end)
        time_range = f" ({start_hm}-{end_hm})" if start_hm and end_hm else ""
        lines.append(f"{it.name}{time_range}, left {left_min} min")
    return lines
