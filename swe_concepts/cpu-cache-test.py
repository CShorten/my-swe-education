import time
import random
from collections import OrderedDict
import statistics
from typing import Any, Dict, List, Optional, Tuple
import threading
import queue

class CacheLevel:
    """Represents a level in the cache hierarchy (L1/L2/L3)"""
    def __init__(self, name: str, size: int, access_time_ms: float):
        self.name = name
        self.size = size
        self.access_time = access_time_ms
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self.cache:
                # Cache hit
                self.hits += 1
                self.cache.move_to_end(key)
                time.sleep(self.access_time)  # Simulate access time
                return self.cache[key]
            # Cache miss
            self.misses += 1
            return None

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self.cache) >= self.size:
                # Evict least recently used item
                self.cache.popitem(last=False)
            self.cache[key] = value
            time.sleep(self.access_time)  # Simulate write time

    def clear_stats(self) -> None:
        with self._lock:
            self.hits = 0
            self.misses = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

class Database:
    """Simulates a slow database with disk access times"""
    def __init__(self, access_time_ms: float = 0.1):
        self.access_time = access_time_ms
        self.data: Dict[str, Any] = {}
        self.reads = 0
        self.writes = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            self.reads += 1
            time.sleep(self.access_time)  # Simulate disk access
            return self.data.get(key)

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            self.writes += 1
            time.sleep(self.access_time)  # Simulate disk write
            self.data[key] = value

class CacheHierarchy:
    """Manages multiple cache levels and database access"""
    def __init__(self):
        # Initialize cache levels with different sizes and access times
        self.l1 = CacheLevel("L1", size=100, access_time_ms=0.001)
        self.l2 = CacheLevel("L2", size=1000, access_time_ms=0.01)
        self.l3 = CacheLevel("L3", size=10000, access_time_ms=0.05)
        self.db = Database()

    def get(self, key: str) -> Optional[Any]:
        # Try getting from each cache level
        value = self.l1.get(key)
        if value is not None:
            return value

        value = self.l2.get(key)
        if value is not None:
            self.l1.put(key, value)
            return value

        value = self.l3.get(key)
        if value is not None:
            self.l2.put(key, value)
            self.l1.put(key, value)
            return value

        # If not in cache, get from database
        value = self.db.get(key)
        if value is not None:
            self.l3.put(key, value)
            self.l2.put(key, value)
            self.l1.put(key, value)
        return value

    def put(self, key: str, value: Any) -> None:
        # Write-through caching
        self.db.put(key, value)
        self.l3.put(key, value)
        self.l2.put(key, value)
        self.l1.put(key, value)

    def clear_stats(self) -> None:
        self.l1.clear_stats()
        self.l2.clear_stats()
        self.l3.clear_stats()

def run_access_pattern_benchmark(
    cache_hierarchy: CacheHierarchy,
    pattern: str,
    num_operations: int
) -> Dict[str, float]:
    """Run benchmark with different access patterns"""
    cache_hierarchy.clear_stats()
    start_time = time.perf_counter()

    # Generate keys based on access pattern
    if pattern == "sequential":
        keys = [f"key_{i}" for i in range(num_operations)]
    elif pattern == "random":
        keys = [f"key_{random.randint(0, num_operations*2)}" 
                for _ in range(num_operations)]
    elif pattern == "locality":
        # Simulate temporal locality with 80/20 rule
        hot_keys = [f"key_{i}" for i in range(int(num_operations * 0.2))]
        keys = [random.choice(hot_keys) if random.random() < 0.8 
                else f"key_{random.randint(0, num_operations)}"
                for _ in range(num_operations)]

    # Pre-populate data
    for key in set(keys):
        cache_hierarchy.put(key, f"value_{key}")

    # Perform reads
    for key in keys:
        cache_hierarchy.get(key)

    end_time = time.perf_counter()
    total_time = end_time - start_time

    return {
        "pattern": pattern,
        "operations": num_operations,
        "total_time": total_time,
        "ops_per_second": num_operations / total_time,
        "l1_hit_rate": cache_hierarchy.l1.hit_rate,
        "l2_hit_rate": cache_hierarchy.l2.hit_rate,
        "l3_hit_rate": cache_hierarchy.l3.hit_rate
    }

def print_results(results: Dict[str, float]) -> None:
    """Pretty print benchmark results"""
    print(f"\nAccess Pattern: {results['pattern']}")
    print(f"Operations: {results['operations']:,}")
    print(f"Total Time: {results['total_time']:.2f} seconds")
    print(f"Operations/second: {results['ops_per_second']:,.2f}")
    print("\nCache Hit Rates:")
    print(f"L1: {results['l1_hit_rate']*100:.1f}%")
    print(f"L2: {results['l2_hit_rate']*100:.1f}%")
    print(f"L3: {results['l3_hit_rate']*100:.1f}%")

def main():
    cache_hierarchy = CacheHierarchy()
    num_operations = 10000

    print("Running Cache Performance Benchmarks...")
    print("=" * 50)

    patterns = ["sequential", "random", "locality"]
    for pattern in patterns:
        results = run_access_pattern_benchmark(
            cache_hierarchy, pattern, num_operations
        )
        print_results(results)

if __name__ == "__main__":
    main()
