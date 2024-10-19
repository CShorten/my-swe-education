package main

import (
    "fmt"
    "sync"
    "time"
)

var (
    counter     int
    mutex       sync.Mutex
    semaphore   = make(chan struct{}, 3) // Limit to 3 concurrent goroutines
)

func incrementWithMutex() {
    mutex.Lock()
    defer mutex.Unlock()

    counter++
    fmt.Println("[Mutex] Counter:", counter)
    time.Sleep(1 * time.Second) // Simulate some work
}

func incrementWithSemaphore() {
    semaphore <- struct{}{} // Acquire a spot
    defer func() { <-semaphore }() // Release the spot

    counter++
    fmt.Println("[Semaphore] Counter:", counter)
    time.Sleep(1 * time.Second) // Simulate some work
}

func main() {
    fmt.Println("Starting Mutex example:")
    for i := 0; i < 5; i++ {
        go incrementWithMutex()
    }

    // Wait for Mutex example to complete
    time.Sleep(6 * time.Second)

    // Reset counter for the Semaphore example
    counter = 0

    fmt.Println("\nStarting Semaphore example:")
    for i := 0; i < 10; i++ {
        go incrementWithSemaphore()
    }

    // Wait for Semaphore example to complete
    time.Sleep(11 * time.Second)
}
