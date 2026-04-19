# Hexagonal Architecture: The `domains` Folder

Hexagonal Architecture (also called **Ports and Adapters**, coined by Alistair Cockburn in 2005) is about isolating your core business logic from the outside world — databases, APIs, UIs, message queues, etc. The core doesn't know or care what's on the other side; it just defines what it needs.

## The core idea

Your application has a **domain** (the business logic) surrounded by **ports** (interfaces that define what the domain needs or offers) and **adapters** (concrete implementations that plug into those ports).

The key asymmetry: **driving adapters** (HTTP controllers, CLI, event consumers) depend on the domain, and **driven adapters** (Postgres repositories, email senders, payment gateways) also depend on the domain — the domain depends on nothing. That's the whole point. Dependencies point inward.

## Ports vs adapters

- **Port** = an interface defined inside the domain, expressing what the domain needs or offers. "I need to save an `Order`." "I offer a `placeOrder` operation."
- **Adapter** = the concrete implementation that lives outside the domain. "Here's how we save an `Order` to Postgres." "Here's the HTTP controller that calls `placeOrder`."

Two flavors:

- **Inbound / driving ports** — the API the domain exposes (use cases). Implemented by application services.
- **Outbound / driven ports** — the API the domain requires from the outside. Implemented by infrastructure adapters.

## The `domains/` folder

A common convention is to organize code by **bounded context** (in DDD terms) under `domains/`, where each subfolder is one self-contained domain. Inside each domain, you split by role — not by technical layer.

Here's a realistic structure for a typical backend service:

```
src/
├── domains/
│   ├── ordering/
│   │   ├── domain/
│   │   │   ├── model/
│   │   │   │   ├── Order.ts
│   │   │   │   ├── OrderLine.ts
│   │   │   │   ├── OrderId.ts              # value object
│   │   │   │   └── OrderStatus.ts
│   │   │   ├── events/
│   │   │   │   ├── OrderPlaced.ts
│   │   │   │   └── OrderCancelled.ts
│   │   │   ├── services/
│   │   │   │   └── PricingPolicy.ts        # pure domain logic
│   │   │   └── errors/
│   │   │       └── InsufficientStock.ts
│   │   ├── application/
│   │   │   ├── ports/
│   │   │   │   ├── in/
│   │   │   │   │   ├── PlaceOrderUseCase.ts
│   │   │   │   │   └── CancelOrderUseCase.ts
│   │   │   │   └── out/
│   │   │   │       ├── OrderRepository.ts
│   │   │   │       ├── PaymentGateway.ts
│   │   │   │       └── NotificationSender.ts
│   │   │   └── services/
│   │   │       ├── PlaceOrderService.ts    # implements PlaceOrderUseCase
│   │   │       └── CancelOrderService.ts
│   │   └── infrastructure/
│   │       ├── persistence/
│   │       │   └── PostgresOrderRepository.ts
│   │       ├── web/
│   │       │   └── OrderController.ts
│   │       └── messaging/
│   │           └── KafkaOrderEventPublisher.ts
│   │
│   ├── catalog/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   │
│   └── shipping/
│       ├── domain/
│       ├── application/
│       └── infrastructure/
└── shared/
    └── kernel/                             # types shared across domains
```

## Why each piece exists

### `domain/` — the pure heart

No framework imports, no database, no HTTP. Just entities, value objects, domain events, and pure functions/policies. You should be able to unit-test this with zero mocks. `Order.place()` knows nothing about SQL.

### `application/ports/in/` — inbound use case interfaces

These are what the outside world is allowed to ask the domain to do. `PlaceOrderUseCase.execute(command: PlaceOrderCommand)`. Controllers and CLI commands depend on these interfaces, not on implementations.

### `application/ports/out/` — outbound interfaces

Interfaces the domain needs the world to fulfill. `OrderRepository.save(order: Order)` is declared here, but implemented in `infrastructure/`. This is the **dependency inversion** that makes the hexagon work: the domain owns the contract, infrastructure conforms to it.

### `application/services/` — orchestration

A `PlaceOrderService` loads an `Order` through the repository port, calls domain methods, and publishes events. It implements an inbound port and depends on outbound ports (as interfaces).

### `infrastructure/` — the messy real-world stuff

Adapters implementing outbound ports (`PostgresOrderRepository`), and adapters invoking inbound ports (`OrderController`). This is the only layer that knows about Postgres, HTTP, Kafka, etc.

## The dependency rule

The iron law:

- `domain/` imports nothing from `application/` or `infrastructure/`
- `application/` imports from `domain/` only
- `infrastructure/` imports from `application/` and `domain/`

If you grep for imports in `domain/` and see anything framework-related, something's wrong.

## Practical notes

Different teams name these folders differently. You'll see `core` instead of `domain`, `adapters/primary` and `adapters/secondary` instead of `infrastructure/web` and `infrastructure/persistence`, or a flatter `usecases/` folder instead of splitting ports and services. The *structure* matters more than the *names* — what you want is: pure core → interfaces at the boundary → implementations outside.

Some teams put one domain per module/package with its own `build.gradle` or `package.json`, which enforces the dependency rule at the build-system level. You literally can't import across bounded contexts except through published contracts. This is heavier but pays off on larger codebases.

For smaller services, people often collapse `domain/` and `application/` into one folder called `domain/`, and keep only `domain/` + `infrastructure/`. Fine for small stuff — just know you're trading explicitness for brevity.
