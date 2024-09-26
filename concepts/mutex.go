package main

import (
    "fmt"
    "sync"
)

// ToDo scale up and benchmark against atomics

func main() {
    var counter int64
    var mutex sync.Mutex
    var wg sync.WaitGroup
    numGoroutines := 10
    incrementsPerGoroutine := 1000

    wg.Add(numGoroutines)
    for i := 0; i < numGoroutines; i++ {
        go func() {
            defer wg.Done()
            for j := 0; j < incrementsPerGoroutine; j++ {
                mutex.Lock()
                counter++
                mutex.Unlock()
            }
        }()
    }

    wg.Wait()
    fmt.Println("Final Counter:", counter)
}
