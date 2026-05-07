  2. Single-Level Copy-on-Write for HNSW Nodes                                                                                                  

  For the HNSW graph itself, Weaviate implements a single-level copy-on-write scheme (introduced alongside HNSW snapshots):                       
  
  - When snapshot mode is active, any HNSW node that gets updated is copied once. The original remains immutable for concurrent readers.          
  - Subsequent mutations to that same node edit the copy in-place — no cascading copies.                                                        
  - When snapshot mode ends, the copies are merged back into a single consistent view and COW is disabled.                                        
                                                                                                                                                  
  This gives readers a stable, immutable view of the graph to traverse without locks, while writers mutate copies. The "single-level" constraint  
  keeps memory overhead bounded — you never get a chain of copy-of-copy-of-copy.
