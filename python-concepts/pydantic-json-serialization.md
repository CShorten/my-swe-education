# Pydantic JSON Serialization Guide

## Overview
Pydantic provides robust tools for JSON serialization and deserialization in Python, allowing seamless conversion between Python objects and JSON data while maintaining type safety and validation.

## Basic Serialization
### Model Definition
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    tags: List[str] = []
    metadata: Optional[dict] = None
```

### JSON Serialization Methods
1. **model_dump_json()**: Converts model to JSON string
```python
user = User(
    id=1,
    name="John Doe",
    email="john@example.com",
    created_at=datetime.now(),
    tags=["customer", "active"]
)
json_string = user.model_dump_json()
```

2. **model_dump()**: Converts model to dictionary
```python
dict_data = user.model_dump()
```

## Advanced Features

### Custom Serialization
```python
from pydantic import Field, computed_field

class Product(BaseModel):
    name: str
    price: float
    currency: str = "USD"
    
    @computed_field
    def price_display(self) -> str:
        return f"{self.currency} {self.price:.2f}"
```

### Exclude/Include Fields
```python
# Exclude specific fields
json_string = user.model_dump_json(exclude={'metadata', 'created_at'})

# Include only specific fields
json_string = user.model_dump_json(include={'id', 'name', 'email'})
```

### Handling Datetime Objects
```python
class Event(BaseModel):
    name: str
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

## Best Practices

1. **Type Annotations**
   - Always use explicit type annotations
   - Leverage Optional[] for nullable fields
   - Use Union[] for fields that can accept multiple types

2. **Validation**
   - Use Field() for additional validation
   - Implement custom validators when needed
   - Set default values appropriately

3. **Error Handling**
```python
from pydantic import ValidationError

try:
    user = User.model_validate_json(invalid_json)
except ValidationError as e:
    print(e.json())
```

## Common Patterns

### Nested Models
```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Customer(BaseModel):
    name: str
    addresses: List[Address]
```

### Custom Serialization Logic
```python
class SecureUser(BaseModel):
    username: str
    password: str
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data['password'] = '******'  # Mask password
        return data
```

## Performance Considerations

1. **Bulk Operations**
   - Use list comprehension for batch serialization
   - Consider using model_dump() instead of model_dump_json() when working with large datasets

2. **Memory Usage**
   - Be mindful of nested models depth
   - Use generators for large datasets
   - Consider pagination for large collections

## Common Issues and Solutions

1. **Circular References**
```python
from typing import ForwardRef

class Node(BaseModel):
    value: str
    parent: Optional['Node'] = None

Node.model_rebuild()  # Required for forward references
```

2. **Custom Types**
```python
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

class CustomType:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Type[Any],
        _handler: GetJsonSchemaHandler,
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(cls),
                core_schema.union_schema([
                    core_schema.str_schema(),
                    core_schema.int_schema(),
                ]),
            ]),
        )
```

## Testing Serialization

```python
def test_user_serialization():
    user_data = {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "created_at": "2024-01-01T00:00:00",
        "tags": ["test"]
    }
    
    user = User.model_validate(user_data)
    assert user.model_dump_json()
    assert user.model_dump()["name"] == "Test User"
```
