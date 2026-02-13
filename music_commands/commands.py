"""Music command handlers - Play, queue, control, and playlist management."""

#region Imports

import discord
import asyncio
import re
import logging
import os
from typing import Optional
import pytubefix as pytube
from shared.config import BotConfig
from shared.pagination import paginate_lines, send_paginated_message

from .state import get_guild_state, get_download_dir
from .helpers import (
    get_youtube_song, get_video_title, _cleanup_audio_file,
    _is_playing, _is_connected, _is_paused
)
from shared.error_helpers import send_user_message

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


#region Commands

# Queue a song to be played
async def queue_song(ctx: discord.Interaction, query: str, from_play: bool = False) -> None:
    """Add a song to the playlist by query or YouTube link.
    
    Args:
        ctx: Discord context
        query: Song name or YouTube URL
        from_play: Whether called from play command
    """
    try:
        # Defer response if not called from play command
        if not from_play:
            await ctx.response.defer()
            
        if not query or not str(query).strip():
            await send_user_message('Please enter a song name or YouTube URL.', ctx=ctx, ephemeral=True)
            return
        
        # Check if the query is a YouTube link
        if re.match(r'^https?:\/\/(?:www\.)?youtube\.com\/watch\?v=[\w-]+$', query):
            video_id = query.split('=')[1]
            # Retrieve the song title
            video_title = await get_video_title(video_id)
            playlist_entry = {"id": video_id, "title": video_title}
        elif re.match(r'^https?:\/\/youtu\.be\/[\w-]+$', query):
            video_id = query.split('/')[-1]
            video_title = await get_video_title(video_id)
            playlist_entry = {"id": video_id, "title": video_title}
        elif query.strip().startswith("http"):
            await send_user_message("Please enter a valid YouTube URL.", ctx=ctx, ephemeral=True)
            return
        else:
            # Get the search query from the message content
            result = await get_youtube_song(query)
            # Get the first video from the search results
            if result:
                playlist_entry = result
            else:
                logger.info("No YouTube results found for query: %s", query)
                await send_user_message("Could not find a video with that name. Please try again.", ctx=ctx, ephemeral=True)
                return
        
        guild_state = get_guild_state(ctx.guild.id)
        guild_state.playlist.append(playlist_entry)
        if not from_play:
            await ctx.followup.send(f"Song `{playlist_entry['title']}` added to the playlist.")
    except Exception as e:
        logger.exception("Error adding song to playlist")
        await send_user_message("Sorry, I couldn't add the song to the playlist. Please try again.", ctx=ctx, ephemeral=True)
        return
    
# Process a voice state update
async def process_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
    client: discord.Client,
) -> None:
    """Handle voice state changes to detect disconnects and bot isolation."""
    try:
        # Check if the member who triggered the update is the bot itself
        if member == client.user:
            # Check if the bot was connected to a voice channel before the update, but not after the update
            if before.channel is not None and after.channel is None:
                # Get the channel where the "/play" command was last used in the guild
                guild_state = get_guild_state(member.guild.id)
                channel = guild_state.last_play_channel
                if channel is not None:
                    # Send a message to the channel
                    await channel.send(f"The bot has disconnected from voice channel `{before.channel.name}`")
                await _cleanup_audio_file(guild_state.filename)
                guild_state.reset()
            return

        # Check if the bot is connected to a voice channel
        guild_state = get_guild_state(member.guild.id)
        if guild_state.voice_client and guild_state.voice_client.is_connected():
            channel = guild_state.voice_client.channel

            # Check if the bot is alone in the voice channel
            if len(channel.members) == 1 and client.user in channel.members:
                # Stop and disconnect if playing or paused
                if guild_state.voice_client.is_playing() or guild_state.voice_client.is_paused():
                    guild_state.voice_client.stop()
                await guild_state.voice_client.disconnect()
                await _cleanup_audio_file(guild_state.filename)
                guild_state.reset()
        elif guild_state.voice_client is not None and not guild_state.voice_client.is_connected():
            guild_state.reset()
    except Exception:
        logger.exception("Error handling voice state update")
        
# Play the next song in the playlist
async def handle_play(ctx: discord.Interaction, guild_state, download_dir: str) -> None:
    """Main playback loop - handles downloading, playing, and cleanup."""
    try:
        while guild_state.playlist:
            # Get the voice channel the user is in
            voice_channel = ctx.user.voice.channel
            
            # Connect to the voice channel
            if not guild_state.voice_client.is_connected():
                guild_state.voice_client = await voice_channel.connect()
            # If the player is paused using the command /pause, I want this to wait until the /resume command is used
            while guild_state.voice_client.is_paused() and guild_state.playlist:
                await asyncio.sleep(1)
            await asyncio.sleep(2)
            guild_state.current_song = guild_state.playlist[0]
            video = guild_state.playlist.pop(0)
            video_id = video["id"]
            # Use pytube to download the audio from the YouTube video
            loop = asyncio.get_event_loop()
            
            try:
                stream = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}")
                        .streams.filter(only_audio=True)
                        .first(),
                    ),
                    timeout=BotConfig.DOWNLOAD_TIMEOUT_SECONDS,
                )
                downloaded_path = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: stream.download(output_path=download_dir),
                    ),
                    timeout=BotConfig.DOWNLOAD_TIMEOUT_SECONDS,
                )
                guild_state.filename = os.path.abspath(downloaded_path)
            except asyncio.TimeoutError:
                await send_user_message("Sorry, I couldn't download the song in time. Please try again.", ctx=ctx, ephemeral=True)
                continue
            except Exception:
                logger.exception("Error downloading audio for video %s", video_id)
                await send_user_message("Sorry, I couldn't download the song. Please try again.", ctx=ctx, ephemeral=True)
                continue
            await ctx.channel.send(f"▶️ Now playing `{guild_state.current_song['title']}` in voice channel \"{guild_state.voice_client.channel}\"")
            audio = discord.FFmpegPCMAudio(guild_state.filename)

            # Play the audio
            guild_state.voice_client.play(audio)
            # Wait for the audio to finish playing
            while (guild_state.voice_client is not None) and guild_state.voice_client.is_playing():
                await asyncio.sleep(1)
            
            # Clean up the file after playing (or skipping)
            if not guild_state.voice_client.is_paused():
                await _cleanup_audio_file(guild_state.filename)
            
        # Disconnect from the voice channel only when playlist is empty (after while loop ends)
        if (guild_state.voice_client is not None) and not guild_state.voice_client.is_paused() and (guild_state.voice_client.is_playing() == False and guild_state.voice_client.is_connected()):
            await guild_state.voice_client.disconnect()
            guild_state.voice_client = None
            guild_state.current_song = None
    except asyncio.CancelledError:
        guild_state.playlist.clear()
        raise


# Play a song
async def play(ctx: discord.Interaction, song: Optional[str]) -> None:
    """Play a song from YouTube - main command handler.
    
    Args:
        ctx: Discord context
        song: Song name or YouTube URL
    """
    # Defer the response immediately to prevent timeout
    await ctx.response.defer()
    
    response_messages = []
    guild_state = get_guild_state(ctx.guild.id)
    download_dir = get_download_dir(ctx.guild.id)
    try:
        if guild_state.voice_client and guild_state.voice_client.is_connected():
            if guild_state.voice_client.is_paused():
                response_messages.append(f"There is already a song that is paused in the voice channel \"{guild_state.voice_client.channel}\". Please use the `/resume` command to resume the song or the `/queue` command to add it to the playlist. If you wish to stop the music and clear the playlist, use the `/stop` command.")
            else:
                response_messages.append(f"I am already playing a song in the voice channel \"{guild_state.voice_client.channel}\". Please use the `/stop` command to stop the current song or use the `/queue` command to add it to the playlist.")
        # Check if the user specified a song
        elif not guild_state.playlist and not song:
            response_messages.append('The playlist is empty. Please specify a song to play.')
        # Check if the bot is already in a voice channel
        elif guild_state.voice_client and guild_state.voice_client.is_connected():
            # Check if the bot is in the same voice channel as the user
            if guild_state.voice_client.channel != ctx.user.voice.channel:
                response_messages.append('You are not in the same voice channel as me. Please join the same voice channel and try again.')
        else:
            # Connect to the voice channel if not already connected
            guild_state.voice_client = await ctx.user.voice.channel.connect()
            
        if not response_messages:  # If there are no error messages
            if not guild_state.playlist:
                # Send status before searching
                await ctx.followup.send("🎵 Searching for song... Please wait...")
                await queue_song(ctx, song, True)
            # Wait for queue_song to complete (playlist populated)
            while not guild_state.playlist:
                await asyncio.sleep(1)
            guild_state.last_play_channel = ctx.channel
            if guild_state.playback_task and not guild_state.playback_task.done():
                await ctx.followup.send("Playback is already running in this server.")
            else:
                guild_state.playback_task = asyncio.create_task(
                    handle_play(ctx, guild_state, download_dir)
                )
        else:  # If there are error messages
            await ctx.followup.send("\n".join(response_messages), ephemeral=True)
    except Exception as e:
        logger.exception("Error playing song")
        if guild_state.voice_client is not None and (guild_state.voice_client.is_playing() == False or guild_state.voice_client.is_connected()):
            await guild_state.voice_client.disconnect()
            guild_state.voice_client = None
        await _cleanup_audio_file(guild_state.filename)
        await send_user_message("Sorry, I couldn't play the song. Please try again.", ctx=ctx, ephemeral=True)
        return
    
# Clear the playlist
async def clear_playlist(ctx: discord.Interaction) -> None:
    """Clear all songs from the playlist.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        guild_state.playlist.clear()
        await ctx.response.send_message("Playlist cleared.")
    except Exception as e:
        logger.exception("Error clearing playlist")
        await send_user_message("Sorry, I couldn't clear the playlist. Please try again.", ctx=ctx, ephemeral=True)
        return
    
# Display the playlist
async def display_playlist(ctx: discord.Interaction) -> None:
    """Display the current playlist to the user.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if not guild_state.playlist:
            await ctx.response.send_message("The playlist is empty.", ephemeral=True)
            return

        lines = [f"{index + 1}. {entry['title']}" for index, entry in enumerate(guild_state.playlist)]
        pages = paginate_lines(lines, page_size=10, header="Current playlist")
        await send_paginated_message(ctx, pages, ephemeral=False)
    except Exception as e:
        logger.exception("Error displaying playlist")
        await send_user_message("Sorry, I couldn't display the playlist. Please try again.", ctx=ctx, ephemeral=True)
        return

# Get the playlist as a string
def get_playlist_string(guild_state) -> str:
    """Get the current playlist as a formatted string.
    
    Returns:
        Formatted playlist string
    """
    if not guild_state.playlist:
        return "Playlist is empty."
    playlist_string = "New playlist:\n"
    for i in range(len(guild_state.playlist)):
        playlist_string += f"{i+1}. {guild_state.playlist[i]['title']}\n"
    return playlist_string
    
# Pause the current song
async def pause(ctx: discord.Interaction) -> None:
    """Pause the currently playing song.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if not _is_playing(guild_state):
            await ctx.response.send_message("There is no song playing.", ephemeral=True)
            return
        if _is_paused(guild_state):
            await ctx.response.send_message("The song is already paused.", ephemeral=True)
            return
        guild_state.voice_client.pause()
        await ctx.response.send_message("Song paused.")
    except Exception as e:
        logger.exception("Error pausing song")
        await send_user_message("Sorry, I couldn't pause the song. Please try again.", ctx=ctx, ephemeral=True)
        return
    
# Resume the current song
async def resume(ctx: discord.Interaction) -> None:
    """Resume the paused song.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if _is_paused(guild_state):
            guild_state.voice_client.resume()
            await ctx.response.send_message("Song resumed.")
            return
        elif _is_playing(guild_state):
            await ctx.response.send_message("The song is not paused.", ephemeral=True)
            return
        else:
            await ctx.response.send_message("There is no song playing.", ephemeral=True)
            return
    except Exception as e:
        logger.exception("Error resuming song")
        await send_user_message("Sorry, I couldn't resume the song. Please try again.", ctx=ctx, ephemeral=True)
        return
    
# Skip the current song
async def skip(ctx: discord.Interaction) -> None:
    """Skip the current song and play the next one.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if _is_playing(guild_state):
            guild_state.voice_client.stop()
            if guild_state.playlist:
                await ctx.response.send_message("Song skipped. Playing next song... Please wait...")
            else:
                await ctx.response.send_message("Song skipped.")
                if guild_state.voice_client:
                    await guild_state.voice_client.disconnect()
            return
        else:
            await ctx.response.send_message("There is no song playing.", ephemeral=True)
            return
    except Exception as e:
        logger.exception("Error skipping song")
        await send_user_message("Sorry, I couldn't skip the song. Please try again.", ctx=ctx, ephemeral=True)
        return
    
# Stop playing music, clear the playlist, and disconnect from the voice channel
async def stop(ctx: discord.Interaction) -> None:
    """Stop playback, clear playlist, and disconnect from voice channel.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if not _is_connected(guild_state):
            await ctx.response.send_message("There is no song playing.", ephemeral=True)
            return
        #stop the audio and disconnect from the voice channel
        guild_state.voice_client.stop()
        await guild_state.voice_client.disconnect()
        if guild_state.playlist:
            guild_state.playlist.clear()
        await ctx.response.send_message("Music stopped. The playlist has been cleared.")
    except Exception as e:
        logger.exception("Error stopping music")
        await send_user_message("Sorry, I couldn't stop the music. Please try again.", ctx=ctx, ephemeral=True)
        return
    
async def swap(ctx: discord.Interaction, index1: int, index2: int) -> None:
    """Swap two songs in the playlist by index.
    
    Args:
        ctx: Discord context
        index1: First song index (1-based)
        index2: Second song index (1-based)
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if not guild_state.playlist:
            await ctx.response.send_message("The playlist is empty.", ephemeral=True)
            return

        if index1 < 1 or index1 > len(guild_state.playlist) or index2 < 1 or index2 > len(guild_state.playlist):
            await ctx.response.send_message("Please enter a valid song number from the playlist.", ephemeral=True)
            return
        index1 -= 1
        index2 -= 1
        temp = guild_state.playlist[index1]
        guild_state.playlist[index1] = guild_state.playlist[index2]
        guild_state.playlist[index2] = temp
        
        # Combine the swap message with the new playlist
        message = f"Swapped songs `{guild_state.playlist[index1]['title']}` and `{guild_state.playlist[index2]['title']}`.\n{get_playlist_string(guild_state)}"
        await ctx.response.send_message(message)
    except Exception as e:
        logger.exception("Error swapping songs")
        await send_user_message("Sorry, I couldn't swap the songs. Please try again.", ctx=ctx, ephemeral=True)
        return
    
async def remove(ctx: discord.Interaction, index: int) -> None:
    """Remove a song from the playlist by index.
    
    Args:
        ctx: Discord context
        index: Song index (1-based)
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if not guild_state.playlist:
            await ctx.response.send_message("The playlist is empty.", ephemeral=True)
            return

        if index < 1 or index > len(guild_state.playlist):
            await ctx.response.send_message("Please enter a valid song number from the playlist.", ephemeral=True)
            return
        index -= 1
        removed_song = guild_state.playlist.pop(index)
        
        # Combine the removal message with the new playlist
        message = f"Removed song `{removed_song['title']}` from the playlist.\n{get_playlist_string(guild_state)}"
        await ctx.response.send_message(message)
    except Exception as e:
        logger.exception("Error removing song")
        await send_user_message("Sorry, I couldn't remove the song. Please try again.", ctx=ctx, ephemeral=True)
        return
    
async def restart(ctx: discord.Interaction) -> None:
    """Restart the current song from the beginning.
    
    Args:
        ctx: Discord context
    """
    try:
        guild_state = get_guild_state(ctx.guild.id)
        if guild_state.voice_client is None or not guild_state.voice_client.is_playing() and not guild_state.voice_client.is_paused():
            await ctx.response.send_message("There is no song playing.", ephemeral=True)
            return
        elif guild_state.voice_client.is_paused():
            await ctx.response.send_message("The song is paused. Please use the `/resume` command to resume the song and then the `/restart` command to restart it.", ephemeral=True)
            return
        guild_state.voice_client.stop()
        # Create a discord.FFmpegPCMAudio object to play the audio
        audio = discord.FFmpegPCMAudio(f"{guild_state.filename}")

        # Play the audio
        guild_state.voice_client.play(audio)
        await ctx.response.send_message("Song restarting... Please wait...")
    except Exception as e:
        logger.exception("Error restarting song")
        await send_user_message("Sorry, I couldn't restart the song. Please try again.", ctx=ctx, ephemeral=True)
        return

#endregion
