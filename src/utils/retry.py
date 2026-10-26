"""Retry decorator with exponential backoff and rate limit handling."""

import functools
import logging
import random
import time
from typing import Callable, Any

logger = logging.getLogger("retry")


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 3.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
):
    """Decorator to retry flaky API calls with exponential backoff.
    
    Catches general exceptions (such as network timeouts, HTTP 429, ResourceExhausted).
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = base_delay

            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    error_msg = str(e)
                    
                    if attempt >= max_retries:
                        logger.error(f"[{func.__name__}] Failed after {max_retries} attempts: {error_msg}")
                        raise

                    # Calculate sleep time with optional jitter
                    sleep_time = min(current_delay, max_delay)
                    if jitter:
                        sleep_time += random.uniform(0.1, 1.0)

                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt}/{max_retries} failed ({type(e).__name__}: {error_msg}). "
                        f"Backing off for {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    current_delay *= backoff_factor

        return wrapper
    return decorator
