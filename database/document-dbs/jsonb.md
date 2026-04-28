# JSONB: Binary JSON in Databases

## What is JSONB?

JSONB ("JSON Binary") is a data type for storing JSON documents in a decomposed binary format rather than as raw text. It was popularized by PostgreSQL, which introduced it in version 9.4 (2014), and has since been adopted in various forms by other systems including SQLite (via the `jsonb` extension added in 3.45), CockroachDB, YugabyteDB, and DuckDB.

The key distinction is *how* the JSON is stored. A plain `JSON` (or `TEXT`) column stores the document exactly as it was written — whitespace, key order, and duplicate keys are preserved verbatim. A `JSONB` column parses the document on insert, throws away the cosmetic details, and writes a structured binary representation to disk.

## Why the Binary Format Matters

Storing JSON as text means that every read has to re-parse the document to do anything with it. If your query needs `data->'user'->>'email'`, the database tokenizes the string, walks the tree, and extracts the field — every single time, on every row.

JSONB skips this. Because the document is already decomposed into a tree structure on disk, accessing a field is a pointer-chase rather than a parse. The tradeoff is straightforward:

- **Writes are slower.** The database parses, validates, and restructures the input.
- **Reads are faster**, sometimes dramatically so for queries that touch nested fields.
- **Storage is usually slightly larger** than the equivalent text, because of the structural overhead, though compression often closes the gap.

## What JSONB Loses

Because JSONB normalizes the document, certain things from the original input are gone:

- **Whitespace and formatting** are not preserved.
- **Key ordering** within an object is not preserved (PostgreSQL stores keys in a canonical order; SQLite's format preserves insertion order but is otherwise opaque).
- **Duplicate keys** are de-duplicated; only the last occurrence survives.
- **Numeric precision** beyond what the native numeric type supports may be lost in some implementations.

If your application depends on byte-exact round-tripping of JSON (signing, hashing, audit trails of the literal payload), use `JSON` or `TEXT` instead.

## Indexing

This is where JSONB earns its keep. Because the structure is known to the database, you can build indexes over JSONB content. PostgreSQL's GIN (Generalized Inverted Index) is the canonical example: a GIN index on a JSONB column lets queries like `data @> '{"status": "active"}'` (containment) or `data ? 'email'` (key existence) run against an index instead of scanning the table.

You can also build expression indexes on specific paths — for example, `CREATE INDEX ON users ((data->>'email'))` — which behaves like a regular B-tree index on that extracted field.

## Operators and Functions

JSONB columns come with a rich operator set. In PostgreSQL the most common ones are:

- `->` extracts a field as JSONB (`data->'user'`)
- `->>` extracts a field as text (`data->>'email'`)
- `#>` and `#>>` extract by path (`data#>'{user,address,city}'`)
- `@>` tests containment (`data @> '{"role": "admin"}'`)
- `?`, `?|`, `?&` test key existence (any/all)
- `||` concatenates/merges objects
- `-` removes a key

Most engines also expose functions to build, modify, and walk JSONB values (`jsonb_set`, `jsonb_build_object`, `jsonb_path_query`, etc.).

## When to Use JSONB

JSONB is a good fit when you have data whose schema genuinely varies by row — user-defined fields, third-party API payloads, event logs with heterogeneous shapes, or feature flags. It also works well as an "escape hatch" column on an otherwise relational table for occasional unstructured metadata.

It is *not* a good fit as a wholesale replacement for relational modeling. If every row has the same fields and you query them frequently, normal columns will be smaller, faster, and easier to constrain. The common failure mode is to dump everything into a single `data JSONB` column, lose the benefits of typed schema enforcement, and end up reinventing the relational model badly inside JSON paths.

## Comparison to Document Stores

A natural question is how a JSONB column compares to a document database like MongoDB. The short version: JSONB gives you flexible-schema document storage *inside* a transactional relational engine. You get JSON's shape-flexibility alongside joins, foreign keys, and ACID transactions across both your structured and unstructured columns. Document stores typically optimize harder for horizontal scale-out and for workloads that are document-shaped end-to-end, but you give up the relational toolkit.

For most applications that already use Postgres, JSONB is the right answer for "I need to store some flexible JSON" — reaching for a separate document database is rarely justified by the JSON storage alone.

## Summary

JSONB trades a slightly more expensive write path and the loss of byte-exact preservation for fast structural access, indexable content, and a rich operator set. It's the default choice for storing JSON in PostgreSQL today, and the same idea has spread to most of the database engines that came after.
