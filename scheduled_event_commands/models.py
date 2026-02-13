"""SQLAlchemy models for scheduled events."""

#region Imports

from sqlalchemy import Column, Integer, Text
from shared.db import Base

#endregion


class ScheduledEvent(Base):
    """Scheduled event record."""

    __tablename__ = "scheduled_events"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, nullable=False, index=True)
    channel_id = Column(Integer, nullable=False)
    discord_event_id = Column(Integer, nullable=True)
    warning_sent = Column(Integer, nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    start_time = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
