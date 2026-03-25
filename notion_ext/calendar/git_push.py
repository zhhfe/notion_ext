"""保存 ICS 文件并推送到 Git。"""

from __future__ import annotations

import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_PUSH_MAX_ATTEMPTS = 3


def save_and_push(
    ics_data: bytes,
    output_dir: str,
    filename: str,
    commit_msg: str = "",
) -> None:
    """保存 ICS 文件到指定目录，并 git add / commit / push。"""
    path = Path(output_dir) / filename
    path.write_bytes(ics_data)

    if not commit_msg:
        commit_msg = f"Update {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    try:
        _run_git(output_dir, "add", filename)
        output = _run_git(output_dir, "commit", "-m", commit_msg)
        if "nothing to commit" in output or "no changes added" in output:
            logger.info("没有需要提交的变更")
            return

        for attempt in range(1, _PUSH_MAX_ATTEMPTS + 1):
            try:
                _run_git(output_dir, "push")
                logger.info("Git push 成功")
                return
            except RuntimeError as exc:
                logger.warning("Git push 失败 (attempt %d/%d): %s", attempt, _PUSH_MAX_ATTEMPTS, exc)
                if attempt < _PUSH_MAX_ATTEMPTS:
                    time.sleep(attempt)
        logger.error("Git push 重试全部失败")
    except RuntimeError as exc:
        logger.error("Git 操作失败: %s", exc)


def _run_git(cwd: str, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    combined = result.stdout + result.stderr
    if result.returncode != 0:
        if "nothing to commit" in combined or "no changes added" in combined:
            return combined
        raise RuntimeError(f"git {' '.join(args)}: {combined.strip()}")
    return combined
