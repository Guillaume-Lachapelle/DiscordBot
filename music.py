import os
from dotenv import load_dotenv
import googleapiclient.discovery
import time
import atexit
import pytube
import discord
import asyncio
import re

#region Constants

# Load environment variables
load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Keep track of the voice client
voice_client = None
filename = None
playlist = []

#endregion


#region atexit

# To be able to delete the music file when the bot is closed
def delete_file_on_exit():
    if filename and os.path.exists(filename):
        time.sleep(1)
        os.remove(filename)

atexit.register(delete_file_on_exit)

#endregion


#region Helper Functions

# Play a video on YouTube
def get_youtube_song(query):
    # Use the YouTube Data API to search for videos that match the query
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
        part="id",
        type="video",
        q=query,
        videoDefinition="high",
        maxResults=1,
        fields="items(id(videoId))"
        )
        response = request.execute()
        return response
    
# Queue a song to be played
async def queue_song(ctx, query, from_play = False):
    global playlist
    try:
        if ctx.user.voice is None:
            await ctx.response.send_message('You are not in a voice channel. Please join a voice channel and try again.')
            return
        
        # Check if the query is a YouTube link
        if re.match(r'^https?:\/\/(?:www\.)?youtube\.com\/watch\?v=[\w-]+$', query):
            video_id = query.split('=')[1]
            # Retrieve the song title
            video_title = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}", use_oauth=True, allow_oauth_cache=True).title
        else:
            # Get the search query from the message content
            response = get_youtube_song(query)
            # Get the first video from the search results
            if response["items"]:
                video_id = response["items"][0]["id"]["videoId"]
                # Retrieve the song title
                video_title = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}", use_oauth=True, allow_oauth_cache=True).title
            else:
                print("No results found")
                await ctx.channel.send("Could not find a video with that name. Please try again.")
                return
        
        playlist_entry = {"id": video_id, "title": video_title}
        playlist.append(playlist_entry)
        if from_play:
            await ctx.channel.send(f"Song `{video_title}` added to the playlist.")
        else:
            await ctx.response.send_message(f"Song `{video_title}` added to the playlist.")
    except Exception as e:
        print(e)
        await ctx.channel.send("Could not add the song to the playlist. Please try again.")
        return
    
# Delete the song file when the bot is disconnected
async def disconnect():
    global filename
    try:
        
        # Check if the file exists
        if os.path.exists(filename):
            # Delete the file
            time.sleep(1)
            os.remove(filename)
    except Exception as e:
        # Print an error message if the file couldn't be deleted
        print(f"Error deleting file: {e}")
        
# Process a voice state update
async def process_voice_state_update(member, before, after, client):
    # Check if the member who triggered the update is the bot itself
    if member == client.user:
        return

    # Get the bot's voice client
    global voice_client

    # Check if the bot is connected to a voice channel
    if voice_client and voice_client.is_connected():
        channel = voice_client.channel

        # Check if the bot is alone in the voice channel
        if len(channel.members) == 1 and client.user in channel.members:
            # Check if the bot is playing something
            if voice_client.is_playing():
                # Stop playing and disconnect
                voice_client.stop()
                await voice_client.disconnect()

                # Delete the file if it exists
                if filename is not None and os.path.exists(filename):
                    # Delete the file
                    time.sleep(1)
                    os.remove(filename)
            else:
                # Disconnect without stopping if not playing
                await voice_client.disconnect()
             
# Delete the song file when the bot is stopped   
async def on_stop():
    global filename
    # Delete the song file if it exists
    if os.path.exists(filename):
        time.sleep(1)
        os.remove(filename)
        
# Play the next song in the playlist
async def handle_play(ctx):
    global voice_client
    global filename
    global playlist
    
    while playlist:
        # Get the voice channel the user is in
        voice_channel = ctx.user.voice.channel
        # Connect to the voice channel\
        if voice_client is None or voice_client.is_connected() == False:
            voice_client = await voice_channel.connect()
        # If the player is paused using the command /pause, I want this to wait until the /resume command is used
        while voice_client.is_paused() and playlist:
            await asyncio.sleep(1)
        time.sleep(2)
        video = playlist.pop(0)
        video_id = video["id"]
        # Use pytube to download the audio from the YouTube video
        loop = asyncio.get_event_loop()
        video = await loop.run_in_executor(None, lambda: pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}", use_oauth=True, allow_oauth_cache=True).streams.filter(only_audio=True).first())
        await loop.run_in_executor(None, lambda: video.download("."))
        filename = video.default_filename
        await ctx.channel.send(f"Playing `{filename[0:-4]}` in voice channel \"{voice_client.channel}\"")
        
        # Create a discord.FFmpegPCMAudio object to play the audio
        audio = discord.FFmpegPCMAudio(f"{filename}")

        # Play the audio
        voice_client.play(audio)
        # Wait for the audio to finish playing
        while (voice_client is not None) and voice_client.is_playing():
            await asyncio.sleep(1)
        if os.path.exists(filename) and not voice_client.is_paused():
            os.remove(filename)
    # Disconnect from the voice channel
    if (voice_client is not None) and not voice_client.is_paused() and (voice_client.is_playing() == False or voice_client.is_connected()):
        await voice_client.disconnect()
        voice_client = None

#endregion


#region Commands

# Play a song
async def play(ctx, song):
    global voice_client
    global filename
    global playlist
    response_messages = []
    try:
        # Check if the user is in a voice channel
        if ctx.user.voice is None:
            response_messages.append('You are not in a voice channel. Please join a voice channel and try again.')
            return
        elif voice_client is not None and voice_client.is_connected() and voice_client.is_paused():
            if voice_client.is_paused():
                response_messages.append(f"There is already a song that is paused in the voice channel \"{voice_client.channel}\". Please use the `/resume` command to resume the song or the `/queue` command to add it to the playlist. If you wish to stop the music and clear the playlist, use the `/stop` command.")
            else:
                response_messages.append(f"I am already playing a song in the voice channel \"{voice_client.channel}\". Please use the `/stop` command to stop the current song or use the `/queue` command to add it to the playlist.")
        # Check if the user specified a song
        elif not playlist and not song:
            response_messages.append('The playlist is empty. Please specify a song to play.')
        # Check if the bot is already in a voice channel
        elif voice_client and voice_client.is_connected():
            # Check if the bot is in the same voice channel as the user
            if voice_client.channel != ctx.user.voice.channel:
                response_messages.append('You are not in the same voice channel as me. Please join the same voice channel and try again.')
        else:
            # Connect to the voice channel if not already connected
            voice_client = await ctx.user.voice.channel.connect()
            
        if not response_messages:  # If there are no error messages
            await ctx.response.send_message("Searching for song... Please wait...")
            if not playlist:
                await queue_song(ctx, song, True)
            while not playlist:
                await asyncio.sleep(1)
            await handle_play(ctx)
        else:  # If there are error messages
            await ctx.response.send_message("\n".join(response_messages))
    except Exception as e:
        print(e)
        if voice_client is not None and (voice_client.is_playing() == False or voice_client.is_connected()):
            await voice_client.disconnect()
            voice_client = None
        if filename is not None and os.path.exists(filename):
            os.remove(filename)
        await ctx.channel.send("Could not play the song. Please try again.")
        return
    
# Clear the playlist
async def clear_playlist(ctx):
    global playlist
    try:
        playlist.clear()
        await ctx.response.send_message("Playlist cleared.")
    except Exception as e:
        print(e)
        await ctx.response.send_message("Could not clear the playlist. Please try again.")
        return
    
# Display the playlist
async def display_playlist(ctx):
    global playlist
    try:
        if not playlist:
            await ctx.response.send_message("The playlist is empty.")
            return
        playlist_string = "Playlist:\n"
        for i in range(len(playlist)):
            playlist_string += f"{i+1}. {playlist[i]['title']}\n"
        await ctx.response.send_message(playlist_string)
    except Exception as e:
        print(e)
        await ctx.response.send_message("Could not display the playlist. Please try again.")
        return
    
# Pause the current song
async def pause(ctx):
    global voice_client
    try:
        if voice_client is None or not voice_client.is_playing():
            await ctx.response.send_message("There is no song playing.")
            return
        if voice_client.is_paused():
            await ctx.response.send_message("The song is already paused.")
            return
        voice_client.pause()
        await ctx.response.send_message("Song paused.")
    except Exception as e:
        print(e)
        await ctx.response.send_message("Could not pause the song. Please try again.")
        return
    
# Resume the current song
async def resume(ctx):
    global voice_client
    try:
        if voice_client is not None and voice_client.is_paused():
            voice_client.resume()
            await ctx.response.send_message("Song resumed.")
            return
        elif voice_client is not None and voice_client.is_playing():
            await ctx.response.send_message("The song is not paused.")
            return
        else:
            await ctx.response.send_message("There is no song playing.")
            return
    except Exception as e:
        print(e)
        await ctx.response.send_message("Could not resume the song. Please try again.")
        return
    
# Skip the current song
async def skip(ctx):
    global voice_client
    global filename
    global playlist
    try:
        if voice_client is not None and voice_client.is_playing():
            voice_client.stop()
            if playlist:
                await ctx.response.send_message("Song skipped. Playing next song...")
            else:
                await ctx.response.send_message("Song skipped.")
                if voice_client:
                    await voice_client.disconnect()
                # voice_client = None
            return
        else:
            await ctx.response.send_message("There is no song playing.")
            return
    except Exception as e:
        print(e)
        await ctx.response.send_message("Could not skip the song. Please try again.")
        return
    
# Stop playing music, clear the playlist, and disconnect from the voice channel
async def stop(ctx):
    global voice_client
    global filename
    global playlist
    try:
        if voice_client is None:
            await ctx.response.send_message("There is no song playing.")
            return
        #stop the audio and disconnect from the voice channel
        if voice_client:
            voice_client.stop()
            await voice_client.disconnect()
            # voice_client = None
        if playlist:
            playlist.clear()
        await ctx.response.send_message("Music stopped. The playlist has been cleared.")
    except Exception as e:
        print(e)
        await ctx.response.send_message("Could not stop playing music. Please try again.")
        return
    
#endregion