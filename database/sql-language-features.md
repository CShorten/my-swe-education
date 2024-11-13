# SQL Language Features: A Comprehensive Guide

## Basic Query Structure
SQL (Structured Query Language) is built around a few core statement types, with SELECT being the most commonly used:

```sql
SELECT column1, column2
FROM table_name
WHERE condition;
```

## Key Features

### 1. Data Querying
- **SELECT**: Retrieves data from one or more tables
- **WHERE**: Filters records based on conditions
- **ORDER BY**: Sorts results
- **GROUP BY**: Groups rows sharing common values
- **HAVING**: Filters grouped results
- **JOIN**: Combines rows from multiple tables
  - INNER JOIN
  - LEFT/RIGHT JOIN
  - FULL OUTER JOIN

### 2. Data Manipulation
- **INSERT**: Adds new records
- **UPDATE**: Modifies existing records
- **DELETE**: Removes records
- **MERGE**: Synchronizes two tables (UPSERT operations)

### 3. Data Definition
- **CREATE**: Defines new database objects
- **ALTER**: Modifies database objects
- **DROP**: Removes database objects
- **TRUNCATE**: Removes all records from a table

### 4. Data Control
- **GRANT**: Assigns privileges
- **REVOKE**: Removes privileges
- **DENY**: Explicitly denies permissions

### 5. Advanced Features

#### Aggregate Functions
- COUNT(): Counts rows
- SUM(): Calculates total
- AVG(): Calculates average
- MAX(): Finds maximum value
- MIN(): Finds minimum value

#### Window Functions
```sql
SELECT column1,
       AVG(column2) OVER (PARTITION BY column3)
FROM table_name;
```

#### Common Table Expressions (CTEs)
```sql
WITH cte_name AS (
    SELECT column1
    FROM table_name
)
SELECT * FROM cte_name;
```

#### Subqueries
- IN/NOT IN
- EXISTS/NOT EXISTS
- Correlated subqueries

### 6. Data Types

#### Numeric Types
- INTEGER
- DECIMAL/NUMERIC
- FLOAT/REAL
- SMALLINT
- BIGINT

#### Character Types
- CHAR
- VARCHAR
- TEXT

#### Date/Time Types
- DATE
- TIME
- TIMESTAMP
- INTERVAL

#### Other Types
- BOOLEAN
- BINARY
- JSON (in modern databases)
- XML

### 7. Constraints

- PRIMARY KEY
- FOREIGN KEY
- UNIQUE
- CHECK
- NOT NULL
- DEFAULT

### 8. Transactions

Transaction control commands:
- BEGIN/START TRANSACTION
- COMMIT
- ROLLBACK
- SAVEPOINT

ACID properties ensured:
- Atomicity
- Consistency
- Isolation
- Durability

### 9. Performance Features

#### Indexing
```sql
CREATE INDEX index_name
ON table_name (column1, column2);
```

#### Views
```sql
CREATE VIEW view_name AS
SELECT column1, column2
FROM table_name
WHERE condition;
```

#### Materialized Views
- Stored query results
- Periodic refresh capabilities
- Improved query performance

## Best Practices

1. Use meaningful table and column names
2. Write maintainable and readable queries
