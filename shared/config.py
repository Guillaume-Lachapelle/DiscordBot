"""Shared configuration constants for the bot."""

#region Imports

from dataclasses import dataclass

#endregion


#region Configuration


@dataclass(frozen=True)
class BotConfig:
    """Centralized configuration values for timeouts and cooldowns.

    Attributes:
        GENERATION_TIMEOUT_SECONDS: AI generation timeout in seconds.
        DOWNLOAD_TIMEOUT_SECONDS: Music download timeout in seconds.
        YOUTUBE_SEARCH_TIMEOUT_SECONDS: YouTube search timeout in seconds.
        YOUTUBE_TITLE_TIMEOUT_SECONDS: YouTube title lookup timeout in seconds.
        QUESTION_COOLDOWN_RATE: Max question requests per window.
        QUESTION_COOLDOWN_PER_SECONDS: Question cooldown window in seconds.
        MUSIC_COOLDOWN_RATE: Max music requests per window.
        MUSIC_COOLDOWN_PER_SECONDS: Music cooldown window in seconds.
    """

    # Timeouts (seconds)
    GENERATION_TIMEOUT_SECONDS: int = 20
    DOWNLOAD_TIMEOUT_SECONDS: int = 30
    YOUTUBE_SEARCH_TIMEOUT_SECONDS: int = 10
    YOUTUBE_TITLE_TIMEOUT_SECONDS: int = 10

    # Cooldowns (rate, per_seconds)
    QUESTION_COOLDOWN_RATE: int = 1
    QUESTION_COOLDOWN_PER_SECONDS: int = 15
    MUSIC_COOLDOWN_RATE: int = 2
    MUSIC_COOLDOWN_PER_SECONDS: int = 10

#endregion
