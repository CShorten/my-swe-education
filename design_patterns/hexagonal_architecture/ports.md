# Ports: The Domain's Contract with the World

Ports are where hexagonal architecture earns its keep. They're the negotiating interface: the domain writes the contract, and everyone else has to sign it.

## What a port actually is

A port is **an interface, defined inside the domain**, that describes one cohesive capability — either something the domain offers or something it needs. That's it. No implementation, no framework types, no JSON, no SQL. Just a contract expressed in the domain's own language.

The crucial thing is ownership: **the domain owns the port**. Infrastructure doesn't "provide" a `UserRepository` interface that the domain happens to use. The domain *declares* what a `UserRepository` is, and infrastructure has to conform. This is dependency inversion — and it's what lets you swap Postgres for DynamoDB, or your email provider from SES to Postmark, without touching a line of business logic.

## Two directions: inbound and outbound

The asymmetry matters. **Inbound ports are implemented by the domain** (an application service). **Outbound ports are implemented by infrastructure** (an adapter). Both interfaces live in the domain module.

| Direction | Who calls whom | Who implements it | Example |
|-----------|---------------|-------------------|---------|
| Inbound (driving, primary) | World calls domain | Domain (application service) | `PlaceOrderUseCase` |
| Outbound (driven, secondary) | Domain calls world | Infrastructure (adapter) | `OrderRepository`, `PaymentGateway` |

## Inbound ports (driving, primary)

An inbound port represents a **use case** — one thing a user, another service, or a scheduled job can ask your domain to do. One port, one operation, expressed in the domain's vocabulary.

```typescript
// domain/application/ports/in/PlaceOrderUseCase.ts
export interface PlaceOrderCommand {
  customerId: CustomerId;
  items: Array<{ productId: ProductId; quantity: number }>;
  shippingAddress: Address;
}

export interface PlaceOrderUseCase {
  execute(command: PlaceOrderCommand): Promise<OrderId>;
}
```

Notice: the command uses domain types (`CustomerId`, `Address`), not HTTP types. No `Request`, no DTOs with JSON field names, no validation annotations from your web framework. The controller's job is to translate incoming JSON into this command — that translation is the adapter's problem, not the domain's.

The implementation is an application service:

```typescript
// domain/application/services/PlaceOrderService.ts
export class PlaceOrderService implements PlaceOrderUseCase {
  constructor(
    private orders: OrderRepository,          // outbound port
    private payments: PaymentGateway,         // outbound port
    private notifier: NotificationSender,     // outbound port
  ) {}

  async execute(command: PlaceOrderCommand): Promise<OrderId> {
    const order = Order.place(command.customerId, command.items, command.shippingAddress);
    await this.payments.authorize(order.total());
    await this.orders.save(order);
    await this.notifier.orderPlaced(order);
    return order.id;
  }
}
```

And the controller just calls it:

```typescript
// infrastructure/web/OrderController.ts
export class OrderController {
  constructor(private placeOrder: PlaceOrderUseCase) {}

  async handlePost(req: Request, res: Response) {
    const command = mapJsonToCommand(req.body);
    const orderId = await this.placeOrder.execute(command);
    res.status(201).json({ orderId: orderId.toString() });
  }
}
```

The controller depends on `PlaceOrderUseCase` — the interface, not `PlaceOrderService`. In practice this often doesn't matter much, but it means you can swap in a decorator (logging, metrics, auth) without the controller knowing.

## Outbound ports (driven, secondary)

An outbound port describes a capability the domain needs from the outside world — persistence, messaging, third-party APIs, clocks, ID generators, anything non-pure.

```typescript
// domain/application/ports/out/OrderRepository.ts
export interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
  findByCustomer(customerId: CustomerId): Promise<Order[]>;
}
```

Same discipline: the interface talks about `Order` and `OrderId`, not rows, not SQL, not ORM entities. A consumer of this port should have no idea whether the implementation is Postgres, Mongo, or an in-memory map.

The adapter lives in infrastructure:

```typescript
// infrastructure/persistence/PostgresOrderRepository.ts
export class PostgresOrderRepository implements OrderRepository {
  constructor(private db: Pool) {}

  async save(order: Order): Promise<void> {
    const row = OrderMapper.toRow(order);
    await this.db.query('INSERT INTO orders ...', [...]);
  }

  async findById(id: OrderId): Promise<Order | null> {
    const result = await this.db.query('SELECT * FROM orders WHERE id = $1', [id.value]);
    return result.rows[0] ? OrderMapper.toDomain(result.rows[0]) : null;
  }

  // ...
}
```

The mapper converts between the DB row shape and the domain `Order`. This translation layer is annoying to write but it's what keeps your domain pure — your `Order` class doesn't need `@Column` decorators or to extend some ORM base class.

## Designing good ports

A few principles that save pain later.

### Ports are small and cohesive

One port, one purpose. Don't make a `DatabaseService` with thirty methods. Make `OrderRepository`, `CustomerRepository`, `OutboxPublisher` as separate ports. This is the Interface Segregation Principle applied to boundaries. A service that only needs to save orders shouldn't depend on a god-interface that also does customer lookups.

### Ports speak the domain's language, not the infrastructure's

Bad: `OrderRepository.executeQuery(sql: string)`. Good: `OrderRepository.findByCustomer(id: CustomerId)`. If you find domain types leaking infrastructure concepts (pagination cursors, transaction objects, HTTP status codes), reconsider.

### Return domain objects, not DTOs or rows

`findById` returns `Order | null`, not `OrderRow` or `OrderDto`. The adapter's job is to build the domain object before handing it back.

### Name by intent, not by implementation

`NotificationSender`, not `EmailService`. `PaymentGateway`, not `StripeClient`. The name should survive changing the implementation. If you later add SMS notifications alongside email, the port name still fits.

### Keep ports synchronous or async, not both

If everything returns `Promise<T>`, stay consistent. Mixing `Promise`-returning and sync methods on the same port makes callers gnarly.

### Don't expose transactions through ports

This is the hard one. If you need a unit of work, define it as a port too (`TransactionManager.runInTransaction(work)`) rather than threading a `Transaction` object through your domain. The domain shouldn't know transactions exist at a type level; it should know that certain operations need to be atomic.

## Common mistakes

**Leaking framework types into ports.** Putting `Request`, `Response`, `@Entity`, or `Observable` in a port interface couples your domain to a framework. If ripping out Express or NestJS would require changing port signatures, something's wrong.

**One giant `Repository<T>` interface for everything.** Generic repositories (`save`, `findById`, `findAll`, `delete`) feel DRY but they encourage anemic domains — you end up calling `repo.findAll().filter(...)` instead of having a meaningful `findPendingOrdersOlderThan(...)` method. Better: write specific methods that express what the use case actually needs.

**Ports that are just wrappers around infrastructure.** If `OrderRepository.save()` maps 1:1 to a SQL insert with the same column names as your domain fields, you haven't really built a port — you've built a thin veneer. That's sometimes fine, but the moment the domain shape diverges from the storage shape (and it will), you'll be glad you put a real mapper there.

**Forgetting that ports are for testing too.** A well-designed outbound port has a trivial in-memory fake you can use in unit tests. If writing an `InMemoryOrderRepository` is painful, your port is probably too coupled to storage mechanics. A good port is trivially fakeable.

**Using the same port for read and write.** Sometimes your write model (aggregate root, invariants, commands) and read model (flat projections, queries for UI) have very different needs. Splitting into `OrderRepository` (write) and `OrderQueries` (read) — a mini-CQRS — often clarifies things. Not always necessary, but worth considering when the read side grows.

## Wiring it up

Ports only work if something actually connects them at startup. This is usually called the **composition root** — one place where you instantiate adapters and inject them into services:

```typescript
// main.ts
const db = new Pool(dbConfig);
const ordersRepo = new PostgresOrderRepository(db);
const payments = new StripePaymentGateway(stripeKey);
const notifier = new SesNotificationSender(sesClient);

const placeOrder = new PlaceOrderService(ordersRepo, payments, notifier);

const controller = new OrderController(placeOrder);
app.post('/orders', (req, res) => controller.handlePost(req, res));
```

This is where a DI container can help on larger codebases, but for most services manual wiring is clearer. The point is: your domain and application code never reference concrete adapters. Only `main.ts` (or your DI module) knows the full graph.
