"""
F1 Strategy Platform v4.0 - Redis Caching Layer
Provides intelligent caching for simulations and ML predictions.
"""
import pickle
import hashlib
from typing import Any, Optional
from functools import wraps
import os

# Try to import redis, fallback to dummy cache if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheManager:
    """
    Intelligent caching manager using Redis.
    Falls back to in-memory dict if Redis is not available.
    """
    
    def __init__(self):
        self._local_cache = {}
        self._redis = None
        self._enabled = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
        
        if REDIS_AVAILABLE and self._enabled:
            try:
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self._redis = redis.from_url(redis_url, decode_responses=False)
                self._redis.ping()
                print("✓ Redis cache connected")
            except Exception as e:
                print(f"⚠ Redis not available, using local cache: {e}")
                self._redis = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._enabled:
            return None
        
        try:
            if self._redis:
                data = self._redis.get(key)
                if data:
                    return pickle.loads(data)
            else:
                return self._local_cache.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)."""
        if not self._enabled:
            return False
        
        try:
            serialized = pickle.dumps(value)
            
            if self._redis:
                self._redis.setex(key, ttl, serialized)
            else:
                self._local_cache[key] = value
            
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._enabled:
            return False
        
        try:
            if self._redis:
                self._redis.delete(key)
            else:
                self._local_cache.pop(key, None)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        try:
            if self._redis:
                self._redis.flushdb()
            else:
                self._local_cache.clear()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            if self._redis:
                info = self._redis.info()
                return {
                    'type': 'redis',
                    'keys': self._redis.dbsize(),
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1)
                }
            else:
                return {
                    'type': 'local',
                    'keys': len(self._local_cache),
                    'used_memory': 'N/A',
                    'hit_rate': 0.0
                }
        except Exception:
            return {'type': 'unknown', 'keys': 0}


# Global cache instance
cache = CacheManager()


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(prefix: str):
    """Invalidate all cache entries with given prefix."""
    # Note: This is a simplified implementation
    # In production, use Redis KEYS or SCAN for pattern matching
    pass


# Simulation cache helpers
def cache_simulation_result(circuit: str, strategy: str, result: dict, ttl: int = 1800):
    """Cache simulation result for 30 minutes."""
    key = f"sim:{circuit}:{strategy}"
    cache.set(key, result, ttl)


def get_cached_simulation(circuit: str, strategy: str) -> Optional[dict]:
    """Get cached simulation result."""
    key = f"sim:{circuit}:{strategy}"
    return cache.get(key)


# ML prediction cache helpers
def cache_prediction(model_type: str, features: tuple, prediction: Any, ttl: int = 3600):
    """Cache ML prediction result."""
    key = cache._generate_key(f"pred:{model_type}", features)
    cache.set(key, prediction, ttl)


def get_cached_prediction(model_type: str, features: tuple) -> Optional[Any]:
    """Get cached prediction."""
    key = cache._generate_key(f"pred:{model_type}", features)
    return cache.get(key)


if __name__ == "__main__":
    # Test cache functionality
    print("Testing Cache Manager")
    print("=" * 50)
    
    # Test basic operations
    cache.set("test_key", {"data": "value"}, ttl=60)
    result = cache.get("test_key")
    print(f"✓ Set/Get: {result}")
    
    # Test with decorator
    @cached(prefix="test", ttl=60)
    def expensive_function(x, y):
        return x * y
    
    r1 = expensive_function(10, 20)
    r2 = expensive_function(10, 20)  # Should come from cache
    print(f"✓ Decorator caching: {r1} == {r2}")
    
    # Stats
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")
    
    print("\nCache manager ready!")
