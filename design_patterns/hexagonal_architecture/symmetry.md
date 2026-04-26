# The Forgotten Symmetry of Hexagonal Architecture

## Why the Shape Doesn't Matter (And Why That's the Point)

Hexagonal architecture, introduced by Alistair Cockburn in 2005, is one of the most widely cited and most widely misunderstood architectural patterns in software. Most teams encounter it as "ports and adapters keep your domain pure" — a useful slogan that smuggles in a misreading of the original idea.

The hexagon shape is arbitrary. Cockburn could have called it triangular architecture, octagonal architecture, or — as he later admitted he probably should have — just "ports and adapters." What matters is what the hexagon was chosen *against*: the rectangle.

A rectangle has a top and a bottom. In layered architecture diagrams, this is load-bearing: the UI sits on top, the database sits at the bottom, and the domain is sandwiched in the middle, structurally subordinate to both. Even when teams adopt dependency inversion to make the database "depend on" the domain, the diagram still encodes a hierarchy. Persistence feels foundational. The UI feels like the surface. The domain feels like the filling.

The hexagon was a deliberate rejection of that geometry. It has no top, no bottom, no privileged side. Every edge is the same. The domain sits in the middle, and every external concern — HTTP handlers, databases, message brokers, file systems, third-party APIs, the test harness — is just another actor poking at one of the equivalent edges. The shape carries no information. The symmetry does.

## Two Kinds of Ports, Shaped by Different Forces

Once you take the symmetry seriously, the most important practical distinction in hexagonal architecture comes into focus: the difference between driving ports and driven ports. These are sometimes called primary and secondary ports, or left-side and right-side ports.

A driving port is one through which an external actor initiates a conversation with the domain. HTTP request handlers, CLI commands, message consumers, scheduled jobs — anything that picks up the phone and calls the domain. A driven port is one through which the domain initiates a conversation with the outside world. Repositories, email senders, payment gateways, clocks, ID generators — anything the domain reaches out to in order to get something done.

This distinction is well-known. What is less well-appreciated is that the two kinds of ports must be designed under fundamentally different pressures, and conflating those pressures is the most common way teams accidentally build layered architecture wearing a hexagonal costume.

### Driving Ports Are Shaped by Use Cases

Driving ports should describe what an external actor wants to accomplish, expressed in the vocabulary of the use case. `PlaceOrder`, `CancelReservation`, `GenerateMonthlyReport`, `RegisterMember`. These are verbs from the outside world's perspective, and their shape should be dictated by the question "what is the actor trying to do?"

A driving port is essentially the application's API to itself. Its method signatures should read like a menu of things you can ask the system to do, with arguments that describe the request in business terms — not in terms of the HTTP framing or the CLI parsing or whatever delivery mechanism happens to be in use today. If your driving port has a parameter called `httpRequest`, the port is wrong. The HTTP adapter should translate that into domain inputs before crossing the boundary.

### Driven Ports Are Shaped by Domain Needs

Driven ports are where most teams quietly abandon the architecture without realizing it. The temptation is overwhelming to define interfaces that look like the underlying technology. `IUserRepository` with `save(user)`, `findById(id)`, `findAll()`, `delete(id)`. These look like ports, but they are not ports in any meaningful sense. They are thin abstractions over a database, and the database's vocabulary has been smuggled into the domain.

A correctly shaped driven port is dictated by what the domain needs to ask for, expressed in the domain's own language. If the use case is "send a re-engagement email to members who haven't logged in for ninety days," the driven port should not be `userRepository.findAll()` followed by domain code that filters by `lastLoginAt`. It should be something like `dormantMembers.since(ninetyDaysAgo)`, returning a collection of domain concepts. The adapter on the other side decides whether that's a SQL query, a Redis lookup, a call to a microservice, or six CSV files on disk. The domain doesn't know and doesn't care.

The shift is subtle but consequential. In the first version, the domain knows it is iterating over a list of users and applying a predicate. In the second version, the domain is asking a collaborator a domain-level question and receiving a domain-level answer. The collaborator's identity — database, service, file — has been fully erased.

## The Real Test for Hexagonal Architecture

The usual selling points for hexagonal architecture are testability and database-swappability. Both are real benefits, but both are downstream consequences of something more fundamental, and both can be achieved in shallow ways that don't actually deliver the architecture's promise.

A sharper test is this: could you swap a driven adapter for something in an entirely different category without the domain noticing? Replacing Postgres with MySQL is trivial and proves nothing — both speak the same vocabulary. The interesting question is whether you could replace your Postgres adapter with an in-memory list, an HTTP call to another service, or a flat-file store, and have the domain remain completely unchanged.

If that swap feels forced — if the port's method names don't quite fit the new adapter, if you find yourself wanting to add `flush()` or `transaction()` to the interface to make the SQL adapter happy — then the port was shaped by the adapter, not by the domain. You have layered architecture in disguise. The domain is depending on a database-flavored abstraction rather than on its own needs expressed in its own words.

## The Conversation You Get to Have

The deepest reason hexagonal architecture matters is not technical. It is conversational.

When the domain is shaped by ports defined in domain language, you get a place in the codebase where the team can have a conversation about the business — what an order is, what cancellation means, what makes a member dormant — without that conversation being constantly derailed by infrastructure vocabulary. The domain becomes a space where domain experts and engineers speak the same language, where the code reads like a description of the business rather than a description of the database schema or the HTTP contract.

This is what the symmetry of the hexagon is really for. Persistence is not "below" the domain. The UI is not "above" it. They are peers, all of them just actors the domain converses with through ports it defined on its own terms. The domain is sovereign, and the ports are its diplomatic protocol.

The hexagon, in the end, is a political statement about who gets to set the vocabulary. The answer is: the domain does. Everything else is an adapter.
