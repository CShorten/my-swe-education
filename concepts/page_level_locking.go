package main

import (
    "fmt"
    "math/rand"
    "sync"
    "time"
)

const (
    PageSize   = 1024 // bytes
    NumPages   = 10
    TotalSize  = PageSize * NumPages
    NumWriters = 5
)

type Page struct {
    data []byte
    lock sync.Mutex
}

type PagedFile struct {
    pages []*Page
}

func NewPagedFile() *PagedFile {
    pages := make([]*Page, NumPages)
    for i := 0; i < NumPages; i++ {
        pages[i] = &Page{
            data: make([]byte, PageSize),
        }
    }
    return &PagedFile{pages: pages}
}

func (pf *PagedFile) Write(pageIndex int, data []byte) {
    page := pf.pages[pageIndex]
    page.lock.Lock()
    defer page.lock.Unlock()

    copy(page.data, data)
}

func (pf *PagedFile) Read(pageIndex int) []byte {
    page := pf.pages[pageIndex]
    page.lock.Lock()
    defer page.lock.Unlock()

    dataCopy := make([]byte, len(page.data))
    copy(dataCopy, page.data)
    return dataCopy
}

func writer(id int, pf *PagedFile, wg *sync.WaitGroup) {
    defer wg.Done()
    rand.Seed(time.Now().UnixNano())

    for i := 0; i < 5; i++ {
        pageIndex := rand.Intn(NumPages)
        data := []byte(fmt.Sprintf("Writer %d writing to page %d", id, pageIndex))
        pf.Write(pageIndex, data)
        fmt.Printf("Writer %d wrote to page %d\n", id, pageIndex)
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    pf := NewPagedFile()
    var wg sync.WaitGroup

    wg.Add(NumWriters)
    for i := 0; i < NumWriters; i++ {
        go writer(i, pf, &wg)
    }
    wg.Wait()

    // Reading all pages
    for i, page := range pf.pages {
        data := page.data
        fmt.Printf("Page %d contains: %s\n", i, string(data))
    }
}
