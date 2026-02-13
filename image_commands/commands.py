"""Image processing commands - Background removal."""

#region Imports

from rembg import remove
from PIL import Image
from io import BytesIO
import logging

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


#region Commands

def remove_background_bytes(image_bytes: bytes) -> bytes:
    """Remove background from image bytes using rembg.

    Args:
        image_bytes: Raw image bytes to process.

    Returns:
        PNG bytes with the background removed.
    """
    try:
        image_input = Image.open(BytesIO(image_bytes))
        output = remove(image_input)
        buffer = BytesIO()
        output.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        logger.exception("Error removing image background from bytes")
        raise
    
#endregion
