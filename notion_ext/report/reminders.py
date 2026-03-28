"""通过 EventKit CLI 读取 macOS「提醒事项」（不启动「提醒事项」应用）。"""

from __future__ import annotations

import json
import logging
import subprocess
import sys

from ..config import REMINDERS_CLI_PATH
from ..models import Reminder

logger = logging.getLogger(__name__)


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
        result = subprocess.run(
            [str(REMINDERS_CLI_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            logger.warning("读取提醒事项失败: %s", err)
            return []

        data = json.loads(result.stdout.strip())
        reminders = []
        for lst in data.get("lists", []):
            for rem in lst.get("reminders", []):
                if rem.get("name"):
                    reminders.append(Reminder(
                        name=rem["name"],
                        completed=bool(rem.get("completed")),
                    ))
        return reminders
    except Exception as exc:
        logger.warning("读取 Apple 提醒事项失败: %s", exc)
        return []
