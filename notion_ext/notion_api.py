"""Notion API 共享基础：请求头、属性提取、带重试的数据库查询与页面更新。"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from .config import NOTION_API_VERSION, NOTION_TOKEN

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


def extract_prop(page: dict, name: str) -> Any:
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


def query_database(db_id: str, body: dict) -> list[dict]:
    """带分页和重试的 Notion 数据库查询，返回原始 page 对象列表。"""
    url = f"{_API_BASE}/databases/{db_id}/query"

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            all_pages: list[dict] = []
            cursor = None
            while True:
                payload = {**body}
                if cursor:
                    payload["start_cursor"] = cursor
                resp = requests.post(url, json=payload, headers=_headers(), timeout=_TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
                all_pages.extend(data.get("results", []))
                if data.get("has_more"):
                    cursor = data.get("next_cursor")
                else:
                    break
            return all_pages
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


def update_page(page_id: str, properties: dict) -> bool:
    """更新 Notion 页面属性，成功返回 True。"""
    url = f"{_API_BASE}/pages/{page_id}"
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = requests.patch(
                url,
                json={"properties": properties},
                headers=_headers(),
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return True
        except requests.HTTPError as exc:
            logger.error("Notion 更新页面 HTTP 错误 (attempt %d/%d): %s", attempt, _MAX_ATTEMPTS, exc)
            return False
        except requests.RequestException as exc:
            logger.error("Notion 更新页面 网络错误 (attempt %d/%d): %s", attempt, _MAX_ATTEMPTS, exc)
            if attempt < _MAX_ATTEMPTS and _is_retriable(exc):
                time.sleep(_BASE_DELAY * (2 ** (attempt - 1)))
                continue
            return False
    return False
