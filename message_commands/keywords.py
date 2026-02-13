"""Message processing and triggering."""

#region Imports

import random
import logging
import discord

#endregion

#region Setup

logger = logging.getLogger(__name__)

#endregion

#region Message Procesing

async def process_message(client: discord.Client, message: discord.Message) -> None:
    """Process incoming messages and respond to keywords.
    
    Args:
        client: Discord client
        message: Discord message object
    """
    content = message.content.lower()
    
    if 'http' in content:
        return
    
    if (client.user.name.lower() in content or (len(message.mentions) > 0 and message.mentions[0].name == client.user.name)) and ('fuck you' not in content) and ('legend' not in content) and not message.reference:
        await message.channel.send('Hello there! How can I help you? Type `/help` to see a list of commands.')
        return
    
    if any(keyword in content for keyword in ['haha','lmao']) and 'http' not in content:
        my_list_laughing = ["https://tenor.com/view/haha-kid-laugh-laughing-gif-10594705",
                            "https://tenor.com/view/lmao-dead-weak-lol-lmfao-gif-16296952",
                            "https://tenor.com/view/baby-toddler-laughing-laugh-toppling-gif-23850035"]
        await message.channel.send(random.choice(my_list_laughing))
        
#endregion