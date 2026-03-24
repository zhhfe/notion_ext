"""CLI 入口：python -m notion_ext"""

from __future__ import annotations

import logging
import sys

from .config import CRON_LOG_PATH
from .dingtalk import send_markdown
from .formatter import format_daily_digest, get_running_todo_lines
from .notion_client import query_today, query_this_week_tasks
from .notify import notify_mac
from .reminders import read_reminders

logger = logging.getLogger("notion_ext")


def _setup_logging() -> None:
    root = logging.getLogger("notion_ext")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.FileHandler(CRON_LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


def main() -> None:
    _setup_logging()
    logger.info("notion_ext 开始")

    today_items = query_today()
    week_items = query_this_week_tasks()
    logger.info("Notion 已拉取: 今日 %d 条, 本周 %d 条", len(today_items), len(week_items))

    running_lines = get_running_todo_lines(today_items)
    if sys.platform == "darwin" and running_lines:
        notify_mac("processing todo", "\n".join(running_lines))

    reminders = read_reminders()
    text = format_daily_digest(today_items, week_items, reminders)

    try:
        send_markdown("Notion 日报", text)
    except Exception as exc:
        logger.error("发送钉钉失败: %s", exc)

    logger.info("notion_ext 结束")


if __name__ == "__main__":
    main()
