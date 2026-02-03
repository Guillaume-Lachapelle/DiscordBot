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

from .state import state
from .helpers import (
    get_youtube_song, get_video_title, _cleanup_audio_file,
    _is_playing, _is_connected, _is_paused, _send_error
)
from shared.error_helpers import send_error_followup, send_error_message

#endregion


#region Setup

logger = logging.getLogger(__name__)
DOWNLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
            if from_play:
                await ctx.channel.send('Please enter a song name or YouTube URL.')
            else:
                await ctx.followup.send('Please enter a song name or YouTube URL.')
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
            if from_play:
                await ctx.channel.send("Please enter a valid YouTube URL.")
            else:
                await ctx.followup.send("Please enter a valid YouTube URL.")
            return
        else:
            # Get the search query from the message content
            result = await get_youtube_song(query)
            # Get the first video from the search results
            if result:
                playlist_entry = result
            else:
                logger.info("No YouTube results found for query: %s", query)
                await ctx.channel.send("Could not find a video with that name. Please try again.")
                return
        
        state.playlist.append(playlist_entry)
        if not from_play:
            await ctx.followup.send(f"Song `{playlist_entry['title']}` added to the playlist.")
    except Exception as e:
        logger.exception("Error adding song to playlist")
        await send_error_followup(ctx, "add the song to the playlist")
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
                channel = state.last_play_channels.get(member.guild.id)
                if channel is not None:
                    # Send a message to the channel
                    await channel.send(f"The bot has disconnected from voice channel `{before.channel.name}`")
                await _cleanup_audio_file(state.filename)
                state.reset()
            return

        # Check if the bot is connected to a voice channel
        if state.voice_client and state.voice_client.is_connected():
            channel = state.voice_client.channel

            # Check if the bot is alone in the voice channel
            if len(channel.members) == 1 and client.user in channel.members:
                # Stop and disconnect if playing or paused
                if state.voice_client.is_playing() or state.voice_client.is_paused():
                    state.voice_client.stop()
                await state.voice_client.disconnect()
                await _cleanup_audio_file(state.filename)
                state.reset()
        elif state.voice_client is not None and not state.voice_client.is_connected():
            state.reset()
    except Exception:
        logger.exception("Error handling voice state update")
        
# Play the next song in the playlist
async def handle_play(ctx: discord.Interaction) -> None:
    """Main playback loop - handles downloading, playing, and cleanup."""
    while state.playlist:
        # Get the voice channel the user is in
        voice_channel = ctx.user.voice.channel
        
        # Connect to the voice channel
        if not state.voice_client.is_connected():
            state.voice_client = await voice_channel.connect()
        # If the player is paused using the command /pause, I want this to wait until the /resume command is used
        while state.voice_client.is_paused() and state.playlist:
            await asyncio.sleep(1)
        await asyncio.sleep(2)
        state.current_song = state.playlist[0]
        video = state.playlist.pop(0)
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
                    lambda: stream.download(output_path=DOWNLOAD_DIR),
                ),
                timeout=BotConfig.DOWNLOAD_TIMEOUT_SECONDS,
            )
            state.filename = os.path.abspath(downloaded_path)
        except asyncio.TimeoutError:
            await send_error_message(ctx.channel, "download the song in time")
            continue
        except Exception:
            await send_error_message(ctx.channel, "download the song")
            continue
        await ctx.channel.send(f"▶️ Now playing `{state.current_song['title']}` in voice channel \"{state.voice_client.channel}\"")
        audio = discord.FFmpegPCMAudio(state.filename)

        # Play the audio
        state.voice_client.play(audio)
        # Wait for the audio to finish playing
        while (state.voice_client is not None) and state.voice_client.is_playing():
            await asyncio.sleep(1)
        
        # Clean up the file after playing (or skipping)
        if not state.voice_client.is_paused():
            await _cleanup_audio_file(state.filename)
        
    # Disconnect from the voice channel only when playlist is empty (after while loop ends)
    if (state.voice_client is not None) and not state.voice_client.is_paused() and (state.voice_client.is_playing() == False and state.voice_client.is_connected()):
        await state.voice_client.disconnect()
        state.voice_client = None
        state.current_song = None


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
    try:
        if state.voice_client and state.voice_client.is_connected():
            if state.voice_client.is_paused():
                response_messages.append(f"There is already a song that is paused in the voice channel \"{state.voice_client.channel}\". Please use the `/resume` command to resume the song or the `/queue` command to add it to the playlist. If you wish to stop the music and clear the playlist, use the `/stop` command.")
            else:
                response_messages.append(f"I am already playing a song in the voice channel \"{state.voice_client.channel}\". Please use the `/stop` command to stop the current song or use the `/queue` command to add it to the playlist.")
        # Check if the user specified a song
        elif not state.playlist and not song:
            response_messages.append('The playlist is empty. Please specify a song to play.')
        # Check if the bot is already in a voice channel
        elif state.voice_client and state.voice_client.is_connected():
            # Check if the bot is in the same voice channel as the user
            if state.voice_client.channel != ctx.user.voice.channel:
                response_messages.append('You are not in the same voice channel as me. Please join the same voice channel and try again.')
        else:
            # Connect to the voice channel if not already connected
            state.voice_client = await ctx.user.voice.channel.connect()
            
        if not response_messages:  # If there are no error messages
            if not state.playlist:
                # Send status before searching
                await ctx.followup.send("🎵 Searching for song... Please wait...")
                await queue_song(ctx, song, True)
            # Wait for queue_song to complete (playlist populated)
            while not state.playlist:
                await asyncio.sleep(1)
            state.last_play_channels[ctx.guild.id] = ctx.channel
            await handle_play(ctx)
        else:  # If there are error messages
            await ctx.followup.send("\n".join(response_messages))
    except Exception as e:
        logger.exception("Error playing song")
        if state.voice_client is not None and (state.voice_client.is_playing() == False or state.voice_client.is_connected()):
            await state.voice_client.disconnect()
            state.voice_client = None
        await _cleanup_audio_file(state.filename)
        await send_error_followup(ctx, "play the song")
        return
    
# Clear the playlist
async def clear_playlist(ctx: discord.Interaction) -> None:
    """Clear all songs from the playlist.
    
    Args:
        ctx: Discord context
    """
    try:
        state.playlist.clear()
        await ctx.response.send_message("Playlist cleared.")
    except Exception as e:
        logger.exception("Error clearing playlist")
        await _send_error(ctx, "clear the playlist")
        return
    
# Display the playlist
async def display_playlist(ctx: discord.Interaction) -> None:
    """Display the current playlist to the user.
    
    Args:
        ctx: Discord context
    """
    try:
        if not state.playlist:
            await ctx.response.send_message("The playlist is empty.")
            return
        playlist_string = get_playlist_string()
        await ctx.response.send_message(playlist_string)
    except Exception as e:
        logger.exception("Error displaying playlist")
        await _send_error(ctx, "display the playlist")
        return

# Get the playlist as a string
def get_playlist_string() -> str:
    """Get the current playlist as a formatted string.
    
    Returns:
        Formatted playlist string
    """
    if not state.playlist:
        return "Playlist is empty."
    playlist_string = "New playlist:\n"
    for i in range(len(state.playlist)):
        playlist_string += f"{i+1}. {state.playlist[i]['title']}\n"
    return playlist_string
    
# Pause the current song
async def pause(ctx: discord.Interaction) -> None:
    """Pause the currently playing song.
    
    Args:
        ctx: Discord context
    """
    try:
        if not _is_playing():
            await ctx.response.send_message("There is no song playing.")
            return
        if _is_paused():
            await ctx.response.send_message("The song is already paused.")
            return
        state.voice_client.pause()
        await ctx.response.send_message("Song paused.")
    except Exception as e:
        logger.exception("Error pausing song")
        await _send_error(ctx, "pause the song")
        return
    
# Resume the current song
async def resume(ctx: discord.Interaction) -> None:
    """Resume the paused song.
    
    Args:
        ctx: Discord context
    """
    try:
        if _is_paused():
            state.voice_client.resume()
            await ctx.response.send_message("Song resumed.")
            return
        elif _is_playing():
            await ctx.response.send_message("The song is not paused.")
            return
        else:
            await ctx.response.send_message("There is no song playing.")
            return
    except Exception as e:
        logger.exception("Error resuming song")
        await _send_error(ctx, "resume the song")
        return
    
# Skip the current song
async def skip(ctx: discord.Interaction) -> None:
    """Skip the current song and play the next one.
    
    Args:
        ctx: Discord context
    """
    try:
        if _is_playing():
            state.voice_client.stop()
            if state.playlist:
                await ctx.response.send_message("Song skipped. Playing next song... Please wait...")
            else:
                await ctx.response.send_message("Song skipped.")
                if state.voice_client:
                    await state.voice_client.disconnect()
            return
        else:
            await ctx.response.send_message("There is no song playing.")
            return
    except Exception as e:
        logger.exception("Error skipping song")
        await _send_error(ctx, "skip the song")
        return
    
# Stop playing music, clear the playlist, and disconnect from the voice channel
async def stop(ctx: discord.Interaction) -> None:
    """Stop playback, clear playlist, and disconnect from voice channel.
    
    Args:
        ctx: Discord context
    """
    try:
        if not _is_connected():
            await ctx.response.send_message("There is no song playing.")
            return
        #stop the audio and disconnect from the voice channel
        state.voice_client.stop()
        await state.voice_client.disconnect()
        if state.playlist:
            state.playlist.clear()
        await ctx.response.send_message("Music stopped. The playlist has been cleared.")
    except Exception as e:
        logger.exception("Error stopping music")
        await _send_error(ctx, "stop the music")
        return
    
async def swap(ctx: discord.Interaction, index1: int, index2: int) -> None:
    """Swap two songs in the playlist by index.
    
    Args:
        ctx: Discord context
        index1: First song index (1-based)
        index2: Second song index (1-based)
    """
    try:
        if not state.playlist:
            await ctx.response.send_message("The playlist is empty.")
            return

        if index1 < 1 or index1 > len(state.playlist) or index2 < 1 or index2 > len(state.playlist):
            await ctx.response.send_message("Please enter a valid song number from the playlist.")
            return
        index1 -= 1
        index2 -= 1
        temp = state.playlist[index1]
        state.playlist[index1] = state.playlist[index2]
        state.playlist[index2] = temp
        
        # Combine the swap message with the new playlist
        message = f"Swapped songs `{state.playlist[index1]['title']}` and `{state.playlist[index2]['title']}`.\n{get_playlist_string()}"
        await ctx.response.send_message(message)
    except Exception as e:
        logger.exception("Error swapping songs")
        await _send_error(ctx, "swap the songs")
        return
    
async def remove(ctx: discord.Interaction, index: int) -> None:
    """Remove a song from the playlist by index.
    
    Args:
        ctx: Discord context
        index: Song index (1-based)
    """
    try:
        if not state.playlist:
            await ctx.response.send_message("The playlist is empty.")
            return

        if index < 1 or index > len(state.playlist):
            await ctx.response.send_message("Please enter a valid song number from the playlist.")
            return
        index -= 1
        removed_song = state.playlist.pop(index)
        
        # Combine the removal message with the new playlist
        message = f"Removed song `{removed_song['title']}` from the playlist.\n{get_playlist_string()}"
        await ctx.response.send_message(message)
    except Exception as e:
        logger.exception("Error removing song")
        await _send_error(ctx, "remove the song")
        return
    
async def restart(ctx: discord.Interaction) -> None:
    """Restart the current song from the beginning.
    
    Args:
        ctx: Discord context
    """
    try:
        if state.voice_client is None or not state.voice_client.is_playing() and not state.voice_client.is_paused():
            await ctx.response.send_message("There is no song playing.")
            return
        elif state.voice_client.is_paused():
            await ctx.response.send_message("The song is paused. Please use the `/resume` command to resume the song and then the `/restart` command to restart it.")
            return
        state.voice_client.stop()
        # Create a discord.FFmpegPCMAudio object to play the audio
        audio = discord.FFmpegPCMAudio(f"{state.filename}")

        # Play the audio
        state.voice_client.play(audio)
        await ctx.response.send_message("Song restarting... Please wait...")
    except Exception as e:
        logger.exception("Error restarting song")
        await _send_error(ctx, "restart the song")
        return

#endregion
