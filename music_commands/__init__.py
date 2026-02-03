"""Music module for Discord bot - YouTube playback and queue management."""

#region Imports

from .commands import (
    play, queue_song, pause, resume, skip, stop, clear_playlist,
    display_playlist, get_playlist_string, swap, remove, restart,
    process_voice_state_update
)
from .state import state, MusicState, reset_state

#endregion


#region Exports

__all__ = [
    'play', 'queue_song', 'pause', 'resume', 'skip', 'stop',
    'clear_playlist', 'display_playlist', 'get_playlist_string',
    'swap', 'remove', 'restart', 'process_voice_state_update',
    'state', 'MusicState', 'reset_state'
]

#endregion
