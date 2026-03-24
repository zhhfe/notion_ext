"""钉钉 Webhook 消息发送。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


def _normalize_markdown(text: str) -> str:
    """钉钉 markdown 在部分客户端不按 \\n 换行，统一成 <br>。"""
    return text.replace("\n", "<br>") if text else text


def _sign_url(webhook: str, secret: str) -> str:
    ts = str(int(time.time() * 1000))
    string_to_sign = f"{ts}\n{secret}"
    sign = base64.b64encode(
        hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    ).decode()
    sep = "&" if "?" in webhook else "?"
    return f"{webhook}{sep}timestamp={ts}&sign={quote(sign)}"


def send_markdown(title: str, text: str) -> None:
    """发送 markdown 消息到钉钉。需 DINGTALK_WEBHOOK 环境变量。"""
    webhook = os.environ.get("DINGTALK_WEBHOOK", "").strip()
    if not webhook:
        logger.warning("未设置 DINGTALK_WEBHOOK，跳过发送")
        return

    secret = os.environ.get("DINGTALK_SECRET", "").strip()
    url = _sign_url(webhook, secret) if secret else webhook

    body = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": _normalize_markdown(text)},
    }
    resp = requests.post(url, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"钉钉发送失败: {data.get('errmsg', data)}")
    logger.info("已发送到钉钉")
