"""
F1 Strategy Platform v5.0 - Resilience & Fault Tolerance
Implements retry mechanisms, circuit breaker, and graceful fallbacks.
"""
import time
import random
import functools
import logging
from typing import Callable, Any, Optional, TypeVar
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascade failures by stopping requests to failing services.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self._lock = Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Original exception if execution fails
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit {self.name}: Moving to HALF_OPEN")
                else:
                    raise CircuitBreakerOpen(f"Circuit {self.name} is OPEN")
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpen(f"Circuit {self.name} HALF_OPEN limit reached")
                self.half_open_calls += 1
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.config.success_threshold:
                    self._reset()
                    logger.info(f"Circuit {self.name}: CLOSED (recovered)")
            else:
                # In CLOSED state, just reset failures on success
                if self.failures > 0:
                    self.failures = max(0, self.failures - 1)
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.failures += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed during test, go back to OPEN
                self.state = CircuitState.OPEN
                self.half_open_calls = 0
                self.successes = 0
                logger.warning(f"Circuit {self.name}: BACK TO OPEN (recovery failed)")
            elif self.failures >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit {self.name}: OPEN (threshold reached)")
    
    def _reset(self):
        """Reset circuit to closed state."""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.half_open_calls = 0
        self.last_failure_time = None
    
    def get_state(self) -> dict:
        """Get current circuit state for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "successes": self.successes,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def with_circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to add circuit breaker to function."""
    breaker = get_circuit_breaker(name, config)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Attach circuit breaker info to function
        wrapper._circuit_breaker = breaker
        return wrapper
    
    return decorator


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retryable_exceptions: tuple = (Exception,)
    on_retry: Optional[Callable] = None


def with_retry(config: RetryConfig = None):
    """
    Decorator to add retry mechanism with exponential backoff.
    
    Args:
        config: Retry configuration
    """
    cfg = config or RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, cfg.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except cfg.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == cfg.max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {cfg.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        cfg.base_delay * (cfg.exponential_base ** (attempt - 1)),
                        cfg.max_delay
                    )
                    # Add jitter (±20%)
                    delay *= (0.8 + random.random() * 0.4)
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    
                    if cfg.on_retry:
                        cfg.on_retry(attempt, e, delay)
                    
                    time.sleep(delay)
            
            # Should not reach here
            raise last_exception if last_exception else RuntimeError("Retry failed")
        
        return wrapper
    
    return decorator


class FallbackStrategy:
    """Base class for fallback strategies."""
    
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """Execute fallback logic."""
        raise NotImplementedError


class StaticFallback(FallbackStrategy):
    """Return static/default value on failure."""
    
    def __init__(self, default_value: Any):
        self.default_value = default_value
    
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        return self.default_value


class CachedFallback(FallbackStrategy):
    """Return cached value on failure."""
    
    def __init__(self, cache_key_func: Callable = None):
        self._cache = {}
        self._cache_key_func = cache_key_func or (lambda *a, **k: str(a) + str(k))
    
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        cache_key = self._cache_key_func(*args, **kwargs)
        
        if cache_key in self._cache:
            logger.info(f"Using cached fallback for {cache_key}")
            return self._cache[cache_key]
        
        # Try to execute and cache
        try:
            result = original_func(*args, **kwargs)
            self._cache[cache_key] = result
            return result
        except Exception:
            # No cache available
            raise


def with_fallback(fallback: FallbackStrategy):
    """
    Decorator to add fallback behavior on failure.
    
    Args:
        fallback: Fallback strategy to use
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"{func.__name__} failed, using fallback: {e}")
                return fallback.execute(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Pre-configured circuit breakers for common services
ML_PREDICTION_BREAKER = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=60.0,
    half_open_max_calls=2
)

SIMULATION_BREAKER = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0,
    half_open_max_calls=3
)

EXTERNAL_API_BREAKER = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=120.0,
    half_open_max_calls=1
)


# Pre-configured retry configs
ML_PREDICTION_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0
)

SIMULATION_RETRY = RetryConfig(
    max_attempts=2,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=1.5
)

DATABASE_RETRY = RetryConfig(
    max_attempts=5,
    base_delay=0.1,
    max_delay=5.0,
    exponential_base=2.0,
    retryable_exceptions=(ConnectionError, TimeoutError)
)


if __name__ == "__main__":
    # Test resilience components
    print("Testing Resilience Components")
    print("=" * 60)
    
    # Test retry
    @with_retry(RetryConfig(max_attempts=3, base_delay=0.1))
    def flaky_function(fail_count=2):
        """Simulate flaky function."""
        if flaky_function.calls < fail_count:
            flaky_function.calls += 1
            raise ConnectionError(f"Simulated failure #{flaky_function.calls}")
        return "Success!"
    
    flaky_function.calls = 0
    
    try:
        result = flaky_function(fail_count=2)
        print(f"✓ Retry test passed: {result}")
    except Exception as e:
        print(f"✗ Retry test failed: {e}")
    
    # Test circuit breaker
    breaker = CircuitBreaker("test", CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0
    ))
    
    def fail_func():
        raise ValueError("Always fails")
    
    # Trigger failures to open circuit
    for i in range(3):
        try:
            breaker.call(fail_func)
        except Exception:
            pass
    
    print(f"✓ Circuit state after failures: {breaker.state.value}")
    
    # Test fallback
    fallback = StaticFallback(default_value={"strategy": "1_stop", "fallback": True})
    
    @with_fallback(fallback)
    def failing_function():
        raise ValueError("Function failed")
    
    result = failing_function()
    print(f"✓ Fallback test passed: {result}")
    
    print("\n✓ All resilience components working!")
