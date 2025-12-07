# Entities vs Value Objects

This is a Domain-Driven Design (DDD) distinction.

## Entities (have identity)
Entities are objects that have a unique identity that persists over time. Two entities are considered different even if all their attributes are identical—what matters is their ID.

## Value Objects (no identity, equality by value)
Value objects are defined entirely by their attributes. They have no conceptual identity—two value objects with the same data are considered equal and interchangeable.
