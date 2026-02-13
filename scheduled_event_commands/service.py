"""Scheduler loop for pending scheduled events."""

#region Imports

import asyncio
import datetime
from typing import Iterable

import discord

from . import repository

#endregion


#region Helpers

def _format_event_message(record: repository.ScheduledEventRecord) -> str:
    description = record.description or "No description"
    return (
        f"**Scheduled Event**\n"
        f"**Title**: {record.title}\n"
        f"**Description**: {description}"
    )


def _format_warning_message(record: repository.ScheduledEventRecord) -> str:
    return (
        f"Reminder: scheduled event **{record.title}** starts in 15 minutes!"
    )


def _parse_event_time(event_time_str: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(event_time_str)

#endregion


#region Scheduler

def get_pending_events() -> Iterable[repository.ScheduledEventRecord]:
    return repository.list_pending_events()


def should_warn(event_time: datetime.datetime, now: datetime.datetime) -> bool:
    warning_time = event_time - datetime.timedelta(minutes=15)
    return warning_time <= now < event_time


def should_send(event_time: datetime.datetime, now: datetime.datetime) -> bool:
    return now >= event_time


async def handle_scheduled_events(bot: discord.Client) -> None:
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.datetime.now().astimezone()
        events = list(get_pending_events())
        for record in events:
            event_time = _parse_event_time(record.start_time)

            if now - event_time > datetime.timedelta(minutes=5):
                repository.mark_sent(record.id)
                continue

            if not record.warning_sent and should_warn(event_time, now):
                channel = bot.get_channel(record.channel_id)
                if channel:
                    await channel.send(_format_warning_message(record))
                repository.mark_warning_sent(record.id)

            if should_send(event_time, now):
                channel = bot.get_channel(record.channel_id)
                if channel:
                    await channel.send(_format_event_message(record))
                repository.mark_sent(record.id)

        await asyncio.sleep(60)

#endregion
