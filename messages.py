import random
import os
from rembg import remove
from PIL import Image
import images
import discord

#region Message Processing

async def process_message(client, message):
    content = message.content.lower()
    
    if 'http' in content:
        return
    
    if any(keyword in content for keyword in ['haha','lmao']) and 'http' not in content:
        my_list_laughing = ["https://tenor.com/view/haha-kid-laugh-laughing-gif-10594705",
                            "https://tenor.com/view/lmao-dead-weak-lol-lmfao-gif-16296952",
                            "https://tenor.com/view/baby-toddler-laughing-laugh-toppling-gif-23850035"]
        await message.channel.send(random.choice(my_list_laughing))
        
    if '!rembg' in content:
        try:
            if len(message.attachments) == 0:
                await message.channel.send("Please attach an image to your message.")
                return
            else:
                attachment = message.attachments[0]
                await attachment.save(attachment.filename)
                await images.remove_background(attachment.filename)
                await message.channel.send(file=discord.File('output.png'))
                os.remove(attachment.filename)
                os.remove('output.png')
                return
        except Exception as e:
            print(e)
            await message.channel.send("Could not remove the background. Please try again.")
            os.remove(attachment.filename)
            return
        
#endregion