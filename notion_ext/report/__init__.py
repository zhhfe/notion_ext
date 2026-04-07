"""日报功能：查询 Notion + macOS 提醒事项 → 发送钉钉。"""

from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from .dingtalk import send_markdown
from .notify import notify_mac
from ..notion_api import update_page
from .queries import query_today, query_this_week_tasks
from .reminders import complete_reminder, read_reminders
from .settings import get_dingtalk_enabled, get_reminders_enabled
from .snapshot import build_daily_digest_snapshot

logger = logging.getLogger(__name__)


def collect_daily_digest_snapshot():
    """查询当前日报数据并构建统一快照。"""
    reminders_enabled = get_reminders_enabled()
    with ThreadPoolExecutor(max_workers=3) as executor:
        today_future = executor.submit(query_today)
        week_future = executor.submit(query_this_week_tasks)
        reminder_future = executor.submit(read_reminders) if reminders_enabled else None
        today_items = today_future.result()
        week_items = week_future.result()
        reminder_items = reminder_future.result() if reminder_future is not None else []
    logger.info(
        "Notion 已拉取: 今日 %d 条, 本周 %d 条, 提醒事项 %d 条 (enabled=%s)",
        len(today_items),
        len(week_items),
        len(reminder_items),
        reminders_enabled,
    )
    return build_daily_digest_snapshot(
        today_items=today_items,
        week_items=week_items,
        reminders=reminder_items,
    )


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


def complete_item(kind: str, item_id: str, value: bool = True) -> tuple[bool, str | None]:
    """更新条目完成状态。返回 (ok, error_message)。"""
    if not item_id:
        return False, "id 不能为空"

    if kind in ("notion_today", "notion_week"):
        ok = update_page(item_id, {"Done": {"checkbox": bool(value)}})
        if not ok:
            return False, "Notion 写回失败"
        return True, None

    if kind == "apple_reminder":
        try:
            complete_reminder(item_id, completed=bool(value))
            return True, None
        except Exception as exc:
            return False, f"提醒事项写回失败: {exc}"

    return False, f"不支持的 kind: {kind}"
