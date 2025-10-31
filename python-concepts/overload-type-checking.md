# Understanding `@overload` for Type Checking in Python

## Table of Contents
1. [Introduction](#introduction)
2. [Basic Concept](#basic-concept)
3. [How @overload Works](#how-overload-works)
4. [Practical Examples](#practical-examples)
5. [Benefits and Use Cases](#benefits-and-use-cases)
6. [Common Patterns](#common-patterns)
7. [Limitations and Gotchas](#limitations-and-gotchas)
8. [Best Practices](#best-practices)

## Introduction

The `@overload` decorator, introduced in Python 3.5 via PEP 484, is a powerful tool for improving static type checking in Python. It allows developers to specify multiple type signatures for a single function, enabling type checkers like mypy, pyright, and IDE tools to provide more precise type information based on the arguments passed to a function.

**Important**: `@overload` is purely for static type checking and has no runtime effect. The decorated stubs never execute.

## Basic Concept

In languages like Java or C++, you can define multiple versions of a function with different parameter types (method overloading). Python doesn't support true overloading at runtime, but `@overload` provides this capability for static type analysis.

```python
from typing import overload, Literal

# Type stubs - these never execute
@overload
def process(data: str) -> str: ...

@overload
def process(data: int) -> int: ...

# Actual implementation - this is what runs
def process(data: str | int) -> str | int:
    if isinstance(data, str):
        return data.upper()
    return data * 2
```

## How @overload Works

### Structure

Every overloaded function follows this pattern:

```python
from typing import overload

@overload
def func(param: TypeA) -> ReturnTypeA: ...

@overload
def func(param: TypeB) -> ReturnTypeB: ...

# Implementation (no @overload decorator)
def func(param: TypeA | TypeB) -> ReturnTypeA | ReturnTypeB:
    # Actual logic here
    pass
```

### Key Rules

1. **Stub bodies use ellipsis (`...`)**: Overload stubs are not implemented
2. **Implementation comes last**: The final definition without `@overload` is the actual code
3. **Implementation must be compatible**: The implementation signature must accept all overload cases
4. **Type checkers only see stubs**: Runtime ignores the stubs completely

## Practical Examples

### Example 1: Return Type Depends on Input Type

```python
from typing import overload

@overload
def get_user(user_id: int) -> dict: ...

@overload
def get_user(user_id: str) -> list[dict]: ...

def get_user(user_id: int | str) -> dict | list[dict]:
    if isinstance(user_id, int):
        return {"id": user_id, "name": "User"}
    # When string, assume it's a search query returning multiple users
    return [{"id": 1, "name": "User1"}, {"id": 2, "name": "User2"}]

# Type checker knows this is dict
user = get_user(123)

# Type checker knows this is list[dict]
users = get_user("john")
```

### Example 2: Optional Parameters Change Return Type

```python
from typing import overload

@overload
def fetch_data(url: str, parse: Literal[True]) -> dict: ...

@overload
def fetch_data(url: str, parse: Literal[False] = False) -> str: ...

def fetch_data(url: str, parse: bool = False) -> dict | str:
    raw_data = f"data from {url}"
    if parse:
        return {"data": raw_data}
    return raw_data

# Type checker knows result is dict
parsed = fetch_data("https://api.example.com", parse=True)

# Type checker knows result is str
raw = fetch_data("https://api.example.com")
```

### Example 3: Async Functions

```python
from typing import overload, Literal

@overload
async def query_database(
    sql: str, 
    return_one: Literal[True]
) -> dict | None: ...

@overload
async def query_database(
    sql: str, 
    return_one: Literal[False] = False
) -> list[dict]: ...

async def query_database(
    sql: str, 
    return_one: bool = False
) -> dict | None | list[dict]:
    # Simulated database query
    results = [{"id": 1}, {"id": 2}]
    if return_one:
        return results[0] if results else None
    return results

# Type checker knows this is dict | None
single = await query_database("SELECT * FROM users WHERE id=1", return_one=True)

# Type checker knows this is list[dict]
multiple = await query_database("SELECT * FROM users")
```

### Example 4: Union Parameters with Different Returns

```python
from typing import overload

class Config:
    pass

class AdvancedConfig:
    pass

@overload
def initialize(config: Config) -> str: ...

@overload
def initialize(config: AdvancedConfig) -> tuple[str, dict]: ...

def initialize(config: Config | AdvancedConfig) -> str | tuple[str, dict]:
    if isinstance(config, AdvancedConfig):
        return ("initialized", {"status": "advanced"})
    return "initialized"

# Type checker knows result is str
status = initialize(Config())

# Type checker knows result is tuple[str, dict]
status, metadata = initialize(AdvancedConfig())
```

## Benefits and Use Cases

### 1. Improved IDE Support

IDEs can provide accurate autocomplete and type hints based on the arguments you're typing:

```python
@overload
def serialize(data: dict, format: Literal["json"]) -> str: ...

@overload
def serialize(data: dict, format: Literal["xml"]) -> bytes: ...

def serialize(data: dict, format: str) -> str | bytes:
    if format == "json":
        return json.dumps(data)
    return data_to_xml_bytes(data)

# IDE knows result is str and suggests string methods
result = serialize({"key": "value"}, format="json")
result.upper()  # ✓ No type error

# IDE knows result is bytes and suggests bytes methods
result = serialize({"key": "value"}, format="xml")
result.decode()  # ✓ No type error
```

### 2. Catch Type Errors Early

```python
@overload
def connect(host: str, port: int) -> Connection: ...

@overload
def connect(connection_string: str) -> Connection: ...

def connect(host_or_conn: str, port: int | None = None) -> Connection:
    if port is not None:
        return Connection(host=host_or_conn, port=port)
    return Connection.from_string(host_or_conn)

# ✓ Type checker accepts this
conn = connect("localhost", 8080)
conn = connect("postgresql://localhost:5432/db")

# ✗ Type checker catches this error
conn = connect("localhost", "8080")  # Error: port should be int, not str
```

### 3. Self-Documenting Code

Overloads serve as inline documentation showing all valid ways to call a function:

```python
@overload
def create_user(name: str, email: str) -> User: ...

@overload
def create_user(user_data: dict) -> User: ...

@overload
def create_user(user_obj: UserProto) -> User: ...

# Anyone reading this immediately knows there are 3 ways to create a user
```

## Common Patterns

### Pattern 1: Literal Types for Mode Selection

One of the most powerful patterns is using `Literal` types to create "mode switches":

```python
from typing import overload, Literal

@overload
def read_file(path: str, mode: Literal["text"]) -> str: ...

@overload
def read_file(path: str, mode: Literal["binary"]) -> bytes: ...

def read_file(path: str, mode: Literal["text", "binary"]) -> str | bytes:
    if mode == "text":
        with open(path, "r") as f:
            return f.read()
    with open(path, "rb") as f:
        return f.read()

# Type checker knows these exact types
text_content: str = read_file("file.txt", mode="text")
binary_content: bytes = read_file("file.bin", mode="binary")
```

### Pattern 2: Optional Parameters Affecting Return Type

```python
from typing import overload

@overload
def get_items(include_metadata: Literal[True]) -> list[tuple[str, dict]]: ...

@overload
def get_items(include_metadata: Literal[False] = False) -> list[str]: ...

def get_items(include_metadata: bool = False) -> list[str] | list[tuple[str, dict]]:
    items = ["item1", "item2"]
    if include_metadata:
        return [(item, {"created": "2024-01-01"}) for item in items]
    return items
```

### Pattern 3: Type Narrowing with isinstance Checks

```python
from typing import overload, TypeVar

T = TypeVar('T')

@overload
def double(value: int) -> int: ...

@overload
def double(value: str) -> str: ...

@overload
def double(value: list[T]) -> list[T]: ...

def double(value: int | str | list) -> int | str | list:
    if isinstance(value, int):
        return value * 2
    if isinstance(value, str):
        return value + value
    return value + value

# Each call has precise typing
num: int = double(5)          # 10
text: str = double("hi")      # "hihi"
items: list[int] = double([1, 2])  # [1, 2, 1, 2]
```

### Pattern 4: Generic Overloads

```python
from typing import overload, TypeVar

T = TypeVar('T')

@overload
def first(items: list[T], default: None = None) -> T | None: ...

@overload
def first(items: list[T], default: T) -> T: ...

def first(items: list[T], default: T | None = None) -> T | None:
    return items[0] if items else default

# Type checker knows return can be None
value = first([1, 2, 3])  # int | None

# Type checker knows return cannot be None
value = first([1, 2, 3], default=0)  # int
value = first([], default=0)  # int (guaranteed not None)
```

## Limitations and Gotchas

### 1. Runtime Behavior

**Critical**: Overloads have NO runtime effect. This code will fail:

```python
@overload
def process(x: int) -> str:
    return str(x)  # This NEVER runs!

@overload
def process(x: str) -> int:
    return int(x)  # This NEVER runs!

def process(x):
    # This is the ONLY code that runs
    # The overloads above are invisible at runtime
    pass

result = process(42)  # Returns None, not "42"!
```

### 2. Implementation Must Cover All Cases

The implementation signature must be compatible with all overload signatures:

```python
# ✗ BAD - implementation doesn't accept all overload cases
@overload
def bad_func(x: int) -> str: ...

@overload
def bad_func(x: str) -> int: ...

def bad_func(x: int) -> str:  # Error: doesn't handle str input
    return str(x)

# ✓ GOOD - implementation handles all cases
def bad_func(x: int | str) -> str | int:
    if isinstance(x, int):
        return str(x)
    return int(x)
```

### 3. Order Matters

More specific overloads should come before more general ones:

```python
# ✗ BAD - general case shadows specific case
@overload
def process(value: object) -> str: ...

@overload
def process(value: int) -> int: ...  # Never matched!

# ✓ GOOD - specific before general
@overload
def process(value: int) -> int: ...

@overload
def process(value: object) -> str: ...
```

### 4. Cannot Overload on Return Type Alone

```python
# ✗ INVALID - same parameters, different returns
@overload
def get_value(key: str) -> int: ...

@overload
def get_value(key: str) -> str: ...  # Error: ambiguous
```

### 5. AsyncGenerator Limitations

As mentioned in your code comment, some type checkers have issues with overloaded async generators:

```python
from typing import AsyncGenerator, overload

# This pattern may not work well with all type checkers
@overload
async def stream(mode: Literal["text"]) -> AsyncGenerator[str, None]: ...

@overload
async def stream(mode: Literal["binary"]) -> AsyncGenerator[bytes, None]: ...

async def stream(mode: str) -> AsyncGenerator[str | bytes, None]:
    # May cause mypy issues due to covariance
    if mode == "text":
        yield "text"
    else:
        yield b"binary"
```

### 6. Not for Dynamic Dispatch

`@overload` doesn't provide runtime dispatch. For that, use `functools.singledispatch`:

```python
from functools import singledispatch

@singledispatch
def process(value):
    raise NotImplementedError(f"Cannot process {type(value)}")

@process.register
def _(value: int):
    return value * 2

@process.register
def _(value: str):
    return value.upper()

# This actually dispatches at runtime based on type
process(5)      # 10
process("hi")   # "HI"
```

## Best Practices

### 1. Keep Overloads Close to Implementation

```python
# ✓ GOOD - overloads and implementation together
@overload
def func(x: int) -> str: ...

@overload
def func(x: str) -> int: ...

def func(x: int | str) -> str | int:
    # Implementation here
    pass
```

### 2. Use Literal Types for Flags

Instead of booleans, use Literal types for better clarity:

```python
# ✗ Less clear
@overload
def fetch(url: str, parse: bool) -> dict | str: ...

# ✓ More clear
@overload
def fetch(url: str, parse: Literal[True]) -> dict: ...

@overload
def fetch(url: str, parse: Literal[False] = False) -> str: ...
```

### 3. Document Unusual Behavior

```python
@overload
def calculate(x: int) -> float: ...

@overload
def calculate(x: float) -> int:
    """
    Note: When input is float, output is rounded to int.
    This is intentional for business logic reasons.
    """
    ...
```

### 4. Test Both Type Checking and Runtime

```python
# Type check tests (for mypy/pyright)
def test_types() -> None:
    result1: str = process(42)  # Should pass type check
    result2: int = process("42")  # Should pass type check

# Runtime tests
def test_runtime() -> None:
    assert process(42) == "42"
    assert process("42") == 42
```

### 5. Consider Using TypeGuard for Complex Cases

For complex type narrowing, consider `TypeGuard`:

```python
from typing import TypeGuard

def is_string_list(val: list) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

def process_list(items: list) -> None:
    if is_string_list(items):
        # Type checker knows items is list[str] here
        result = ", ".join(items)
```

### 6. Use Protocol for Structural Typing

When overloading based on object capabilities, consider Protocol:

```python
from typing import Protocol, overload

class Drawable(Protocol):
    def draw(self) -> None: ...

class Serializable(Protocol):
    def serialize(self) -> str: ...

@overload
def process(obj: Drawable) -> None: ...

@overload
def process(obj: Serializable) -> str: ...

def process(obj: Drawable | Serializable) -> None | str:
    if hasattr(obj, 'draw'):
        obj.draw()
        return None
    return obj.serialize()
```

## Conclusion

The `@overload` decorator is a powerful tool for improving type safety and code clarity in Python. While it requires some initial learning, the benefits of precise type checking, better IDE support, and self-documenting code make it invaluable for large codebases and library development.

**Key Takeaways:**
- `@overload` is purely for static type checking
- Use it when return types depend on input types
- Combine with `Literal` types for powerful mode switches
- Always provide an implementation that handles all overload cases
- Remember that overloads have zero runtime effect

**When to Use:**
- ✓ Return type depends on input type or value
- ✓ Different parameter combinations return different types
- ✓ You want precise type checking for API boundaries
- ✓ Library code that benefits from clear type signatures

**When Not to Use:**
- ✗ Runtime dispatch needed (use `singledispatch` instead)
- ✗ Simple functions with single return type
- ✗ Internal utility functions not part of public API
- ✗ When adding unnecessary complexity
