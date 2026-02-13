"""Poll commands cog - Create polls with reactions."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands

from poll_commands import PollCreateModal
from shared.error_helpers import guild_only

#endregion


class PollCog(commands.GroupCog, name="polls", description="Polls"):
    """Poll creation commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the PollCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="create", description="Create a poll")
    @guild_only()
    async def create(self, interaction: discord.Interaction):
        """Open the poll creation modal."""
        await interaction.response.send_modal(PollCreateModal())
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the PollCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(PollCog(bot))
