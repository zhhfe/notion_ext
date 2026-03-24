"""通过 JXA 读取 macOS「提醒事项」。"""

from __future__ import annotations

import json
import logging
import subprocess
import sys

from .config import JXA_SCRIPT_PATH
from .models import Reminder

logger = logging.getLogger(__name__)


def read_reminders() -> list[Reminder]:
    """读取 macOS 提醒事项，非 macOS 或失败时返回空列表。"""
    if sys.platform != "darwin":
        return []

    if not JXA_SCRIPT_PATH.exists():
        logger.warning("JXA 脚本不存在: %s", JXA_SCRIPT_PATH)
        return []

    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", str(JXA_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning("读取提醒事项失败: %s", result.stderr.strip() or result.stdout.strip())
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
