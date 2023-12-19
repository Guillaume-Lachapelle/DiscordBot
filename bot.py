import os
from dotenv import load_dotenv
import discord
import messages
import music
import stocks
import ai
from discord import app_commands
import asyncio

#region Constants

# Load environment variables
load_dotenv()

# Bot's token
token = os.getenv('DISCORD_TOKEN')

# Discord client
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

#endregion


#region Helper Functions

# Get the default channel of the server
def get_default_channel(guild):
    for channel in guild.channels:
        if channel.name == 'general':
            return channel
        
# Return all the bot's commands dynamically
def get_commands():
    command_list = []
    for command in tree.get_commands():
        command_list.append(f"`/{command.name}` - {command.description}")
    return "The following commands are available:\n\n" + "\n".join(command_list)
        
#endregion


#region Slash Commands

@tree.command(name="sync", description="Syncs the bot's commands with the server")
async def sync(ctx):
    await ctx.response.send_message("Syncing commands... Please wait...")
    await tree.sync()
    await ctx.followup.send("Sync complete!")

@tree.command(name="help", description="Displays all the available commands with a description of each one")
async def help(ctx):
    await ctx.response.send_message(get_commands())
    
@tree.command(name="ping", description="Pings the bot to check if it is online")
async def ping(ctx):
    await ctx.response.send_message("Pong!")
    
@tree.command(name="rembg", description="Removes the background from an image")
async def rembg(ctx):
    await ctx.response.send_message("To process attachments, please use the command `!rembg` and send the image as an attachment.")
    
@tree.command(name="question", description="Ask a question and the bot will try to answer it")
async def question(ctx, question: str):
    try:
        await ctx.response.send_message("Generating response... Please wait...")
        response = await ai.generate_response(question)
        await ctx.followup.send(response)
    except Exception as e:
        await ctx.followup.send("Could not generate response. Please try again.")
    
@tree.command(name="generate-image", description="Generate an image based on a prompt")
async def generate_image(ctx, prompt: str):
    try:
        await ctx.response.send_message("Generating image... Please wait...")
        image = await ai.generate_image(prompt)
        await ctx.followup.send(image)
    except Exception as e:
        await ctx.followup.send("Could not generate image. Please try again.")
        
@tree.command(name="stock-ticker", description="Get the stock ticker of a company")
async def stock_ticker(ctx, company: str):
    try:
        await ctx.response.send_message("Getting stock ticker... Please wait...")
        ticker = await stocks.find_ticker(company)
        await ctx.followup.send(ticker)
    except Exception as e:
        await ctx.followup.send("Could not get stock ticker. Please try again.")
        
@tree.command(name="stock-info", description="Get historical information about a stock")
async def stock_info(ctx, ticker: str):
    try:
        await ctx.response.send_message("Getting stock information... Please wait...")
        await stocks.generate_data(ticker)
    except Exception as e:
            print(e)
            await ctx.followup.send('Could not get stock information. Please try again.')
    if os.path.exists('stocks.csv'):
        with open('stocks.csv', 'rb') as f:
            file = discord.File(f)
            await ctx.followup.send(file=file)
    if(os.path.exists('stocks.csv')):
            os.remove('stocks.csv')
            
@tree.command(name="play", description="Play a song")
async def play(ctx, song: str = None):
    try:
        await music.play(ctx, song)
    except Exception as e:
        print(e)
        await ctx.followup.send("Could not play the song. Please try again.")
        
@tree.command(name="queue", description="Add a song to the playlist")
async def queue(ctx, song: str):
    await music.queue_song(ctx, song)
    
@tree.command(name="clear", description="Clear the playlist")
async def clear(ctx):
    await music.clear_playlist(ctx)
    
@tree.command(name="playlist", description="Display the playlist")
async def playlist(ctx):
    await music.display_playlist(ctx)
    
@tree.command(name="pause", description="Pause the current song")
async def pause(ctx):
    await music.pause(ctx)
    
@tree.command(name="resume", description="Resume the current song")
async def resume(ctx):
    await music.resume(ctx)
    
@tree.command(name="skip", description="Skip the current song")
async def skip(ctx):
    await music.skip(ctx)
    
@tree.command(name="stop", description="Stop playing music, clear the playlist, and disconnect from the voice channel")
async def stop(ctx):
    await music.stop(ctx)

#endregion


#region Discord Events

@client.event
async def on_ready():
    asyncio.create_task(tree.sync())
    print(f"Logged in as \"{client.user.name}\"")
    print(f"ID: {client.user.id}")
    print('------')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
        
    if (client.user.name in message.content or (len(message.mentions) > 0 and message.mentions[0].name == client.user.name)) and not message.reference:
        await message.channel.send('Hello there! How can I help you? Type `!help` to see a list of commands.')
    
    # Delegate messages to messages.py
    try:
        await messages.process_message(client, message)
    except Exception as e:
        print(e)
        await message.channel.send("Could not process the message. Please try again.")
        return
    
@client.event
async def on_disconnect():
    await music.disconnect()
    
@client.event
async def on_voice_state_update(member, before, after):
    await music.process_voice_state_update(member, before, after, client)
    
@client.event
async def on_stop():
    await music.on_stop()
    
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
    await general_channel.send("Hello, I am a Discord bot! I am here to help with various tasks and provide information.\nTo get started, type `/help` to see a list of commands.")

#endregion


client.run(token)