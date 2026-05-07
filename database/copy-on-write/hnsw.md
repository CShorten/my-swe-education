# Copy-on-Write for HNSW Nodes

HNSW is a graph. Each node has a list of neighbors at each level, and search traversal works by following those neighbor pointers. When you insert a new vector, you don't just add a node — you also modify the neighbor lists of existing nodes to wire the new node into the graph. Deletions and updates similarly mutate existing nodes' edge lists.
This creates a classic concurrency problem: a reader traversing the graph might be reading a node's neighbor list at the exact moment a writer is modifying it. The reader could see a partially updated list, follow a dangling pointer, or skip neighbors. Worst case: crash. Best case: degraded recall.
The naive solutions are all bad:

- Coarse lock on the whole graph — kills read concurrency entirely

- Per-node read-write lock — readers block writers and vice versa, plus the lock-acquisition overhead at every hop in a graph traversal is brutal (you might touch thousands of nodes per query)

- Stop-the-world during snapshots — pauses ingestion for as long as the snapshot takes, which on a 100M-vector index could be many seconds

What you want is for readers to never block, never lock, and always see a consistent view, while writers can keep mutating in the background.

### What copy-on-write does

`The core idea`: immutability for readers, mutation for writers, achieved by copying.

When the system enters snapshot mode (because a snapshot is being taken, or for some other reason that needs a stable point-in-time view), the graph becomes logically frozen for readers. Writers don't stop — but the first time a writer touches any given node after entering snapshot mode, instead of mutating that node in place, it allocates a fresh copy of the node, applies the mutation to the copy, and atomically swaps a pointer so future operations see the copy.

The original node still exists in memory, untouched. Readers that started their traversal before the swap, or readers that hold a reference to the original snapshot view, continue reading the original. They see a consistent pre-snapshot graph. New readers — or the snapshot writer itself — see the new version through the swapped pointer.
This is the same idea behind:

MVCC in Postgres — old row versions stay around for transactions that need to see them
Persistent data structures in functional programming — Clojure's vectors, Haskell's Data.Map
Linux's fork() — child process gets COW pages, only diverges when written
Filesystem snapshots in ZFS and Btrfs

The pattern is general: when you need to give a reader a stable view of mutating state without locking, you make writes produce new versions instead of mutating in place.
The "single-level" part
This is the constraint that makes Weaviate's implementation memory-bounded, and it's worth understanding precisely.
A naive COW scheme might copy on every mutation. So if node X gets updated three times during snapshot mode, you'd get: original → copy1 → copy2 → copy3. That's a chain of versions, each pinned in memory until no reader references them. Under sustained write load, this chain grows unboundedly and you get a memory blow-up that looks a lot like a GC pathology — lots of "garbage" versions hanging around, each holding references to neighbor nodes, none reclaimable until the slowest reader finishes.
Single-level COW says: there's the original, and there's at most one copy. The first write to a node during snapshot mode allocates the copy. The second, third, and Nth writes mutate the copy in place. So the memory overhead is bounded by 2 × (number of nodes touched during snapshot mode), never worse.
The trade-off this implies: readers don't get arbitrary point-in-time snapshots. They get either "the pre-snapshot view" (the originals) or "the current view" (which includes the in-place mutations to copies). You can't, for example, ask for "the view as it was 30 seconds into snapshot mode but not 60 seconds in." For HNSW snapshots — where the goal is "give me a consistent view of the index for backup purposes" — that's exactly what you need and no more.
It also means snapshot mode is bounded in duration. You enter it, take the snapshot (which involves walking the graph and serializing it), and exit. The longer snapshot mode lasts, the more nodes get copied, the more memory is held. So this scheme assumes snapshots are taken occasionally rather than being a continuous mode of operation.
Why this matters for the read concurrency story

This is part of how Weaviate keeps the read path fast even when the system is doing heavy background work. A snapshot is exactly the kind of long-running operation that, in a less carefully designed system, would cause read latency spikes. With single-level COW:

Readers traversing the HNSW graph during a snapshot don't acquire locks on nodes. They follow pointers as they always do.
Writers don't block waiting for readers to finish. They produce copies and move on.
The snapshot itself can walk the original immutable graph at its own pace without coordinating with readers or writers.
When snapshot mode ends, the copies are merged back (the in-place edits become the canonical state), the originals are released, and COW is disabled. Memory returns to baseline.

Crucially, this isn't the only mechanism Weaviate uses for read/write concurrency — it's the specific scheme used during snapshots. The general read-during-write story under normal operation involves async indexing (writes go through a queue and are applied to the graph in batches by dedicated workers, decoupled from the user-facing write path) and finer-grained synchronization on neighbor list updates. The COW scheme layers on top to handle the snapshot case specifically.
