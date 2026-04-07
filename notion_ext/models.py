from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TodayTask:
    id: str
    name: str
    status: Optional[str]
    done: bool
    time_start: Optional[str] = None
    time_end: Optional[str] = None


@dataclass
class WeekTask:
    task_name: str
    done: bool
    id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None


@dataclass
class Reminder:
    id: str
    name: str
    completed: bool


@dataclass
class CalendarEvent:
    uid: str
    summary: str
    start: str
    end: str


@dataclass
class TodaySnapshotItem:
    id: str
    name: str
    status: Optional[str]
    done: bool
    time_start: Optional[str]
    time_end: Optional[str]
    display_time: str


@dataclass
class WeekSnapshotItem:
    task_name: str
    done: bool
    id: str
    start_date: Optional[str]
    end_date: Optional[str]
    weekday_range: str


@dataclass
class ReminderSnapshotItem:
    id: str
    name: str
    completed: bool


@dataclass
class ProgressSnapshot:
    done_count: int
    total_count: int
    percent: int
    bar: str


@dataclass
class TodaySectionSnapshot:
    progress: ProgressSnapshot
    items: list[TodaySnapshotItem]


@dataclass
class WeekSectionSnapshot:
    progress: ProgressSnapshot
    items: list[WeekSnapshotItem]


@dataclass
class ReminderSectionSnapshot:
    pending_count: int
    items: list[ReminderSnapshotItem]


@dataclass
class PeriodProgressSnapshot:
    percent: int


@dataclass
class PeriodsSnapshot:
    month: PeriodProgressSnapshot
    quarter: PeriodProgressSnapshot
    year: PeriodProgressSnapshot


@dataclass
class DailyDigestSnapshot:
    generated_at: str
    title: str
    text: str
    running_items: list[str]
    today: TodaySectionSnapshot
    week: WeekSectionSnapshot
    reminders: ReminderSectionSnapshot
    periods: PeriodsSnapshot
