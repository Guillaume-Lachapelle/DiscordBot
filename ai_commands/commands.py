"""AI command handlers - Google Gemini integration."""

#region Imports

import os
import logging
import asyncio
from typing import Any, Optional, List
import google.generativeai as genai
from shared.retry_helpers import run_with_retries
from dotenv import load_dotenv
from shared.config import BotConfig

#endregion


#region Constants

# Load environment variables
load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

logger = logging.getLogger(__name__)

FALLBACK_MODELS: List[str] = [
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash',
    'gemini-2.5-pro',
    'gemini-3-flash-preview',
]

#endregion


#region Commands

async def generate_response(message: str, model: Optional[Any] = None) -> str:
    """Generate an AI response with model fallback and timeouts.

    Args:
        message: Prompt to send to the model.
        model: Preferred model name (optional).

    Returns:
        The generated response text.
    """
    # If no model is specified, or the specified model is invalid, create a list of models to try.
    if model not in FALLBACK_MODELS:
        models_to_try = FALLBACK_MODELS
    else:
        # Start with the preferred model, then add the others as fallbacks.
        models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]

    last_error = None
    for current_model in models_to_try:
        try:
            # Attempt to use the specified model
            llm = genai.GenerativeModel(current_model)
            response = await run_with_retries(
                lambda: asyncio.wait_for(
                    llm.generate_content_async(message),
                    timeout=BotConfig.GENERATION_TIMEOUT_SECONDS,
                ),
                retries=1,
                delay_seconds=0.5,
                backoff=2.0,
                retry_exceptions=(asyncio.TimeoutError,),
            )
            return response.text
        except asyncio.TimeoutError:
            last_error = "timeout"
            logger.warning("AI generation timed out for model %s", current_model)
            continue
        except (genai.types.StopCandidateException, genai.types.BlockedPromptException) as e:
            # Handle content-specific errors immediately
            logger.warning("Content error with model %s: %s", current_model, e)
            return f"Could not generate a response due to safety filters or content restrictions."
        except Exception as e:
            # Catch other exceptions and try the next model
            last_error = e
            logger.exception("Error with model %s. Falling back to next model.", current_model)
            continue

    # If all models fail
    error_message = f"An unexpected error occurred: {last_error}" if last_error else "All available models failed."
    return f"Could not generate response. {error_message} Please try again later."
    
#endregion
