"""Scheduled events cog - Schedule and manage scheduled events."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
import scheduled_event_commands
from scheduled_event_commands.ui import (
    ScheduledEventCreateModal,
    ScheduledEventSelectView,
)
from scheduled_event_commands import repository
from shared.config import BotConfig
from shared.error_helpers import guild_only

#endregion


class ScheduledEventCog(commands.GroupCog, name="events", description="Scheduled events"):
    """Scheduled event scheduling and management commands."""

    def __init__(self, bot: commands.Bot):
        """Initialize the ScheduledEventCog.

        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot

    #region Commands

    @app_commands.command(
        name="set",
        description="Set a scheduled event for a specified date and time",
    )
    @guild_only()
    @app_commands.checks.cooldown(
        BotConfig.SCHEDULED_EVENT_COOLDOWN_RATE,
        BotConfig.SCHEDULED_EVENT_COOLDOWN_PER_SECONDS,
    )
    async def set_event(self, interaction: discord.Interaction):
        """Create a scheduled event at the specified date and time.

        Args:
            interaction: Discord interaction context.
        """
        await interaction.response.send_modal(ScheduledEventCreateModal())

    @app_commands.command(
        name="list",
        description="List all upcoming scheduled events",
    )
    @guild_only()
    async def list_events(self, interaction: discord.Interaction):
        """List all upcoming scheduled events.

        Args:
            interaction: Discord interaction context.
        """
        await scheduled_event_commands.list_scheduled_events(interaction)

    @app_commands.command(
        name="delete",
        description="Delete a specific scheduled event by its index",
    )
    @guild_only()
    @app_commands.describe(index="Number of the scheduled event to delete")
    async def delete_event(self, interaction: discord.Interaction, index: int):
        """Delete a scheduled event by its index.

        Args:
            interaction: Discord interaction context.
            index: Scheduled event index.
        """
        await scheduled_event_commands.delete_scheduled_event(interaction, index)

    @app_commands.command(
        name="delete-all",
        description="Delete all scheduled events",
    )
    @guild_only()
    async def delete_all_events(self, interaction: discord.Interaction):
        """Delete all scheduled events.

        Args:
            interaction: Discord interaction context.
        """
        await scheduled_event_commands.delete_all_scheduled_events(interaction)

    @app_commands.command(
        name="modify",
        description="Modify a scheduled event using a modal",
    )
    @guild_only()
    async def modify_event(self, interaction: discord.Interaction):
        """Modify a scheduled event using a modal.

        Args:
            interaction: Discord interaction context.
        """
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        records = repository.list_pending_events_by_guild(interaction.guild.id)
        if not records:
            await interaction.response.send_message("No scheduled events found.", ephemeral=True)
            return

        view = ScheduledEventSelectView(records)
        await interaction.response.send_message(
            "Select the event you want to edit.",
            embed=view.build_embed(),
            view=view,
            ephemeral=True,
        )
        view.message = await interaction.original_response()

    #endregion


async def setup(bot: commands.Bot):
    """Load the ScheduledEventCog.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(ScheduledEventCog(bot))
