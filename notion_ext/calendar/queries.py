"""日历同步用 Notion 查询：最近一个月的任务。"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..config import NOTION_TODAY_DB_ID
from ..models import CalendarEvent
from ..notion_api import extract_prop, query_database


def query_recent_tasks(days: int = 30) -> list[CalendarEvent]:
    """查询最近 N 天内有时间的 Notion 任务，返回日历事件列表。"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    body = {
        "filter": {
            "property": "Time",
            "date": {"on_or_after": cutoff},
        }
    }

    pages = query_database(NOTION_TODAY_DB_ID, body)
    events = []
    for page in pages:
        name = extract_prop(page, "Name") or ""
        if not name:
            continue
        time_obj = extract_prop(page, "Time")
        start = time_obj.get("start") if time_obj else None
        end = time_obj.get("end") if time_obj else None
        if not start or not end:
            continue
        events.append(CalendarEvent(
            uid=page.get("id", ""),
            summary=name,
            start=start,
            end=end,
        ))
    return events
