"""
Retry utilities with exponential backoff for handling rate limits and transient failures.
"""
import asyncio
import logging
from typing import TypeVar, Callable, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_status_codes: Optional[list[int]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            retry_on_status_codes: HTTP status codes that should trigger a retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status_codes = retry_on_status_codes or [429, 500, 502, 503, 504]


def calculate_backoff_delay(
    attempt: int,
    initial_delay: float,
    max_delay: float,
    exponential_base: float
) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (0-indexed)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        
    Returns:
        Delay in seconds for this attempt
    """
    delay = initial_delay * (exponential_base ** attempt)
    return min(delay, max_delay)


async def retry_with_backoff(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from successful function execution
        
    Raises:
        Exception: The last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - return result
            if attempt > 0:
                logger.info(
                    f"Retry successful after {attempt} attempts",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt
                    }
                )
            return result
            
        except Exception as e:
            last_exception = e
            
            # Check if we should retry
            should_retry = False
            
            # Check for HTTP status code in exception
            if hasattr(e, 'status_code'):
                if e.status_code in config.retry_on_status_codes:
                    should_retry = True
            elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code in config.retry_on_status_codes:
                    should_retry = True
            else:
                # For non-HTTP exceptions, retry on specific types
                if isinstance(e, (ConnectionError, TimeoutError)):
                    should_retry = True
            
            # If this is the last attempt or we shouldn't retry, raise
            if attempt >= config.max_retries or not should_retry:
                logger.error(
                    f"All retry attempts exhausted for {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "attempts": attempt + 1,
                        "error": str(e)
                    }
                )
                raise
            
            # Calculate backoff delay
            delay = calculate_backoff_delay(
                attempt,
                config.initial_delay,
                config.max_delay,
                config.exponential_base
            )
            
            logger.warning(
                f"Retry attempt {attempt + 1}/{config.max_retries} for {func.__name__}",
                extra={
                    "function": func.__name__,
                    "attempt": attempt + 1,
                    "delay": delay,
                    "error": str(e)
                }
            )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @with_retry(RetryConfig(max_retries=3))
        async def fetch_data():
            # ... code that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator
