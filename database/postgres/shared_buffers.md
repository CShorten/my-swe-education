## Postgres shared‑buffer assumptions & why new engines pick columnar blocks

The buffer manager allocates a single shared pool (shared_buffers) in 8 KB disk‑page units; every access—whether one row or 300 MB—moves whole 8 KB pages through that cache.​

This row‑store assumption simplifies locking and WAL but makes high‑bandwidth scans memory‑bound. Column stores instead group values of one column together into larger, compressed blocks, bypassing the 8 KB granularity and letting the engine stream data directly to SIMD registers.​

A build‑from‑scratch system (ClickHouse, DuckDB) is free to decide: block size, compression granularity, in‑process vs. client/server, GPU offload, etc.—choices that are hard to shoehorn into Postgres’ shared buffer architecture.
