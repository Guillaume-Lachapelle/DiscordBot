"""YouTube API integration for music search and metadata."""

#region Imports

import os
import asyncio
import logging
import googleapiclient.discovery
import googleapiclient.errors
import pytubefix as pytube
from dotenv import load_dotenv
from shared.retry_helpers import run_with_retries
from shared.config import BotConfig

#endregion


#region Setup

# Load environment variables
load_dotenv()

_YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

logger = logging.getLogger(__name__)

#endregion


#region Functions

# Play a video on YouTube
async def get_youtube_song(query):
    """Search YouTube for a song and get video ID and title.
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with 'id' and 'title' keys, or None if not found
    """
    # Use the YouTube Data API to search for videos that match the query
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=_YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="id",
        type="video",
        q=query,
        videoDefinition="high",
        maxResults=1,
        fields="items(id(videoId))"
    )
    loop = asyncio.get_running_loop()
    try:
        response = await run_with_retries(
            lambda: asyncio.wait_for(
                loop.run_in_executor(None, request.execute),
                timeout=BotConfig.YOUTUBE_SEARCH_TIMEOUT_SECONDS,
            ),
            retries=2,
            delay_seconds=0.5,
            backoff=2.0,
            retry_exceptions=(asyncio.TimeoutError,),
        )
    except googleapiclient.errors.HttpError as e:
        status = e.resp.status if e.resp is not None else None
        if status in (403, 429):
            logger.warning("YouTube API rate limit hit for query: %s", query)
        else:
            logger.exception("YouTube API error for query: %s", query)
        return None
    except asyncio.TimeoutError:
        logger.warning("YouTube search timed out for query: %s", query)
        return None
    
    if response.get("items"):
        video_id = response["items"][0]["id"]["videoId"]
        video_title = await get_video_title(video_id)
        return {"id": video_id, "title": video_title}
    return None


# Get the title of a YouTube video
async def get_video_title(video_id):
    """Get the title of a YouTube video using pytube.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Video title string, or None if error occurs
    """
    try:
        loop = asyncio.get_running_loop()
        return await run_with_retries(
            lambda: asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}").title
                ),
                timeout=BotConfig.YOUTUBE_TITLE_TIMEOUT_SECONDS,
            ),
            retries=2,
            delay_seconds=0.5,
            backoff=2.0,
            retry_exceptions=(asyncio.TimeoutError,),
        )
    except asyncio.TimeoutError:
        logger.warning("YouTube title lookup timed out for video: %s", video_id)
        return None
    except Exception as e:
        logger.exception("Error retrieving video title for %s", video_id)

        #endregion
        return None
