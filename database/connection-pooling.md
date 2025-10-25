# Database Connection Pooling

## What is Connection Pooling?

Connection pooling is a technique used to maintain a cache of database connections that can be reused when future requests to the database are required. Instead of opening and closing a new connection for every database operation, applications reuse connections from a pool, which significantly improves performance.

## Why Use Connection Pooling?

Creating a new database connection is expensive because it involves:
- Network handshake with the database server
- Authentication
- Session initialization
- Resource allocation on both client and server

Connection pooling solves this by:
- **Reducing latency**: Reusing existing connections eliminates connection overhead
- **Improving throughput**: More database operations can be performed in less time
- **Managing resources**: Limits the number of concurrent connections to prevent overwhelming the database
- **Better scalability**: Applications can handle more concurrent users efficiently

## How Connection Pooling Works

1. **Initialization**: A pool of connections is created when the application starts
2. **Acquisition**: When a client needs a database connection, it requests one from the pool
3. **Usage**: The client uses the connection to execute queries
4. **Release**: When finished, the connection is returned to the pool (not closed)
5. **Reuse**: The connection becomes available for other clients
6. **Cleanup**: Idle connections may be closed after a timeout, and unhealthy connections are removed

## Python Implementation of a Connection Pool

Below is a complete implementation of a connection pooler that works with a Python-based database implementation.

### Simple Database Implementation

First, let's create a simple mock database and connection class:

```python
import time
import random
from typing import Any, Optional


class DatabaseConnection:
    """Simulates a database connection with open/close overhead."""
    
    _id_counter = 0
    
    def __init__(self, host: str, port: int, database: str):
        DatabaseConnection._id_counter += 1
        self.connection_id = DatabaseConnection._id_counter
        self.host = host
        self.port = port
        self.database = database
        self.is_open = False
        self.last_used = None
        
    def connect(self):
        """Simulate the overhead of establishing a connection."""
        if self.is_open:
            raise RuntimeError(f"Connection {self.connection_id} is already open")
        
        # Simulate network latency and handshake
        time.sleep(0.1)
        self.is_open = True
        print(f"🔌 Connection {self.connection_id} opened to {self.database}")
        
    def close(self):
        """Close the database connection."""
        if not self.is_open:
            raise RuntimeError(f"Connection {self.connection_id} is already closed")
        
        self.is_open = False
        print(f"🔒 Connection {self.connection_id} closed")
        
    def execute(self, query: str) -> Any:
        """Execute a query on this connection."""
        if not self.is_open:
            raise RuntimeError(f"Cannot execute query: Connection {self.connection_id} is closed")
        
        self.last_used = time.time()
        # Simulate query execution
        time.sleep(0.01)
        return f"Result from connection {self.connection_id}: {query}"
    
    def is_healthy(self) -> bool:
        """Check if the connection is still healthy."""
        if not self.is_open:
            return False
        
        # Simulate occasional connection failures
        return random.random() > 0.05  # 5% chance of being unhealthy


class MockDatabase:
    """Mock database server."""
    
    def __init__(self, host: str = "localhost", port: int = 5432, database: str = "mydb"):
        self.host = host
        self.port = port
        self.database = database
        
    def create_connection(self) -> DatabaseConnection:
        """Create a new connection to this database."""
        return DatabaseConnection(self.host, self.port, self.database)
```

### Connection Pool Implementation

Now, let's implement the connection pooler:

```python
import threading
from queue import Queue, Empty, Full
from contextlib import contextmanager
from typing import Optional
import time


class ConnectionPool:
    """
    A thread-safe connection pool for database connections.
    
    Features:
    - Minimum and maximum pool size
    - Connection validation before reuse
    - Idle connection cleanup
    - Thread-safe acquire/release operations
    - Context manager support
    """
    
    def __init__(
        self,
        database: MockDatabase,
        min_size: int = 2,
        max_size: int = 10,
        max_idle_time: float = 300.0,  # 5 minutes
        timeout: float = 30.0
    ):
        """
        Initialize the connection pool.
        
        Args:
            database: The database to connect to
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections allowed
            max_idle_time: Maximum time (seconds) a connection can be idle
            timeout: Maximum time (seconds) to wait for a connection
        """
        self.database = database
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.timeout = timeout
        
        # Thread-safe queue to store available connections
        self._pool: Queue = Queue(maxsize=max_size)
        
        # Track the total number of connections created
        self._connection_count = 0
        self._count_lock = threading.Lock()
        
        # Flag to indicate if pool is closed
        self._closed = False
        
        # Initialize the pool with minimum connections
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Create the minimum number of connections."""
        print(f"📊 Initializing connection pool (min={self.min_size}, max={self.max_size})")
        for _ in range(self.min_size):
            conn = self._create_new_connection()
            self._pool.put(conn)
            
    def _create_new_connection(self) -> DatabaseConnection:
        """Create and open a new database connection."""
        with self._count_lock:
            if self._connection_count >= self.max_size:
                raise RuntimeError("Maximum number of connections reached")
            
            conn = self.database.create_connection()
            conn.connect()
            self._connection_count += 1
            
        return conn
    
    def _validate_connection(self, conn: DatabaseConnection) -> bool:
        """
        Validate that a connection is still usable.
        
        Args:
            conn: The connection to validate
            
        Returns:
            True if the connection is healthy, False otherwise
        """
        if not conn.is_open:
            return False
            
        # Check if connection has been idle too long
        if conn.last_used:
            idle_time = time.time() - conn.last_used
            if idle_time > self.max_idle_time:
                print(f"⏰ Connection {conn.connection_id} exceeded max idle time")
                return False
        
        # Check connection health
        if not conn.is_healthy():
            print(f"💔 Connection {conn.connection_id} is unhealthy")
            return False
            
        return True
    
    def acquire(self, timeout: Optional[float] = None) -> DatabaseConnection:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection (uses pool default if None)
            
        Returns:
            A database connection
            
        Raises:
            RuntimeError: If pool is closed or timeout occurs
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        
        while True:
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise RuntimeError(f"Timeout waiting for connection ({timeout}s)")
            
            try:
                # Try to get a connection from the pool
                remaining_timeout = timeout - elapsed
                conn = self._pool.get(timeout=min(remaining_timeout, 1.0))
                
                # Validate the connection
                if self._validate_connection(conn):
                    print(f"✅ Acquired connection {conn.connection_id} from pool")
                    return conn
                else:
                    # Connection is invalid, close it and create a new one
                    self._close_connection(conn)
                    
            except Empty:
                # No connection available, try to create a new one
                with self._count_lock:
                    if self._connection_count < self.max_size:
                        try:
                            conn = self._create_new_connection()
                            print(f"➕ Created new connection {conn.connection_id}")
                            return conn
                        except Exception as e:
                            print(f"❌ Failed to create new connection: {e}")
                            
                # If we can't get or create a connection, wait and retry
                time.sleep(0.1)
    
    def release(self, conn: DatabaseConnection):
        """
        Return a connection to the pool.
        
        Args:
            conn: The connection to return
        """
        if self._closed:
            self._close_connection(conn)
            return
        
        # Validate before returning to pool
        if self._validate_connection(conn):
            try:
                self._pool.put_nowait(conn)
                print(f"↩️  Released connection {conn.connection_id} back to pool")
            except Full:
                # Pool is full, close the connection
                print(f"⚠️  Pool full, closing connection {conn.connection_id}")
                self._close_connection(conn)
        else:
            # Connection is invalid, don't return it to the pool
            self._close_connection(conn)
    
    def _close_connection(self, conn: DatabaseConnection):
        """Close a connection and decrement the count."""
        try:
            if conn.is_open:
                conn.close()
        finally:
            with self._count_lock:
                self._connection_count -= 1
    
    @contextmanager
    def connection(self, timeout: Optional[float] = None):
        """
        Context manager for acquiring and releasing connections.
        
        Usage:
            with pool.connection() as conn:
                result = conn.execute("SELECT * FROM users")
        """
        conn = self.acquire(timeout=timeout)
        try:
            yield conn
        finally:
            self.release(conn)
    
    def close(self):
        """Close all connections in the pool."""
        if self._closed:
            return
            
        print("🛑 Closing connection pool...")
        self._closed = True
        
        # Close all connections in the pool
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                self._close_connection(conn)
            except Empty:
                break
        
        print(f"✅ Connection pool closed ({self._connection_count} connections remaining)")
    
    def get_stats(self) -> dict:
        """Get statistics about the pool."""
        return {
            "total_connections": self._connection_count,
            "available_connections": self._pool.qsize(),
            "in_use_connections": self._connection_count - self._pool.qsize(),
            "max_size": self.max_size,
            "min_size": self.min_size,
            "closed": self._closed
        }
```

### Usage Examples

Here's how to use the connection pool:

```python
def example_basic_usage():
    """Basic usage of the connection pool."""
    print("\n" + "="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    # Create database and pool
    db = MockDatabase()
    pool = ConnectionPool(db, min_size=2, max_size=5)
    
    try:
        # Acquire a connection
        conn = pool.acquire()
        
        # Use the connection
        result = conn.execute("SELECT * FROM users")
        print(f"Query result: {result}")
        
        # Release the connection back to the pool
        pool.release(conn)
        
        # Check pool statistics
        stats = pool.get_stats()
        print(f"\nPool stats: {stats}")
        
    finally:
        pool.close()


def example_context_manager():
    """Using the connection pool with context manager."""
    print("\n" + "="*60)
    print("Example 2: Context Manager")
    print("="*60)
    
    db = MockDatabase()
    pool = ConnectionPool(db, min_size=2, max_size=5)
    
    try:
        # Connection is automatically released when exiting the context
        with pool.connection() as conn:
            result = conn.execute("INSERT INTO users VALUES (1, 'Alice')")
            print(f"Query result: {result}")
        
        print("\nConnection automatically returned to pool")
        
    finally:
        pool.close()


def example_concurrent_usage():
    """Demonstrate concurrent usage of the connection pool."""
    print("\n" + "="*60)
    print("Example 3: Concurrent Usage")
    print("="*60)
    
    db = MockDatabase()
    pool = ConnectionPool(db, min_size=2, max_size=5)
    
    def worker(worker_id: int, num_queries: int):
        """Worker function that executes multiple queries."""
        for i in range(num_queries):
            with pool.connection() as conn:
                query = f"SELECT * FROM data WHERE worker={worker_id} AND query={i}"
                result = conn.execute(query)
                print(f"Worker {worker_id}: {result}")
            time.sleep(0.05)  # Simulate some processing time
    
    try:
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i, 3))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Final statistics
        stats = pool.get_stats()
        print(f"\nFinal pool stats: {stats}")
        
    finally:
        pool.close()


def example_pool_exhaustion():
    """Demonstrate what happens when pool is exhausted."""
    print("\n" + "="*60)
    print("Example 4: Pool Exhaustion Handling")
    print("="*60)
    
    db = MockDatabase()
    pool = ConnectionPool(db, min_size=1, max_size=2, timeout=2.0)
    
    try:
        # Acquire all available connections
        conn1 = pool.acquire()
        conn2 = pool.acquire()
        
        print("\nAll connections in use. Trying to acquire another...")
        
        # This will timeout because pool is exhausted
        try:
            conn3 = pool.acquire(timeout=1.0)
        except RuntimeError as e:
            print(f"❌ Expected error: {e}")
        
        # Release a connection
        pool.release(conn1)
        
        # Now we can acquire again
        conn3 = pool.acquire()
        print(f"✅ Successfully acquired connection after release")
        
        # Cleanup
        pool.release(conn2)
        pool.release(conn3)
        
    finally:
        pool.close()


# Run all examples
if __name__ == "__main__":
    example_basic_usage()
    time.sleep(0.5)
    
    example_context_manager()
    time.sleep(0.5)
    
    example_concurrent_usage()
    time.sleep(0.5)
    
    example_pool_exhaustion()
```

## Key Concepts Demonstrated

### Thread Safety
The pool uses a `Queue` which is thread-safe, and a lock (`threading.Lock`) to protect the connection count. This allows multiple threads to safely acquire and release connections concurrently.

### Connection Validation
Before reusing a connection, the pool validates that it's still healthy and hasn't been idle too long. Invalid connections are discarded and replaced with new ones.

### Dynamic Pool Sizing
The pool starts with a minimum number of connections and can grow up to the maximum size as needed. This balances resource usage with performance.

### Timeout Handling
If no connection is available and the pool is at maximum capacity, the `acquire()` method will wait for a configurable timeout before raising an error.

### Resource Management
The context manager pattern (`with pool.connection()`) ensures connections are always properly returned to the pool, even if an exception occurs.

## Best Practices

1. **Set appropriate pool sizes**: Too small and you'll have contention; too large and you'll waste resources
2. **Use context managers**: Always use `with pool.connection()` to ensure connections are released
3. **Monitor pool statistics**: Track metrics like connection usage to optimize pool configuration
4. **Handle timeouts gracefully**: Implement retry logic or backoff strategies when the pool is exhausted
5. **Validate connections**: Always check that connections are healthy before reuse
6. **Close the pool properly**: Call `pool.close()` when shutting down to clean up resources

## Performance Benefits

Without connection pooling, creating 100 connections might take 10+ seconds. With pooling, those same 100 operations reuse just a few connections and complete in under a second, representing a 10x or greater speedup for connection-heavy workloads.
