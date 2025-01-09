# Event Loop Debugging Techniques

## Debug Mode
The simplest way to enable debug logging is by setting the event loop to debug mode:

```python
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode
loop = asyncio.get_event_loop()
loop.set_debug(True)
```

## Built-in Debug Tools

### Slow Callback Warnings
When debug mode is enabled, you'll get warnings for callbacks that take too long:

```python
loop.slow_callback_duration = 0.1  # Set threshold to 100ms
```

### Resource Tracking
You can track unclosed resources:

```python
import asyncio.events as events
events.set_event_loop_policy(events.ResourceTrackingEventLoopPolicy())
```

## Task Inspection Tools

### Current Task State
Get information about running tasks:

```python
import asyncio

async def debug_tasks():
    for task in asyncio.all_tasks():
        print(f"Task: {task.get_name()}")
        print(f"State: {task._state}")
        print(f"Stack: {task.get_stack()}")
```

### Exception Handling
Set up custom exception handlers to catch and debug errors:

```python
def exception_handler(loop, context):
    print(f"Exception details: {context}")

loop.set_exception_handler(exception_handler)
```

## Advanced Debugging

### asyncio Debug Command Line
You can enable debug mode from the command line:

```bash
python -X dev program.py
# or
PYTHONASYNCIODEBUG=1 python program.py
```

### Using aiomonitor
For real-time monitoring, you can use the aiomonitor library:

```python
from aiomonitor import start_monitor

async def main():
    with start_monitor(loop):
        # Your async code here
        pass
```

### Profile Async Code
Use async-profiler to understand performance:

```python
from async_profiler import profiler

@profiler
async def my_coroutine():
    # Your code here
    pass
```

## Common Debug Patterns

### Timeout Detection
Identify hanging tasks:

```python
async def with_timeout(coro, timeout):
    try:
        async with asyncio.timeout(timeout):
            await coro
    except TimeoutError:
        print(f"Operation timed out after {timeout} seconds")
```

### Task Creation Tracking
Monitor where tasks are being created:

```python
async def tracked_task(coro):
    task = asyncio.create_task(coro)
    frame = sys._getframe(1)
    print(f"Task created at {frame.f_code.co_filename}:{frame.f_lineno}")
    return await task
```

## Best Practices for Debugging

1. Always enable debug mode during development
2. Set up comprehensive logging
3. Use descriptive task names
4. Implement proper error handling
5. Monitor task lifecycle events
6. Track resource usage
7. Use timeouts for long-running operations

Remember that the event loop's debug mode does add overhead, so it should typically be disabled in production unless needed for specific troubleshooting.
