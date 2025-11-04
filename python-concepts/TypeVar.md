# Understanding TypeVar in Python: A Complete Guide

## What is TypeVar?

`TypeVar` creates a **placeholder for a type** that will be specified later. Think of it like a variable, but for types instead of values.

```python
from typing import TypeVar

# Regular variable - holds a value
x = 5

# Type variable - represents a type
T = TypeVar("T")
```

## Basic Syntax

### Unbounded TypeVar

```python
T = TypeVar("T")
```

This creates a type variable that can be **any type at all**:

```python
# Could be a string
value1: list[T]  # where T = str

# Could be an integer  
value2: list[T]  # where T = int

# Could be a custom class
value3: list[T]  # where T = MyCustomClass
```

**The string `"T"`** is just the name for error messages. By convention, it matches the variable name.

### Bounded TypeVar

```python
from typing import TypeVar

class Animal:
    def make_sound(self) -> str:
        return "..."

T = TypeVar("T", bound=Animal)
```

The `bound=Animal` means this type variable **must be a subclass of Animal** (or Animal itself):

```python
class Dog(Animal):  # ✅ Valid - subclass of Animal
    def make_sound(self) -> str:
        return "Woof!"

class Car:  # ❌ Invalid - not an Animal
    def drive(self) -> None:
        pass

# This works:
def pet(animal: T) -> T: ...
pet(Dog())  # ✅ OK

# This would cause a type error:
pet(Car())  # ❌ Type checker complains
```

## Why Use TypeVars?

### Without TypeVars (Bad):

```python
from typing import Any

class Box:
    def __init__(self, item: Any):
        self.item = item
    
    def get(self) -> Any:
        return self.item
```

Every time you use this class, type checkers can't help you:

```python
box = Box("hello")
item = box.get()  # Type: Any (no type information!)
item.upper()  # No autocomplete, no type checking
```

### With TypeVars (Good):

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Box(Generic[T]):
    def __init__(self, item: T):
        self.item = item
    
    def get(self) -> T:
        return self.item
```

Now when you create an instance, types are preserved:

```python
box: Box[str] = Box("hello")
item = box.get()  # Type: str (type checker knows!)
item.upper()  # ✅ Autocomplete works! Type checking works!
```

## Using TypeVars with Functions

### Simple Function Example

```python
T = TypeVar("T")

def identity(value: T) -> T:
    """Returns the same value passed in, preserving its type."""
    return value

# Type checker knows these:
x = identity(5)        # Type: int
y = identity("hello")  # Type: str
z = identity([1, 2])   # Type: list[int]
```

### Function with Bounded TypeVar

```python
from typing import TypeVar

class Comparable:
    def __lt__(self, other) -> bool:
        ...

T = TypeVar("T", bound=Comparable)

def minimum(a: T, b: T) -> T:
    """Returns the smaller of two values."""
    return a if a < b else b

# Works with anything that implements comparison
result = minimum(5, 10)           # int
result = minimum("a", "z")        # str
result = minimum(my_obj1, my_obj2)  # MyComparableClass
```

## Using TypeVars with Classes

### Generic Container Example

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self):
        self._items: list[T] = []
    
    def push(self, item: T) -> None:
        self._items.append(item)
    
    def pop(self) -> T:
        return self._items.pop()
    
    def peek(self) -> T:
        return self._items[-1]
```

Using it:

```python
# Stack of integers
int_stack: Stack[int] = Stack()
int_stack.push(42)
int_stack.push(100)
value = int_stack.pop()  # Type: int

# Stack of strings
str_stack: Stack[str] = Stack()
str_stack.push("hello")
str_stack.push("world")
text = str_stack.pop()  # Type: str

# Type checking catches errors:
int_stack.push("oops")  # ❌ Type error: expected int, got str
```

### Multiple TypeVars

```python
K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type

class Cache(Generic[K, V]):
    def __init__(self):
        self._data: dict[K, V] = {}
    
    def set(self, key: K, value: V) -> None:
        self._data[key] = value
    
    def get(self, key: K) -> V | None:
        return self._data.get(key)
```

Using it:

```python
# Cache with string keys and integer values
cache: Cache[str, int] = Cache()
cache.set("age", 25)
cache.set("count", 100)
age = cache.get("age")  # Type: int | None

# Cache with integer keys and custom objects
class User:
    name: str

user_cache: Cache[int, User] = Cache()
user_cache.set(1, User(name="Alice"))
user = user_cache.get(1)  # Type: User | None
```

## Bounded vs Constrained TypeVars

### Bounded TypeVar (Single Upper Bound)

```python
from typing import TypeVar

class Shape:
    def area(self) -> float:
        ...

T = TypeVar("T", bound=Shape)

def total_area(shapes: list[T]) -> float:
    """Works with Shape or any subclass."""
    return sum(s.area() for s in shapes)

# Valid with any Shape subclass
circles: list[Circle] = [...]
rectangles: list[Rectangle] = [...]
total_area(circles)     # ✅ OK if Circle extends Shape
total_area(rectangles)  # ✅ OK if Rectangle extends Shape
```

### Constrained TypeVar (Multiple Specific Types)

```python
from typing import TypeVar

# Only allows str or bytes, nothing else
AnyStr = TypeVar("AnyStr", str, bytes)

def concat(a: AnyStr, b: AnyStr) -> AnyStr:
    """Concatenates two strings or two bytes, but not mixed."""
    return a + b

concat("hello", "world")  # ✅ OK, returns str
concat(b"hello", b"world")  # ✅ OK, returns bytes
concat("hello", b"world")  # ❌ Type error: can't mix str and bytes
concat(123, 456)  # ❌ Type error: int not allowed
```

## Real-World Examples

### Example 1: Repository Pattern

```python
from typing import TypeVar, Generic, Protocol

class Identifiable(Protocol):
    id: int

T = TypeVar("T", bound=Identifiable)

class Repository(Generic[T]):
    def __init__(self):
        self._items: dict[int, T] = {}
    
    def add(self, item: T) -> None:
        self._items[item.id] = item
    
    def get(self, id: int) -> T | None:
        return self._items.get(id)
    
    def all(self) -> list[T]:
        return list(self._items.values())

# Usage:
class User:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class Product:
    def __init__(self, id: int, title: str):
        self.id = id
        self.title = title

user_repo: Repository[User] = Repository()
user_repo.add(User(1, "Alice"))
user = user_repo.get(1)  # Type: User | None

product_repo: Repository[Product] = Repository()
product_repo.add(Product(1, "Laptop"))
product = product_repo.get(1)  # Type: Product | None
```

### Example 2: API Response Wrapper

```python
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None
    error: str | None

# Usage with different data types:
class UserData(BaseModel):
    id: int
    name: str

class OrderData(BaseModel):
    order_id: str
    total: float

def get_user(user_id: int) -> ApiResponse[UserData]:
    return ApiResponse(
        success=True,
        data=UserData(id=user_id, name="Alice"),
        error=None
    )

def get_order(order_id: str) -> ApiResponse[OrderData]:
    return ApiResponse(
        success=True,
        data=OrderData(order_id=order_id, total=99.99),
        error=None
    )

# Type checker knows the data type:
user_response = get_user(1)
if user_response.data:
    print(user_response.data.name)  # ✅ Knows this is UserData

order_response = get_order("123")
if order_response.data:
    print(order_response.data.total)  # ✅ Knows this is OrderData
```

### Example 3: Decorator with Type Preservation

```python
from typing import TypeVar, Callable, ParamSpec

P = ParamSpec("P")  # For function parameters
R = TypeVar("R")     # For return type

def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that logs function calls while preserving type information."""
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Returned {result}")
        return result
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

@log_calls
def greet(name: str) -> str:
    return f"Hello, {name}!"

# Type information is preserved:
result = add(2, 3)      # Type: int
message = greet("Bob")  # Type: str
```

## Common Patterns and Best Practices

### Pattern 1: Self-Returning Methods

```python
from typing import TypeVar

T = TypeVar("T", bound="Builder")

class Builder:
    def __init__(self):
        self._config = {}
    
    def set_name(self: T, name: str) -> T:
        self._config["name"] = name
        return self  # Returns same type as instance
    
    def set_age(self: T, age: int) -> T:
        self._config["age"] = age
        return self

class ExtendedBuilder(Builder):
    def set_email(self: T, email: str) -> T:
        self._config["email"] = email
        return self

# Method chaining preserves the actual type:
builder = ExtendedBuilder()
result = builder.set_name("Alice").set_age(30).set_email("a@example.com")
# Type of result is ExtendedBuilder, not just Builder!
```

### Pattern 2: Factory Functions

```python
from typing import TypeVar, Type

T = TypeVar("T")

def create_instance(cls: Type[T], *args, **kwargs) -> T:
    """Generic factory function."""
    return cls(*args, **kwargs)

class Dog:
    def __init__(self, name: str):
        self.name = name

class Cat:
    def __init__(self, name: str):
        self.name = name

dog = create_instance(Dog, "Buddy")  # Type: Dog
cat = create_instance(Cat, "Whiskers")  # Type: Cat
```

### Pattern 3: Converters

```python
from typing import TypeVar, Callable

Input = TypeVar("Input")
Output = TypeVar("Output")

class Converter(Generic[Input, Output]):
    def __init__(self, converter_func: Callable[[Input], Output]):
        self._func = converter_func
    
    def convert(self, value: Input) -> Output:
        return self._func(value)

# String to int converter
str_to_int: Converter[str, int] = Converter(int)
number = str_to_int.convert("42")  # Type: int

# List to length converter
list_to_len: Converter[list, int] = Converter(len)
length = list_to_len.convert([1, 2, 3])  # Type: int
```

## Common Pitfalls

### Pitfall 1: Using TypeVar as a Type

```python
T = TypeVar("T")

# ❌ Wrong: Using TypeVar directly as a type
def process(data: T) -> None:  # This doesn't work as you might expect
    pass

# ✅ Correct: Use TypeVar in a generic context
def process(data: list[T]) -> T:  # Now T is bound properly
    return data[0]
```

### Pitfall 2: TypeVar Scope

```python
T = TypeVar("T")

# ❌ Wrong: T is unrelated in each function
def func1(x: T) -> T:
    return x

def func2(y: T) -> T:
    return y

result = func2(func1(5))  # T could be different types!

# ✅ Correct: Use explicitly in a single context
def transform(x: T, transformer: Callable[[T], T]) -> T:
    return transformer(x)
```

### Pitfall 3: Mixing Type Vars

```python
T = TypeVar("T")
U = TypeVar("U")

# ❌ This allows mixing types incorrectly
def bad_combine(a: T, b: U) -> T | U:
    return a if random.choice([True, False]) else b

# ✅ Better: Make the relationship explicit
def good_combine(a: T, b: T) -> T:
    return a if random.choice([True, False]) else b
```

## Summary

**TypeVars enable generic programming with type safety:**

| Feature | Syntax | Purpose |
|---------|--------|---------|
| **Unbounded** | `T = TypeVar("T")` | Any type allowed |
| **Bounded** | `T = TypeVar("T", bound=BaseClass)` | Must inherit from base |
| **Constrained** | `T = TypeVar("T", str, bytes)` | Only specific types |
| **Multiple** | `K = TypeVar("K"); V = TypeVar("V")` | Independent type params |

**Key Benefits:**
- ✅ Write reusable, generic code
- ✅ Preserve type information through transformations
- ✅ Enable better IDE autocomplete
- ✅ Catch type errors at development time
- ✅ Self-documenting code with clear type relationships

**Use TypeVars when you want code that works with multiple types while maintaining type safety!** 🎯
