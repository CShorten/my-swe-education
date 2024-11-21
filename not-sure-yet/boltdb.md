# BoltDB Technical Report

## Overview
BoltDB is an embedded key-value database written in Go, inspired by LMDB. It provides ACID transactions with serializable isolation, supporting multiple read-only transactions and one read-write transaction at a time.

## Key Features
- Single-file database with zero external dependencies
- ACID transactions with MVCC
- Memory-mapped B+tree architecture
- Thread-safe concurrent access
- Append-only data file design
- Sub-millisecond range scans

## Technical Architecture
BoltDB uses a B+tree structure stored in a memory-mapped file. Each transaction operates on a consistent snapshot of the database, implementing MVCC through a copy-on-write B+tree.

### Storage Format
- Page-based storage (4KB pages)
- Freelist tracks unused pages
- Meta pages store root bucket information
- Branch and leaf pages form B+tree structure

### Performance Characteristics
- Read Performance: O(log n) for point queries
- Write Performance: O(log n) for insertions
- Space Overhead: ~50 bytes per key-value pair
- Practical Limits: ~256TB maximum database size

## Use Cases
- Embedded applications requiring durability
- Local caching and storage
- Application configuration storage
- Message queues and logging systems

## Limitations
- Single write transaction at a time
- No client-server architecture
- Limited query capabilities
- Database size limited by available RAM

## Status
Development ceased in 2018, but the codebase remains stable and is used in production by projects like etcd and Consul.
