# Callbacks on Observability

A callback is one of those concepts that's simple at its core but takes on different shapes in different contexts. This report starts with the fundamentals and connects them to the OpenTelemetry observable-instrument case.

## The Core Idea

A callback is a function that you give to *someone else* to call later, rather than calling it yourself. You hand off a reference to the function — not the result of running it — and the receiver decides when (and whether, and how many times) to invoke it.

The dynamic is "don't call us, we'll call you." You're inverting who controls the timing.

```go
// Direct call: you decide when it runs
result := computeValue()

// Callback: you give the function to someone else; they decide when
register(computeValue)
// ... later, the registrar calls computeValue() on its own schedule
```

The trick that makes this possible in essentially every modern language is that **functions are values**. You can pass a function as an argument, store it in a struct, put it in a map, return it from another function. The function isn't tied to "being called right now" — it's a thing you can hold onto and invoke later.

## A Minimal Example

Consider a simple "do this thing for each item in this list" pattern:

```go
func forEach(items []int, fn func(int)) {
    for _, item := range items {
        fn(item)  // call the callback for each element
    }
}

forEach([]int{1, 2, 3}, func(x int) {
    fmt.Println(x * 2)
})
```

The `forEach` function doesn't know what you want to do with each item — it just knows it has a function `fn` and is supposed to call it once per element. *You* supplied the "what" by passing in an anonymous function. *forEach* supplied the "when" by deciding to call it inside its loop.

This is callbacks in their simplest form. Every higher-order function — `map`, `filter`, `sort.Slice` with a less-than function, `http.HandleFunc` — is built on the same idea.

## Why You'd Use One

Callbacks solve a specific problem: **the code that knows *when* something should happen is different from the code that knows *what* should happen.**

- The HTTP router knows when a request arrives. *Your* code knows what to do with it. → You register a handler callback.
- A sort algorithm knows when it needs to compare two elements. Your code knows how *your* type compares. → You pass a less-than callback.
- The OS knows when a signal fires. Your code knows what to clean up. → You register a signal handler.
- The OTel SDK knows when an export tick happens. Your code knows how to compute the current row count. → You register an observable callback.

In every case, separating "when" from "what" is the entire point. The library or framework can be generic — it doesn't have to know about your domain — and your code can be specific without having to manage timing or scheduling itself.

## The Lifecycle of a Callback

Most callback systems have three phases, and it's worth seeing them clearly:

**1. Registration.** You give the callback to the receiver. This usually returns immediately — nothing has been called yet. The receiver just stores the function reference somewhere (a slice, a map, a struct field).

```go
meter.RegisterCallback(myCallback, gauge)  // returns now; myCallback hasn't run
```

**2. Invocation.** Some time later — could be microseconds, could be hours — the receiver decides to call the callback. From the callback's perspective, this is just a normal function call; it has no idea it was invoked from "the outside" rather than from regular code.

```go
// inside the SDK, on each export tick:
err := myCallback(ctx, observer)
```

**3. Deregistration (sometimes).** Many callback APIs return a handle that lets you unregister. This matters for cleanup — long-lived callbacks can hold references to objects that should otherwise be garbage collected, or can keep doing work after the thing that registered them has logically gone away.

```go
registration, err := meter.RegisterCallback(myCallback, gauge)
defer registration.Unregister()
```

Not every callback API has all three phases. A `forEach` callback only has invocation — there's no registration step, the function is passed and called immediately. A signal handler has registration but no obvious deregistration.

## Closures: The Thing That Makes Callbacks Powerful

A callback by itself is just "call this function later." What makes callbacks genuinely useful is that they can capture *state* from where they were defined. This is called a **closure**, and it's what lets a callback know what to do without you having to thread arguments through the registration call.

```go
func registerMemoryCountGauge(meter metric.Meter, db *sql.DB, tenantID string) {
    gauge, _ := meter.Int64ObservableGauge("memory_count")

    meter.RegisterCallback(func(ctx context.Context, o metric.Observer) error {
        // This closure captures `db` and `tenantID` from the surrounding function.
        // When the SDK calls this later, those variables are still available.
        var count int64
        err := db.QueryRowContext(ctx,
            "SELECT COUNT(*) FROM memories WHERE tenant_id = $1",
            tenantID,
        ).Scan(&count)
        if err != nil {
            return err
        }
        o.ObserveInt64(gauge, count)
        return nil
    }, gauge)
}
```

The anonymous function passed to `RegisterCallback` references `db`, `tenantID`, and `gauge` — variables from the *outer* function. By the time the SDK actually invokes this callback (potentially long after `registerMemoryCountGauge` has returned), those variables would normally be gone. Closures keep them alive: the captured variables are bundled with the function reference and live as long as the callback does.

This is what makes callback APIs ergonomic. You configure what the callback should do at registration time using whatever variables are in scope, and the runtime keeps that context around for you.

## How the OTel Case Works Specifically

When you call `meter.RegisterCallback(fn, gauge)`, the OTel SDK stores `fn` in a registry associated with that gauge. Nothing has happened yet — `fn` hasn't run.

Then a goroutine inside the SDK ticks on the export interval (every 60 seconds by default). On each tick, it walks its registry of callbacks and calls each one, passing in a fresh `context.Context` and an `Observer` it created for this tick. Your callback runs, queries the database, calls `o.ObserveInt64(gauge, count)` to record the value, and returns. The SDK takes that recorded value, attaches it to the metric data point, batches it with everything else, and ships it via the configured exporter (OTLP/gRPC, OTLP/HTTP, etc.).

The SDK never had to know what your gauge measures, where the data comes from, or how to query Postgres. It just knew "I have a function I'm supposed to call on each tick, and whatever it does, it will end up calling `o.ObserveInt64` to tell me the current value." Your code never had to know when ticks happen, how export works, or how data gets shipped. You just knew "I have a function that computes the current row count."

That's the whole pattern. The SDK supplies the timing; you supply the value-computing logic; the closure carries the context (database handle, tenant ID, gauge reference) from registration time into invocation time.

## A Few Subtleties Worth Knowing

**Callbacks run in the caller's goroutine, on the caller's timeline.** Your OTel callback runs on the SDK's exporter goroutine, not on yours. This means it shouldn't block forever, shouldn't panic without recovery, and should respect the context's deadline. A slow database query in a metrics callback can stall the entire metrics pipeline.

**Errors in callbacks need to be handled by the caller.** When your callback returns an error, the SDK has to decide what to do — usually "log it and skip this gauge for this tick." Errors don't propagate back to the registration site, because by then nobody's listening. This is one of the trade-offs of callbacks: the call site that registered the function isn't on the stack when the function runs, so you lose the natural error-return path.

**Callback APIs vs. channels (in Go specifically).** Go often gives you a choice between "register a callback" and "receive on a channel." Callbacks are simpler when the work is short and stateless; channels are usually better when you want to apply backpressure, fan out to multiple consumers, or integrate with `select` and cancellation. OTel uses callbacks because the work *should* be short — compute a value, return it — and the SDK wants synchronous control over the timing.

## Where the Pattern Comes Up

Callbacks are everywhere once you start looking:

- **HTTP handlers** — `http.HandleFunc("/path", handler)` registers a callback the server invokes per request.
- **Sort comparators** — `sort.Slice(s, less)` invokes `less` whenever it needs to compare two elements.
- **Event listeners in UI frameworks** — `button.OnClick(handler)`.
- **Goroutine completion in Go** — slightly different shape, but `errgroup.Group.Go(fn)` is "register this work to run; we'll call it concurrently."
- **Database driver hooks, HTTP middleware (`func(http.Handler) http.Handler`), interceptors (Temporal, gRPC), signal handlers, retry policies, validators, timer callbacks**.

The shape varies — sometimes the callback is called once, sometimes per event, sometimes on a schedule — but the core inversion is the same: you supply behavior, the framework supplies timing.

That's really the whole concept. The library calls you instead of you calling the library, and closures carry the necessary context across that gap.
