"""Shared error message helpers and validation checks."""

#region Imports

from typing import Any
import discord

#endregion


#region Functions


async def check_voice_channel(ctx: discord.Interaction) -> bool:
    """Check if user is in a voice channel. Sends error message if not.

    Args:
        ctx: Discord interaction context

    Returns:
        True if user is in voice channel, False otherwise
    """
    if ctx.user.voice is None:
        message = "You must be in a voice channel to use this command."
        try:
            if hasattr(ctx, "response") and hasattr(ctx.response, "is_done") and ctx.response.is_done():
                await ctx.followup.send(message)
            else:
                await ctx.response.send_message(message)
        except Exception:
            await ctx.channel.send(message)
        return False
    return True


async def send_error_followup(ctx: Any, action: str) -> None:
    """Send a consistent error message for a failed action.

    Args:
        ctx: Discord interaction context
        action: Action description (e.g., "play the song")
    """
    message = f"Sorry, I couldn't {action}. Please try again."
    try:
        if hasattr(ctx, "response") and hasattr(ctx.response, "is_done") and ctx.response.is_done():
            await ctx.followup.send(message)
        else:
            await ctx.response.send_message(message)
    except Exception:
        # Fallback if response already sent or unavailable
        await ctx.channel.send(message)


async def send_error_message(channel: Any, action: str) -> None:
    """Send a consistent error message to a channel.

    Args:
        channel: Discord channel
        action: Action description (e.g., "process that message")
    """
    await channel.send(f"Sorry, I couldn't {action}. Please try again.")

#endregion
