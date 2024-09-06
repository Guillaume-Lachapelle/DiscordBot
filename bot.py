import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
from dotenv import load_dotenv
import discord
import messages
import music
import stocks
import polls
import ai
import reminders
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
    try:
        await ctx.response.send_message("Syncing commands... Please wait...")
        await tree.sync()
        await ctx.followup.send("Sync complete!")
    except Exception as e:
        await ctx.followup.send(f"Sync failed: {e}")

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
    
@tree.command(name="poll", description="Create a poll")
async def poll(ctx, question: str, option1: str, option2: str, option3: str = None, option4: str = None, option5: str = None, option6: str = None, option7: str = None, option8: str = None, option9: str = None, option10: str = None):
    options = [option for option in (option1, option2, option3, option4, option5, option6, option7, option8, option9, option10) if option is not None]
    await polls.create_poll(ctx, question, options)
    
@tree.command(name="swap", description="Swap two songs in the playlist")
async def swap(ctx, index1: int, index2: int):
    await music.swap(ctx, index1, index2)
    
@tree.command(name="remove", description="Remove a song from the playlist")
async def remove(ctx, index: int):
    await music.remove(ctx, index)
    
@tree.command(name="restart", description="Restart the current song")
async def restart(ctx):
    await music.restart(ctx)
    
@tree.command(name="set-reminder", description="Set a reminder for a specified date and time (format: YYYY-MM-DD HH:MM)")
async def set_reminder(ctx, date: str, time: str, title: str, message: str, channel_name: str = None):
    await reminders.add_reminder(ctx, date, time, title, message, channel_name)
    
@tree.command(name="list-reminders", description="List all upcoming reminders")
async def view_reminders(ctx):
    await reminders.list_reminders(ctx)
    
@tree.command(name="delete-reminder", description="Delete a specific reminder by its index")
async def delete_reminder(ctx, index: int):
    await reminders.delete_reminder(ctx, index)
    
@tree.command(name="delete-all-reminders", description="Delete all reminders")
async def delete_all_reminders(ctx):
    await reminders.delete_all_reminders(ctx)
    
@tree.command(name="modify-reminder", description="Modify a specific reminder by its index. The fields you leave empty will remain unchanged")
async def modify_reminder(ctx, index: int, new_date: str = None, new_time: str = None, new_title: str = None, new_message: str = None, new_channel_name: str = None):
    await reminders.modify_reminder(ctx, index, new_date, new_time, new_title, new_message, new_channel_name)

#endregion


#region Discord Events

@client.event
async def on_ready():
    asyncio.create_task(tree.sync())
    print(f"Logged in as \"{client.user.name}\"")
    print(f"ID: {client.user.id}")
    print('------')
    client.loop.create_task(reminders.handle_reminders(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
        
    if (client.user.name in message.content or (len(message.mentions) > 0 and message.mentions[0].name == client.user.name)) and not message.reference:
        await message.channel.send('Hello there! How can I help you? Type `!help` to see a list of commands.')
    
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
    
# @client.event
# async def on_stop():
#     await music.on_stop()
    
@client.event
async def on_member_join(member):
    general_channel = member.guild.system_channel
    embed=discord.Embed(title="Welcome!",description=f"{member.mention} Just Joined {member.guild.name}!",color=0x00ff00)
    await general_channel.send(embed=embed)
    
@client.event
async def on_guild_join(guild):
    # Send a greeting message to the general channel
    general_channel = guild.system_channel
    await general_channel.send("Hello, I am a Discord bot! I am here to help with various tasks and provide information.\nTo get started, type `/help` to see a list of commands.")

#endregion


client.run(token)