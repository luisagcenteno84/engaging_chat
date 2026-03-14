from __future__ import annotations

from datetime import datetime
from typing import Iterable

from google.cloud import firestore

from .config import settings


_client: firestore.Client | None = None


def get_client() -> firestore.Client:
    global _client
    if _client is None:
        if settings.project_id:
            _client = firestore.Client(project=settings.project_id, database=settings.firestore_database)
        else:
            _client = firestore.Client(database=settings.firestore_database)
    return _client


def now_utc() -> datetime:
    return datetime.utcnow()


def iso_date(dt: datetime | None = None) -> str:
    target = dt or now_utc()
    return target.strftime('%Y-%m-%d')


def chunked(items: Iterable, size: int = 10):
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch
