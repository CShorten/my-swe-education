# Go's `slog.Handler`: The Backend Behind Structured Logging

## Context: `log/slog`

Go 1.21 (August 2023) added `log/slog` to the standard library — Go's official structured logging package. Before `slog`, the ecosystem was fragmented across `logrus`, `zap`, `zerolog`, and others, each with its own API. `slog` standardizes the *frontend* (the API you call: `slog.Info`, `slog.With`, etc.) while leaving the *backend* — where and how log records actually get written — pluggable through the `Handler` interface.

That backend is `slog.Handler`.

## The Interface

`slog.Handler` is a small interface with four methods:

```go
type Handler interface {
    Enabled(ctx context.Context, level Level) bool
    Handle(ctx context.Context, record Record) error
    WithAttrs(attrs []Attr) Handler
    WithGroup(name string) Handler
}
```

Each method has a specific job:

**`Enabled`** is a fast pre-check. Before `slog` builds a `Record` (which involves allocating, capturing a timestamp, walking the call stack for source info), it asks the handler whether a log at this level would actually be emitted. If `Enabled` returns false, `slog` skips the work entirely. This is how you make disabled debug logs nearly free.

**`Handle`** is where the actual work happens. It receives a fully-formed `Record` — timestamp, level, message, attributes, source location — and is responsible for formatting it and writing it somewhere. A JSON handler marshals to JSON and writes to an `io.Writer`; a handler shipping to a SaaS observability backend might serialize to their wire format and enqueue to a network buffer.

**`WithAttrs`** returns a new handler that has additional attributes pre-attached. When you call `logger.With("tenant_id", "abc")`, `slog` calls `WithAttrs` on the handler under the hood. Good handlers pre-format these attributes once at `WithAttrs` time rather than re-formatting them on every log call — this is the main performance lever in handler design.

**`WithGroup`** returns a new handler where subsequent attributes are nested under a group name. `logger.WithGroup("http").Info("req", "method", "GET")` produces output like `{"http": {"method": "GET"}}` in JSON. It's how you namespace attributes without naming collisions.

## What Comes Built In

The standard library ships two handlers:

**`slog.TextHandler`** writes `key=value` pairs, one record per line. Reasonable for local development and human-readable logs.

**`slog.JSONHandler`** writes one JSON object per line (JSONL). This is the workhorse for production — every log aggregator (Datadog, Loki, Elasticsearch, CloudWatch) ingests JSONL natively, and structured fields become queryable without regex parsing.

Both take a `slog.HandlerOptions` struct that controls level, source-location capture, and an `AttrReplacer` function for redacting or transforming attributes (useful for scrubbing PII or normalizing field names).

## Why the Interface Matters

The handler abstraction is what makes `slog` worth adopting over rolling your own logger or sticking with `zap`. A few patterns it enables:

**Composition.** Handlers wrap other handlers. You can write a handler that adds trace context to every record (pulling `trace_id` and `span_id` out of `context.Context`) and delegates the actual writing to a `JSONHandler` underneath. This is the standard pattern for OTel integration — the `otelslog` bridge from the OpenTelemetry contrib repo does exactly this, ensuring every log line is correlated with the active span.

**Routing.** A handler can dispatch based on level or attributes — errors to one destination, debug to another, audit logs to a separate sink with stricter durability. The handler is just a Go type, so you have full control.

**Testing.** A trivial in-memory handler that appends records to a slice makes log assertions straightforward in tests, without the parsing-stdout dance that string-based loggers require.

**Performance handlers.** Third-party handlers like `phsym/zeroslog` (a `zerolog` backend for `slog`) or the `slog-zap` bridge let you keep the standard `slog` API while getting the allocation profile of the high-performance loggers. You write against the standard interface and swap backends without touching call sites.

## The Performance Contract

Worth knowing if you're writing or choosing a handler: `slog`'s design assumes handlers handle concurrent calls to `Handle` safely (the standard handlers do, via an internal mutex around the writer), and that `WithAttrs`/`WithGroup` return *independent* handlers that can be used concurrently with the original. The `Record` passed to `Handle` should not be retained past the call without cloning — its `Attrs` may share backing arrays with the caller.

The biggest practical performance trap is failing to pre-format in `WithAttrs`. A naive handler that just stores the attrs in a slice and re-serializes them on every `Handle` call will be much slower than one that builds a partial output buffer at `WithAttrs` time and just appends per-record fields in `Handle`. The standard `JSONHandler` does the right thing here, which is why it's competitive with `zap` for most workloads despite being part of the standard library.

## Where It Fits

For a typical Go service, the usual setup is: `slog.NewJSONHandler` writing to stdout, wrapped by an OTel bridge handler that injects trace context, with an `AttrReplacer` to canonicalize a few field names so they line up with whatever your log aggregator expects. That gives you trace-correlated structured logs with maybe ten lines of setup code, and the option to swap any layer (different format, different destination, different bridge) without touching the rest of the codebase.

The deeper point is that `slog.Handler` is a clean example of the "narrow interface, wide implementations" Go pattern — the same shape that makes `io.Reader`, `http.Handler`, and `database/sql/driver.Driver` so durable. The interface is small enough to implement in an afternoon, and that's what made the ecosystem coalesce around it quickly after 1.21 shipped.
