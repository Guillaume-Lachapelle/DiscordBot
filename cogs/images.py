"""Image commands cog - image processing tools."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import io

import image_commands
from shared.error_helpers import send_user_message

#endregion


class ImagesCog(commands.GroupCog, name="images", description="Image tools"):
    """Image processing commands."""

    def __init__(self, bot: commands.Bot):
        """Initialize the ImagesCog.

        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot

    #region Commands

    @app_commands.command(
        name="remove-background",
        description="Removes the background from an image",
    )
    @app_commands.describe(image="Image attachment to process")
    async def remove_background(self, interaction: discord.Interaction, image: discord.Attachment):
        """Remove the background from an attached image.

        Args:
            interaction: Discord interaction context.
            image: Image attachment to process.
        """
        try:
            if image.content_type and not image.content_type.startswith("image/"):
                await send_user_message("Please attach a valid image file.", ctx=interaction, ephemeral=True)
                return

            await interaction.response.defer()
            image_bytes = await image.read()
            output_bytes = image_commands.remove_background_bytes(image_bytes)
            filename = f"remove_background_{Path(image.filename).stem}.png"
            file = discord.File(io.BytesIO(output_bytes), filename=filename)
            await interaction.followup.send(file=file)
        except Exception:
            await send_user_message(
                "Sorry, I couldn't remove the background. Please try again.",
                ctx=interaction,
                ephemeral=True,
            )

    #endregion


async def setup(bot: commands.Bot):
    """Load the ImagesCog.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(ImagesCog(bot))
