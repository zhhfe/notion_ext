"""项目配置：从 .env 文件和环境变量加载。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

# ── Notion ────────────────────────────────────────────────
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_TODAY_DB_ID = os.environ.get("NOTION_TODAY_DB_ID", "")
NOTION_WEEK_DB_ID = os.environ.get("NOTION_WEEK_DB_ID", "")
NOTION_DEFAULT_PAGE_ID = os.environ.get("NOTION_DEFAULT_PAGE_ID", "")
NOTION_API_VERSION = "2022-06-28"

# ── Calendar sync ─────────────────────────────────────────
_ics_raw = os.environ.get("ICS_OUTPUT_PATH", "notion_ext/calendar")
ICS_OUTPUT_PATH = str(Path(_ics_raw) if Path(_ics_raw).is_absolute() else PROJECT_ROOT / _ics_raw)
ICS_FILE_NAME = os.environ.get("ICS_FILE_NAME", "calendar.ics")
ICS_AUTO_PUSH_GIT = os.environ.get("ICS_AUTO_PUSH_GIT", "").lower() in ("true", "1", "yes")
ICS_GIT_COMMIT_MSG = os.environ.get("ICS_GIT_COMMIT_MSG", "Update calendar from Notion")
CALENDAR_SERVER_PORT = int(os.environ.get("CALENDAR_SERVER_PORT", "33189"))

# ── Schedule ──────────────────────────────────────────────
REPORT_CRON_MINUTE = os.environ.get("REPORT_CRON_MINUTE", "0,30")
REPORT_CRON_HOUR = os.environ.get("REPORT_CRON_HOUR", "10-22")
TZ = os.environ.get("TZ", "Asia/Shanghai")
DINGTALK_ENABLED_DEFAULT = os.environ.get("DINGTALK_ENABLED", "true").lower() in ("true", "1", "yes")
REMINDERS_ENABLED_DEFAULT = os.environ.get("REMINDERS_ENABLED", "false").lower() in ("true", "1", "yes")

# ── Paths ─────────────────────────────────────────────────
LOG_PATH = PROJECT_ROOT / "notion_ext.log"
REPORT_SETTINGS_PATH = PROJECT_ROOT / "notion_ext_report_settings.json"


def _resolve_reminders_cli_path() -> Path:
    """EventKit 命令行工具路径；可用环境变量 NOTION_EXT_REMINDERS_CLI 覆盖。"""
    override = os.environ.get("NOTION_EXT_REMINDERS_CLI")
    if override:
        return Path(override).expanduser()
    root = PROJECT_ROOT / "read_reminders_cli"
    for rel in (
        ".build/release/read_reminders_cli",
        ".build/arm64-apple-macosx/release/read_reminders_cli",
        ".build/x86_64-apple-macosx/release/read_reminders_cli",
    ):
        p = root / rel
        if p.is_file():
            return p
    return root / ".build" / "release" / "read_reminders_cli"


REMINDERS_CLI_PATH = _resolve_reminders_cli_path()
