# Concepts

## Writing without Synchronization
Simple example to illustrate that if you don't lock the file while writing, you will get an unpredictable write order when appending. ToDo -- add data corruption example.

## Page-level locking
Divide a file into fixed-size pages and use a mutex for each page.

## Atomics
Atomic operations are indivisible actions that complete without interference from other threads. Useful for simple synchronization, use Mutexes when blocking changes to multiple variables or other more complex logic.

## Multiversion Concurrenty Control (MVCC)
Allows multiple transactions to access different versions of data simultaneously without locking with Versioning, Snapshots, and Consistency. Allows high concurrency without locking by maintaining multiple versions of data.

## Read Committed vs. Serializable Isolation
Control the visibility of data changes across transactions, balancing performance and consistency.
