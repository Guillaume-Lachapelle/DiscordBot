"""Shared retry helpers for transient failures."""

#region Imports

import asyncio
from typing import Any, Awaitable, Callable, Tuple, Type

#endregion


#region Functions


async def run_with_retries(
    task_factory: Callable[[], Awaitable[Any]],
    retries: int = 2,
    delay_seconds: float = 0.5,
    backoff: float = 2.0,
    retry_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Any:
    """Run an awaitable factory with retries and exponential backoff.

    Args:
        task_factory: Callable that returns the awaitable to execute.
        retries: Number of retries after the first attempt.
        delay_seconds: Initial delay between retries in seconds.
        backoff: Backoff multiplier for delay.
        retry_exceptions: Exception types that should trigger a retry.

    Returns:
        The result of the awaitable.

    Raises:
        The last exception if all retries are exhausted.
    """
    attempt = 0
    delay = delay_seconds
    while True:
        try:
            return await task_factory()
        except retry_exceptions:
            attempt += 1
            if attempt > retries:
                raise
            await asyncio.sleep(delay)
            delay *= backoff

#endregion
