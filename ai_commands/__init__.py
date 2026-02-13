"""AI module for Discord bot - Gemini API integration."""

#region Imports

from .commands import FALLBACK_MODELS, generate_response

#endregion


#region Exports

__all__ = [
	'FALLBACK_MODELS',
	'generate_response',
]

#endregion
