from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TodayTask:
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


@dataclass
class Reminder:
    name: str
    completed: bool


@dataclass
class CalendarEvent:
    uid: str
    summary: str
    start: str
    end: str
