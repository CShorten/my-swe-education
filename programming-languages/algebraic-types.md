# Understanding Algebraic Types in Programming

Algebraic Data Types (ADTs) are composite types formed by combining other types using sum and product operations. They are fundamental to functional programming but their concepts can be implemented in Python as well. This guide explores the two main categories of algebraic types: product types and sum types.

## Relationship with Generics

While algebraic types and generics are related concepts, they serve different purposes:

- **Generics** allow you to write code that works with any type, providing type parameters that can be filled in later. They're about parametric polymorphism.
- **Algebraic Types** are about combining types to create new ones. They're about type construction.

You can use both together - generic algebraic types are particularly powerful. Here's an example:

```python
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class List(Generic[T]):
    """A generic linked list - both generic and an algebraic type"""
    def __init__(self, head: Optional[T] = None, tail: Optional['List[T]'] = None):
        self.head = head
        self.tail = tail
```

## Product Types

Product types represent combinations of multiple values, where all fields exist simultaneously. In mathematics, these are like Cartesian products.

### Using Pydantic for Product Types

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: int
    username: str
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    class Config:
        frozen = True  # Makes the model immutable

# Pydantic handles validation automatically
try:
    user = User(
        id=1,
        username="john_doe",
        email="invalid-email"  # This will raise a validation error
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

### Nested Product Types with Pydantic

```python
from pydantic import BaseModel
from typing import List as TypeList

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class Company(BaseModel):
    name: str
    addresses: TypeList[Address]
    
# The total number of possible values is the product of all possible values
# for each field in both Address and Company
```

## Sum Types

Sum types (also called variant types or tagged unions) represent alternatives where a value can be one of several possibilities.

### Sum Types with Pydantic

```python
from pydantic import BaseModel
from typing import Literal, Union

class Success(BaseModel):
    status: Literal["success"]
    data: dict

class Error(BaseModel):
    status: Literal["error"]
    error_code: int
    message: str

# ApiResponse is a sum type
ApiResponse = Union[Success, Error]

def handle_response(response: ApiResponse) -> str:
    match response:
        case Success(data=data):
            return f"Success: {data}"
        case Error(message=msg):
            return f"Error: {msg}"

# Example usage
success = Success(status="success", data={"user_id": 123})
error = Error(status="error", error_code=404, message="Not found")
```

### Generic Sum Types with Pydantic

```python
from typing import Generic, TypeVar, Union
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')
E = TypeVar('E')

class Result(GenericModel, Generic[T, E]):
    """A generic result type that can hold either a success value or an error"""
    value: Union[T, E]
    is_success: bool

    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        return cls(value=value, is_success=True)

    @classmethod
    def error(cls, error: E) -> 'Result[T, E]':
        return cls(value=error, is_success=False)

# Example usage with Pydantic models
class UserData(BaseModel):
    id: int
    name: str

class ValidationError(BaseModel):
    code: int
    message: str

# Create a specific Result type for user operations
UserResult = Result[UserData, ValidationError]

def create_user(name: str) -> UserResult:
    if len(name) < 3:
        return UserResult.error(
            ValidationError(code=400, message="Name too short")
        )
    return UserResult.success(
        UserData(id=1, name=name)
    )
```

## Pattern Matching with Pydantic Models

```python
from pydantic import BaseModel
from typing import Union, Literal

class Circle(BaseModel):
    type: Literal["circle"]
    radius: float

class Rectangle(BaseModel):
    type: Literal["rectangle"]
    width: float
    height: float

Shape = Union[Circle, Rectangle]

def calculate_area(shape: Shape) -> float:
    match shape:
        case Circle(radius=r):
            return 3.14159 * r * r
        case Rectangle(width=w, height=h):
            return w * h
        case _:
            raise ValueError("Unknown shape")
```

## Best Practices

1. Use Pydantic models for product types to get:
   - Automatic validation
   - JSON serialization/deserialization
   - Data parsing and cleaning
   - IDE support
2. Combine generics with algebraic types for maximum flexibility
3. Use Literal types to create type-safe discriminated unions
4. Leverage Pydantic's GenericModel for reusable generic types
5. Make illegal states unrepresentable through type design
6. Use frozen models when immutability is desired
7. Take advantage of Pydantic's built-in validation features

## Key Differences Between Generics and Algebraic Types

1. **Scope**:
   - Generics: Define type parameters that can be filled in later
   - Algebraic Types: Define new types by combining existing types

2. **Purpose**:
   - Generics: Enable code reuse with type safety
   - Algebraic Types: Model data structures and domain concepts

3. **Composition**:
   - Generics: Parameterize types with other types
   - Algebraic Types: Combine types using sum and product operations

4. **Usage**:
   - Generics: Often used with collections and algorithms
   - Algebraic Types: Often used for domain modeling and error handling

Algebraic types provide a powerful way to model complex domains and ensure type safety. When combined with Pydantic's validation capabilities and Python's type system, they become even more powerful for building robust applications.
