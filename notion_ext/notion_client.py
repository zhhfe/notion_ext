"""Notion API 查询：今日 todo + 本周任务。"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import requests

from .config import NOTION_API_VERSION, NOTION_TODAY_DB_ID, NOTION_TOKEN, NOTION_WEEK_DB_ID
from .models import TodayTask, WeekTask

logger = logging.getLogger(__name__)

_API_BASE = "https://api.notion.com/v1"
_MAX_ATTEMPTS = 5
_BASE_DELAY = 1.5
_TIMEOUT = 90


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def _extract_prop(page: dict, name: str) -> Any:
    """从 Notion page 对象中按类型提取属性值。"""
    prop = page.get("properties", {}).get(name)
    if not prop:
        return None
    ptype = prop.get("type")
    if ptype == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title") or [])
    if ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text") or [])
    if ptype == "select":
        sel = prop.get("select")
        return sel.get("name") if sel else None
    if ptype == "checkbox":
        return prop.get("checkbox", False)
    if ptype == "date":
        return prop.get("date")
    if ptype == "formula":
        formula = prop.get("formula", {})
        for key in ("string", "number", "boolean"):
            if formula.get(key) is not None:
                return formula[key]
        d = formula.get("date")
        return d.get("start") if d else None
    return prop.get(ptype)


def _is_retriable(exc: Exception) -> bool:
    return isinstance(exc, (requests.ConnectionError, requests.Timeout))


def _query_db(db_id: str, payload: dict) -> dict:
    """POST Notion database query，成功返回 JSON，失败抛异常。"""
    url = f"{_API_BASE}/databases/{db_id}/query"
    resp = requests.post(url, json=payload, headers=_headers(), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── 今日 todo ──────────────────────────────────────────────


def query_today(now: Optional[datetime] = None) -> list[TodayTask]:
    """查询 Notion 今日条目。失败返回空列表，不中断主流程。"""
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

    for attempt in range(1, _MAX_ATTEMPTS):
        try:
            data = _query_db(NOTION_TODAY_DB_ID, body)
            items = []
            for page in data.get("results", []):
                time_prop = page.get("properties", {}).get("Time", {})
                raw_date = time_prop.get("date") if time_prop.get("type") == "date" else None
                items.append(TodayTask(
                    name=_extract_prop(page, "Name") or "",
                    status=_extract_prop(page, "Status"),
                    done=bool(_extract_prop(page, "Done")),
                    time_start=raw_date.get("start") if raw_date else None,
                    time_end=raw_date.get("end") if raw_date else None,
                ))
            return items
        except requests.HTTPError as exc:
            logger.error("Notion HTTP 错误 (attempt %d/%d): %s", attempt, _MAX_ATTEMPTS, exc)
            return []
        except requests.RequestException as exc:
            logger.error("Notion 网络错误 (attempt %d/%d): %s", attempt, _MAX_ATTEMPTS, exc)
            if attempt < _MAX_ATTEMPTS and _is_retriable(exc):
                time.sleep(_BASE_DELAY * (2 ** (attempt - 1)))
                continue
            return []
    return []


# ── 本周任务 ──────────────────────────────────────────────


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

    base_filter = {
        "and": [
            {"property": "Start Date", "date": {"on_or_after": week_start}},
            {"property": "Start Date", "date": {"before": week_end}},
            {"property": "End Date", "date": {"on_or_after": week_start}},
            {"property": "End Date", "date": {"before": week_end}},
        ]
    }

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            all_items: list[WeekTask] = []
            cursor = None
            while True:
                payload: dict = {"filter": base_filter}
                if cursor:
                    payload["start_cursor"] = cursor
                data = _query_db(NOTION_WEEK_DB_ID, payload)
                for page in data.get("results", []):
                    start_obj = _extract_prop(page, "Start Date")
                    end_obj = _extract_prop(page, "End Date")
                    all_items.append(WeekTask(
                        task_name=_extract_prop(page, "Task name") or "",
                        start_date=start_obj.get("start") if start_obj else None,
                        end_date=(end_obj.get("start") or end_obj.get("end")) if end_obj else None,
                        done=bool(_extract_prop(page, "Done")),
                        id=page.get("id", ""),
                    ))
                if data.get("has_more"):
                    cursor = data.get("next_cursor")
                else:
                    break

            all_items.sort(key=lambda t: t.start_date or "")
            return all_items
        except requests.HTTPError as exc:
            logger.error("Notion 本周任务 HTTP 错误 (attempt %d/%d): %s", attempt, _MAX_ATTEMPTS, exc)
            return []
        except requests.RequestException as exc:
            logger.error("Notion 本周任务 网络错误 (attempt %d/%d): %s", attempt, _MAX_ATTEMPTS, exc)
            if attempt < _MAX_ATTEMPTS and _is_retriable(exc):
                time.sleep(_BASE_DELAY * (2 ** (attempt - 1)))
                continue
            return []
    return []
