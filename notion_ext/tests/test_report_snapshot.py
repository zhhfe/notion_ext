from __future__ import annotations

import json
import unittest
from datetime import datetime
from unittest.mock import patch

from notion_ext.calendar.server import get_response_for_path
from notion_ext.models import Reminder, TodayTask, WeekTask
from notion_ext.report import complete_item
from notion_ext.report.snapshot import build_daily_digest_snapshot, snapshot_to_dict


class DailyDigestSnapshotTests(unittest.TestCase):
    def test_build_snapshot_includes_sorted_sections_and_progress(self) -> None:
        snapshot = build_daily_digest_snapshot(
            today_items=[
                TodayTask(
                    id="today-done",
                    name="已完成任务",
                    status="done",
                    done=True,
                    time_start="2026-04-03T12:00:00+08:00",
                    time_end="2026-04-03T13:00:00+08:00",
                ),
                TodayTask(
                    id="today-doing",
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
                Reminder(id="rem-a", name="提醒 A", completed=False),
                Reminder(id="rem-b", name="提醒 B", completed=True),
            ],
            now=datetime.fromisoformat("2026-04-03T09:30:00+08:00"),
        )

        self.assertEqual(snapshot.today.progress.done_count, 1)
        self.assertEqual(snapshot.today.progress.total_count, 2)
        self.assertEqual(snapshot.today.items[0].name, "进行中任务")
        self.assertEqual(snapshot.today.items[0].id, "today-doing")
        self.assertEqual(snapshot.today.items[0].display_time, "09:00 - 10:00")
        self.assertEqual(snapshot.week.items[0].weekday_range, "周一 - 周二")
        self.assertEqual(snapshot.reminders.pending_count, 1)
        self.assertEqual(snapshot.reminders.items[0].id, "rem-a")
        self.assertEqual(snapshot.reminders.items[0].name, "提醒 A")
        self.assertEqual(len(snapshot.running_items), 1)
        self.assertEqual(snapshot.periods.month.percent, 10)
        self.assertEqual(snapshot.periods.quarter.percent, 3)
        self.assertEqual(snapshot.periods.year.percent, 25)

        data = snapshot_to_dict(snapshot)
        self.assertEqual(data["today"]["progress"]["percent"], 50)
        self.assertEqual(data["week"]["progress"]["done_count"], 1)
        self.assertIn("periods", data)
        self.assertIn("month", data["periods"])

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

    @patch("notion_ext.calendar.server.complete_item")
    def test_report_complete_endpoint(self, mock_complete_item) -> None:
        from notion_ext.calendar.server import get_response_for_request

        mock_complete_item.return_value = (True, None)
        status, content_type, body = get_response_for_request(
            "POST",
            "/report/complete",
            b'{"kind":"notion_today","id":"page-1"}',
        )
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["ok"], True)
        mock_complete_item.assert_called_once_with("notion_today", "page-1", value=True)

        status, _, body = get_response_for_request(
            "POST",
            "/report/complete",
            b'{"kind":"","id":"x"}',
        )
        self.assertEqual(status, 400)
        self.assertIn("缺少 kind", body.decode("utf-8"))

        mock_complete_item.reset_mock()
        mock_complete_item.return_value = (False, "Notion 写回失败")
        status, _, body = get_response_for_request(
            "POST",
            "/report/complete",
            b'{"kind":"notion_week","id":"page-2"}',
        )
        self.assertEqual(status, 500)
        self.assertIn("Notion 写回失败", body.decode("utf-8"))

        status, _, body = get_response_for_request(
            "POST",
            "/report/complete",
            b'{"kind":"notion_week","id":"page-2","value":"x"}',
        )
        self.assertEqual(status, 400)
        self.assertIn("value 必须为布尔值", body.decode("utf-8"))

    @patch("notion_ext.calendar.server.set_dingtalk_enabled")
    @patch("notion_ext.calendar.server.set_reminders_enabled")
    @patch("notion_ext.calendar.server.get_report_settings")
    def test_report_settings_endpoints(self, mock_get_settings, mock_set_reminders, mock_set_enabled) -> None:
        mock_get_settings.return_value = {"dingtalk_enabled": True, "reminders_enabled": False}

        status, content_type, body = get_response_for_path("/report/settings")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["dingtalk_enabled"], True)
        self.assertEqual(payload["reminders_enabled"], False)

        from notion_ext.calendar.server import get_response_for_request

        status, content_type, body = get_response_for_request(
            "POST",
            "/report/settings",
            b'{"dingtalk_enabled": false, "reminders_enabled": true}',
        )
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body.decode("utf-8"))
        mock_set_enabled.assert_called_once_with(False)
        mock_set_reminders.assert_called_once_with(True)

    @patch("notion_ext.report.complete_reminder")
    @patch("notion_ext.report.update_page")
    def test_complete_item_routes_to_backends(self, mock_update_page, mock_complete_reminder) -> None:
        mock_update_page.return_value = True
        ok, error = complete_item("notion_today", "page-123", True)
        self.assertTrue(ok)
        self.assertIsNone(error)
        mock_update_page.assert_called_once_with("page-123", {"Done": {"checkbox": True}})

        ok, error = complete_item("apple_reminder", "rem-1", False)
        self.assertTrue(ok)
        self.assertIsNone(error)
        mock_complete_reminder.assert_called_once_with("rem-1", completed=False)
