package main

import (
    "fmt"
    "sync"
    "time"
)

type VersionedValue struct {
    timestamp time.Time
    value     int
}

type MVCCDatabase struct {
    data map[string][]VersionedValue
    lock sync.RWMutex
}

func NewMVCCDatabase() *MVCCDatabase {
    return &MVCCDatabase{
        data: make(map[string][]VersionedValue),
    }
}

func (db *MVCCDatabase) Write(key string, value int) {
    db.lock.Lock()
    defer db.lock.Unlock()

    version := VersionedValue{
        timestamp: time.Now(),
        value:     value,
    }
    db.data[key] = append(db.data[key], version)
}

func (db *MVCCDatabase) Read(key string, txTime time.Time) (int, bool) {
    db.lock.RLock()
    defer db.lock.RUnlock()

    versions, exists := db.data[key]
    if !exists {
        return 0, false
    }

    for i := len(versions) - 1; i >= 0; i-- {
        if versions[i].timestamp.Before(txTime) || versions[i].timestamp.Equal(txTime) {
            return versions[i].value, true
        }
    }
    return 0, false
}

func main() {
    db := NewMVCCDatabase()

    db.Write("x", 10)

    tx1Time := time.Now()
    time.Sleep(10 * time.Millisecond)
    db.Write("x", 20)

    var wg sync.WaitGroup
    wg.Add(2)

    go func() {
        defer wg.Done()
        value, _ := db.Read("x", tx1Time)
        fmt.Println("Transaction 1 reads x =", value)
    }()

    go func() {
        defer wg.Done()
        value, _ := db.Read("x", time.Now())
        fmt.Println("Transaction 2 reads x =", value)
    }()

    wg.Wait()
}
