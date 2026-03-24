"""项目配置：从 .env 文件和环境变量加载。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_TODAY_DB_ID = os.environ.get("NOTION_TODAY_DB_ID", "")
NOTION_WEEK_DB_ID = os.environ.get("NOTION_WEEK_DB_ID", "")
NOTION_API_VERSION = "2022-06-28"

CRON_LOG_PATH = PROJECT_ROOT / "cron.log"
JXA_SCRIPT_PATH = PROJECT_ROOT / "read_reminders.jxa"
