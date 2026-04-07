"""HTTP 服务器：提供 calendar.ics 订阅端点。"""

from __future__ import annotations

import json
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
from ..report import collect_daily_digest_snapshot, complete_item
from ..report.settings import get_report_settings, set_dingtalk_enabled, set_reminders_enabled
from ..report.snapshot import snapshot_to_dict

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


def _build_report_overlay() -> bytes:
    snapshot = collect_daily_digest_snapshot()
    return json.dumps(snapshot_to_dict(snapshot), ensure_ascii=False).encode("utf-8")


def _build_report_text() -> bytes:
    snapshot = collect_daily_digest_snapshot()
    return snapshot.text.encode("utf-8")


def _build_report_settings() -> bytes:
    return json.dumps(get_report_settings(), ensure_ascii=False).encode("utf-8")


def _update_report_settings(body: bytes) -> bytes:
    data = json.loads((body or b"{}").decode("utf-8"))
    dingtalk_enabled = bool(data.get("dingtalk_enabled", True))
    reminders_enabled = bool(data.get("reminders_enabled", False))
    set_dingtalk_enabled(dingtalk_enabled)
    set_reminders_enabled(reminders_enabled)
    return json.dumps(get_report_settings(), ensure_ascii=False).encode("utf-8")


def _complete_report_item(body: bytes) -> tuple[int, bytes]:
    try:
        data = json.loads((body or b"{}").decode("utf-8"))
    except json.JSONDecodeError:
        return 400, json.dumps({"ok": False, "error": "请求体不是有效 JSON"}, ensure_ascii=False).encode("utf-8")

    kind = data.get("kind")
    item_id = data.get("id")
    value = data.get("value", True)
    if not isinstance(kind, str) or not kind:
        return 400, json.dumps({"ok": False, "error": "缺少 kind"}, ensure_ascii=False).encode("utf-8")
    if not isinstance(item_id, str) or not item_id:
        return 400, json.dumps({"ok": False, "error": "缺少 id"}, ensure_ascii=False).encode("utf-8")
    if not isinstance(value, bool):
        return 400, json.dumps({"ok": False, "error": "value 必须为布尔值"}, ensure_ascii=False).encode("utf-8")

    ok, error = complete_item(kind, item_id, value=value)
    if ok:
        return 200, json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
    if error and error.startswith("不支持的 kind"):
        return 400, json.dumps({"ok": False, "error": error}, ensure_ascii=False).encode("utf-8")
    return 500, json.dumps({"ok": False, "error": error or "写回失败"}, ensure_ascii=False).encode("utf-8")


def get_response_for_path(path: str) -> tuple[int, str, bytes]:
    return get_response_for_request("GET", path, b"")


def get_response_for_request(method: str, path: str, body: bytes = b"") -> tuple[int, str, bytes]:
    if path == "/calendar.ics":
        return 200, "text/calendar; charset=utf-8", _sync_and_get_ics()
    if path == "/report/overlay":
        return 200, "application/json; charset=utf-8", _build_report_overlay()
    if path == "/report/text":
        return 200, "text/plain; charset=utf-8", _build_report_text()
    if path == "/report/settings" and method == "GET":
        return 200, "application/json; charset=utf-8", _build_report_settings()
    if path == "/report/settings" and method == "POST":
        return 200, "application/json; charset=utf-8", _update_report_settings(body)
    if path == "/report/complete" and method == "POST":
        status, payload = _complete_report_item(body)
        return status, "application/json; charset=utf-8", payload
    return 404, "text/plain; charset=utf-8", b"Not Found"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            status, content_type, data = get_response_for_request("GET", self.path)
        except Exception as exc:
            logger.error("生成 %s 失败: %s", self.path, exc, exc_info=True)
            self.send_error(500)
            return

        if status == 404:
            self.send_error(404)
            return

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length > 0 else b""
            status, content_type, data = get_response_for_request("POST", self.path, body)
        except Exception as exc:
            logger.error("处理 %s 失败: %s", self.path, exc, exc_info=True)
            self.send_error(500)
            return

        if status == 404:
            self.send_error(404)
            return

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

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
