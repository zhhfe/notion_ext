"""生成 iCalendar (.ics) 内容。"""

from __future__ import annotations

from datetime import datetime, timezone

from icalendar import Alarm, Calendar, Event

from ..models import CalendarEvent


def _parse_iso(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def generate_ics(events: list[CalendarEvent]) -> bytes:
    """将日历事件列表转换为 ICS 二进制数据。"""
    cal = Calendar()
    cal.add("prodid", "-//NotionExt//Notion Calendar//CN")
    cal.add("method", "PUBLISH")
    cal.add("version", "2.0")

    for ev in events:
        event = Event()
        event.add("uid", ev.uid)
        event.add("summary", ev.summary)
        try:
            event.add("dtstart", _parse_iso(ev.start))
            event.add("dtend", _parse_iso(ev.end))
        except (ValueError, TypeError):
            continue
        event.add("dtstamp", datetime.now(timezone.utc))

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"notion task: {ev.summary}")
        event.add_component(alarm)

        cal.add_component(event)

    return cal.to_ical()
