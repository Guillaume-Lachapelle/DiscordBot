from rembg import remove
from PIL import Image
import os
import discord
import sys

#region Commands

# Remove background from image
async def handle_remove_background(message):
    try:
        if len(message.attachments) == 0:
            await message.channel.send("Please attach an image to your message.")
            return
        else:
            attachment = message.attachments[0]
            await attachment.save(attachment.filename)
            await remove_background(attachment.filename)
            await message.channel.send(file=discord.File('output.png'))
            os.remove(attachment.filename)
            os.remove('output.png')
            return
    except Exception as e:
        print(e)
        await message.channel.send("Could not remove the background. Please try again.")
        os.remove(attachment.filename)
        return

# Remove background from image
async def remove_background(image):
    try:
        image_input = Image.open(image)
        output = remove(image_input)
        output.save("output.png")
        return
    except Exception as e:
        print(e)
        print("Error occurred at line:", sys.exc_info()[-1].tb_lineno)
        return
    
#endregion