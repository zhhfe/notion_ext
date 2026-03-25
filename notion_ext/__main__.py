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


def _setup_logging() -> None:
    root = logging.getLogger("notion_ext")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.FileHandler(config.LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


def _run_report_safe() -> None:
    """供调度器调用，捕获异常避免中断定时任务。"""
    try:
        from .report import run_report
        run_report()
    except Exception as exc:
        logger.error("定时日报执行失败: %s", exc, exc_info=True)


def _serve() -> None:
    """启动 HTTP 服务 + 定时任务，常驻运行。"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    from .calendar.notion_updater import update_default_page_time
    from .calendar.server import run_server

    # 定时任务
    scheduler = BackgroundScheduler(timezone=config.TZ)
    scheduler.add_job(
        _run_report_safe,
        CronTrigger(minute=config.REPORT_CRON_MINUTE, hour=config.REPORT_CRON_HOUR),
        id="daily_report",
        name="钉钉日报",
    )
    scheduler.start()
    logger.info(
        "定时任务已注册: 日报 (hour=%s, minute=%s, tz=%s)",
        config.REPORT_CRON_HOUR,
        config.REPORT_CRON_MINUTE,
        config.TZ,
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