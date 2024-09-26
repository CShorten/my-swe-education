package main

import (
    "fmt"
    "os"
    "sync"
)

func writeToFile(filename, content string, wg *sync.WaitGroup) {
    defer wg.Done()

    file, err := os.OpenFile(filename, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0644)
    if err != nil {
        fmt.Println("Error opening file:", err)
        return
    }
    defer file.Close()

    for i := 0; i < 5; i++ {
        _, err := file.WriteString(content)
        if err != nil {
            fmt.Println("Error writing to file:", err)
            return
        }
    }
}

func main() {
    var wg sync.WaitGroup
    filename := "test.txt"

    wg.Add(2)
    go writeToFile(filename, "AAAAA\n", &wg)
    go writeToFile(filename, "BBBBB\n", &wg)
    wg.Wait()

    data, err := os.ReadFile(filename)
    if err != nil {
        fmt.Println("Error reading file:", err)
        return
    }
    fmt.Println("File Content:\n", string(data))
}
