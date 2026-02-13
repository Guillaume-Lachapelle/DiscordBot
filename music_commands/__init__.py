"""Music module for Discord bot - YouTube playback and queue management."""

#region Imports

from .commands import (
    play, queue_song, pause, resume, skip, stop, clear_playlist,
    display_playlist, get_playlist_string, swap, remove, restart,
    process_voice_state_update
)
from .state import get_guild_state, reset_guild_state, reset_all_states, shutdown_all

#endregion


#region Exports

__all__ = [
    'play', 'queue_song', 'pause', 'resume', 'skip', 'stop',
    'clear_playlist', 'display_playlist', 'get_playlist_string',
    'swap', 'remove', 'restart', 'process_voice_state_update',
    'get_guild_state', 'reset_guild_state', 'reset_all_states', 'shutdown_all'
]

#endregion
