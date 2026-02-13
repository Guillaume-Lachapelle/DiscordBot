"""Scheduled event command handlers - thin wrappers for service layer."""

#region Imports

from typing import Optional
import discord

from . import service
from .scheduler import handle_scheduled_events

#endregion


#region Commands

__all__ = [
    "add_scheduled_event",
    "list_scheduled_events",
    "delete_scheduled_event",
    "delete_all_scheduled_events",
    "modify_scheduled_event",
    "initialize_storage",
    "handle_scheduled_events",
]


def initialize_storage() -> None:
    service.initialize_storage()


async def add_scheduled_event(
    ctx: discord.Interaction,
    date: str,
    time: str,
    title: str,
    message: str,
    channel_name: Optional[str] = None,
) -> None:
    await service.add_scheduled_event(ctx, date, time, title, message, channel_name)


async def list_scheduled_events(ctx: discord.Interaction) -> None:
    await service.list_scheduled_events(ctx)


async def delete_scheduled_event(ctx: discord.Interaction, nth_index: int) -> None:
    await service.delete_scheduled_event(ctx, nth_index)


async def delete_all_scheduled_events(ctx: discord.Interaction) -> None:
    await service.delete_all_scheduled_events(ctx)


async def modify_scheduled_event(
    ctx: discord.Interaction,
    nth_index: int,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
    new_title: Optional[str] = None,
    new_message: Optional[str] = None,
    new_channel_name: Optional[str] = None,
) -> None:
    await service.modify_scheduled_event(
        ctx,
        nth_index,
        new_date,
        new_time,
        new_title,
        new_message,
        new_channel_name,
    )

#endregion
