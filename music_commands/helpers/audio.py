"""Audio file handling and cleanup."""

#region Imports

import os
import asyncio
import logging

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


#region Functions


async def _cleanup_audio_file(file_path):
    """Clean up audio file with error handling.
    
    Args:
        file_path: Path to the audio file to delete
    """
    try:
        if file_path and os.path.exists(file_path):
            await asyncio.sleep(1)
            os.remove(file_path)
            logger.info("Cleaned up audio file: %s", file_path)
    except FileNotFoundError:
        # File already deleted, no action needed
        pass
    except Exception as e:
        logger.warning("Error deleting file %s: %s", file_path, e)

#endregion
