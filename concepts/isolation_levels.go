package main

import (
    "database/sql"
    "fmt"
    "log"
    "sync"

    _ "github.com/mattn/go-sqlite3"
)

func readCommittedExample(db *sql.DB, wg *sync.WaitGroup) {
    defer wg.Done()

    tx, err := db.Begin()
    if err != nil {
        log.Fatal(err)
    }
    defer tx.Rollback()

    var value int
    err = tx.QueryRow("SELECT balance FROM accounts WHERE id = 1").Scan(&value)
    if err != nil {
        fmt.Println("Read Committed: Error reading value:", err)
        return
    }
    fmt.Println("Read Committed: Initial balance =", value)

    // Simulate delay
    // time.Sleep(1 * time.Second)

    err = tx.QueryRow("SELECT balance FROM accounts WHERE id = 1").Scan(&value)
    if err != nil {
        fmt.Println("Read Committed: Error reading value:", err)
        return
    }
    fmt.Println("Read Committed: Balance after delay =", value)

    tx.Commit()
}

func serializableExample(db *sql.DB, wg *sync.WaitGroup) {
    defer wg.Done()

    tx, err := db.BeginTx(nil, &sql.TxOptions{Isolation: sql.LevelSerializable})
    if err != nil {
        log.Fatal(err)
    }
    defer tx.Rollback()

    var value int
    err = tx.QueryRow("SELECT balance FROM accounts WHERE id = 1").Scan(&value)
    if err != nil {
        fmt.Println("Serializable: Error reading value:", err)
        return
    }
    fmt.Println("Serializable: Initial balance =", value)

    // Simulate delay
    // time.Sleep(1 * time.Second)

    err = tx.QueryRow("SELECT balance FROM accounts WHERE id = 1").Scan(&value)
    if err != nil {
        fmt.Println("Serializable: Error reading value:", err)
        return
    }
    fmt.Println("Serializable: Balance after delay =", value)

    tx.Commit()
}

func main() {
    db, err := sql.Open("sqlite3", ":memory:")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    _, err = db.Exec("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER)")
    if err != nil {
        log.Fatal(err)
    }

    // Insert initial data
    _, err = db.Exec("INSERT INTO accounts (id, balance) VALUES (1, 100)")
    if err != nil {
        log.Fatal(err)
    }

    var wg sync.WaitGroup
    wg.Add(2)

    go readCommittedExample(db, &wg)

    // Simulate another transaction updating the balance
    go func() {
        defer wg.Done()

        tx, err := db.Begin()
        if err != nil {
            log.Fatal(err)
        }
        defer tx.Rollback()

        _, err = tx.Exec("UPDATE accounts SET balance = balance + 50 WHERE id = 1")
        if err != nil {
            fmt.Println("Error updating balance:", err)
            return
        }

        tx.Commit()
    }()

    wg.Wait()
}
