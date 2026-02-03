"""Reminder commands cog - Schedule and manage reminders."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

import reminder_commands

#endregion


class ReminderCog(commands.Cog):
    """Reminder scheduling and management commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the ReminderCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="set-reminder", description="Set a reminder for a specified date and time (format: YYYY-MM-DD HH:MM)")
    @app_commands.describe(
        date="Date in YYYY-MM-DD format",
        time="Time in HH:MM (24-hour) format",
        title="Reminder title",
        message="Reminder message",
        channel_name="Optional channel name (defaults to #reminders if it exists; otherwise the first channel)"
    )
    async def set_reminder(self, interaction: discord.Interaction, date: str, time: str, title: str, message: str, channel_name: Optional[str] = None):
        """Create a reminder at the specified date and time.

        Args:
            interaction: Discord interaction context.
            date: Date in YYYY-MM-DD format.
            time: Time in HH:MM format.
            title: Reminder title.
            message: Reminder message.
            channel_name: Optional channel name override.
        """
        await reminder_commands.add_reminder(interaction, date, time, title, message, channel_name)
    
    @app_commands.command(name="list-reminders", description="List all upcoming reminders")
    async def list_reminders(self, interaction: discord.Interaction):
        """List all upcoming reminders.

        Args:
            interaction: Discord interaction context.
        """
        await reminder_commands.list_reminders(interaction)
    
    @app_commands.command(name="delete-reminder", description="Delete a specific reminder by its index")
    @app_commands.describe(index="Number of the reminder to delete")
    async def delete_reminder(self, interaction: discord.Interaction, index: int):
        """Delete a reminder by its index.

        Args:
            interaction: Discord interaction context.
            index: Reminder index.
        """
        await reminder_commands.delete_reminder(interaction, index)
    
    @app_commands.command(name="delete-all-reminders", description="Delete all reminders")
    async def delete_all_reminders(self, interaction: discord.Interaction):
        """Delete all reminders.

        Args:
            interaction: Discord interaction context.
        """
        await reminder_commands.delete_all_reminders(interaction)
    
    @app_commands.command(name="modify-reminder", description="Modify a specific reminder by its index. The fields you leave empty will remain unchanged")
    @app_commands.describe(
        index="Number of the reminder to modify",
        new_date="New date in YYYY-MM-DD format (optional)",
        new_time="New time in HH:MM (24-hour) format (optional)",
        new_title="New title (optional)",
        new_message="New message (optional)",
        new_channel_name="New channel name (optional)"
    )
    async def modify_reminder(self, interaction: discord.Interaction, index: int, new_date: Optional[str] = None, new_time: Optional[str] = None, new_title: Optional[str] = None, new_message: Optional[str] = None, new_channel_name: Optional[str] = None):
        """Modify a reminder by its index.

        Args:
            interaction: Discord interaction context.
            index: Reminder index.
            new_date: New date (optional).
            new_time: New time (optional).
            new_title: New title (optional).
            new_message: New message (optional).
            new_channel_name: New channel name (optional).
        """
        await reminder_commands.modify_reminder(interaction, index, new_date, new_time, new_title, new_message, new_channel_name)
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the ReminderCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(ReminderCog(bot))
