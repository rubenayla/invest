"""
Caching Layer for Investment Analysis System

This package provides efficient caching mechanisms for API responses,
financial data, and computation results to improve performance and
reduce external API calls.
"""

from .cache_manager import CacheManager
from .cache_backends import MemoryCache, FileCache, RedisCache
from .cache_decorators import cached_api_call, cached_computation

# Export main interfaces
__all__ = [
    'CacheManager',
    'MemoryCache', 
    'FileCache',
    'RedisCache',
    'cached_api_call',
    'cached_computation',
]