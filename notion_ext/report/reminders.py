"""通过 EventKit CLI 读取 macOS「提醒事项」（不启动「提醒事项」应用）。"""

from __future__ import annotations

import json
import logging
import subprocess
import sys

from ..config import REMINDERS_CLI_PATH
from ..models import Reminder

logger = logging.getLogger(__name__)


def _run_reminders_cli(*args: str) -> str:
    result = subprocess.run(
        [str(REMINDERS_CLI_PATH), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(err or "read_reminders_cli exit code != 0")
    return result.stdout.strip()


def _read_live_reminders() -> list[Reminder]:
    output = _run_reminders_cli()

    data = json.loads(output)
    reminders: list[Reminder] = []
    for lst in data.get("lists", []):
        for rem in lst.get("reminders", []):
            if rem.get("name"):
                reminders.append(
                    Reminder(
                        id=rem.get("id") or "",
                        name=rem["name"],
                        completed=bool(rem.get("completed")),
                    )
                )
    return reminders


def read_reminders() -> list[Reminder]:
    """读取 macOS 提醒事项，非 macOS 或失败时返回空列表。"""
    if sys.platform != "darwin":
        return []

    if not REMINDERS_CLI_PATH.exists():
        logger.warning(
            "提醒事项 CLI 不存在: %s（在 read_reminders_cli 目录执行 swift build -c release）",
            REMINDERS_CLI_PATH,
        )
        return []

    try:
        return _read_live_reminders()
    except Exception as exc:
        message = str(exc)
        if "未获得「提醒事项」访问权限" in message:
            logger.warning(
                "读取 Apple 提醒事项失败: %s。请在「系统设置 -> 隐私与安全性 -> 提醒事项」中允许 read_reminders_cli。",
                message,
            )
        else:
            logger.warning("读取 Apple 提醒事项失败: %s", exc)
        return []


def complete_reminder(reminder_id: str, completed: bool = True) -> bool:
    """按 identifier 更新提醒项完成状态。"""
    if sys.platform != "darwin":
        raise RuntimeError("仅支持 macOS 提醒事项写回")
    if not reminder_id:
        raise RuntimeError("提醒事项 id 不能为空")
    if not REMINDERS_CLI_PATH.exists():
        raise RuntimeError(f"提醒事项 CLI 不存在: {REMINDERS_CLI_PATH}")

    _run_reminders_cli("--set-completed", reminder_id, "true" if completed else "false")
    return True
