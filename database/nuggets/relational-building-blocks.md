# Relational Operators Implementation Guide

## Overview
This guide demonstrates low-level implementations of fundamental relational operators in Golang, showing how database management systems might implement these operations at a basic level.

## Core Data Structures
```go
package relational

import (
    "fmt"
    "strings"
)

// Column represents a database column
type Column struct {
    Name     string
    Type     string
    Nullable bool
}

// Schema represents table structure
type Schema struct {
    Columns []Column
}

// Row represents a single database row
type Row struct {
    Values []interface{}
}

// Table represents a database table
type Table struct {
    Schema Schema
    Rows   []Row
}

// Predicate represents a filtering condition
type Predicate func(Row, Schema) bool

// NewTable creates a new table with given schema
func NewTable(schema Schema) *Table {
    return &Table{
        Schema: schema,
        Rows:   make([]Row, 0),
    }
}
```

## Relational Operators Implementation

### Selection (σ)
```go
// Select implements the selection operator (σ)
// Returns rows that satisfy the given predicate
func (t *Table) Select(pred Predicate) *Table {
    result := NewTable(t.Schema)
    
    for _, row := range t.Rows {
        if pred(row, t.Schema) {
            result.Rows = append(result.Rows, row)
        }
    }
    
    return result
}

// Example usage:
func ExampleSelect() {
    // Create sample table
    schema := Schema{
        Columns: []Column{
            {Name: "id", Type: "int"},
            {Name: "name", Type: "string"},
            {Name: "age", Type: "int"},
        },
    }
    
    table := NewTable(schema)
    table.Rows = []Row{
        {Values: []interface{}{1, "John", 25}},
        {Values: []interface{}{2, "Jane", 30}},
        {Values: []interface{}{3, "Bob", 25}},
    }
    
    // Select rows where age = 25
    result := table.Select(func(r Row, s Schema) bool {
        ageIdx := 2 // Index of age column
        return r.Values[ageIdx].(int) == 25
    })
}
```

### Projection (π)
```go
// Project implements the projection operator (π)
// Returns specified columns from the table
func (t *Table) Project(columnNames []string) *Table {
    // Create new schema with selected columns
    newSchema := Schema{
        Columns: make([]Column, len(columnNames)),
    }
    
    // Map column indices
    indices := make([]int, len(columnNames))
    for i, name := range columnNames {
        for j, col := range t.Schema.Columns {
            if col.Name == name {
                indices[i] = j
                newSchema.Columns[i] = col
                break
            }
        }
    }
    
    // Create new table with projected columns
    result := NewTable(newSchema)
    
    for _, row := range t.Rows {
        newRow := Row{
            Values: make([]interface{}, len(columnNames)),
        }
        for i, idx := range indices {
            newRow.Values[i] = row.Values[idx]
        }
        result.Rows = append(result.Rows, newRow)
    }
    
    return result
}
```

### Union (∪)
```go
// Union implements the union operator (∪)
// Returns all rows from both tables, removing duplicates
func (t *Table) Union(other *Table) (*Table, error) {
    // Check schema compatibility
    if !t.Schema.Equals(other.Schema) {
        return nil, fmt.Errorf("incompatible schemas for union")
    }
    
    result := NewTable(t.Schema)
    seen := make(map[string]bool)
    
    // Add rows from first table
    for _, row := range t.Rows {
        key := row.Hash()
        if !seen[key] {
            result.Rows = append(result.Rows, row)
            seen[key] = true
        }
    }
    
    // Add rows from second table
    for _, row := range other.Rows {
        key := row.Hash()
        if !seen[key] {
            result.Rows = append(result.Rows, row)
            seen[key] = true
        }
    }
    
    return result, nil
}

// Helper method to generate hash for row
func (r Row) Hash() string {
    parts := make([]string, len(r.Values))
    for i, v := range r.Values {
        parts[i] = fmt.Sprintf("%v", v)
    }
    return strings.Join(parts, "|")
}
```

### Set Difference (-)
```go
// Difference implements the set difference operator (-)
// Returns rows in first table that are not in second table
func (t *Table) Difference(other *Table) (*Table, error) {
    // Check schema compatibility
    if !t.Schema.Equals(other.Schema) {
        return nil, fmt.Errorf("incompatible schemas for difference")
    }
    
    result := NewTable(t.Schema)
    seen := make(map[string]bool)
    
    // Mark all rows from second table
    for _, row := range other.Rows {
        seen[row.Hash()] = true
    }
    
    // Add rows from first table that aren't in second
    for _, row := range t.Rows {
        if !seen[row.Hash()] {
            result.Rows = append(result.Rows, row)
        }
    }
    
    return result, nil
}
```

### Cartesian Product (×)
```go
// CartesianProduct implements the cartesian product operator (×)
// Returns all possible combinations of rows from both tables
func (t *Table) CartesianProduct(other *Table) *Table {
    // Create new schema combining both tables
    newSchema := Schema{
        Columns: make([]Column, len(t.Schema.Columns)+len(other.Schema.Columns)),
    }
    
    copy(newSchema.Columns, t.Schema.Columns)
    copy(newSchema.Columns[len(t.Schema.Columns):], other.Schema.Columns)
    
    result := NewTable(newSchema)
    
    // Generate all combinations
    for _, row1 := range t.Rows {
        for _, row2 := range other.Rows {
            newRow := Row{
                Values: make([]interface{}, len(row1.Values)+len(row2.Values)),
            }
            copy(newRow.Values, row1.Values)
            copy(newRow.Values[len(row1.Values):], row2.Values)
            result.Rows = append(result.Rows, newRow)
        }
    }
    
    return result
}
```

### Join (⋈)
```go
// Join implements the natural join operator (⋈)
// Returns rows that match on common columns
func (t *Table) Join(other *Table, pred Predicate) *Table {
    // Find common columns
    commonCols := make(map[string]struct{})
    commonIndices := make(map[string]struct {
        left  int
        right int
    })
    
    for i, col1 := range t.Schema.Columns {
        for j, col2 := range other.Schema.Columns {
            if col1.Name == col2.Name {
                commonCols[col1.Name] = struct{}{}
                commonIndices[col1.Name] = struct {
                    left  int
                    right int
                }{i, j}
            }
        }
    }
    
    // Create new schema
    newSchema := Schema{
        Columns: make([]Column, 0),
    }
    
    // Add columns from left table
    newSchema.Columns = append(newSchema.Columns, t.Schema.Columns...)
    
    // Add non-common columns from right table
    for _, col := range other.Schema.Columns {
        if _, exists := commonCols[col.Name]; !exists {
            newSchema.Columns = append(newSchema.Columns, col)
        }
    }
    
    result := NewTable(newSchema)
    
    // Perform join
    for _, row1 := range t.Rows {
        for _, row2 := range other.Rows {
            // Check if rows match on common columns
            matches := true
            for colName, indices := range commonIndices {
                if row1.Values[indices.left] != row2.Values[indices.right] {
                    matches = false
                    break
                }
            }
            
            if matches && pred(row1, t.Schema) {
                // Create joined row
                newRow := Row{
                    Values: make([]interface{}, len(newSchema.Columns)),
                }
                
                // Copy values from left table
                copy(newRow.Values, row1.Values)
                
                // Copy non-common values from right table
                rightIdx := len(row1.Values)
                for i, col := range other.Schema.Columns {
                    if _, exists := commonCols[col.Name]; !exists {
                        newRow.Values[rightIdx] = row2.Values[i]
                        rightIdx++
                    }
                }
                
                result.Rows = append(result.Rows, newRow)
            }
        }
    }
    
    return result
}
```

## Usage Examples

```go
func main() {
    // Create sample tables
    employeesSchema := Schema{
        Columns: []Column{
            {Name: "id", Type: "int"},
            {Name: "name", Type: "string"},
            {Name: "dept_id", Type: "int"},
        },
    }
    
    departmentsSchema := Schema{
        Columns: []Column{
            {Name: "dept_id", Type: "int"},
            {Name: "dept_name", Type: "string"},
        },
    }
    
    employees := NewTable(employeesSchema)
    employees.Rows = []Row{
        {Values: []interface{}{1, "John", 1}},
        {Values: []interface{}{2, "Jane", 2}},
        {Values: []interface{}{3, "Bob", 1}},
    }
    
    departments := NewTable(departmentsSchema)
    departments.Rows = []Row{
        {Values: []interface{}{1, "Engineering"}},
        {Values: []interface{}{2, "Marketing"}},
    }
    
    // Example: Select all employees in Engineering department
    result := employees.Join(departments, func(r Row, s Schema) bool {
        return true  // No additional conditions
    }).Select(func(r Row, s Schema) bool {
        deptNameIdx := 4  // Index of dept_name in joined table
        return r.Values[deptNameIdx].(string) == "Engineering"
    }).Project([]string{"name"})
    
    // Print results
    for _, row := range result.Rows {
        fmt.Printf("Name: %v\n", row.Values[0])
    }
}
```

## Performance Considerations

1. **Indexing**
   - Implement B-tree or hash indexes for faster lookups
   - Use indexes for join operations
   - Consider covering indexes for projections

2. **Memory Management**
   - Use row buffering for large tables
   - Implement pagination for large result sets
   - Consider memory-efficient hash tables for unions

3. **Optimization**
   - Push down selections before joins
   - Use hash joins for large tables
   - Implement join ordering optimization

4. **Concurrency**
   - Implement row-level locking
   - Use MVCC for concurrent operations
   - Consider parallel execution for large operations

[More details](https://github.com/CShorten/my-swe-education/blob/main/database/nuggets/relational-building-blocks.md)
