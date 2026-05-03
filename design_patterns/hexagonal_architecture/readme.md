# Hexagonal Architecture

<img width="1254" height="1254" alt="hexagonal-architecture" src="https://github.com/user-attachments/assets/250300d3-23c8-4873-9f9c-32705f803c31" />

Hexagonal Architecture (also called Ports and Adapters, introduced by Alistair Cockburn) is built on the principle of isolating an application's core business logic from external concerns like databases, UIs, and third-party services. The domain sits at the center and defines *ports*—abstract interfaces describing what it needs from or offers to the outside world—while *adapters* on the periphery implement those ports to connect with specific technologies (a Postgres adapter, a REST adapter, a CLI adapter, etc.). Dependencies flow inward: the core knows nothing about adapters, only about its own ports, which inverts the traditional layered dependency on infrastructure. This symmetry between driving adapters (which invoke the application, like HTTP controllers or test harnesses) and driven adapters (which the application invokes, like repositories or message brokers) means you can swap implementations freely, test the core in isolation with fakes, and defer infrastructure decisions—keeping business rules technology-agnostic and the system resilient to change.

## Misc. Nuggets

Driving (primary) adapters drive the application — like REST controllers or CLI handlers. Driven (secondary) adapters are driven BY the application — like database or messaging clients.

For example, a Postgres repository is driven by the core — the application calls it to persist data. REST controllers, gRPC handlers, and CLI handlers all drive the application.
