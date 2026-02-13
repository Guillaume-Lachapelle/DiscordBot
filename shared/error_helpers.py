"""Shared error message helpers and validation checks."""

#region Imports

from typing import Any
import logging
import discord
from discord import app_commands

#endregion


#region Functions

logger = logging.getLogger(__name__)


async def send_user_message(message: str, *, ctx: Any = None, ephemeral: bool = False) -> None:
    """Safely send a message to an interaction or channel.

    Args:
        ctx: Discord interaction context
        message: Message to send
        ephemeral: Whether to send the message ephemerally
    """
    try:
        if hasattr(ctx, "response") and hasattr(ctx.response, "is_done") and ctx.response.is_done():
            await ctx.followup.send(message, ephemeral=ephemeral)
        elif hasattr(ctx, "response"):
            await ctx.response.send_message(message, ephemeral=ephemeral)
        elif hasattr(ctx, "channel"):
            await ctx.channel.send(message)
        elif hasattr(ctx, "send"):
            await ctx.send(message)
    except discord.NotFound:
        # Interaction expired; nothing to respond to.
        logger.debug("Interaction expired before response was sent")
    except Exception:
        logger.exception("Failed to send interaction response")
        if hasattr(ctx, "channel"):
            await ctx.channel.send(message)
        elif hasattr(ctx, "send"):
            await ctx.send(message)


async def check_voice_channel(ctx: discord.Interaction) -> bool:
    """Check if user is in a voice channel. Sends error message if not.

    Args:
        ctx: Discord interaction context

    Returns:
        True if user is in voice channel, False otherwise
    """
    if ctx.user.voice is None:
        message = "You must be in a voice channel to use this command."
        await send_user_message(message, ctx=ctx, ephemeral=True)
        return False
    return True


def guild_only():
    """Ensure a slash command runs in a guild, not DMs."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await send_user_message(
                "This command can only be used in a server.",
                ctx=interaction,
                ephemeral=True,
            )
            return False
        return True

    return app_commands.check(predicate)


#endregion
