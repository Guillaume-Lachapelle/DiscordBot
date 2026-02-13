"""Music state management - per-guild playback state."""

#region Imports

import os
import time
import asyncio
import atexit
import shutil
from typing import Optional, Dict, List
import discord

#endregion


#region State Class


DOWNLOADS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))


class GuildMusicState:
    """Per-guild state for music playback."""

    def __init__(self) -> None:
        self.voice_client: Optional[discord.VoiceClient] = None
        self.filename: Optional[str] = None
        self.playlist: List[Dict[str, str]] = []
        self.last_play_channel: Optional[discord.TextChannel] = None
        self.current_song: Optional[Dict[str, str]] = None
        self.playback_task: Optional[asyncio.Task] = None

    def reset(self) -> None:
        self.voice_client = None
        self.filename = None
        self.playlist = []
        self.current_song = None
        self.last_play_channel = None
        self.playback_task = None


_guild_states: Dict[int, GuildMusicState] = {}


def get_guild_state(guild_id: int) -> GuildMusicState:
    if guild_id not in _guild_states:
        _guild_states[guild_id] = GuildMusicState()
    return _guild_states[guild_id]


def list_guild_states() -> List[GuildMusicState]:
    return list(_guild_states.values())


def reset_guild_state(guild_id: int) -> None:
    if guild_id in _guild_states:
        _guild_states[guild_id].reset()


def reset_all_states() -> None:
    for state in _guild_states.values():
        state.reset()


def get_download_dir(guild_id: int) -> str:
    path = os.path.join(DOWNLOADS_ROOT, str(guild_id))
    os.makedirs(path, exist_ok=True)
    return path


def cleanup_downloads_on_exit() -> None:
    if os.path.exists(DOWNLOADS_ROOT):
        shutil.rmtree(DOWNLOADS_ROOT, ignore_errors=True)


async def shutdown_all() -> None:
    for state in _guild_states.values():
        state.playlist.clear()
        if state.playback_task and not state.playback_task.done():
            state.playback_task.cancel()
        if state.voice_client:
            try:
                source = state.voice_client.source
                if state.voice_client.is_playing() or state.voice_client.is_paused():
                    state.voice_client.stop()
                if source is not None:
                    cleanup = getattr(source, "cleanup", None)
                    if callable(cleanup):
                        cleanup()
                    process = getattr(source, "process", None)
                    if process is not None and process.poll() is None:
                        process.terminate()
                        if process.poll() is None:
                            process.kill()
                try:
                    await asyncio.wait_for(
                        state.voice_client.disconnect(force=True),
                        timeout=2,
                    )
                except asyncio.TimeoutError:
                    pass
            except Exception:
                pass
        if state.filename and os.path.exists(state.filename):
            try:
                os.remove(state.filename)
            except Exception:
                pass
        state.reset()

    cleanup_downloads_on_exit()


atexit.register(cleanup_downloads_on_exit)

#endregion
