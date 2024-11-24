# Mypy: Static Type Checking in Python

## Introduction

Mypy is a static type checker for Python that helps catch type-related bugs before runtime. It's designed to combine Python's dynamic nature with the benefits of static typing.

## Installation and Basic Setup

```bash
pip install mypy
```

### Basic Configuration (mypy.ini or setup.cfg)
```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
```

## Type Hints Basics

### Basic Type Annotations
```python
from typing import List, Dict, Optional, Union, Tuple

# Variable annotations
name: str = "John"
age: int = 30
scores: List[int] = [85, 92, 78]
user_data: Dict[str, Union[str, int]] = {
    "name": "John",
    "age": 30
}

# Function annotations
def greet(name: str) -> str:
    return f"Hello, {name}!"

# Optional parameters
def process_data(data: Optional[str] = None) -> str:
    if data is None:
        return "No data provided"
    return data.upper()

# Union types
def process_identifier(id_: Union[int, str]) -> str:
    return str(id_)

# Type aliases
UserId = Union[int, str]
UserDict = Dict[UserId, Dict[str, Union[str, int]]]
```

### Advanced Type Hints

```python
from typing import TypeVar, Generic, Callable, Iterator, Protocol

# Generic types
T = TypeVar('T')
S = TypeVar('S')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []
    
    def push(self, item: T) -> None:
        self.items.append(item)
    
    def pop(self) -> T:
        return self.items.pop()

# Protocols (structural subtyping)
class Drawable(Protocol):
    def draw(self) -> None: ...

def render(drawable: Drawable) -> None:
    drawable.draw()

# Callable types
Transform = Callable[[str], str]

def apply_transform(text: str, transform: Transform) -> str:
    return transform(text)
```

## Common Patterns and Best Practices

### Type Guards
```python
from typing import TypeGuard

def is_string_list(val: List[object]) -> TypeGuard[List[str]]:
    return all(isinstance(x, str) for x in val)

def process_strings(values: List[object]) -> None:
    if is_string_list(values):
        # Type checker knows values is List[str]
        print(", ".join(values))
```

### Type Assertions
```python
from typing import cast

def get_first_item(items: List[object]) -> str:
    first_item = items[0]
    # Tell mypy this is definitely a string
    return cast(str, first_item)
```

### Custom Types
```python
from typing import NewType, Literal

UserId = NewType('UserId', int)
Role = Literal['admin', 'user', 'guest']

def process_user(user_id: UserId, role: Role) -> None:
    pass

# Usage
user_id = UserId(123)
process_user(user_id, 'admin')
```

## Integration with GitHub Actions

```yaml
name: Type Check

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  typecheck:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install mypy
        pip install types-all  # Install type stubs for common packages
    
    - name: Run mypy
      run: mypy .
```

## Common Issues and Solutions

### Missing Type Stubs
```bash
# Install type stubs for third-party packages
pip install types-requests types-PyYAML

# Or use stub packages directly from typeshed
pip install types-all
```

### Handling Dynamic Attributes
```python
from typing import Any

class DynamicClass:
    def __init__(self) -> None:
        self.__dict__: Dict[str, Any] = {}
    
    def __getatt
