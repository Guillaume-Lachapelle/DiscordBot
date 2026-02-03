"""Error handling helpers."""

#region Imports

from typing import Any
from shared.error_helpers import send_error_followup

#endregion


#region Functions


async def _send_error(ctx: Any, action: str) -> None:
    """Send a consistent error message for a failed action.
    
    Args:
        ctx: Discord context
        action: Action description (e.g., "clear the playlist")
    """
    await send_error_followup(ctx, action)

#endregion
