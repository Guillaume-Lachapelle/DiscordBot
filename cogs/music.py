"""Music commands cog - YouTube playback and queue management."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
import logging

import music_commands
from shared.error_helpers import send_error_followup, check_voice_channel
from shared.config import BotConfig

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


class MusicCog(commands.Cog):
    """Music playback commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the MusicCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="play", description="Play a song")
    @app_commands.checks.cooldown(BotConfig.MUSIC_COOLDOWN_RATE, BotConfig.MUSIC_COOLDOWN_PER_SECONDS)
    @app_commands.describe(song="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, song: str = None):
        """Play a song or queue the next one.

        Args:
            interaction: Discord interaction context.
            song: Song name or YouTube URL.
        """
        try:
            if not await check_voice_channel(interaction):
                return
            await music_commands.play(interaction, song)
        except Exception as e:
            logger.exception("Error playing song")
            await send_error_followup(interaction, "play the song")
    
    @app_commands.command(name="queue", description="Add a song to the playlist")
    @app_commands.checks.cooldown(BotConfig.MUSIC_COOLDOWN_RATE, BotConfig.MUSIC_COOLDOWN_PER_SECONDS)
    @app_commands.describe(song="Song name or YouTube URL")
    async def queue(self, interaction: discord.Interaction, song: str):
        """Queue a song to the playlist.

        Args:
            interaction: Discord interaction context.
            song: Song name or YouTube URL.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.queue_song(interaction, song)
    
    @app_commands.command(name="clear", description="Clear the playlist")
    async def clear(self, interaction: discord.Interaction):
        """Clear the music playlist.

        Args:
            interaction: Discord interaction context.
        """
        await music_commands.clear_playlist(interaction)
    
    @app_commands.command(name="playlist", description="Display the playlist")
    async def playlist(self, interaction: discord.Interaction):
        """Display the current playlist.

        Args:
            interaction: Discord interaction context.
        """
        await music_commands.display_playlist(interaction)
    
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        """Pause the current song.

        Args:
            interaction: Discord interaction context.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.pause(interaction)
    
    @app_commands.command(name="resume", description="Resume the current song")
    async def resume(self, interaction: discord.Interaction):
        """Resume the current song.

        Args:
            interaction: Discord interaction context.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.resume(interaction)
    
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skip the current song.

        Args:
            interaction: Discord interaction context.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.skip(interaction)
    
    @app_commands.command(name="stop", description="Stop playing music, clear the playlist, and disconnect from the voice channel")
    async def stop(self, interaction: discord.Interaction):
        """Stop playback and clear the playlist.

        Args:
            interaction: Discord interaction context.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.stop(interaction)
    
    @app_commands.command(name="swap", description="Swap two songs in the playlist")
    @app_commands.describe(index1="Number of the first song in the playlist", index2="Number of the second song in the playlist")
    async def swap(self, interaction: discord.Interaction, index1: int, index2: int):
        """Swap two songs in the playlist by index.

        Args:
            interaction: Discord interaction context.
            index1: First song index.
            index2: Second song index.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.swap(interaction, index1, index2)
    
    @app_commands.command(name="remove", description="Remove a song from the playlist")
    @app_commands.describe(index="Number of the song to remove from the playlist")
    async def remove(self, interaction: discord.Interaction, index: int):
        """Remove a song from the playlist by index.

        Args:
            interaction: Discord interaction context.
            index: Song index to remove.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.remove(interaction, index)
    
    @app_commands.command(name="restart", description="Restart the current song")
    async def restart(self, interaction: discord.Interaction):
        """Restart the current song from the beginning.

        Args:
            interaction: Discord interaction context.
        """
        if not await check_voice_channel(interaction):
            return
        await music_commands.restart(interaction)
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the MusicCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(MusicCog(bot))
