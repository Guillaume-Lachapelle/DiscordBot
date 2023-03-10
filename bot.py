import os
import atexit
import asyncio
import discord
import openai
import random
import googleapiclient.discovery
import pytube
import time

#region Constants

# Bot's token
token = '{you discord bot token}'

openai.api_key = "{your openai api key}"

YOUTUBE_API_KEY = '{your youtube api key}'

client = discord.Client(intents=discord.Intents.all())

# Keep track of the voice client
voice_client = None
filename = None

#endregion

#region atexit

# To be able to delete the music file when the bot is closed
def delete_file_on_exit():
    if os.path.exists(filename):
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
def get_youtube_song(message, query):
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

# Return all the bot's commands
def get_commands():
    return 'The following commands are available:\n\n\t`!help` - Displays this message\n\
    `@HelperBot` or `HelperBot` - I will send you a prompt asking how I can help you\n\
    `haha` or `lmao` - I will react with a laughing GIF\n\
    `!question` - Ask any question after this command and I will try to answer it\n\
    `!generate-image` - I will generate an image based on your prompt\n\
    `!play` - I will play the song you request (It may help to put the title inside "" quotations)\n\
    `!stop` - I will stop playing the song\n\
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
    
    if '!help' in content:
        await message.channel.send(get_commands())
    if (client.user.name in message.content or (len(message.mentions) > 0 and message.mentions[0].name == client.user.name)):
        await message.channel.send('Hello there! How can I help you? Type `!help` to see a list of commands.')
    if content.startswith('!question'):
        await message.channel.send('Generating response... Please wait...')
        response = generate_response(content[10:-1])
        await message.channel.send(response)
    if content.startswith('!generate-image'):
        await message.channel.send("Generating image... Please wait...")
        response = generate_image(content[16:-1])
        await message.channel.send(response)
    if ('haha' in content or 'lmao' in content) and 'http' not in content:
        my_list_laughing = [1,2,3]
        choice = random.choice(my_list_laughing)
        if choice == 1:
            await message.channel.send('https://tenor.com/view/haha-kid-laugh-laughing-gif-10594705')
        if choice == 2:
            await message.channel.send('https://tenor.com/view/lmao-dead-weak-lol-lmfao-gif-16296952')
        if choice == 3:
            await message.channel.send('https://tenor.com/view/baby-toddler-laughing-laugh-toppling-gif-23850035')
    if message.content.startswith("!play"):
        if voice_client is not None and voice_client.is_connected():
            await message.channel.send(f"I am already playing a song in the voice channel \"{voice_client.channel}\". Please use the `!stop` command to stop the current song.")
            return
        if message.author.voice is None:
            await message.channel.send('You are not in a voice channel. Please join a voice channel and try again.')
            return
        # Get the search query from the message content
        response = get_youtube_song(message, content[6:-1])
        # Get the first video from the search results
        if response["items"]:
            video_id = response["items"][0]["id"]["videoId"]
        else:
            print("No results found")
            await message.channel.send("Could not find a video with that name. Please try again.")
            return
        # Get the voice channel the user is in
        voice_channel = message.author.voice.channel
        # Connect to the voice channel\
        if voice_client is None or voice_client.is_connected() == False:
            voice_client = await voice_channel.connect()
        # Use pytube to download the audio from the YouTube video
        video = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}").streams.filter(only_audio=True).first()
        video.download(".")
        filename = video.default_filename
        await message.channel.send(f"Playing `{filename[0:-4]}` in voice channel \"{voice_client.channel}\"")
        
        # Create a discord.FFmpegPCMAudio object to play the audio
        audio = discord.FFmpegPCMAudio(f"{filename}")

        # Play the audio
        voice_client.play(audio)
        # Wait for the audio to finish playing
        while (voice_client is not None) and voice_client.is_playing():
            await asyncio.sleep(1)
        # Disconnect from the voice channel
        if (voice_client is not None) and (voice_client.is_playing() == False or voice_client.is_connected()):
            await voice_client.disconnect()
            voice_client = None
        
    elif message.content == "!stop":
        if voice_client is None:
            await message.channel.send('I am not playing a song.')
            return
        # Stop the audio and disconnect from the voice channel
        if voice_client:
            voice_client.stop()
            await voice_client.disconnect()
            voice_client = None
            
    if (voice_client is None) and (filename is not None) and os.path.exists(filename):
        try:
            time.sleep(1)
            os.remove(filename)
        except(PermissionError):
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
        if voice_client:
            voice_client.stop()
            # Disconnect from the voice channel
            await before.channel.voice_client.disconnect()
        if filename is not None and os.path.exists(filename):
            time.sleep(1)
            os.remove(filename)
    # If the member stopped playing the audio or left the voice channel
    if (before.channel is not None) and (after.channel is not None):
        if (member == client.user and (not after.channel)) or (before.channel and before.channel.id == after.channel.id):
            if voice_client:
                # Stop the audio
                voice_client.stop()
                # Disconnect from the voice channel
                await voice_client.disconnect()
            if filename is not None and os.path.exists(filename):
                time.sleep(1)
                os.remove(filename)
    if member == client.user:
        if before.channel is not None and after.channel is None:
            voice_client = None
            # The bot has left the voice channel, delete the file
            if os.path.exists(filename):
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