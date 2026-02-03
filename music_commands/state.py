"""Music state management - Centralized state class for music playback."""

#region Imports

import os
import time
import atexit
from typing import Optional, Dict, List
import discord

#endregion


#region State Class


class MusicState:
    """Centralized state management for music playback.
    
    Attributes:
        voice_client: Current voice client connection.
        filename: Path to currently downloaded audio file.
        playlist: Queue of songs to play.
        last_play_channels: Map of guild IDs to last play command channels.
        current_song: Currently playing song metadata.
    """
    
    def __init__(self):
        """Initialize empty music state."""
        self.voice_client: Optional[discord.VoiceClient] = None
        self.filename: Optional[str] = None
        self.playlist: List[Dict[str, str]] = []
        self.last_play_channels: Dict[int, discord.TextChannel] = {}
        self.current_song: Optional[Dict[str, str]] = None
    
    def reset(self) -> None:
        """Reset all state variables to initial values."""
        self.voice_client = None
        self.filename = None
        self.playlist = []
        self.current_song = None
    
    def delete_file_on_exit(self) -> None:
        """Delete the last downloaded audio file on shutdown."""
        if self.filename and os.path.exists(self.filename):
            time.sleep(1)
            os.remove(self.filename)


# Global singleton instance - import this in other modules
state = MusicState()

# Register cleanup on exit
atexit.register(state.delete_file_on_exit)


# Backwards compatibility functions
def reset_state() -> None:
    """Reset all global state variables."""
    state.reset()


def delete_file_on_exit() -> None:
    """Delete the last downloaded audio file on shutdown."""
    state.delete_file_on_exit()

#endregion
