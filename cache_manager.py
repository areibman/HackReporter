"""
Cache manager for optimizing API calls and file processing
"""
import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for API responses and file processing results"""
    
    def __init__(self, cache_dir: str = "cache", ttl_seconds: int = 3600):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
    def _get_cache_key(self, key_data: Union[str, Dict, list]) -> str:
        """Generate a cache key from input data"""
        if isinstance(key_data, (dict, list)):
            key_str = json.dumps(key_data, sort_keys=True)
        else:
            key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired"""
        return time.time() - cache_entry.get('timestamp', 0) > self.ttl_seconds
    
    def get(self, key_data: Union[str, Dict, list]) -> Optional[Any]:
        """
        Get cached data
        
        Args:
            key_data: Data to generate cache key from
            
        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._get_cache_key(key_data)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not self._is_expired(entry):
                logger.debug(f"Cache hit (memory): {cache_key[:8]}...")
                return entry['data']
            else:
                del self.memory_cache[cache_key]
        
        # Check disk cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                
                if not self._is_expired(entry):
                    # Store in memory cache for faster access
                    self.memory_cache[cache_key] = entry
                    logger.debug(f"Cache hit (disk): {cache_key[:8]}...")
                    return entry['data']
                else:
                    # Remove expired cache file
                    cache_path.unlink()
            except (pickle.PickleError, EOFError) as e:
                logger.warning(f"Failed to load cache file {cache_path}: {e}")
                cache_path.unlink()
        
        logger.debug(f"Cache miss: {cache_key[:8]}...")
        return None
    
    def set(self, key_data: Union[str, Dict, list], value: Any) -> None:
        """
        Store data in cache
        
        Args:
            key_data: Data to generate cache key from
            value: Data to cache
        """
        cache_key = self._get_cache_key(key_data)
        entry = {
            'data': value,
            'timestamp': time.time()
        }
        
        # Store in memory cache
        self.memory_cache[cache_key] = entry
        
        # Store in disk cache
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
            logger.debug(f"Cached: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {e}")
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries
        
        Args:
            pattern: Optional pattern to match cache keys (if None, clears all)
            
        Returns:
            Number of entries cleared
        """
        cleared = 0
        
        # Clear memory cache
        if pattern:
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
                cleared += 1
        else:
            cleared += len(self.memory_cache)
            self.memory_cache.clear()
        
        # Clear disk cache
        if pattern:
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    if pattern in str(entry.get('data', '')):
                        cache_file.unlink()
                        cleared += 1
                except:
                    pass
        else:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
                cleared += 1
        
        logger.info(f"Cleared {cleared} cache entries")
        return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_entries = len(self.memory_cache)
        disk_entries = len(list(self.cache_dir.glob("*.pkl")))
        
        total_size = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            total_size += cache_file.stat().st_size
        
        return {
            'memory_entries': memory_entries,
            'disk_entries': disk_entries,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# Global cache instance
cache_manager = CacheManager()