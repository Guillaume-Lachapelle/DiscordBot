# DiscordBot - Experimenting with Python and APIs

This is a Discord bot built with Python and discord.py. It provides slash commands and message-based features for music, reminders, AI responses, stock lookup, polls, and image background removal.

## Features

- **Music Playback**: YouTube audio streaming with queue management (play, queue, pause, resume, skip, stop, swap, remove, restart)
- **Reminders**: Schedule notifications with date/time, list active reminders, modify or delete them
- **AI Responses**: Ask questions using Google Gemini with model fallback support
- **Polls**: Create polls with up to 10 options and reaction-based voting
- **Image Processing**: Remove backgrounds from images using rembg

## Architecture

- **Modular Design**: Commands organized by feature (music_commands, ai_commands, stock_commands, etc.)
- **Centralized Configuration**: Timeout and cooldown constants in `shared/config.py`
- **Robust Error Handling**: Consistent error messages with retry logic for API calls
- **State Management**: Music playback state managed through a singleton MusicState class
- **Type Safety**: PEP 484 type hints throughout the codebase
- **Logging**: Python logging module for debugging and monitoring

## Requirements

- Python 3.10+ (tested with Python 3.12)
- Discord bot token
- API keys for Gemini and YouTube Data API

## Setup

1. Create a virtual environment (recommended)
2. Install dependencies:
	- pip install -r requirements.txt
3. Create a .env file in the project root with the following:

	DISCORD_TOKEN=your_discord_bot_token
	GEMINI_API_KEY=your_gemini_api_key
	YOUTUBE_API_KEY=your_youtube_api_key

4. Run the bot:
	- python bot.py

## Auto-Start on Windows (Task Scheduler)

To have the bot automatically start when Windows boots (even when locked):

1. Copy `start_bot.example.bat` to `start_bot.bat`
2. Edit `start_bot.bat` and update the paths:
   - Set the bot folder path (e.g., `C:\YourPath\DiscordBotPython`)
   - Set the full path to `python.exe` (find it with `where.exe python`)
3. Open Task Scheduler (`Win + R`, type `taskschd.msc`)
4. Create a new task with these settings:
   - **General Tab:**
     - Name: `Discord Bot`
     - Select "Run whether user is logged on or not"
     - Check "Run with highest privileges"
   - **Triggers Tab:**
     - New trigger: "At startup"
     - Delay task for 30 seconds
   - **Actions Tab:**
     - Action: "Start a program"
     - Program/script: Full path to your `start_bot.bat` file
   - **Settings Tab:**
     - Check "Allow task to be run on demand"
     - Check "If the task fails, restart every: 1 minute"
     - Uncheck "Stop the task if it runs longer than..."
5. Save the task (you'll need to enter your Windows password, not PIN)
6. Test by right-clicking the task and selecting "Run"

**Note:** The `start_bot.bat` file is gitignored since it contains system-specific paths.

## Commands

### General
- /help
- /ping

### AI
- /question

### Music
- /play
- /queue
- /clear
- /playlist
- /pause
- /resume
- /skip
- /stop
- /swap
- /remove
- /restart

### Reminders
- /set-reminder
- /list-reminders
- /modify-reminder
- /delete-reminder
- /delete-all-reminders

### Polls
- /poll

### Images
- !rembg (message command with an image attachment)

## Notes

- The .env file is ignored by git to protect API keys.
- Some commands are rate-limited to prevent spam.
- Music commands require being in a voice channel.
