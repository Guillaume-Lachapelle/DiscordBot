"""Image processing commands - Background removal."""

#region Imports

from rembg import remove
from PIL import Image
import os
import discord
import logging
from shared.error_helpers import send_error_message

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


#region Commands

# Remove background from image
async def handle_remove_background(message: discord.Message) -> None:
    """Handle remove background command from user message.
    
    Args:
        message: Discord message with image attachment
    """
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
        logger.exception("Error handling background removal")
        await send_error_message(message.channel, "remove the background")
        os.remove(attachment.filename)
        return

# Remove background from image
async def remove_background(image: str) -> None:
    """Remove background from an image file using rembg.
    
    Args:
        image: Path to image file
    """
    try:
        image_input = Image.open(image)
        output = remove(image_input)
        output.save("output.png")
        return
    except Exception as e:
        logger.exception("Error removing image background")
        return
    
#endregion
