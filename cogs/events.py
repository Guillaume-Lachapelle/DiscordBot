"""Events cog - Discord event handlers."""

#region Imports

import discord
from discord.ext import commands
import logging

import message_commands
import music_commands
import scheduled_event_commands
from music_commands.state import list_guild_states
from music_commands.helpers import _cleanup_audio_file
from shared.error_helpers import send_user_message

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


class EventsCog(commands.Cog):
    """Discord event handlers."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the EventsCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Events
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Handle bot ready event and start background tasks."""
        try:
            logger.info("Syncing slash commands...")
            synced = await self.bot.tree.sync()
            logger.info(f"Synced {len(synced)} commands globally")
        except Exception:
            logger.exception("Failed to sync slash commands")
        
        print(f"Logged in as \"{self.bot.user.name}\"")
        print(f"ID: {self.bot.user.id}")
        print('------')

        scheduled_event_commands.initialize_storage()
        self.bot.loop.create_task(scheduled_event_commands.handle_scheduled_events(self.bot))
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle incoming messages for keyword commands.

        Args:
            message: Discord message.
        """
        # Ignore messages from the bot itself or replies from the bot
        if message.author == self.bot.user or (
            message.reference and 
            getattr(message.reference.resolved, "author", None) == self.bot.user
        ):
            return

        try:
            await message_commands.process_message(self.bot, message)
        except Exception as e:
            logger.exception("Error processing message")
            await send_user_message("Sorry, I couldn't process that message. Please try again.", ctx=message)
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        """Handle bot disconnect event and cleanup state."""
        try:
            for guild_state in list_guild_states():
                await _cleanup_audio_file(guild_state.filename)
                guild_state.reset()
        except Exception:
            logger.exception("Error cleaning up audio files on disconnect")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state updates and music cleanup.

        Args:
            member: Member whose voice state changed.
            before: Previous voice state.
            after: New voice state.
        """
        await music_commands.process_voice_state_update(member, before, after, self.bot)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send a welcome message when a new member joins.

        Args:
            member: New guild member.
        """
        general_channel = member.guild.system_channel
        if general_channel:
            embed = discord.Embed(
                title="Welcome!", 
                description=f"{member.mention} Just Joined {member.guild.name}!", 
                color=0x00ff00
            )
            await general_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Send a greeting message when the bot joins a guild.

        Args:
            guild: Discord guild.
        """
        general_channel = guild.system_channel
        if general_channel:
            await general_channel.send(
                "Hello, I am a Discord bot! I am here to help with various tasks and provide information.\n"
                "To get started, type `/help` to see a list of commands."
            )
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the EventsCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(EventsCog(bot))
