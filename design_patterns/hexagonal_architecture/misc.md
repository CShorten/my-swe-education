### Compile-Time Interface Assertion

```golang
var _ ports.XService = (*Service)(nil)
```

This is an idiomatic Go trick. It assigns `nil` (cast to `*Service`) to the blank identifier with type `ports.MemoryService`.
It does nothing at runtime but forces the compiler to verify that `*Service` satisfies the `Service` interface.
If you ever remove a method or change a signature, the build breaks here, loudly, instead of silently at some caller's site.

The port (ports.Service) is the driving side of the hexagon -- the interface that driving adapters (HTTP Handlers, gRPC servers, CLI) call into.
