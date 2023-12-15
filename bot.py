import os
import atexit
import asyncio
import discord
import openai
import random
import googleapiclient.discovery
import pytube
import time
import stocks
from dotenv import load_dotenv
from rembg import remove
from PIL import Image

#region Constants

# Bot's token
# Load environment variables from .env file
load_dotenv()

# Bot's token
token = os.getenv('DISCORD_TOKEN')

# Currently expired. Openai free trial is over...
openai.api_key = os.getenv('OPENAI_API_KEY')

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

client = discord.Client(intents=discord.Intents.all())

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

# Get the default channel of the server
def get_default_channel(guild):
    for channel in guild.channels:
        if channel.name == 'general':
            return channel

# Use the GPT-3 API to generate a response to a message
def generate_response(message):
    model_engine = "text-davinci-002"
    prompt = (f"{message}\n")
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    message = completions.choices[0].text
    return message

# Use the openai API to generate an image
def generate_image(message):
    # Use DALL-E to generate the image
    response = openai.Image.create(
      model="image-alpha-001",
      prompt=message,
    )
    return response.data[0]['url']

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
async def queue_song(message, query):
    global playlist
    try:
        if message.author.voice is None:
            await message.channel.send('You are not in a voice channel. Please join a voice channel and try again.')
            return
        # Get the search query from the message content
        response = get_youtube_song(query)
        # Get the first video from the search results
        if response["items"]:
            video_id = response["items"][0]["id"]["videoId"]
            # retrieve the song title
            video_title = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}", use_oauth=True, allow_oauth_cache=True).title
            playlist_entry = {"id": video_id, "title": video_title}
            playlist.append(playlist_entry)
        else:
            print("No results found")
            await message.channel.send("Could not find a video with that name. Please try again.")
            return
        await message.channel.send("Song added to the playlist.")
    except Exception as e:
        print(e)
        await message.channel.send("Could not add the song to the playlist. Please try again.")
        return
    
# Remove background from image
def remove_background(image):
    image_input = Image.open(image)
    output = remove(image_input)
    output.save("output.png")

# Return all the bot's commands
def get_commands():
    return 'The following commands are available:\n\n\t`!help` - Displays this message\n\
    `@HelperBot` or `HelperBot` - I will send you a prompt asking how I can help you\n\
    `haha` or `lmao` - I will react with a laughing GIF\n\
    `!question` - Ask any question after this command and I will try to answer it\n\
    `!generate-image` - I will generate an image based on your prompt\n\
    `!stock-ticker` - I will return the ticker symbol of the stock you request\n\
    `!stock-info` - I will return the stock information of the stock you request\n\
    `!play` - I will play the song you request (It may help to put the title inside "" quotations)\n\
    `!stop` - I will stop playing the song and clear the music queue\n\
    `!queue` - I will queue the song and it will be played after the one playing is done\n\
    `!clear` - I will clear the music queue\n\
    `!playlist` - I will tell you how many songs are in queue\n\
    `!pause` - I will pause the song\n\
    `!resume` - I will resume the song\n\
    `!rembg` - I will remove the background from the image you attach\n\
    I will also make sure to greet you when you join the server!'
    
#endregion

#region Discord Events

@client.event
async def on_message(message):
    content = message.content.lower()
    if message.author == client.user:
        return
    
    global voice_client
    global filename
    global playlist
    
    if '!help' in content:
        await message.channel.send(get_commands())
    if (client.user.name in message.content or (len(message.mentions) > 0 and message.mentions[0].name == client.user.name)) and not message.reference:
        await message.channel.send('Hello there! How can I help you? Type `!help` to see a list of commands.')
    if content.startswith('!question'):
        await message.channel.send('Generating response... Please wait...')
        response = generate_response(content[10:])
        await message.channel.send(response)
    if content.startswith('!generate-image'):
        await message.channel.send("Generating image... Please wait...")
        response = generate_image(content[16:])
        await message.channel.send(response)
    if any(keyword in content for keyword in ['haha','lmao']) and 'http' not in content:
        my_list_laughing = ["https://tenor.com/view/haha-kid-laugh-laughing-gif-10594705",
                            "https://tenor.com/view/lmao-dead-weak-lol-lmfao-gif-16296952",
                            "https://tenor.com/view/baby-toddler-laughing-laugh-toppling-gif-23850035"]
        await message.channel.send(random.choice(my_list_laughing))
    if ('!stock-ticker' in content) and 'http' not in content:
        try:
            ticker = await stocks.find_ticker(content[14:])
            await message.channel.send(ticker)
        except:
            await message.channel.send('Could not find that stock. Please try again.')
    if ('!stock-info' in content) and 'http' not in content:
        try:
            await stocks.generate_data(content[12:])
        except Exception as e:
            print(e)
            await message.channel.send('Could not execute command.')
        if os.path.exists('stocks.csv'):
            with open('stocks.csv', 'rb') as f:
                file = discord.File(f)
                await message.channel.send(file=file)
        if(os.path.exists('stocks.csv')):
            os.remove('stocks.csv')
    if message.content.startswith("!play") and not message.content.startswith("!playlist"):
        try:
            if voice_client is not None and voice_client.is_connected() and voice_client.is_playing():
                if voice_client.is_paused():
                    await message.channel.send(f"There is already a song that is paused in the voice channel \"{voice_client.channel}\". Please use the `!resume` command to resume the song or the `!queue` command to add it to the playlist. If you wish to stop the music and clear the playlist, use the `!stop` command.")
                else:
                    await message.channel.send(f"I am already playing a song in the voice channel \"{voice_client.channel}\". Please use the `!stop` command to stop the current song or use the `!queue` command to add it to the playlist.")
                return
            if message.author.voice is None:
                await message.channel.send('You are not in a voice channel. Please join a voice channel and try again.')
                return
            if voice_client and voice_client.is_paused():
                await message.channel.send('I am currently paused. Please use the `!resume` command to resume the song.')
                return
            # Check if the playlist is empty
            if not playlist and content[6:] == "":
                await message.channel.send("Please enter a song name.")
                return
            if not playlist:
                await queue_song(message, content[6:])
            while playlist:
                # Get the voice channel the user is in
                voice_channel = message.author.voice.channel
                # Connect to the voice channel\
                if voice_client is None or voice_client.is_connected() == False:
                    voice_client = await voice_channel.connect()
                # If the player is paused using the command !pause, I want this to wait until the !resume command is used
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
                await message.channel.send(f"Playing `{filename[0:-4]}` in voice channel \"{voice_client.channel}\"")
                
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
        except Exception as e:
            print(e)
            if voice_client is not None and (voice_client.is_playing() == False or voice_client.is_connected()):
                await voice_client.disconnect()
                voice_client = None
            if os.path.exists(filename):
                os.remove(filename)
            await message.channel.send("Could not play the song. Please try again.")
            return
            
    if message.content.startswith("!queue"):
        await queue_song(message, content[7:])
        
    if message.content.startswith("!clear"):
        playlist.clear()
        await message.channel.send("The playlist has been cleared.")
    
    if message.content.startswith("!playlist"):
        if not playlist:
            await message.channel.send("The playlist is empty.")
        else:
            # Print the playlist titles and send as a single message
            playlist_string = ""
            for video in playlist:
                playlist_string += f"{video['title']}\n"
            await message.channel.send(f"The playlist contains {len(playlist)} song(s).\n {playlist_string}")
    
    if message.content.startswith("!pause"):
        try:
            if voice_client is not None and voice_client.is_playing():
                voice_client.pause()
                await message.channel.send("Music playback paused.")
            else:
                await message.channel.send("No song is currently playing.")
        except Exception as e:
            print(e)
            await message.channel.send("Could not pause the song. Please try again.")
            return
        
    if message.content.startswith("!resume"):
        try:
            if voice_client is not None and voice_client.is_paused():
                voice_client.resume()
                await message.channel.send("Music playback resumed.")
            elif voice_client is not None and voice_client.is_playing():
                await message.channel.send("Music playback is already resumed.")
            else:
                await message.channel.send("No song is currently paused.")
        except Exception as e:
            print(e)
            await message.channel.send("Could not resume the song. Please try again.")
            return
    
    if message.content.startswith("!skip"):
        try:
            if voice_client is not None and voice_client.is_playing():
                voice_client.stop()
                await message.channel.send("Song skipped.")
            else:
                await message.channel.send("No song is currently playing.")
        except Exception as e:
            print(e)
            await message.channel.send("Could not skip the song. Please try again.")
            return
        
    elif message.content == "!stop":
        if voice_client is None:
            await message.channel.send('I am not playing a song.')
            return
        # Stop the audio and disconnect from the voice channel
        if voice_client:
            voice_client.stop()
            await voice_client.disconnect()
            voice_client = None
            
        playlist.clear()
        await message.channel.send("Music stopped. The playlist has been cleared.")
            
    if (voice_client is None) and (filename is not None):
        try:
            time.sleep(1)
            current_directory = os.getcwd()
            files = os.listdir(current_directory)
            for file in files:
                if file.endswith(".mp4"):
                    os.remove(file)
        except(PermissionError):
            return
        
    if ('!rembg' in content) and 'http' not in content:
        try:
            if len(message.attachments) == 0:
                await message.channel.send("Please attach an image to your message.")
                return
            else:
                attachment = message.attachments[0]
                await attachment.save(attachment.filename)
                remove_background(attachment.filename)
                await message.channel.send(file=discord.File('output.png'))
                os.remove(attachment.filename)
                os.remove('output.png')
                return
        except Exception as e:
            print(e)
            await message.channel.send("Could not remove the background. Please try again.")
            os.remove(attachment.filename)
            return
        
@client.event
async def on_disconnect():
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
        
# In the on_voice_state_update event handler
@client.event
async def on_voice_state_update(member, before, after):
    global voice_client
    if before.channel is not None and (before.channel.members == [] or before.channel.members == [client.user]):
        if voice_client and not (voice_client.is_paused()):
            voice_client.stop()
            # Disconnect from the voice channel
            await voice_client.disconnect()
        if filename is not None and os.path.exists(filename) and not (voice_client.is_paused()):
            time.sleep(1)
            os.remove(filename)
    # If the member stopped playing the audio or left the voice channel
    if (before.channel is not None) and (after.channel is not None):
        if (member == client.user and (not after.channel)) or (before.channel and before.channel.id == after.channel.id):
            if voice_client and not (voice_client.is_paused()):
                # Stop the audio
                voice_client.stop()
                # Disconnect from the voice channel
                await voice_client.disconnect()
            if filename is not None and os.path.exists(filename) and not (voice_client.is_paused()):
                time.sleep(1)
                os.remove(filename)
    if member == client.user:
        if before.channel is not None and after.channel is None:
            voice_client = None
            # The bot has left the voice channel, delete the file
            if filename is not None and os.path.exists(filename) and voice_client and not (voice_client.is_paused()):
                time.sleep(1)
                os.remove(filename)

@client.event
async def on_ready():
    print(f"Logged in as \"{client.user.name}\"")
    print(f"ID: {client.user.id}")
    print('------')
        
@client.event
async def on_stop():
    global filename
    # Delete the song file if it exists
    if os.path.exists(filename):
        time.sleep(1)
        os.remove(filename)
        
@client.event
async def on_member_join(member):
    server = member.guild
    general_channel = get_default_channel(member.guild)
    embed=discord.Embed(title="Welcome!",description=f"{member.mention} Just Joined {server.name}!",color=0x00ff00)
    await general_channel.send(embed=embed)
    
@client.event
async def on_guild_join(guild):
    # Send a greeting message to the general channel
    general_channel = get_default_channel(guild)
    await general_channel.send("Hello, I am a Discord bot! I am here to help with various tasks and provide information.\nTo get started, type `!help` to see a list of commands.")
    
#endregion

client.run(token)