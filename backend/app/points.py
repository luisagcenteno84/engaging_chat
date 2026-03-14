from __future__ import annotations

from datetime import datetime, timedelta

from .config import settings
from .db import iso_date


def calculate_streak(last_active_date: str | None, today: str) -> int:
    if not last_active_date:
        return 1
    try:
        last = datetime.strptime(last_active_date, '%Y-%m-%d').date()
        cur = datetime.strptime(today, '%Y-%m-%d').date()
    except ValueError:
        return 1

    if cur == last:
        return 0  # no change
    if cur == last + timedelta(days=1):
        return 1
    return -1  # reset


def points_for_correct() -> int:
    return settings.points_correct


def points_for_daily_login() -> int:
    return settings.points_daily_login


def points_for_topic_complete() -> int:
    return settings.points_topic_complete


def is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {'true', '1', 'yes', 'y'}


def normalize_topic(topic: str | None) -> str:
    if not topic:
        return 'General'
    return topic.strip().title()


def today_iso() -> str:
    return iso_date()
