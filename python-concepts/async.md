# Python Asyncio: TaskGroup vs. gather()

## Overview

This report compares two common approaches for managing concurrent tasks in Python's asyncio:

1. Using the `asyncio.TaskGroup()` context manager
2. Using the `asyncio.gather()` function

## Code Examples

### TaskGroup Approach

```python
async with asyncio.TaskGroup() as tg:
    task = tg.create_task(...)
    
task.result()
```

### gather Approach

```python
results = await asyncio.gather(*tasks)
```

## Key Differences

| Feature | TaskGroup | gather |
|---------|-----------|--------|
| **Availability** | Python 3.11+ | All asyncio-supported Python versions |
| **Task Creation** | Dynamic creation inside context manager | Tasks typically created beforehand |
| **Error Handling** | Tasks continue running if one fails; error propagates when exiting context | By default, other tasks continue if one fails; can set `return_exceptions=True` |
| **Result Access** | Individual: `task.result()` | All results returned as a list |
| **Cancellation** | All tasks automatically cancelled when context exits | Tasks not automatically cancelled |
| **Structure** | More structured approach with clear boundaries | More flexible but less structured |
| **Scope** | Tasks are explicitly part of a defined group | No explicit grouping concept |

## Use Case Recommendations

### When to Use TaskGroup

- For Python 3.11+ projects
- When you need structured task management with clear boundaries
- When you need fine-grained control over each task
- When automatic cancellation on context exit is desirable
- For dynamic task creation based on runtime conditions

### When to Use gather

- For backward compatibility with older Python versions
- When you need a simple way to run and await multiple pre-created tasks
- When you want all results collected in a single list
- When you need the flexibility to handle errors differently
- For simpler, more concise code when managing a fixed set of tasks

## Implementation Notes

### TaskGroup Error Handling

With TaskGroup, if one task raises an exception:
1. All other tasks continue running
2. When exiting the context manager, the first exception is re-raised
3. Any other exceptions are added as suppressed exceptions

### gather Error Handling

With gather:
1. By default, if any task raises an exception, it's propagated
2. With `return_exceptions=True`, exceptions are returned as results instead
3. You must check each result to see if it's an exception

## Conclusion

Both methods effectively manage concurrent tasks, but with different approaches:

- **TaskGroup** offers a more structured, context-managed approach with automatic cancellation
- **gather** provides a simpler, more flexible approach for collecting results from multiple tasks

Choose based on your Python version requirements, error handling needs, and preference for structure versus flexibility.
