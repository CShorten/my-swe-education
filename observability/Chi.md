# Chi Middleware: HTTP Middleware in Go's `chi` Router

## Context: What Chi Is

[`chi`](https://github.com/go-chi/chi) is a lightweight, idiomatic HTTP router for Go, built entirely on top of the standard library's `net/http` interfaces. It's one of the most popular routing libraries in the Go ecosystem — alongside `gorilla/mux` (now in maintenance mode), `gin`, and `echo` — and it's distinguished by a deliberate choice: it doesn't invent its own handler type. A `chi` handler is just an `http.Handler`, and `chi` middleware is just an `http.Handler` wrapper. This means everything in the standard library and the broader Go HTTP ecosystem composes with `chi` without adapters.

`chi`'s router is a radix tree, so route matching is fast and supports URL parameters (`/users/{id}`), nested sub-routers, and route groups. Middleware is the second pillar of the library, and it's where most of the ergonomic value lives.

## What Middleware Is, in `chi` Terms

Middleware in `chi` is a function with this signature:

```go
func(next http.Handler) http.Handler
```

It takes the next handler in the chain and returns a new handler that wraps it. The wrapper typically does something before calling `next.ServeHTTP(w, r)`, something after, or both — and may short-circuit the chain entirely (e.g., an auth middleware that returns 401 without calling `next`).

This is the same shape used by `net/http` directly; `chi` just gives you a clean way to register middleware on a router and have it apply to all matching routes.

```go
r := chi.NewRouter()

r.Use(middleware.Logger)
r.Use(middleware.Recoverer)
r.Use(middleware.RequestID)

r.Get("/health", healthHandler)
r.Route("/api", func(r chi.Router) {
    r.Use(authMiddleware)        // applies only to /api/*
    r.Get("/users/{id}", getUser)
})
```

Two things to notice. First, `r.Use` is global to that router (or sub-router) — order matters, and middleware runs in registration order on the way in, reverse order on the way out. Second, `r.Route` creates a sub-router with its own middleware stack, so you can scope concerns like authentication to specific URL prefixes without applying them to public endpoints.

## The Built-In Middleware Package

`chi` ships a companion package, `github.com/go-chi/chi/v5/middleware`, with a set of commonly needed pieces. The ones you'll actually use most:

**`Logger`** writes a structured log line per request — method, path, status, duration, bytes written. Useful for development; in production most teams replace it with a custom middleware that emits via `slog` or zap with trace context attached.

**`Recoverer`** recovers from panics in downstream handlers, logs a stack trace, and returns 500. This should be near the top of every middleware stack — without it, a panic in any handler crashes the whole process.

**`RequestID`** generates a unique ID per request (or reads one from an inbound `X-Request-ID` header), stores it in the request context, and echoes it on the response. Essential for log correlation across services.

**`RealIP`** rewrites `r.RemoteAddr` based on `X-Forwarded-For` or `X-Real-IP` headers, so handlers behind a load balancer see the actual client IP.

**`Timeout`** wraps the request context with a deadline. Handlers checking `ctx.Done()` will get cancelled when the timeout fires. Worth pairing with handler code that actually respects context cancellation — middleware alone doesn't kill goroutines that ignore `ctx`.

**`Compress`** gzip-encodes responses for clients that send `Accept-Encoding: gzip`.

**`StripSlashes` / `RedirectSlashes`** normalize trailing slashes — pick one, apply consistently.

**`Throttle` / `ThrottleBacklog`** cap concurrent in-flight requests, returning 503 (or queueing up to a backlog) when over capacity. A simple form of load shedding.

**`CleanPath`** normalizes URL paths (collapsing `..`, double slashes), defending against a class of routing tricks.

**`AllowContentType` / `SetHeader` / `NoCache`** small utilities for the obvious things.

There's also a `Heartbeat` for cheap healthchecks and a `Profiler` that mounts `net/http/pprof` under a sub-route, which is convenient but should be locked down or omitted in production.

## Writing Your Own

The middleware shape is small enough that you'll write your own routinely. A typical pattern — say, attaching a tenant ID from a header to the request context:

```go
func tenantContext(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        tenantID := r.Header.Get("X-Tenant-ID")
        if tenantID == "" {
            http.Error(w, "missing tenant", http.StatusBadRequest)
            return
        }
        ctx := context.WithValue(r.Context(), tenantKey, tenantID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

Three idioms worth internalizing here. Pass values through `context.Context`, not through globals or middleware-local state. Use a typed unexported key (`type tenantKeyType struct{}; var tenantKey tenantKeyType`) to avoid context-key collisions across packages. And always call `r.WithContext(ctx)` to produce a new request — `*http.Request` is shallow-copied, the context is propagated, and downstream handlers see your additions.

For middleware that needs to inspect the *response* (status code, bytes written), `chi` provides `middleware.WrapResponseWriter`, which wraps `http.ResponseWriter` so you can read these values after `next.ServeHTTP` returns. The built-in `Logger` uses this; so does any latency or metrics middleware you'd write.

## Composition with the Ecosystem

Because `chi` middleware is just `func(http.Handler) http.Handler`, it composes directly with everything else in the Go HTTP world:

**`otelhttp`.** Wrap your router (or specific handlers) with `otelhttp.NewHandler` to get an OpenTelemetry span per request, with the standard semantic conventions (`http.method`, `http.route`, `http.status_code`). The span context flows through `r.Context()`, so any downstream code — middleware, handlers, database calls — picks it up automatically.

**`slog`.** A small middleware that pulls the request ID and trace ID out of context and attaches them to a request-scoped logger gives you structured logs correlated with traces, with no per-handler boilerplate.

**Authentication libraries.** Anything that exposes `func(http.Handler) http.Handler` — JWT validators, session middleware, OAuth flows — slots in directly via `r.Use`.

**`net/http` itself.** You can also mount a `chi` router as a handler inside a non-`chi` server, or wrap a `chi` router with non-`chi` middleware. There's no framework lock-in; it's all `http.Handler` underneath.

## A Few Practical Notes

**Order matters, and it's not obvious.** A typical stack reads top-to-bottom in execution order on the way in: `RequestID` → `RealIP` → `Recoverer` → `Logger` → `Timeout` → auth → handler. Put `Recoverer` *before* `Logger` so panics are caught and the log entry still gets written. Put `RequestID` first so every other middleware can include it.

**Don't put expensive work in middleware that runs on every route.** Middleware on the root router runs for healthchecks, metrics scrapes, and 404s. Scope expensive things (DB lookups, external calls) to sub-routers that actually need them.

**`r.Use` only works before routes are defined on that router.** Calling `Use` after registering a route panics. This is intentional — it prevents subtle bugs where some routes have a middleware and others don't depending on registration order.

**Sub-routers inherit parent middleware.** A middleware registered on the root router runs for every sub-router too, in addition to whatever the sub-router adds. This is usually what you want, but it means you can't *remove* middleware from a sub-router — only add to it.

## Where It Fits

`chi` middleware is the standard answer for "where do cross-cutting HTTP concerns live in a Go service." It's the layer that handles trace context propagation, request logging, panic recovery, auth, rate limiting, and tenant scoping — the things that need to wrap every (or nearly every) request without polluting handler code. Because the interface is just `http.Handler`, you can build a stack incrementally, swap pieces, test middleware in isolation, and keep the door open to dropping `chi` entirely if you ever needed to, without rewriting handlers.

The deeper appeal is the same one that made `slog.Handler` work: a narrow interface (`func(http.Handler) http.Handler`), wide implementations, and full composability with the standard library. It's a small amount of API surface that gets a lot of mileage.
