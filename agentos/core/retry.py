"""Retry Logic with Exponential Backoff for AgentOS"""

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            jitter: Add random jitter to prevent thundering herd
            retry_exceptions: Tuple of exception types to retry on
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions


# Default configurations for different scenarios
DEFAULT_LLM_RETRY = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

AGGRESSIVE_RETRY = RetryConfig(
    max_retries=5,
    initial_delay=0.5,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)

GENTLE_RETRY = RetryConfig(
    max_retries=2,
    initial_delay=2.0,
    max_delay=10.0,
    exponential_base=1.5,
    jitter=True,
)


def calculate_delay(
    attempt: int,
    initial_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
) -> float:
    """
    Calculate delay for the given attempt number using exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    # Calculate exponential delay
    delay = initial_delay * (exponential_base**attempt)

    # Cap at max delay
    delay = min(delay, max_delay)

    # Add jitter (0-50% of the delay)
    if jitter:
        jitter_amount = delay * random.uniform(0, 0.5)
        delay += jitter_amount

    return delay


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
):
    """
    Decorator that adds retry logic with exponential backoff to a function.

    Args:
        config: RetryConfig instance (uses DEFAULT_LLM_RETRY if not provided)
        on_retry: Optional callback called on each retry with (attempt, exception, delay)

    Returns:
        Decorated function
    """
    if config is None:
        config = DEFAULT_LLM_RETRY

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retry_exceptions as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = calculate_delay(
                            attempt,
                            config.initial_delay,
                            config.max_delay,
                            config.exponential_base,
                            config.jitter,
                        )

                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        if on_retry:
                            on_retry(attempt, e, delay)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


async def async_retry_with_backoff(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    **kwargs,
) -> Any:
    """
    Async version of retry with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments for the function
        config: RetryConfig instance
        on_retry: Optional callback on retry
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function
    """
    import asyncio

    if config is None:
        config = DEFAULT_LLM_RETRY

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except config.retry_exceptions as e:
            last_exception = e

            if attempt < config.max_retries:
                delay = calculate_delay(
                    attempt,
                    config.initial_delay,
                    config.max_delay,
                    config.exponential_base,
                    config.jitter,
                )

                logger.warning(
                    f"Async attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                if on_retry:
                    on_retry(attempt, e, delay)

                await asyncio.sleep(delay)
            else:
                logger.error(f"All async attempts failed: {e}")

    raise last_exception


class RetryableError(Exception):
    """Exception that should trigger a retry"""

    pass


class NonRetryableError(Exception):
    """Exception that should NOT trigger a retry"""

    pass


# Common LLM API errors that should be retried
LLM_RETRY_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    RetryableError,
)

# Specific retry config for LLM API calls
LLM_API_RETRY = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retry_exceptions=LLM_RETRY_EXCEPTIONS,
)
