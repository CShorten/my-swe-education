# Memory Leaks in Go: Analysis and Examples

Memory leaks in Go occur when allocated memory is not properly released, despite no longer being needed by the program. While Go's garbage collector handles most memory management, leaks can still occur in specific scenarios.

## Common Causes

1. Goroutine leaks
2. Unbounded caches
3. Unclosed resources
4. Slice references

## Example: Goroutine Leak

```go
package main

import (
    "fmt"
    "runtime"
    "time"
)

func leakyWorker() {
    ch := make(chan int)
    
    go func() {
        val := <-ch  // This goroutine will never receive a value
        fmt.Println("Received:", val)
    }()
    
    // Channel is never written to, goroutine remains blocked forever
}

func main() {
    // Print initial goroutine count
    fmt.Println("Initial goroutines:", runtime.NumGoroutine())
    
    // Create multiple leaky workers
    for i := 0; i < 10000; i++ {
        leakyWorker()
    }
    
    // Print final goroutine count and wait
    fmt.Println("Final goroutines:", runtime.NumGoroutine())
    time.Sleep(time.Second)
}
```

## Analysis

In this example, each `leakyWorker()` creates a goroutine that waits for a channel receive operation. Since the channel is never written to:

1. The goroutine remains blocked indefinitely
2. Memory associated with the goroutine cannot be garbage collected
3. System resources are gradually consumed

## Prevention Strategies

1. Always use channel closing mechanisms
2. Implement proper cancellation using `context`
3. Set appropriate timeouts
4. Monitor goroutine counts during development

## Fixed Version

```go
func nonLeakyWorker(ctx context.Context) {
    ch := make(chan int)
    
    go func() {
        select {
        case val := <-ch:
            fmt.Println("Received:", val)
        case <-ctx.Done():
            return
        }
    }()
}
```

This version properly handles cleanup using context cancellation, preventing the memory leak.
