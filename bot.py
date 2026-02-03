"""Discord bot entry point with Cogs architecture."""

#region Imports

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_LOG_LEVEL'] = 'ERROR'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from dotenv import load_dotenv
import discord
from discord.ext import commands
import logging
import asyncio

#endregion


#region Setup

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
_required_env_vars = {
    'DISCORD_TOKEN': 'Discord bot token',
    'GEMINI_API_KEY': 'Google Gemini API key',
    'YOUTUBE_API_KEY': 'YouTube Data API key'
}

_missing_vars = []
for var, description in _required_env_vars.items():
    if not os.getenv(var):
        _missing_vars.append(f"{var} ({description})")

if _missing_vars:
    print("ERROR: Missing required environment variables:")
    for var in _missing_vars:
        print(f"  - {var}")
    print("\nPlease add these to your .env file and restart the bot.")
    exit(1)

# Bot's token
token = os.getenv('DISCORD_TOKEN')

#endregion


#region Bot Initialization

# Discord client with Cogs
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Remove default help command to use custom one
bot.remove_command('help')

#endregion


#region Cog Loading

async def load_cogs():
    """Load all cog modules."""
    cogs = [
        'cogs.general',
        'cogs.music',
        'cogs.ai',
        'cogs.reminders',
        'cogs.polls',
        'cogs.events'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.exception(f"Failed to load cog {cog}: {e}")

#endregion


#region Main

async def main():
    """Initialize and run the bot."""
    async with bot:
        await load_cogs()
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass

#endregion
