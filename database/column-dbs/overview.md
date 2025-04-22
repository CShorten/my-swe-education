# Modern Database Storage Formats

In a brand‑new database engine you're free to store data in whatever physical shape best serves your workload—huge column "stripes," compressed Parquet‑style pages, multi‑tier object‑store "blobs," or in‑memory Apache Arrow buffers that GPUs can scan directly. PostgreSQL can't easily adopt those shapes because every row must still flow through its 8 KB shared‑buffer pages; a green‑field engine can jettison that constraint and optimize for modern CPUs, GPUs, and cloud storage.

## For the professional software engineer

### 1. Why columnar freedom matters

Row stores like Postgres read whole 8 KB pages even when a query touches one column; column stores keep each column in its own contiguous region so they fetch only the bytes needed, compress them better, and vectorize execution.

### 2. Column stripes

In ORC (and similarly in ClickHouse and Delta), data is grouped into large stripes—typically 64‑256 MB—which each contain all the columns for a slice of rows plus index and footer metadata.

Because stripes are independent, different nodes in a distributed job can process them in parallel, and the format can skip entire stripes when min/max statistics show no match for a predicate.

### 3. Compressed Parquet‑like pages

Inside a Parquet file (or DuckDB's zones), each column chunk is further split into data pages that hold 50–100 K values plus optional dictionary and statistics headers.

Pages choose a codec—ZSTD, LZ4, Delta‑Binary‑Packed, etc.—independently, letting hot columns favor speed and archival columns favor ratio.

Readers can jump straight to the page footer offsets, issue a handful of range GETs from S3, and decompress only the predicates they need.

### 4. Tiered blobs (hot + cold object storage)

Engines such as ClickHouse expose storage policies that move older parts from SSD to cheap object stores (S3, Azure Blob) while keeping a local cache for recent data—classic hot / warm / cold tiers.

A new engine can wire tiering logic into its table engine so queries automatically hydrate cold parts into local NVMe and evict them later, without the double‑buffer penalty Postgres would pay.

### 5. GPU‑friendly Arrow buffers

Apache Arrow defines a zero‑copy, columnar in‑memory layout that aligns each column's values, validity bitmaps, and offsets so that SIMD units—or entire GPUs via CUDA—can scan millions of values with one kernel launch.

RAPIDS cuDF, Spark + Rapids, and other frameworks map Arrow buffers directly into device memory, eliminating row decoders and giving 10‑100× speed‑ups on joins and aggregations.

### 6. Why Postgres can't morph into this easily

Every tuple must pass through the 8 KB shared‑buffer pool, and MVCC visibility checks expect that fixed page size.

Changing page format would break WAL replay, replication, vacuum, and dozens of index AMs—hence extensions like cstore_fdw remain bolt‑ons that bypass most of the executor.

A clean‑slate engine can pick any block size, lay columns contiguously, and design a WAL or immutable‑part merge strategy that never touches Postgres' heavy lock manager.

## For the high‑school student

### Think of a database as a huge library

**Row‑store (Postgres)**: every "book" has the whole story—title and every chapter—in one cover. Even if you want just Chapter 2 you still pull the whole book off the shelf.

**Column‑store freedom**: you can shelve all Chapter 2s together, all Chapter 3s together, and so on. Now you grab only the chapters you need, much faster.

### What are the special terms?

| Term | Plain‑English analogy |
|------|----------------------|
| Column stripe | A giant box that holds only chapter 2 (or "column B") for 50,000 books at once; whole boxes can be skipped if the chapter index says the word you're searching for isn't inside. |
| Compressed Parquet page | Inside the box, pages are vacuum‑packed bags—each squishes the words to save space; some bags use a dictionary, others use zip‑like tricks. |
| Tiered blob | Fresh, popular books stay on the library's front shelf (fast SSD). Older books move to the basement or an off‑site warehouse (cheap S3) but can be recalled automatically. |
| GPU‑friendly Arrow buffer | Imagine the words already printed on transparent film so a high‑speed scanner (the GPU) can shine light through many pages at once instead of flipping them one by one. |

### Why inventing your own layout helps

Because a new engine controls how the boxes, bags, and shelves are built, it can:

- Keep only the chapters you ask for on the desk.
- Use the best shrink‑wrap for each chapter.
- Store rarely‑read chapters in the warehouse automatically.
- Hand the transparent film directly to a super‑fast scanner (GPU).

Postgres is like a classic library whose shelves and book sizes are fixed; you can't suddenly shrink‑wrap chapters without rebuilding the whole building. That's why ClickHouse, DuckDB, and other new engines start from scratch—they design the shelves and the shrink‑wrap to match today's hardware and cloud.
