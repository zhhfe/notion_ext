"""日报运行时设置（含钉钉发送开关）。"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from ..config import DINGTALK_ENABLED_DEFAULT, REMINDERS_ENABLED_DEFAULT, REPORT_SETTINGS_PATH

_LOCK = threading.RLock()
_CACHE: dict | None = None


def _read_settings_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_settings_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _get_settings() -> dict:
    global _CACHE
    with _LOCK:
        if _CACHE is None:
            _CACHE = _read_settings_file(REPORT_SETTINGS_PATH)
        return dict(_CACHE)


def _set_settings(data: dict) -> None:
    global _CACHE
    with _LOCK:
        _CACHE = dict(data)
        _write_settings_file(REPORT_SETTINGS_PATH, _CACHE)


def get_dingtalk_enabled() -> bool:
    data = _get_settings()
    value = data.get("dingtalk_enabled")
    if isinstance(value, bool):
        return value
    return DINGTALK_ENABLED_DEFAULT


def set_dingtalk_enabled(enabled: bool) -> dict:
    data = _get_settings()
    data["dingtalk_enabled"] = bool(enabled)
    _set_settings(data)
    return {"dingtalk_enabled": bool(enabled)}


def get_reminders_enabled() -> bool:
    data = _get_settings()
    value = data.get("reminders_enabled")
    if isinstance(value, bool):
        return value
    return REMINDERS_ENABLED_DEFAULT


def set_reminders_enabled(enabled: bool) -> dict:
    data = _get_settings()
    data["reminders_enabled"] = bool(enabled)
    _set_settings(data)
    return {"reminders_enabled": bool(enabled)}


def get_report_settings() -> dict:
    return {
        "dingtalk_enabled": get_dingtalk_enabled(),
        "reminders_enabled": get_reminders_enabled(),
    }
