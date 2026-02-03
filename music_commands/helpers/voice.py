"""Voice client state helpers."""

#region Imports

from ..state import state

#endregion


#region Functions


def _is_playing() -> bool:
    """Check if the voice client is currently playing.
    
    Returns:
        True if playing, False otherwise
    """
    return state.voice_client is not None and state.voice_client.is_playing()


def _is_connected() -> bool:
    """Check if the voice client is connected to a voice channel.
    
    Returns:
        True if connected, False otherwise
    """
    return state.voice_client is not None and state.voice_client.is_connected()


def _is_paused() -> bool:
    """Check if the voice client is paused.
    
    Returns:
        True if paused, False otherwise
    """
    return state.voice_client is not None and state.voice_client.is_paused()

#endregion
