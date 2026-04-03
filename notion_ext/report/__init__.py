"""日报功能：查询 Notion + macOS 提醒事项 → 发送钉钉。"""

from __future__ import annotations

import logging
import sys

from .dingtalk import send_markdown
from .notify import notify_mac
from .queries import query_today, query_this_week_tasks
from .reminders import read_reminders
from .settings import get_dingtalk_enabled
from .snapshot import build_daily_digest_snapshot

logger = logging.getLogger(__name__)


def collect_daily_digest_snapshot():
    """查询当前日报数据并构建统一快照。"""
    today_items = query_today()
    week_items = query_this_week_tasks()
    reminder_items = read_reminders()
    logger.info(
        "Notion 已拉取: 今日 %d 条, 本周 %d 条, 提醒事项 %d 条",
        len(today_items),
        len(week_items),
        len(reminder_items),
    )
    return build_daily_digest_snapshot(today_items, week_items, reminder_items)


def run_report() -> None:
    logger.info("日报任务开始")

    snapshot = collect_daily_digest_snapshot()
    running_lines = snapshot.running_items
    if sys.platform == "darwin" and running_lines:
        notify_mac("processing todo", "\n".join(running_lines))

    if get_dingtalk_enabled():
        try:
            send_markdown(snapshot.title, snapshot.text)
        except Exception as exc:
            logger.error("发送钉钉失败: %s", exc)
    else:
        logger.info("已关闭钉钉发送，跳过发送")

    logger.info("日报任务结束")
