"""Validation and user-facing helpers for scheduled events."""

#region Imports

import datetime
from typing import List, Optional, Tuple

import discord

from shared.db import init_db, engine
from shared.error_helpers import send_user_message
from shared.pagination import paginate_lines, send_paginated_message
from . import repository

#endregion


#region Helpers

def _normalize_description(description: Optional[str]) -> str:
    if description is None:
        return ""
    return description.strip()


def _normalize_title(title: str) -> str:
    return title.strip()

#endregion


#region Service

def initialize_storage() -> None:
    init_db()
    _ensure_discord_event_column()
    _ensure_warning_sent_column()


def _parse_datetime(date_str: str, time_str: str) -> datetime.datetime:
    return datetime.datetime.strptime(
        f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)


def _validate_time(date_str: str, time_str: str) -> Tuple[bool, str]:
    try:
        parsed = _parse_datetime(date_str, time_str)
    except ValueError:
        return False, "Invalid date or time format. Use YYYY-MM-DD and HH:MM."

    now = datetime.datetime.now().astimezone()
    if parsed <= now:
        return False, "Please provide a future date and time."

    return True, ""


def _ensure_discord_event_column() -> None:
    with engine.connect() as connection:
        result = connection.exec_driver_sql("PRAGMA table_info('scheduled_events');")
        columns = {row[1] for row in result}
        if "discord_event_id" in columns:
            return
        connection.exec_driver_sql(
            "ALTER TABLE scheduled_events ADD COLUMN discord_event_id INTEGER;"
        )


def _ensure_warning_sent_column() -> None:
    with engine.connect() as connection:
        result = connection.exec_driver_sql("PRAGMA table_info('scheduled_events');")
        columns = {row[1] for row in result}
        if "warning_sent" in columns:
            return
        connection.exec_driver_sql(
            "ALTER TABLE scheduled_events ADD COLUMN warning_sent INTEGER;"
        )


def _prepare_event(
    title: str,
    description: Optional[str],
    date_str: str,
    time_str: str,
) -> Tuple[bool, str, Optional[str], Optional[str], Optional[datetime.datetime]]:
    normalized_title = _normalize_title(title)
    normalized_description = _normalize_description(description)

    if not normalized_title:
        return False, "Please provide a non-empty title.", None, None, None

    valid, error = _validate_time(date_str, time_str)
    if not valid:
        return False, error, None, None, None

    start_time = _parse_datetime(date_str, time_str)
    return True, "", normalized_title, normalized_description, start_time


def _resolve_channel(
    guild: discord.Guild, channel_name: Optional[str]
) -> Optional[discord.TextChannel]:
    if channel_name:
        lowered = channel_name.lstrip("#").lower()
        for channel in guild.text_channels:
            if channel.name.lower() == lowered:
                return channel
        return None

    for channel in guild.text_channels:
        if channel.name == "scheduled-events":
            return channel

    return guild.text_channels[0] if guild.text_channels else None


def add_event(
    guild: discord.Guild,
    channel: discord.TextChannel,
    title: str,
    description: Optional[str],
    date_str: str,
    time_str: str,
) -> Tuple[bool, str]:
    prepared, error, normalized_title, normalized_description, start_time = _prepare_event(
        title,
        description,
        date_str,
        time_str,
    )
    if not prepared or not start_time:
        return False, error

    repository.create_event(
        guild_id=guild.id,
        channel_id=channel.id,
        title=normalized_title,
        description=normalized_description,
        start_time=start_time,
    )
    return True, f"Scheduled event set for {date_str} at {time_str}!"


def list_events(guild: discord.Guild) -> List[repository.ScheduledEventRecord]:
    return repository.list_pending_events_by_guild(guild.id)


def delete_event_by_index(
    guild: discord.Guild, index: int
) -> Tuple[bool, str, Optional[repository.ScheduledEventRecord]]:
    record = repository.get_pending_event_by_index(guild.id, index)
    if not record:
        return False, "Invalid event number.", None

    deleted = repository.delete_event_by_id(record.id)
    if not deleted:
        return False, "Unable to delete event. Please try again.", None

    return True, "Event deleted.", deleted


def delete_all_events(guild: discord.Guild) -> Tuple[bool, str, int]:
    count = repository.delete_all_events_by_guild(guild.id)
    if count == 0:
        return False, "No scheduled events to delete.", 0
    return True, f"Deleted {count} scheduled event(s).", count


def modify_event_by_index(
    guild: discord.Guild,
    index: int,
    title: str,
    description: Optional[str],
    date_str: str,
    time_str: str,
    channel: discord.TextChannel,
) -> Tuple[bool, str, Optional[repository.ScheduledEventRecord]]:
    record = repository.get_pending_event_by_index(guild.id, index)
    if not record:
        return False, "Invalid event number.", None

    normalized_title = _normalize_title(title)
    normalized_description = _normalize_description(description)

    if not normalized_title:
        return False, "Please provide a non-empty title.", None

    valid, error = _validate_time(date_str, time_str)
    if not valid:
        return False, error, None

    start_time = _parse_datetime(date_str, time_str)

    updated = repository.update_event(
        event_id=record.id,
        start_time=start_time,
        title=normalized_title,
        description=normalized_description,
        channel_id=channel.id,
    )
    if not updated:
        return False, "Unable to update event. Please try again.", None

    refreshed = repository.get_pending_event_by_index(guild.id, index)
    return True, "Event updated.", refreshed

#endregion


#region Interaction Handlers

async def add_scheduled_event(
    ctx: discord.Interaction,
    date: str,
    time: str,
    title: str,
    message: str,
    channel_name: Optional[str] = None,
) -> None:
    if not ctx.guild:
        await send_user_message("This command can only be used in a server.", ctx=ctx, ephemeral=True)
        return

    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=True)

    channel = _resolve_channel(ctx.guild, channel_name)
    if not channel:
        await send_user_message("Unable to find a text channel for this event.", ctx=ctx, ephemeral=True)
        return

    prepared, error, normalized_title, normalized_description, start_time = _prepare_event(
        title,
        message,
        date,
        time,
    )
    if not prepared or not start_time or normalized_title is None or normalized_description is None:
        await send_user_message(error, ctx=ctx, ephemeral=True)
        return

    try:
        scheduled_event = await ctx.guild.create_scheduled_event(
            name=normalized_title,
            start_time=start_time,
            end_time=start_time + datetime.timedelta(hours=1),
            description=normalized_description or None,
            entity_type=discord.EntityType.external,
            location=channel.mention,
            privacy_level=discord.PrivacyLevel.guild_only,
        )
    except Exception:
        await send_user_message(
            "Failed to create the Discord scheduled event. Please try again.",
            ctx=ctx,
            ephemeral=True,
        )
        return

    repository.create_event(
        guild_id=ctx.guild.id,
        channel_id=channel.id,
        discord_event_id=scheduled_event.id,
        title=normalized_title,
        description=normalized_description,
        start_time=start_time,
    )

    await send_user_message(
        f"Scheduled event set for {date} at {time}!",
        ctx=ctx,
        ephemeral=False,
    )


async def list_scheduled_events(ctx: discord.Interaction) -> None:
    if not ctx.guild:
        await send_user_message("This command can only be used in a server.", ctx=ctx, ephemeral=True)
        return

    events = list_events(ctx.guild)
    if not events:
        await send_user_message("No scheduled events found.", ctx=ctx, ephemeral=True)
        return

    lines = []
    for index, record in enumerate(events, start=1):
        event_time = _parse_event_time(record.start_time)
        channel = ctx.guild.get_channel(record.channel_id)
        channel_label = f"#{channel.name}" if channel else "Unknown channel"
        lines.append(
            f"{index}. {event_time.strftime('%Y-%m-%d %H:%M')} - {record.title} ({channel_label})"
        )

    pages = paginate_lines(lines, page_size=10, header="Upcoming scheduled events")
    await send_paginated_message(ctx, pages, ephemeral=False)


async def delete_scheduled_event(ctx: discord.Interaction, nth_index: int) -> None:
    if not ctx.guild:
        await send_user_message("This command can only be used in a server.", ctx=ctx, ephemeral=True)
        return

    record = repository.get_pending_event_by_index(ctx.guild.id, nth_index)
    if not record:
        await send_user_message("Invalid event number.", ctx=ctx, ephemeral=True)
        return

    if record.discord_event_id:
        try:
            scheduled_event = await ctx.guild.fetch_scheduled_event(record.discord_event_id)
            await scheduled_event.delete()
        except Exception:
            await send_user_message(
                "Failed to delete the Discord scheduled event. Please try again.",
                ctx=ctx,
                ephemeral=True,
            )
            return

    success, response, _ = delete_event_by_index(ctx.guild, nth_index)
    await send_user_message(response, ctx=ctx, ephemeral=not success)


async def delete_all_scheduled_events(ctx: discord.Interaction) -> None:
    if not ctx.guild:
        await send_user_message("This command can only be used in a server.", ctx=ctx, ephemeral=True)
        return

    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=True)

    events = repository.list_pending_events_by_guild(ctx.guild.id)
    for record in events:
        if not record.discord_event_id:
            continue
        try:
            scheduled_event = await ctx.guild.fetch_scheduled_event(record.discord_event_id)
            await scheduled_event.delete()
        except Exception:
            await send_user_message(
                "Failed to delete one or more Discord scheduled events. Please try again.",
                ctx=ctx,
                ephemeral=True,
            )
            return

    success, response, _ = delete_all_events(ctx.guild)
    await send_user_message(response, ctx=ctx, ephemeral=not success)


async def modify_scheduled_event(
    ctx: discord.Interaction,
    nth_index: int,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
    new_title: Optional[str] = None,
    new_message: Optional[str] = None,
    new_channel_name: Optional[str] = None,
) -> None:
    if not ctx.guild:
        await send_user_message("This command can only be used in a server.", ctx=ctx, ephemeral=True)
        return

    record = repository.get_pending_event_by_index(ctx.guild.id, nth_index)
    if not record:
        await send_user_message("Invalid event number.", ctx=ctx, ephemeral=True)
        return

    event_time = _parse_event_time(record.start_time)
    date_value = new_date or event_time.strftime("%Y-%m-%d")
    time_value = new_time or event_time.strftime("%H:%M")
    title_value = new_title or record.title
    message_value = new_message or record.description

    channel = _resolve_channel(ctx.guild, new_channel_name) if new_channel_name else ctx.guild.get_channel(record.channel_id)
    if not channel:
        await send_user_message("Unable to find a text channel for this event.", ctx=ctx, ephemeral=True)
        return

    await update_scheduled_event(
        ctx,
        record,
        date_value,
        time_value,
        title_value,
        message_value,
        channel.name,
    )


def _parse_event_time(event_time_str: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(event_time_str)


async def update_scheduled_event(
    ctx: discord.Interaction,
    record: repository.ScheduledEventRecord,
    date_value: str,
    time_value: str,
    title_value: str,
    message_value: Optional[str],
    channel_name: Optional[str],
) -> None:
    if not ctx.guild:
        await send_user_message("This command can only be used in a server.", ctx=ctx, ephemeral=True)
        return

    channel = _resolve_channel(ctx.guild, channel_name) if channel_name else ctx.guild.get_channel(record.channel_id)
    if not channel:
        await send_user_message("Unable to find a text channel for this event.", ctx=ctx, ephemeral=True)
        return

    prepared, error, normalized_title, normalized_description, start_time = _prepare_event(
        title_value,
        message_value,
        date_value,
        time_value,
    )
    if not prepared or not start_time or normalized_title is None or normalized_description is None:
        await send_user_message(error, ctx=ctx, ephemeral=True)
        return

    if record.discord_event_id:
        try:
            scheduled_event = await ctx.guild.fetch_scheduled_event(record.discord_event_id)
            await scheduled_event.edit(
                name=normalized_title,
                start_time=start_time,
                end_time=start_time + datetime.timedelta(hours=1),
                description=normalized_description or None,
                entity_type=discord.EntityType.external,
                location=channel.mention,
                privacy_level=discord.PrivacyLevel.guild_only,
            )
        except Exception:
            await send_user_message(
                "Failed to update the Discord scheduled event. Please try again.",
                ctx=ctx,
                ephemeral=True,
            )
            return

    updated = repository.update_event(
        event_id=record.id,
        start_time=start_time,
        title=normalized_title,
        description=normalized_description,
        channel_id=channel.id,
    )
    if not updated:
        await send_user_message(
            "Unable to update event. Please try again.",
            ctx=ctx,
            ephemeral=True,
        )
        return

    await send_user_message("Event updated.", ctx=ctx, ephemeral=False)

#endregion
