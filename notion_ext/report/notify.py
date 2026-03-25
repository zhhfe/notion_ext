"""macOS 系统通知。"""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def notify_mac(title: str, message: str) -> None:
    """发送 macOS 系统通知，非 macOS 静默跳过。"""
    if sys.platform != "darwin":
        return
    escaped_title = title.replace('"', '\\"')
    escaped_msg = message.replace('"', '\\"')
    script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except Exception as exc:
        logger.error("发送本地通知失败: %s", exc)
