"""Database access helpers for scheduled events."""

#region Imports

import datetime
from dataclasses import dataclass
from typing import Iterator, List, Optional
from contextlib import contextmanager

from sqlalchemy import select

from shared.db import SessionLocal
from .models import ScheduledEvent

#endregion


@dataclass(frozen=True)
class ScheduledEventRecord:
    """Scheduled event data transferred outside the session."""

    id: int
    guild_id: int
    channel_id: int
    discord_event_id: Optional[int]
    warning_sent: bool
    title: str
    description: str
    start_time: str
    status: str


#region Helpers

@contextmanager
def session_scope() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _to_record(row: ScheduledEvent) -> ScheduledEventRecord:
    return ScheduledEventRecord(
        id=row.id,
        guild_id=row.guild_id,
        channel_id=row.channel_id,
        discord_event_id=row.discord_event_id,
        warning_sent=bool(row.warning_sent),
        title=row.title,
        description=row.description,
        start_time=row.start_time,
        status=row.status,
    )

#endregion


#region Queries

def create_event(
    guild_id: int,
    channel_id: int,
    title: str,
    description: str,
    start_time: datetime.datetime,
    discord_event_id: Optional[int] = None,
) -> ScheduledEventRecord:
    with session_scope() as session:
        record = ScheduledEvent(
            guild_id=guild_id,
            channel_id=channel_id,
            discord_event_id=discord_event_id,
            warning_sent=0,
            title=title,
            description=description,
            start_time=start_time.isoformat(),
            created_at=datetime.datetime.now().astimezone().isoformat(),
            status="pending",
        )
        session.add(record)
        session.flush()
        return _to_record(record)


def list_pending_events() -> List[ScheduledEventRecord]:
    with session_scope() as session:
        rows = session.execute(
            select(ScheduledEvent)
            .where(ScheduledEvent.status == "pending")
            .order_by(ScheduledEvent.start_time)
        ).scalars().all()
        return [_to_record(row) for row in rows]


def list_pending_events_by_guild(guild_id: int) -> List[ScheduledEventRecord]:
    with session_scope() as session:
        rows = session.execute(
            select(ScheduledEvent)
            .where(ScheduledEvent.guild_id == guild_id)
            .where(ScheduledEvent.status == "pending")
            .order_by(ScheduledEvent.start_time)
        ).scalars().all()
        return [_to_record(row) for row in rows]


def get_pending_event_by_index(guild_id: int, index: int) -> Optional[ScheduledEventRecord]:
    if index < 1:
        return None
    rows = list_pending_events_by_guild(guild_id)
    if index > len(rows):
        return None
    return rows[index - 1]


def delete_event_by_id(event_id: int) -> Optional[ScheduledEventRecord]:
    with session_scope() as session:
        row = session.get(ScheduledEvent, event_id)
        if not row:
            return None
        record = _to_record(row)
        session.delete(row)
        return record


def delete_all_events_by_guild(guild_id: int) -> int:
    with session_scope() as session:
        rows = session.execute(
            select(ScheduledEvent)
            .where(ScheduledEvent.guild_id == guild_id)
        ).scalars().all()
        count = len(rows)
        for row in rows:
            session.delete(row)
        return count


def update_event(
    event_id: int,
    start_time: datetime.datetime,
    title: str,
    description: str,
    channel_id: int,
) -> bool:
    with session_scope() as session:
        row = session.get(ScheduledEvent, event_id)
        if not row:
            return False
        row.start_time = start_time.isoformat()
        row.title = title
        row.description = description
        row.channel_id = channel_id
        return True


def mark_sent(event_id: int) -> bool:
    with session_scope() as session:
        row = session.get(ScheduledEvent, event_id)
        if not row:
            return False
        row.status = "sent"
        return True


def mark_warning_sent(event_id: int) -> bool:
    with session_scope() as session:
        row = session.get(ScheduledEvent, event_id)
        if not row:
            return False
        row.warning_sent = 1
        return True

#endregion
