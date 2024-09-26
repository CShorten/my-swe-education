package main

import (
    "fmt"
    "sync"
    "time"
)

type VersionedValue struct {
    timestamp int64
    value     int
}

type MVCCStore struct {
    data map[string][]VersionedValue
    lock sync.RWMutex
}

func NewMVCCStore() *MVCCStore {
    return &MVCCStore{
        data: make(map[string][]VersionedValue),
    }
}

func (store *MVCCStore) Write(key string, value int) {
    store.lock.Lock()
    defer store.lock.Unlock()

    version := VersionedValue{
        timestamp: time.Now().UnixNano(),
        value:     value,
    }
    store.data[key] = append(store.data[key], version)
}

func (store *MVCCStore) Read(key string, snapshotTime int64) (int, bool) {
    store.lock.RLock()
    defer store.lock.RUnlock()

    versions, exists := store.data[key]
    if !exists {
        return 0, false
    }

    // Find the latest version not newer than snapshotTime
    for i := len(versions) - 1; i >= 0; i-- {
        if versions[i].timestamp <= snapshotTime {
            return versions[i].value, true
        }
    }
    return 0, false
}

func main() {
    store := NewMVCCStore()

    // Transaction 1 starts
    tx1Time := time.Now().UnixNano()
    store.Write("x", 10)

    // Transaction 2 starts
    tx2Time := time.Now().UnixNano()
    store.Write("x", 20)

    // Transaction 1 reads
    value, _ := store.Read("x", tx1Time)
    fmt.Println("Transaction 1 reads x =", value)

    // Transaction 2 reads
    value, _ = store.Read("x", tx2Time)
    fmt.Println("Transaction 2 reads x =", value)
}
