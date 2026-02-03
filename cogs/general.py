"""General commands cog - Help, ping, and sync commands."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands

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
    async def sync(self, interaction: discord.Interaction):
        """Sync slash commands to the server.

        Args:
            interaction: Discord interaction context.
        """
        try:
            await interaction.response.send_message("Syncing commands... Please wait...")
            await self.bot.tree.sync()
            await interaction.followup.send("Sync complete!")
        except Exception as e:
            await interaction.followup.send(f"Sync failed: {e}")
    
    @app_commands.command(name="help", description="Displays all the available commands with a description of each one")
    async def help(self, interaction: discord.Interaction):
        """Send the list of available commands.

        Args:
            interaction: Discord interaction context.
        """
        command_list = []
        for command in self.bot.tree.get_commands():
            command_list.append(f"`/{command.name}` - {command.description}")
        message = "The following commands are available:\n\n" + "\n".join(command_list)
        await interaction.response.send_message(message)
    
    @app_commands.command(name="ping", description="Pings the bot to check if it is online")
    async def ping(self, interaction: discord.Interaction):
        """Respond with a simple heartbeat message.

        Args:
            interaction: Discord interaction context.
        """
        await interaction.response.send_message("Pong!")
    
    @app_commands.command(name="rembg", description="Removes the background from an image")
    async def rembg(self, interaction: discord.Interaction):
        """Explain how to use the image background removal command.

        Args:
            interaction: Discord interaction context.
        """
        await interaction.response.send_message(
            "To process attachments, please use the command `!rembg` and send the image as an attachment."
        )
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the GeneralCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(GeneralCog(bot))
