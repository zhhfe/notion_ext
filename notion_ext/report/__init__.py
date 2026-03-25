"""日报功能：查询 Notion + macOS 提醒事项 → 发送钉钉。"""

from __future__ import annotations

import logging
import sys

from .dingtalk import send_markdown
from .formatter import format_daily_digest, get_running_todo_lines
from .notify import notify_mac
from .queries import query_today, query_this_week_tasks
from .reminders import read_reminders

logger = logging.getLogger(__name__)


def run_report() -> None:
    logger.info("日报任务开始")

    today_items = query_today()
    week_items = query_this_week_tasks()
    logger.info("Notion 已拉取: 今日 %d 条, 本周 %d 条", len(today_items), len(week_items))

    running_lines = get_running_todo_lines(today_items)
    if sys.platform == "darwin" and running_lines:
        notify_mac("processing todo", "\n".join(running_lines))

    reminder = read_reminders()
    text = format_daily_digest(today_items, week_items, reminder)

    try:
        send_markdown("Notion 日报", text)
    except Exception as exc:
        logger.error("发送钉钉失败: %s", exc)

    logger.info("日报任务结束")
