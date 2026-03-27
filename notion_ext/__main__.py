"""
notion_ext 入口

启动模式：
    python -m notion_ext            启动服务（HTTP + 定时日报）
    python -m notion_ext report     手动执行一次日报（调试用）
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys

from . import config

logger = logging.getLogger("notion_ext")


class _StreamToLogger:
    """将 write() 调用转发到 logging，用于重定向 stdout/stderr。"""

    def __init__(self, log: logging.Logger, level: int) -> None:
        self._log = log
        self._level = level
        self._buf = ""

    def write(self, msg: str) -> None:
        if msg and msg.strip():
            self._log.log(self._level, msg.rstrip())

    def flush(self) -> None:
        pass


def _setup_logging() -> None:
    root = logging.getLogger("notion_ext")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    real_stderr = sys.stderr

    console = logging.StreamHandler(real_stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.FileHandler(config.LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    sys.stdout = _StreamToLogger(logging.getLogger("notion_ext.stdout"), logging.INFO)
    sys.stderr = _StreamToLogger(logging.getLogger("notion_ext.stderr"), logging.ERROR)


def _run_report_safe() -> None:
    """供调度器调用，捕获异常避免中断定时任务。"""
    try:
        from .report import run_report
        run_report()
    except Exception as exc:
        logger.error("定时日报执行失败: %s", exc, exc_info=True)


def _clean_log_file() -> None:
    """清空日志文件，保留文件句柄。"""
    try:
        log_path = config.LOG_PATH
        if log_path.exists():
            log_path.write_text("", encoding="utf-8")
            logger.info("日志文件已清理: %s", log_path)
    except Exception as exc:
        logger.error("清理日志文件失败: %s", exc, exc_info=True)


def _serve() -> None:
    """启动 HTTP 服务 + 定时任务，常驻运行。"""
    from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    from .calendar.notion_updater import update_default_page_time
    from .calendar.server import run_server

    misfire_grace = 3600

    scheduler = BackgroundScheduler(timezone=config.TZ)
    scheduler.add_job(
        _run_report_safe,
        CronTrigger(minute=config.REPORT_CRON_MINUTE, hour=config.REPORT_CRON_HOUR),
        id="daily_report",
        name="钉钉日报",
        misfire_grace_time=misfire_grace,
    )
    scheduler.add_job(
        _clean_log_file,
        CronTrigger(hour=3, minute=0),
        id="clean_log",
        name="清理日志文件",
        misfire_grace_time=misfire_grace,
    )

    def _on_scheduler_event(event):
        if hasattr(event, "job_id"):
            if event.code == EVENT_JOB_MISSED:
                logger.warning("定时任务错过执行: %s", event.job_id)
            elif event.code == EVENT_JOB_ERROR:
                logger.error("定时任务执行异常: %s", event.job_id, exc_info=event.exception)
            elif event.code == EVENT_JOB_EXECUTED:
                logger.debug("定时任务完成: %s", event.job_id)

    scheduler.add_listener(_on_scheduler_event, EVENT_JOB_EXECUTED | EVENT_JOB_MISSED | EVENT_JOB_ERROR)
    scheduler.start()
    logger.info(
        "定时任务已注册: 日报 (hour=%s, minute=%s, tz=%s), 日志清理 (03:00), misfire_grace=%ds",
        config.REPORT_CRON_HOUR,
        config.REPORT_CRON_MINUTE,
        config.TZ,
        misfire_grace,
    )

    # 启动时更新默认页面时间
    update_default_page_time()

    # HTTP 服务（主线程阻塞）
    def _shutdown(signum, frame):
        logger.info("收到信号 %s，正在关闭...", signum)
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    run_server()


def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(prog="notion_ext", description="Notion 扩展工具")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("report", help="手动执行一次日报（调试用）")

    args = parser.parse_args()

    if args.command == "report":
        from .report import run_report
        run_report()
    else:
        _serve()


if __name__ == "__main__":
    main()