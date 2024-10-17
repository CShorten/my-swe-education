# 01 - Relational Model & Algebra

[Link](https://www.youtube.com/watch?v=APqWIjtzNGE)

### What is a DBMS trying to do for you?

### Example -- Digital Music

```python
class Aritst(BaseModel):
  name: str
  year: int
  country: enum
```

### Read files

Ah! This is so slow!!

```python
for line in file.readlines():
  record = parse(line)
  if record[0] == "GZA":
    print(int(record[1]))
```

```golang
func parse(line string) []string {
    return strings.Split(strings.TrimSpace(line), ",")
}

file, err := os.Open("artists.txt")
if err != nil {
    log.Fatal(err)
}
defer file.Close()

scanner := bufio.NewScanner(file)
for scanner.Scan() {
    record := parse(scanner.Text())
    if record[0] == "GZA" {
        year, err := strconv.Atoi(record[1])
        if err == nil {
            fmt.Println(year)
        }
    }
}
```

Why is this slow?
- Disk I/O Bottleneck -- reading from disk is slower than accessing memory.
- Parsing each line individually
- Lack of indexing - no quick way to find records matching a condition...

## Brainstorming -- How do you read files faster?

How do cursors actually work?

```python
import struct

def write_records(filename, records):
    with open(filename, 'wb') as f:
        for record in records:
            name = record['name'].ljust(30)[:30].encode('utf-8')
            year = struct.pack('i', record['year'])
            country = record['country'].ljust(20)[:20].encode('utf-8')
            f.write(name + year + country)

# Sample data
artists = [
    {'name': 'GZA', 'year': 1966, 'country': 'USA'},
    {'name': 'Bjork', 'year': 1965, 'country': 'Iceland'},
    {'name': 'Daft Punk', 'year': 1993, 'country': 'France'},
    # ... more records
]

write_records('artists.dat', artists)

class Cursor:
    RECORD_SIZE = 54  # 30 bytes for name, 4 bytes for year, 20 bytes for country

    def __init__(self, filename):
        self.file = open(filename, 'rb')
        self.position = 0
        self.file_size = self._get_file_size()

    def _get_file_size(self):
        current_pos = self.file.tell()
        self.file.seek(0, 2)  # Move to end of file
        size = self.file.tell()
        self.file.seek(current_pos)
        return size

    def fetch_next(self):
        if self.position >= self.file_size:
            return None  # End of file
        self.file.seek(self.position)
        record_data = self.file.read(self.RECORD_SIZE)
        self.position += self.RECORD_SIZE
        return self._parse_record(record_data)

    def fetch_prev(self):
        if self.position - self.RECORD_SIZE < 0:
            return None  # Start of file
        self.position -= self.RECORD_SIZE
        self.file.seek(self.position)
        record_data = self.file.read(self.RECORD_SIZE)
        return self._parse_record(record_data)

    def _parse_record(self, data):
        name = data[:30].decode('utf-8').strip()
        year = struct.unpack('i', data[30:34])[0]
        country = data[34:].decode('utf-8').strip()
        return {'name': name, 'year': year, 'country': country}

    def close(self):
        self.file.close()
```

# Golang

```golang
package main

import (
    "encoding/binary"
    "fmt"
    "os"
    "strings"
)

const RecordSize = 54

type Artist struct {
    Name    string
    Year    int32
    Country string
}

func writeRecords(filename string, records []Artist) error {
    file, err := os.Create(filename)
    if err != nil {
        return err
    }
    defer file.Close()

    for _, record := range records {
        nameBytes := []byte(fmt.Sprintf("%-30s", record.Name)[:30])
        yearBytes := make([]byte, 4)
        binary.LittleEndian.PutUint32(yearBytes, uint32(record.Year))
        countryBytes := []byte(fmt.Sprintf("%-20s", record.Country)[:20])

        data := append(nameBytes, yearBytes...)
        data = append(data, countryBytes...)

        _, err := file.Write(data)
        if err != nil {
            return err
        }
    }
    return nil
}

func main() {
    artists := []Artist{
        {"GZA", 1966, "USA"},
        {"Bjork", 1965, "Iceland"},
        {"Daft Punk", 1993, "France"},
        // ... more records
    }

    err := writeRecords("artists.dat", artists)
    if err != nil {
        fmt.Println("Error writing records:", err)
    }
}
```

# Data Integrity

Flat file limitations

-- How do you find a particular recrod...

-- What if we now wnat to create a new application that uses the same database? What if that application is running on a different machine?

# What if two threads try to write to the same file at the same time?

^ Love this one

-- What if the machine crashes while our progarm is updating a record?

^^ Even better

-- What if we want to replicate the database on multiple machines for high availability?
