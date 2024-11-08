# Memcached: A Comprehensive Guide
## Understanding Memcached

Memcached is a high-performance, distributed memory caching system designed to speed up dynamic web applications by alleviating database load. It works by storing data and objects in memory, which reduces the need to access an external data source (like a database or API).

### Key Features

1. **Simple Key-Value Store**: Data is stored in key-value pairs
2. **Distributed Architecture**: Can run across multiple machines
3. **In-Memory Storage**: All data is stored in RAM for fast access
4. **No Persistence**: Data is volatile and cleared on restart
5. **LRU Eviction**: Least Recently Used items are removed when memory is full

## Basic Concepts

### Data Structure
- Keys: Up to 250 bytes
- Values: Up to 1MB by default
- Expiration time: Can be set per item
- Memory: No disk storage, all data in RAM

### Common Operations
- `get`: Retrieve item
- `set`: Store item
- `add`: Store only if not exists
- `replace`: Store only if exists
- `delete`: Remove item
- `incr/decr`: Increment/decrement numeric values
- `flush_all`: Clear all items

## Python Implementation

### Using `pymemcache`

```python
from pymemcache.client.base import Client

def basic_memcached_operations():
    # Connect to Memcached
    client = Client(('localhost', 11211))
    
    # Store a value
    client.set('hello', 'world', expire=3600)
    
    # Retrieve a value
    result = client.get('hello')
    print(result)  # b'world'
    
    # Store multiple values
    client.set_multi({
        'key1': 'value1',
        'key2': 'value2'
    })
    
    # Retrieve multiple values
    results = client.get_multi(['key1', 'key2'])
    
    # Delete a value
    client.delete('hello')
    
    # Increment a counter
    client.set('counter', '0')
    client.incr('counter', 1)
    
    # Close connection
    client.close()

# Using with serialization
from pymemcache.client.base import Client
from pymemcache import serde
import json

def json_serializer(key, value):
    if isinstance(value, str):
        return value, 1
    return json.dumps(value), 2

def json_deserializer(key, value, flags):
    if flags == 1:
        return value.decode('utf-8')
    if flags == 2:
        return json.loads(value.decode('utf-8'))
    raise Exception("Unknown serialization format")

client = Client(
    ('localhost', 11211),
    serializer=json_serializer,
    deserializer=json_deserializer
)
```

## Go Implementation

### Using `gomemcache`

```go
package main

import (
    "github.com/bradfitz/gomemcache/memcache"
    "encoding/json"
)

func basicMemcachedOperations() error {
    // Connect to Memcached
    mc := memcache.New("localhost:11211")
    
    // Store a value
    err := mc.Set(&memcache.Item{
        Key: "hello",
        Value: []byte("world"),
        Expiration: 3600,
    })
    if err != nil {
        return err
    }
    
    // Retrieve a value
    item, err := mc.Get("hello")
    if err != nil {
        return err
    }
    
    // Delete a value
    err = mc.Delete("hello")
    if err != nil {
        return err
    }
    
    // Increment a counter
    _, err = mc.Increment("counter", 1)
    if err != nil {
        return err
    }
    
    return nil
}

// Storing structured data
type User struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
}

func storeStructuredData(mc *memcache.Client, user User) error {
    // Serialize the struct
    userData, err := json.Marshal(user)
    if err != nil {
        return err
    }
    
    // Store in Memcached
    err = mc.Set(&memcache.Item{
        Key: "user:1",
        Value: userData,
        Expiration: 3600,
    })
    return err
}
```

## Best Practices

### 1. Key Design
```python
# Good key design examples
user_key = f"user:{user_id}"           # user:1234
post_key = f"post:{post_id}:{type}"    # post:5678:details
cache_key = f"{prefix}:{entity}:{id}"   # app:user:1234
```

### 2. Error Handling
- Handle connection failures gracefully
- Implement fallback mechanisms
- Use timeouts appropriately
- Handle cache misses

### 3. Memory Management
```python
# Set reasonable expiration times
client.set('temporary', 'value', expire=3600)  # 1 hour
client.set('session', 'data', expire=86400)    # 1 day
client.set('static', 'content', expire=604800) # 1 week
```

### 4. Performance Optimization
```python
# Batch operations when possible
def batch_get_user_data(user_ids):
    keys = [f"user:{uid}" for uid in user_ids]
    return client.get_multi(keys)
```

## Common Use Cases

1. **Session Storage**
```python
def get_session(session_id):
    key = f"session:{session_id}"
    return client.get(key)

def set_session(session_id, data):
    key = f"session:{session_id}"
    client.set(key, data, expire=3600)
```

2. **Cache Warming**
```python
def warm_cache(keys):
    for key in keys:
        value = database.get(key)
        client.set(key, value, expire=3600)
```

3. **Rate Limiting**
```python
def check_rate_limit(user_id):
    key = f"rate:{user_id}"
    count = client.get(key)
    if not count:
        client.set(key, 1, expire=60)
        return True
    if int(count) > 100:  # 100 requests per minute
        return False
    client.incr(key, 1)
    return True
```

## Monitoring and Management

### Key Metrics to Monitor
1. Hit Rate
2. Memory Usage
3. Evictions
4. Network Traffic
5. Connection Count

### Common Commands
```bash
# Check stats
echo "stats" | nc localhost 11211

# Monitor in real-time
watch "echo stats | nc localhost 11211"

# Check slabs info
echo "stats slabs" | nc localhost 11211
```

## Common Pitfalls

1. **Not Setting Expiration Times**
   - Always set appropriate expiration times
   - Avoid indefinite caching unless necessary

2. **Key Collisions**
   - Use proper key naming conventions
   - Include version/type in keys when needed

3. **Large Objects**
   - Keep objects under 1MB
   - Split large objects if necessary

4. **Cache Stampede**
   - Implement staggered expiration
   - Use cache warming strategies

5. **Invalid Data Types**
   - Ensure proper serialization
   - Handle type conversion errors

6. **Memory Management**
   - Monitor memory usage
   - Handle eviction properly
