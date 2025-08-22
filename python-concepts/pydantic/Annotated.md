# Pydantic `Annotated`: A Comprehensive Guide

## Introduction

Pydantic's `Annotated` feature, introduced in Pydantic v2, leverages Python's `typing.Annotated` to provide a more expressive and flexible way to define field constraints, validation rules, and metadata. This approach separates type information from validation logic, making code more readable and maintainable.

## Basic Syntax

The `Annotated` type allows you to attach metadata to type hints:

```python
from typing import Annotated
from pydantic import BaseModel, Field

class User(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=50)]
    age: Annotated[int, Field(ge=0, le=150)]
    email: Annotated[str, Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')]
```

## Core Components

### Field Constraints

`Annotated` works seamlessly with Pydantic's `Field` function to define validation rules:

```python
from typing import Annotated
from pydantic import BaseModel, Field
from decimal import Decimal

class Product(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    price: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    description: Annotated[str, Field(default="", max_length=500)]
    in_stock: Annotated[bool, Field(default=True)]
```

### Custom Validators

You can combine `Annotated` with custom validation functions:

```python
from typing import Annotated
from pydantic import BaseModel, Field, field_validator
import re

def validate_phone(v):
    if not re.match(r'^\+?1?\d{9,15}$', v):
        raise ValueError('Invalid phone number format')
    return v

PhoneNumber = Annotated[str, Field(description="Phone number in international format")]

class Contact(BaseModel):
    name: str
    phone: PhoneNumber
    
    @field_validator('phone')
    @classmethod
    def check_phone(cls, v):
        return validate_phone(v)
```

## Advanced Usage

### Multiple Constraints

You can stack multiple annotations for complex validation:

```python
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints
from pydantic.types import constr

Username = Annotated[
    str,
    Field(min_length=3, max_length=20),
    Field(pattern=r'^[a-zA-Z0-9_]+$'),
    Field(description="Username must be alphanumeric with underscores")
]

class Account(BaseModel):
    username: Username
    password: Annotated[str, Field(min_length=8, description="Minimum 8 characters")]
```

### Type Aliases with Annotations

Create reusable type aliases with built-in validation:

```python
from typing import Annotated
from pydantic import BaseModel, Field

# Define reusable types
PositiveInt = Annotated[int, Field(gt=0)]
NonEmptyStr = Annotated[str, Field(min_length=1)]
EmailStr = Annotated[str, Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')]

class User(BaseModel):
    id: PositiveInt
    name: NonEmptyStr
    email: EmailStr
    age: Annotated[int, Field(ge=13, le=120, description="Age in years")]
```

### Documentation and Metadata

`Annotated` is excellent for embedding documentation:

```python
from typing import Annotated
from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    status: Annotated[
        int, 
        Field(
            ge=100, 
            le=599,
            description="HTTP status code",
            examples=[200, 404, 500]
        )
    ]
    message: Annotated[
        str,
        Field(
            max_length=200,
            description="Response message",
            examples=["Success", "Not Found", "Internal Server Error"]
        )
    ]
    data: Annotated[
        dict,
        Field(
            default_factory=dict,
            description="Response payload data"
        )
    ]
```

## Benefits and Advantages

### Improved Readability

`Annotated` separates type information from validation logic, making code easier to read and understand:

```python
# Clear separation of concerns
Price = Annotated[float, Field(gt=0, description="Price in USD")]
Quantity = Annotated[int, Field(ge=1, description="Item quantity")]

class OrderItem(BaseModel):
    price: Price
    quantity: Quantity
```

### Reusability

Define validation rules once and reuse them across models:

```python
from typing import Annotated
from pydantic import BaseModel, Field

# Reusable constraints
IDField = Annotated[int, Field(gt=0, description="Unique identifier")]
NameField = Annotated[str, Field(min_length=1, max_length=100)]

class User(BaseModel):
    id: IDField
    name: NameField

class Product(BaseModel):
    id: IDField
    name: NameField
```

### Enhanced IDE Support

Better IDE support with clearer type hints and validation information visible in tooltips and autocompletion.

## Practical Examples

### Configuration Model

```python
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from pathlib import Path

class DatabaseConfig(BaseModel):
    host: Annotated[str, Field(description="Database host")]
    port: Annotated[int, Field(ge=1, le=65535, default=5432)]
    database: Annotated[str, Field(min_length=1)]
    username: Annotated[str, Field(min_length=1)]
    password: Annotated[str, Field(min_length=8)]
    ssl_mode: Annotated[
        Literal["disable", "allow", "prefer", "require"], 
        Field(default="prefer")
    ]

class AppConfig(BaseModel):
    debug: Annotated[bool, Field(default=False)]
    log_level: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR"], 
        Field(default="INFO")
    ]
    secret_key: Annotated[str, Field(min_length=32)]
    database: DatabaseConfig
```

### API Model with Validation

```python
from typing import Annotated, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class UserCreate(BaseModel):
    username: Annotated[
        str, 
        Field(
            min_length=3, 
            max_length=20,
            pattern=r'^[a-zA-Z0-9_]+$',
            description="Username (alphanumeric and underscore only)"
        )
    ]
    email: Annotated[EmailStr, Field(description="Valid email address")]
    password: Annotated[
        str,
        Field(
            min_length=8,
            description="Password (minimum 8 characters)",
        )
    ]
    role: Annotated[UserRole, Field(default=UserRole.USER)]
    is_active: Annotated[bool, Field(default=True)]

class UserResponse(BaseModel):
    id: Annotated[int, Field(gt=0)]
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
```

## Migration from Pydantic v1

### Before (Pydantic v1)
```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=150)
```

### After (Pydantic v2 with Annotated)
```python
from typing import Annotated
from pydantic import BaseModel, Field

class User(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=50)]
    age: Annotated[int, Field(ge=0, le=150)]
```

## Best Practices

### Create Type Aliases for Common Patterns

```python
from typing import Annotated
from pydantic import Field

# Common field types
ID = Annotated[int, Field(gt=0, description="Unique identifier")]
Name = Annotated[str, Field(min_length=1, max_length=100)]
Email = Annotated[str, Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')]
```

### Use Descriptive Field Documentation

```python
class User(BaseModel):
    age: Annotated[
        int, 
        Field(
            ge=13, 
            le=120,
            description="User's age in years (must be 13 or older)",
            examples=[25, 30, 45]
        )
    ]
```

### Combine with Custom Validators When Needed

```python
from typing import Annotated
from pydantic import BaseModel, Field, field_validator

class Account(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=20)]
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v
```

## Conclusion

Pydantic's `Annotated` feature represents a significant improvement in how we define and validate data models. It provides better separation of concerns, improved readability, enhanced reusability, and superior IDE support. By leveraging `Annotated`, you can create more maintainable and self-documenting code while taking full advantage of Python's type system.

The combination of clear type hints, embedded validation rules, and comprehensive documentation makes `Annotated` an essential tool for modern Python development with Pydantic.
