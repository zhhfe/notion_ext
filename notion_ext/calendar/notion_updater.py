"""更新 Notion 默认页面的 Time 属性为当前时间（心跳/模板刷新）。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from ..config import NOTION_DEFAULT_PAGE_ID
from ..notion_api import update_page

logger = logging.getLogger(__name__)


def update_default_page_time() -> None:
    """将配置中的默认页面 Time 设为当前时间。未配置 page_id 时静默跳过。"""
    if not NOTION_DEFAULT_PAGE_ID:
        return
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    properties = {
        "Time": {
            "date": {
                "start": now,
                "end": now,
            }
        }
    }
    if update_page(NOTION_DEFAULT_PAGE_ID, properties):
        logger.info("已更新默认页面时间")
    else:
        logger.error("更新默认页面时间失败")
