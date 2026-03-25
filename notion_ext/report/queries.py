"""日报用 Notion 查询：今日 todo + 本周任务。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from ..config import NOTION_TODAY_DB_ID, NOTION_WEEK_DB_ID
from ..models import TodayTask, WeekTask
from ..notion_api import extract_prop, query_database


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

    pages = query_database(NOTION_TODAY_DB_ID, body)
    items = []
    for page in pages:
        time_prop = page.get("properties", {}).get("Time", {})
        raw_date = time_prop.get("date") if time_prop.get("type") == "date" else None
        items.append(TodayTask(
            name=extract_prop(page, "Name") or "",
            status=extract_prop(page, "Status"),
            done=bool(extract_prop(page, "Done")),
            time_start=raw_date.get("start") if raw_date else None,
            time_end=raw_date.get("end") if raw_date else None,
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

    body = {
        "filter": {
            "and": [
                {"property": "Start Date", "date": {"on_or_after": week_start}},
                {"property": "Start Date", "date": {"before": week_end}},
                {"property": "End Date", "date": {"on_or_after": week_start}},
                {"property": "End Date", "date": {"before": week_end}},
            ]
        }
    }

    pages = query_database(NOTION_WEEK_DB_ID, body)
    items = []
    for page in pages:
        start_obj = extract_prop(page, "Start Date")
        end_obj = extract_prop(page, "End Date")
        items.append(WeekTask(
            task_name=extract_prop(page, "Task name") or "",
            start_date=start_obj.get("start") if start_obj else None,
            end_date=(end_obj.get("start") or end_obj.get("end")) if end_obj else None,
            done=bool(extract_prop(page, "Done")),
            id=page.get("id", ""),
        ))
    items.sort(key=lambda t: t.start_date or "")
    return items
