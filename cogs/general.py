"""General commands cog - Help, ping, and sync commands."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
from shared.error_helpers import send_user_message

#endregion


class GeneralCog(commands.Cog):
    """General utility commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the GeneralCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="sync", description="Syncs the bot's commands with the server")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        """Sync slash commands to the server.

        Args:
            interaction: Discord interaction context.
        """
        try:
            await interaction.response.defer(ephemeral=True)
            synced = await self.bot.tree.sync(guild=None)
            await interaction.followup.send(
                f"Global sync complete ({len(synced)} commands).",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(f"Sync failed: {e}", ephemeral=True)

    @sync.error
    async def sync_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Provide a friendly error when non-admins try to use /sync."""
        if isinstance(error, app_commands.MissingPermissions):
            await send_user_message(
                "You need Administrator permission to use `/sync`.",
                ctx=interaction,
                ephemeral=True,
            )
            return
        raise error

    @app_commands.command(name="help", description="Displays all the available commands with a description of each one")
    async def help(self, interaction: discord.Interaction):
        """Send the list of available commands.

        Args:
            interaction: Discord interaction context.
        """
        command_list = []
        for command in self.bot.tree.walk_commands():
            if isinstance(command, app_commands.Group):
                continue
            if command.qualified_name in {"help", "ping", "sync"}:
                continue
            command_list.append(
                f"`/{command.qualified_name}` - {command.description}"
            )
        command_list.sort()
        message = "The following commands are available:\n\n" + "\n".join(command_list)
        await interaction.response.send_message(message)
    
    @app_commands.command(name="ping", description="Pings the bot to check if it is online")
    async def ping(self, interaction: discord.Interaction):
        """Respond with a simple heartbeat message.

        Args:
            interaction: Discord interaction context.
        """
        await interaction.response.send_message("Pong!", ephemeral=True)
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the GeneralCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(GeneralCog(bot))
