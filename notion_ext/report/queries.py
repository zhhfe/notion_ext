"""日报用 Notion 查询：今日 todo + 本周任务。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from ..config import NOTION_TODAY_DB_ID, NOTION_WEEK_DB_ID
from ..models import TodayTask, WeekTask
from ..notion_api import extract_prop, query_database

_TIME_START_CANDIDATES = ("start", "start_time", "from", "begin")
_TIME_END_CANDIDATES = ("end", "end_time", "to", "finish")


def _extract_time_range(page: dict, property_name: str = "Time") -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], list[str]]:
    """从 Notion date 属性提取开始/结束时间，并返回实际使用的键名。"""
    prop = page.get("properties", {}).get(property_name, {})
    raw_date = prop.get("date") if prop.get("type") == "date" else None
    if not isinstance(raw_date, dict):
        return None, None, None, None, []

    available_keys = list(raw_date.keys())
    start_key = next((key for key in _TIME_START_CANDIDATES if key in raw_date), None)
    end_key = next((key for key in _TIME_END_CANDIDATES if key in raw_date), None)
    start_value = raw_date.get(start_key) if start_key else None
    end_value = raw_date.get(end_key) if end_key else None
    return start_value, end_value, start_key, end_key, available_keys


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value if "T" in value else f"{value}T00:00:00"
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def _parse_iso_timestamp(value: Optional[str]) -> Optional[float]:
    dt = _parse_iso_datetime(value)
    return dt.timestamp() if dt else None


_REPORT_QUERY_TIMEOUT = 12
_REPORT_QUERY_MAX_ATTEMPTS = 2


def query_today(now: Optional[datetime] = None) -> list[TodayTask]:
    """查询 Notion 今日条目。失败返回空列表。"""
    now = now or datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    body = {
        "filter": {
            "and": [
                {"property": "Time", "date": {"on_or_after": today_str}},
                {"property": "Time", "date": {"before": tomorrow_str}},
            ]
        }
    }

    pages = query_database(
        NOTION_TODAY_DB_ID,
        body,
        timeout=_REPORT_QUERY_TIMEOUT,
        max_attempts=_REPORT_QUERY_MAX_ATTEMPTS,
    )
    items = []
    for page in pages:
        time_start, time_end, start_key, end_key, available_keys = _extract_time_range(page, "Time")
        items.append(TodayTask(
            id=page.get("id", ""),
            name=extract_prop(page, "Name") or "",
            status=extract_prop(page, "Status"),
            done=bool(extract_prop(page, "Done")),
            time_start=time_start,
            time_end=time_end,
        ))
    return items


def _get_week_range(now: Optional[datetime] = None) -> tuple[str, str]:
    """返回 (本周一, 下周一) 的 YYYY-MM-DD 字符串，左闭右开。"""
    now = now or datetime.now()
    d = now.replace(hour=0, minute=0, second=0, microsecond=0)
    monday = d - timedelta(days=d.weekday())
    next_monday = monday + timedelta(days=7)
    return monday.strftime("%Y-%m-%d"), next_monday.strftime("%Y-%m-%d")


def query_this_week_tasks(now: Optional[datetime] = None) -> list[WeekTask]:
    """查询本周任务（含分页），失败返回空列表。"""
    week_start, week_end = _get_week_range(now)
    week_start_ts = datetime.fromisoformat(f"{week_start}T00:00:00").timestamp()
    week_end_ts = datetime.fromisoformat(f"{week_end}T00:00:00").timestamp()

    body = {
        "filter": {
            "and": [
                {"property": "Time", "date": {"on_or_after": week_start}},
                {"property": "Time", "date": {"before": week_end}},
            ]
        }
    }

    pages = query_database(
        NOTION_WEEK_DB_ID,
        body,
        timeout=_REPORT_QUERY_TIMEOUT,
        max_attempts=_REPORT_QUERY_MAX_ATTEMPTS,
    )
    items = []
    for page in pages:
        time_start, time_end, start_key, end_key, available_keys = _extract_time_range(page, "Time")

        start_ts = _parse_iso_timestamp(time_start)
        end_ts = _parse_iso_timestamp(time_end) if time_end else start_ts
        if start_ts is not None and end_ts is not None:
            # 使用 Time 的开始/结束时间判断是否落在本周（有交集即可）。
            if end_ts < week_start_ts or start_ts >= week_end_ts:
                continue

        items.append(WeekTask(
            task_name=extract_prop(page, "Task name") or "",
            start_date=(time_start or "")[:10] or None,
            end_date=(time_end or time_start or "")[:10] or None,
            time_start=time_start,
            time_end=time_end,
            done=bool(extract_prop(page, "Done")),
            id=page.get("id", ""),
        ))
    items.sort(key=lambda task: _parse_iso_timestamp(task.time_start) or float("inf"))
    return items
