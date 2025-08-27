# Anti-Corruption Layer (ACL)

A design pattern focused on managing the complexities of serialization and deserialization when an application interacts with an external system or library.

The core purpose is to create a translation layer that prevents the external library's data structures (in this case, from the weaviate-python-client) from "leaking" into and complicating the application's internal logic.

## The Core Problem: Impedance Mismatch
In software engineering, there's often an "impedance mismatch" between different parts of a system. Here, the mismatch is between:

Serializable Data Formats: Simple, universal formats like JSON, which consist of strings, numbers, booleans, lists, and dictionaries. These are essential for sending data over a network (e.g., in an API request), storing it in a cache, or saving it to a database.

Complex Python Objects: The weaviate library uses rich, custom Python classes like wvc.query.Move and Filter.all_of(...). These objects have methods and specific internal states. They cannot be directly represented in JSON.

Imagine you're building a web API using FastAPI (which relies on Pydantic) that allows users to submit complex search queries to a Weaviate database. You can't simply tell your API to expect a weaviate.classes.filters._Filters object in an incoming HTTP request. The code you provided bridges this exact gap.

## How The Code Implements the Solution
This code builds a robust translation layer using Pydantic's validation system to convert simple dictionary/JSON-like structures back into the functional weaviate objects.

1. Custom Pydantic Models as Data Transfer Objects (DTOs)
The code defines Pydantic models (_FilterAndOrSerialise, _HybridNearTextDeserialise, etc.) that mirror the structure of the Weaviate objects but are designed to be easily created from simple Python dictionaries. These act as Data Transfer Objects (DTOs)—their only job is to carry data between the serialized world and the application's domain.

For instance, _FilterAndOrSerialise can be created from a simple dictionary like {"combine": "and", "filters": [...]}.

2. Using Validators for Deserialization Logic
The key mechanism is the @BeforeValidator. These functions intercept the data before Pydantic tries to validate it and apply custom conversion logic.

deserialise_move: Takes a dictionary and explicitly constructs a wvc.query.Move object from it.

deserialise_filter: This is a more complex example that handles polymorphism (when a value can be one of several types). It uses a try...except block to first see if the incoming data represents a simple filter, and if not, it tries to parse it as a complex and/or combination. This makes the deserialization process flexible and robust.

3. Handling Unions and Disambiguation
The _HybridNear... models demonstrate a common technique for serializing a union type (where a value can be either a _HybridNearText or a _HybridNearVector).

The field serialised_class: Literal["_HybridNearText"] is added as a discriminator. When the complex Weaviate object is turned into a dictionary (serialized), this field is added to make it unambiguous what type of object it was. The deserialise_hybrid_vector_type function can then use this field to know which Pydantic DTO to use for validation and reconstruction.

## Broader Software Engineering Significance
This pattern is a cornerstone of modern, service-oriented architecture for several reasons:

Decoupling: Your application's core logic doesn't need to know about the messy details of how weaviate objects are constructed. It can operate on simple, serializable dictionaries or Pydantic models. If the weaviate library changes its classes in a future update, you only need to update this "anti-corruption layer," not your entire application.

Interoperability: It makes your system interoperable. The complex Weaviate query, once serialized, can be sent to any other service, stored in any database, or passed around as plain text, because it has been translated into a universal format.

Maintainability: It isolates the complex, brittle translation logic into one place. This makes the code easier to understand, test, and maintain.

Robustness: By using Pydantic, you get automatic data validation. The system will raise clear errors if an API client sends malformed query data, preventing invalid data from reaching the Weaviate database and causing unexpected errors.
