from __future__ import annotations

import json
import unittest
from datetime import datetime
from unittest.mock import patch

from notion_ext.calendar.server import get_response_for_path
from notion_ext.models import Reminder, TodayTask, WeekTask
from notion_ext.report.snapshot import build_daily_digest_snapshot, snapshot_to_dict


class DailyDigestSnapshotTests(unittest.TestCase):
    def test_build_snapshot_includes_sorted_sections_and_progress(self) -> None:
        snapshot = build_daily_digest_snapshot(
            today_items=[
                TodayTask(
                    name="已完成任务",
                    status="done",
                    done=True,
                    time_start="2026-04-03T12:00:00+08:00",
                    time_end="2026-04-03T13:00:00+08:00",
                ),
                TodayTask(
                    name="进行中任务",
                    status="doing",
                    done=False,
                    time_start="2026-04-03T09:00:00+08:00",
                    time_end="2026-04-03T10:00:00+08:00",
                ),
            ],
            week_items=[
                WeekTask(
                    task_name="周任务 A",
                    done=False,
                    id="a",
                    start_date="2026-04-06",
                    end_date="2026-04-07",
                ),
                WeekTask(
                    task_name="周任务 B",
                    done=True,
                    id="b",
                    start_date="2026-04-08",
                    end_date="2026-04-08",
                ),
            ],
            reminders=[
                Reminder(name="提醒 A", completed=False),
                Reminder(name="提醒 B", completed=True),
            ],
            now=datetime.fromisoformat("2026-04-03T09:30:00+08:00"),
        )

        self.assertEqual(snapshot.today.progress.done_count, 1)
        self.assertEqual(snapshot.today.progress.total_count, 2)
        self.assertEqual(snapshot.today.items[0].name, "进行中任务")
        self.assertEqual(snapshot.today.items[0].display_time, "09:00 - 10:00")
        self.assertEqual(snapshot.week.items[0].weekday_range, "周一 - 周二")
        self.assertEqual(snapshot.reminders.pending_count, 1)
        self.assertEqual(snapshot.reminders.items[0].name, "提醒 A")
        self.assertEqual(len(snapshot.running_items), 1)

        data = snapshot_to_dict(snapshot)
        self.assertEqual(data["today"]["progress"]["percent"], 50)
        self.assertEqual(data["week"]["progress"]["done_count"], 1)

    @patch("notion_ext.calendar.server.collect_daily_digest_snapshot")
    def test_report_endpoints(self, mock_collect) -> None:
        snapshot = build_daily_digest_snapshot(
            today_items=[],
            week_items=[],
            reminders=[],
            now=datetime.fromisoformat("2026-04-03T08:00:00+08:00"),
        )
        mock_collect.return_value = snapshot

        status, content_type, body = get_response_for_path("/report/overlay")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["title"], "Notion 日报")
        self.assertIn("today", payload)

        status, content_type, body = get_response_for_path("/report/text")
        self.assertEqual(status, 200)
        self.assertIn("text/plain", content_type)
        self.assertIn("今日 todo", body.decode("utf-8"))

        status, _, _ = get_response_for_path("/missing")
        self.assertEqual(status, 404)

    @patch("notion_ext.calendar.server.set_dingtalk_enabled")
    @patch("notion_ext.calendar.server.get_report_settings")
    def test_report_settings_endpoints(self, mock_get_settings, mock_set_enabled) -> None:
        mock_get_settings.return_value = {"dingtalk_enabled": True}
        mock_set_enabled.return_value = {"dingtalk_enabled": False}

        status, content_type, body = get_response_for_path("/report/settings")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["dingtalk_enabled"], True)

        from notion_ext.calendar.server import get_response_for_request

        status, content_type, body = get_response_for_request(
            "POST",
            "/report/settings",
            b'{"dingtalk_enabled": false}',
        )
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["dingtalk_enabled"], False)
        mock_set_enabled.assert_called_once_with(False)
