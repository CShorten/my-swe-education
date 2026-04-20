# The `services` Folder in Hexagonal Architecture

## The Three-Folder Mental Model

In a typical Go hexagonal layout, the three folders have very specific jobs:

| Folder | Role | Knows About |
|---|---|---|
| `internal/domain` | Core business entities, value objects, domain rules | Nothing outside itself |
| `internal/ports` | Interfaces (contracts) for what the app needs and offers | `domain` only |
| `internal/service` | Application logic that orchestrates domain + ports | `domain` + `ports` |

The `service` layer is the **hexagon itself** — it is the application core that gets wrapped by adapters on the outside.

## What `service` Actually Does

A service is a **use-case orchestrator**. It doesn't contain business rules (those live in `domain`), and it doesn't talk to infrastructure directly (that's what `ports` hide). Instead, it:

1. Receives a request from a **driving adapter** (HTTP handler, CLI, gRPC server)
2. Validates inputs and coordinates domain objects
3. Calls **driven adapters** through port interfaces (database, LLM, message bus)
4. Returns a result or domain error

Think of it as the answer to the question: *"What does my application do, independent of how it's deployed or stored?"*

## The Service Struct: Dependencies as Ports

```go
type Service struct {
    store             ports.DataStore
    embeddingService  ports.EmbeddingService
    modelService      ports.ModelService
}
```

Every field is a `ports.*` interface, never a concrete type. This is the heart of the hexagonal architecture: the core depends only on abstractions it defines itself. These are driven ports, the interfaces the core needs the outside world to fulfill for it.

## Concrete Example

Mapping this to something close to your world — imagine an Engram-like memory service:

```go
// internal/domain/memory.go
package domain

type Memory struct {
    ID         string
    ScopeID    string
    Content    string
    Properties map[string]string
}

func (m *Memory) Validate() error { /* business rules */ }
```

```go
// internal/ports/ports.go
package ports

type MemoryRepository interface {
    Save(ctx context.Context, m *domain.Memory) error
    FindByScope(ctx context.Context, scopeID string) ([]*domain.Memory, error)
}

type Embedder interface {
    Embed(ctx context.Context, text string) ([]float32, error)
}
```

```go
// internal/service/memory_service.go
package service

type MemoryService struct {
    repo     ports.MemoryRepository
    embedder ports.Embedder
}

func (s *MemoryService) Commit(ctx context.Context, scopeID, content string) (*domain.Memory, error) {
    m := &domain.Memory{ScopeID: scopeID, Content: content}
    if err := m.Validate(); err != nil {
        return nil, err
    }

    // Coordinate two ports — but we don't know or care that
    // one is Weaviate and the other is Voyage.
    vec, err := s.embedder.Embed(ctx, content)
    if err != nil {
        return nil, err
    }
    m.ID = generateID(vec)

    if err := s.repo.Save(ctx, m); err != nil {
        return nil, err
    }
    return m, nil
}
```

Notice the service **depends on interfaces, never concrete implementations**. The Weaviate client lives in something like `internal/adapters/weaviate/` and satisfies `ports.MemoryRepository`. Swap it for Postgres tomorrow and the service doesn't change a line.

## Why Keep Services Thin

A common failure mode is letting services turn into a dumping ground. A healthy service method is usually 10–40 lines and reads like a recipe. If you see branching business logic piling up, that logic probably belongs in a domain method or a dedicated domain service.

Rough heuristic for where code belongs:

- **"This rule is always true about a Memory"** → `domain`
- **"This is how we store/fetch/embed a Memory"** → `ports` + adapter
- **"This is what happens when a user commits a memory"** → `service`

## Dependency Direction

The golden rule: **dependencies point inward**.

```
HTTP handler → service → ports ← Weaviate adapter
                  ↓
               domain
```

The adapters on the right side implement the ports; the service never imports the adapter package. This is what makes the core testable — in unit tests you pass in fake implementations of `ports.MemoryRepository` and never touch a real database.

## Testing Consequences

Because services only depend on interfaces, service tests are:

- Fast (no network, no DB)
- Deterministic (fakes, not mocks-with-expectations)
- Focused on orchestration logic, not infrastructure quirks

Infrastructure correctness gets tested separately at the adapter layer (integration tests against a real Weaviate, real Postgres, etc.).

## Common Pitfalls

- **Anemic services that just forward to the repo.** If `service.GetX` literally calls `repo.GetX` and returns, you probably don't need the service method — or it's a sign the domain logic got pushed somewhere else.
- **Services calling other services directly in sprawling chains.** Prefer composing at the edge (the HTTP handler wires things) or introducing a domain event.
- **Importing adapter packages from `service`.** This quietly breaks the hexagon. Enforce it with a lint rule or an architecture test.
- **Putting transaction/DB concerns in the service.** Wrap them in a port (e.g., `UnitOfWork`) so the service stays infrastructure-agnostic.

## TL;DR

`internal/service` is where **use cases** live. It's the verb layer — the "what the application does" — sitting between pure domain objects and the outside world it reaches through ports. Keep it thin, keep it dependent on interfaces only, and the rest of hexagonal architecture's benefits fall out for free.
