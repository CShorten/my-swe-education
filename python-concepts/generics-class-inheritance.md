# Generics for Class Inheritance

This kind of syntax is common in type-safe frameworks where different nodes in a computational graph have typed inputs and outputs (e.g. pipeline DAGs, LLM workflow frameworks, or data processing graphs).
By parameterizing BaseNode with input and output types, you get:

Static type checking in editors (mypy, pyright, etc.)

Safer subclassing — e.g., you can’t pass the wrong data type to a node.

Self-documenting code — it’s obvious what kind of data flows through this node.

```python
from typing import Generic, TypeVar

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")

class BaseNode(Generic[TIn, TOut]):
    def run(self, data: TIn) -> TOut:
        raise NotImplementedError

class MultiplyInput:
    x: float
    y: float

class MultiplyOutput:
    result: float

class MultiplyNode(BaseNode[MultiplyInput, MultiplyOutput]):
    def run(self, data: MultiplyInput) -> MultiplyOutput:
        return MultiplyOutput(result=data.x * data.y)
```
