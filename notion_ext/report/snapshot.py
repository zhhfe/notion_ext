"""日报快照：统一服务于钉钉发送和本地客户端展示。"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from calendar import monthrange

from ..models import (
    DailyDigestSnapshot,
    PeriodProgressSnapshot,
    PeriodsSnapshot,
    ProgressSnapshot,
    Reminder,
    ReminderSectionSnapshot,
    ReminderSnapshotItem,
    TodaySectionSnapshot,
    TodaySnapshotItem,
    TodayTask,
    WeekSectionSnapshot,
    WeekSnapshotItem,
    WeekTask,
)
from .formatter import (
    format_daily_digest,
    get_running_todo_lines,
)

_WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _parse_iso(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def _to_hm(iso: str | None) -> str:
    dt = _parse_iso(iso)
    return dt.strftime("%H:%M") if dt else ""


def _ymd_to_weekday(ymd: str | None) -> str:
    if not ymd:
        return ""
    try:
        day = datetime.strptime(ymd, "%Y-%m-%d")
    except (ValueError, TypeError):
        return ""
    return _WEEKDAY_CN[day.weekday()]


def _weekday_range(start_ymd: str | None, end_ymd: str | None) -> str:
    start = _ymd_to_weekday(start_ymd)
    end = _ymd_to_weekday(end_ymd)
    if not start and not end:
        return ""
    if not end or start == end:
        return start
    return f"{start} - {end}"


def _progress_pct(done: int, total: int) -> int:
    return round(done / total * 100) if total > 0 else 0


def _progress_bar(done: int, total: int, width: int = 10) -> str:
    pct = _progress_pct(done, total)
    filled = round(width * pct / 100)
    return f"({'▮' * filled}{'▯' * (width - filled)} {pct}%)"


def _start_ts(iso: str | None) -> float:
    dt = _parse_iso(iso)
    return dt.timestamp() if dt else float("inf")


def _format_time_range(start_iso: str | None, end_iso: str | None) -> str:
    start = _to_hm(start_iso)
    end = _to_hm(end_iso)
    if start and end:
        return f"{start} - {end}"
    return start or ""


def _build_progress(done_count: int, total_count: int) -> ProgressSnapshot:
    return ProgressSnapshot(
        done_count=done_count,
        total_count=total_count,
        percent=_progress_pct(done_count, total_count),
        bar=_progress_bar(done_count, total_count),
    )


def _build_calendar_periods(now: datetime) -> PeriodsSnapshot:
    month_total = monthrange(now.year, now.month)[1]
    month_elapsed = now.day

    quarter_start_month = ((now.month - 1) // 3) * 3 + 1
    quarter_start = date(now.year, quarter_start_month, 1)
    quarter_elapsed = (now.date() - quarter_start).days + 1
    quarter_total = 90

    year_elapsed = now.timetuple().tm_yday
    year_total = 365

    month_percent = _progress_pct(month_elapsed, month_total)
    quarter_percent = _progress_pct(min(quarter_elapsed, quarter_total), quarter_total)
    year_percent = _progress_pct(min(year_elapsed, year_total), year_total)

    return PeriodsSnapshot(
        month=PeriodProgressSnapshot(percent=month_percent),
        quarter=PeriodProgressSnapshot(percent=quarter_percent),
        year=PeriodProgressSnapshot(percent=year_percent),
    )


def build_daily_digest_snapshot(
    today_items: list[TodayTask],
    week_items: list[WeekTask],
    reminders: list[Reminder],
    now: datetime | None = None,
) -> DailyDigestSnapshot:
    now = now or datetime.now()

    today_sorted = sorted(today_items, key=lambda item: _start_ts(item.time_start))
    today_done = sum(1 for item in today_items if item.done)
    today_snapshot = TodaySectionSnapshot(
        progress=_build_progress(today_done, len(today_items)),
        items=[
            TodaySnapshotItem(
                id=item.id,
                name=item.name,
                status=item.status,
                done=item.done,
                time_start=item.time_start,
                time_end=item.time_end,
                display_time=_format_time_range(item.time_start, item.time_end),
            )
            for item in today_sorted
        ],
    )

    week_sorted = sorted(week_items, key=lambda item: _start_ts(item.time_start))
    week_done = sum(1 for item in week_items if item.done)
    week_snapshot = WeekSectionSnapshot(
        progress=_build_progress(week_done, len(week_items)),
        items=[
            WeekSnapshotItem(
                task_name=item.task_name,
                done=item.done,
                id=item.id,
                start_date=item.start_date,
                end_date=item.end_date,
                weekday_range=_weekday_range(item.start_date, item.end_date),
            )
            for item in week_sorted
        ],
    )

    pending_reminders = [item for item in reminders if not item.completed]
    reminder_snapshot = ReminderSectionSnapshot(
        pending_count=len(pending_reminders),
        items=[
            ReminderSnapshotItem(id=item.id, name=item.name, completed=item.completed)
            for item in pending_reminders
        ],
    )

    return DailyDigestSnapshot(
        generated_at=now.isoformat(),
        title="Notion 日报",
        text=format_daily_digest(today_items, week_items, reminders),
        running_items=get_running_todo_lines(today_items, now=now),
        today=today_snapshot,
        week=week_snapshot,
        reminders=reminder_snapshot,
        periods=_build_calendar_periods(now),
    )


def snapshot_to_dict(snapshot: DailyDigestSnapshot) -> dict:
    """dataclass -> dict，供 HTTP JSON 接口返回。"""
    return asdict(snapshot)
