**Registry Pattern**
- Acts like a "global phonebook" for objects
- Maintains a central store of objects by name/key
- Objects are typically already constructed when added to registry
- Main purpose is object lookup and retrieval
- Example use case:
```python
class ShapeRegistry:
    def __init__(self):
        self._shapes = {}
    
    def register(self, name: str, shape: Shape):
        self._shapes[name] = shape
    
    def get_shape(self, name: str) -> Shape:
        return self._shapes[name]

# Usage
registry = ShapeRegistry()
registry.register("small_square", Square(5))
my_shape = registry.get_shape("small_square")
```

**Factory Pattern**
- Focused on object creation
- Encapsulates the logic for constructing objects
- Objects are created on-demand when requested
- Main purpose is hiding complex object creation
- Example use case:
```python
class ShapeFactory:
    def create_shape(self, shape_type: str, **params) -> Shape:
        if shape_type == "square":
            return Square(side_length=params["side_length"])
        elif shape_type == "circle":
            return Circle(radius=params["radius"])
        raise ValueError(f"Unknown shape type: {shape_type}")

# Usage
factory = ShapeFactory()
new_square = factory.create_shape("square", side_length=5)
```

The key distinction is that a Registry manages existing objects while a Factory creates new ones. They're often used together:
- Factory creates the objects
- Registry stores them for later lookup
