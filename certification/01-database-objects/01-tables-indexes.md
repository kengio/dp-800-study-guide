---
title: Tables, Data Types, and Indexes
type: study-material
tags:
  - dp-800
  - tables
  - indexes
  - column-store
  - data-types
---

# Tables, Data Types, and Indexes

## Overview

Designing and implementing tables is foundational to the DP-800 exam. This covers choosing appropriate data types, designing clustered and non-clustered indexes, and when to use column store indexes for analytical workloads.

> [!abstract]
> - Covers B-tree indexes (clustered, non-clustered), columnstore indexes (CCI, NCCI), and index maintenance
> - Heap tables have no clustered index; adding a CI converts the heap
> - Key exam topics: choosing index type for OLTP vs analytics, fill factor, index fragmentation

> [!tip] What the Exam Tests
> - Choose between **clustered columnstore (CCI)** and clustered B-tree based on workload: CCI = analytics/bulk-load; B-tree = OLTP point lookups
> - Recognize that a **non-clustered columnstore index (NCCI)** can be added to an existing rowstore table for mixed workloads
> - Know that **fill factor** reduces page splits by leaving space in leaf pages — lower fill factor = less splits, more space used

## Table Design

### Choosing Data Types

| Category | Types | Guidance |
| :--- | :--- | :--- |
| **Integer** | `tinyint`, `smallint`, `int`, `bigint` | Use the smallest type that fits the range |
| **Decimal** | `decimal(p,s)`, `numeric(p,s)` | Use for financial data; avoid `float`/`real` for exact values |
| **Character** | `char(n)`, `varchar(n)`, `nvarchar(n)` | Use `nvarchar` for Unicode; `varchar(max)` up to 2 GB |
| **Date/Time** | `date`, `time`, `datetime2`, `datetimeoffset` | Prefer `datetime2` over legacy `datetime` |
| **Binary** | `varbinary(n)`, `varbinary(max)` | For BLOBs; consider Azure Blob Storage for very large objects |
| **Other** | `uniqueidentifier`, `bit`, `xml`, `json` (via `nvarchar`) | `uniqueidentifier` for GUIDs |

```sql
CREATE TABLE dbo.Orders (
    OrderId     INT             NOT NULL IDENTITY(1,1),
    CustomerId  INT             NOT NULL,
    OrderDate   datetime2(0)    NOT NULL DEFAULT GETUTCDATE(),
    TotalAmount decimal(18,2)   NOT NULL,
    Notes       nvarchar(1000)  NULL,
    CONSTRAINT PK_Orders PRIMARY KEY CLUSTERED (OrderId)
);
```

### Column Size Considerations

- `nvarchar(max)` prevents row compression and some index features; use explicit size when possible
- `varchar(max)` / `varbinary(max)` columns stored off-row when > 8000 bytes
- Use `SPARSE` columns for columns that are mostly NULL (must be a supported type)

## Index Types

### Clustered Index

- Defines the physical sort order of the table (one per table)
- Typically on the primary key
- B-tree structure; all data pages are the leaf level

```sql
-- Clustered index already exists via PRIMARY KEY CLUSTERED above
-- Or create explicitly:
CREATE CLUSTERED INDEX CIX_Orders_OrderDate
ON dbo.Orders (OrderDate);
```

### Non-Clustered Index

- Separate B-tree structure with pointers back to the clustered index
- Up to 999 non-clustered indexes per table

```sql
CREATE NONCLUSTERED INDEX NIX_Orders_CustomerId
ON dbo.Orders (CustomerId)
INCLUDE (OrderDate, TotalAmount);
```

### Column Store Index

Column store indexes store data by column rather than by row, enabling high-compression and vectorized execution — ideal for analytical queries scanning large datasets.

| Type | Use Case |
| :--- | :--- |
| **Clustered Columnstore Index (CCI)** | Full analytical/DW tables; replaces B-tree clustered index |
| **Non-Clustered Columnstore Index (NCCI)** | Add analytical capability to OLTP tables without replacing the rowstore |

```sql
-- Clustered Columnstore (replaces traditional clustered index)
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactSales
ON dbo.FactSales;

-- Non-Clustered Columnstore (alongside existing indexes)
CREATE NONCLUSTERED COLUMNSTORE INDEX NCCI_Orders_Analytics
ON dbo.Orders (OrderDate, CustomerId, TotalAmount);
```

**Column store key features:**

- Batch mode execution — processes ~900 rows per batch (vs row-by-row)
- Delta store — rowgroup buffer for newly inserted rows before compression
- Row group elimination — skips compressed row groups where min/max don't match the filter
- Not suitable for single-row lookups; combine with rowstore for mixed workloads

> [!warning] Common Mistake
> A CCI on an OLTP table with frequent single-row updates has high write overhead — the delta rowstore helps but it's not free. Don't recommend CCI for pure OLTP scenarios on the exam.

## Heap vs Clustered Table

| Aspect | Heap (no clustered index) | Clustered Table |
| :--- | :--- | :--- |
| **Storage** | IAM + data pages in any order | Sorted B-tree pages |
| **INSERT** | Fast (append) | May cause page splits |
| **SELECT by PK** | Full scan (no order) | Efficient seek |
| **Forwarding pointers** | Yes (after UPDATEs) | No |
| **Best for** | Staging/bulk load, then index | Most OLTP tables |

## Filtered Indexes

A filtered index is a non-clustered index with a `WHERE` clause predicate, indexing only the rows that satisfy the filter. This reduces index size and maintenance overhead compared to a full non-clustered index.

**When to use:**

- Sparse columns where only a fraction of rows have meaningful values
- Partial data subsets (e.g., only active or pending records)
- Filtering out NULL values from optional columns

**Syntax:**

```sql
-- Index only on active orders
CREATE NONCLUSTERED INDEX IX_Orders_Active
ON Orders(CustomerID, OrderDate)
WHERE Status = 'Active';

-- Index for non-NULL optional columns
CREATE NONCLUSTERED INDEX IX_Employees_Manager
ON Employees(ManagerID)
WHERE ManagerID IS NOT NULL;
```

**Limitations:**

- The query optimizer will not use a filtered index if the query uses a parameter or variable for the filter column — only literal values in the WHERE clause reliably match the filter predicate
- Cannot be used as a covering index for queries that also need rows outside the filter
- Not supported in all scenarios (e.g., cannot be used with `OR` predicates in some cases)

## Included Columns

The `INCLUDE` clause adds non-key columns to the leaf level of a non-clustered index, creating a **covering index** that satisfies a query entirely from the index without a key lookup back to the base table.

**Key vs. included column decisions:**

| Aspect | Key Column | Included Column |
| :--- | :--- | :--- |
| **Sorted** | Yes — in B-tree order | No — stored only at leaf level |
| **16-key limit** | Counts toward limit | Does not count |
| **Use for** | WHERE, JOIN ON, ORDER BY | SELECT output columns only |
| **Index size** | Affects all B-tree levels | Affects leaf level only |

```sql
-- Covering index for a common query pattern
CREATE NONCLUSTERED INDEX IX_Orders_Customer_Covering
ON Orders(CustomerID, OrderDate)
INCLUDE (TotalAmount, Status, ShipDate);
```

> **Exam tip:** Included columns eliminate key lookups (shown as RID Lookup or Key Lookup operators in execution plans). When a query selects columns not in the index key, SQL Server performs a key lookup for each row — adding those columns to `INCLUDE` removes this extra operation.

## Index Compression

Compression reduces the on-disk and in-memory size of index and table data, trading slight CPU overhead for reduced I/O.

**ROW compression:** Stores fixed-length data types in a variable-length format, eliminating storage for trailing zeros and spaces. Compatible with most index types.

**PAGE compression:** Builds on ROW compression and adds:

- **Prefix compression** — stores a common prefix per column once per page, replacing repeated values with shorter references
- **Dictionary compression** — replaces repeated values anywhere on the page with dictionary entries

**COLUMNSTORE compression:** Handled separately from row/page compression. Columnstore uses its own encoding (delta store for new rows → compressed row groups after ~1 M rows). Do not apply ROW/PAGE compression to columnstore indexes.

**Evaluate before applying:**

```sql
-- Estimate savings first
EXEC sp_estimate_data_compression_savings
    @schema_name = 'dbo',
    @object_name = 'Orders',
    @index_id = NULL,
    @partition_number = NULL,
    @data_compression = 'PAGE';

-- Apply compression
ALTER TABLE Orders REBUILD WITH (DATA_COMPRESSION = PAGE);
ALTER INDEX IX_Orders_Customer ON Orders REBUILD WITH (DATA_COMPRESSION = ROW);
```

## Index Design Considerations

Choosing which columns to index — and how — has a significant impact on query performance and write overhead.

- **Index WHERE, JOIN ON, ORDER BY columns first** — these are the columns the optimizer most needs to seek and sort on
- **Avoid over-indexing** — every non-clustered index adds overhead to `INSERT`, `UPDATE`, and `DELETE` operations because each index must be maintained
- **Fill factor** — percentage of each leaf page left free during an index build or rebuild (default `0` = 100% full); a lower fill factor (e.g., 80) leaves room for inserts and reduces page splits on write-heavy tables
- **Statistics** — SQL Server automatically creates statistics for indexed columns; these statistics drive cardinality estimates in the query optimizer
- **Index key order matters** — for composite indexes, put the most selective (highest cardinality) equality columns first, then range columns

## Use Cases

- **Column store indexes**: Data warehouse fact tables, reporting aggregations over millions of rows
- **Non-clustered with INCLUDE**: Covering indexes to avoid key lookups in common query patterns
- **Heaps**: Temporary staging tables for bulk inserts before final processing
- **Filtered indexes**: Active-record patterns, nullable foreign keys, partial dataset queries
- **Index compression**: Large tables with repetitive data where I/O is the bottleneck

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Index fragmentation | Frequent INSERT/UPDATE/DELETE | Rebuild (`ALTER INDEX ... REBUILD`) or reorganize |
| Page splits | Sequential GUID PKs cause random inserts | Use `NEWSEQUENTIALID()` or `INT IDENTITY` |
| Delta store large | Low row count inserts into columnstore | Batch inserts to fill row groups (min 102,400 rows) |
| `nvarchar(max)` off-row | Value exceeds 8000 bytes | Expected behavior; consider chunking large text |
| Filtered index not used | Query uses variable/parameter instead of literal | Rewrite query to use literal value or use `OPTION (RECOMPILE)` |
| Key lookup in plan | Index missing SELECT columns | Add missing columns to `INCLUDE` clause |

## Best Practices

- Prefer `INT IDENTITY` or `NEWSEQUENTIALID()` over `NEWID()` as clustering keys to avoid random page splits
- Always run `sp_estimate_data_compression_savings` before applying compression to production tables
- Add columns needed only in `SELECT` to `INCLUDE`, not to the index key, to keep key width narrow
- Use filtered indexes on low-cardinality flag columns (e.g., `IsActive`, `Status`) rather than full indexes
- Review execution plans for Key Lookup and RID Lookup operators — these indicate missing covered columns

## Exam Tips

- Know the difference between **clustered columnstore** (replaces rowstore) vs **non-clustered columnstore** (supplements rowstore)
- Batch mode execution is available with columnstore indexes — a key performance differentiator
- `datetime2` is preferred over `datetime` for new development (greater precision, more range)
- `INCLUDE` columns in non-clustered indexes create covering indexes without widening the key
- Filtered indexes are not used by the optimizer when the filter column is compared to a variable or parameter — only literals match reliably
- PAGE compression = ROW compression + prefix + dictionary; always estimate savings first with `sp_estimate_data_compression_savings`

## Key Takeaways

- Choose the smallest data type that meets requirements
- Clustered index = physical row order; only one per table
- Column store indexes enable vectorized batch execution for analytics
- Non-clustered columnstore can be added to OLTP tables for hybrid workloads
- Filtered indexes reduce index size by covering only a subset of rows
- INCLUDE columns eliminate key lookups by creating covering indexes at the leaf level
- ROW and PAGE compression reduce storage/I/O at the cost of slight CPU overhead

## Practice Questions

**Practice Question**

A query `SELECT CustomerID, TotalAmount FROM Orders WHERE Status = 'Pending'` performs a key lookup. Which index change eliminates the key lookup?

A. Add a filtered index on Status = 'Pending'
B. Add CustomerID and TotalAmount as INCLUDE columns to the existing Status index
C. Rebuild the clustered index with PAGE compression
D. Create a second clustered index on Status

> [!success]- Answer
> **B — Add CustomerID and TotalAmount as INCLUDE columns to the existing Status index**
>
> Including the SELECT columns (CustomerID, TotalAmount) in the index creates a covering index — the query engine finds everything it needs at the leaf level without a key lookup. A filtered index (A) would help selectivity but doesn't eliminate the key lookup. You cannot have two clustered indexes (D).

## Related Topics

- [02-Specialized Tables](./02-specialized-tables.md)
- [04-Constraints & Sequences](./04-constraints-sequences.md)
- [05-Partitioning](./05-partitioning.md)

## Official Documentation

- [Tables (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/tables/tables)
- [Columnstore Indexes Guide](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview)
- [Index Design Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide)
- [Create Filtered Indexes](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/create-filtered-indexes)
- [Data Compression](https://learn.microsoft.com/en-us/sql/relational-databases/data-compression/data-compression)

---

**[↑ Back to Section](./README.md) | [Next →](./02-specialized-tables.md)**
