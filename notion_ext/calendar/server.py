"""HTTP 服务器：提供 calendar.ics 订阅端点。"""

from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from ..config import (
    CALENDAR_SERVER_PORT,
    ICS_AUTO_PUSH_GIT,
    ICS_FILE_NAME,
    ICS_GIT_COMMIT_MSG,
    ICS_OUTPUT_PATH,
)
from .ics_generator import generate_ics
from .notion_updater import update_default_page_time
from .queries import query_recent_tasks

logger = logging.getLogger(__name__)


def _sync_and_get_ics() -> bytes:
    """查询 Notion → 生成 ICS；异步更新默认页面时间和推送 Git。"""
    threading.Thread(target=update_default_page_time, daemon=True).start()

    events = query_recent_tasks()
    ics_data = generate_ics(events)

    if ICS_AUTO_PUSH_GIT and ICS_OUTPUT_PATH:
        from .git_push import save_and_push
        threading.Thread(
            target=save_and_push,
            args=(ics_data, ICS_OUTPUT_PATH, ICS_FILE_NAME, ICS_GIT_COMMIT_MSG),
            daemon=True,
        ).start()

    return ics_data


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/calendar.ics":
            try:
                data = _sync_and_get_ics()
                self.send_response(200)
                self.send_header("Content-Type", "text/calendar; charset=utf-8")
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:
                logger.error("生成 ICS 失败: %s", exc)
                self.send_error(500)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args) -> None:
        logger.info(format, *args)


def run_server(port: int = 0) -> None:
    port = port or CALENDAR_SERVER_PORT
    server = HTTPServer(("0.0.0.0", port), _Handler)
    logger.info("日历服务启动: http://0.0.0.0:%d/calendar.ics", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("日历服务关闭")
        server.shutdown()
