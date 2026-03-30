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

## Heap vs Clustered Table

| Aspect | Heap (no clustered index) | Clustered Table |
| :--- | :--- | :--- |
| **Storage** | IAM + data pages in any order | Sorted B-tree pages |
| **INSERT** | Fast (append) | May cause page splits |
| **SELECT by PK** | Full scan (no order) | Efficient seek |
| **Forwarding pointers** | Yes (after UPDATEs) | No |
| **Best for** | Staging/bulk load, then index | Most OLTP tables |

## Use Cases

- **Column store indexes**: Data warehouse fact tables, reporting aggregations over millions of rows
- **Non-clustered with INCLUDE**: Covering indexes to avoid key lookups in common query patterns
- **Heaps**: Temporary staging tables for bulk inserts before final processing

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Index fragmentation | Frequent INSERT/UPDATE/DELETE | Rebuild (`ALTER INDEX ... REBUILD`) or reorganize |
| Page splits | Sequential GUID PKs cause random inserts | Use `NEWSEQUENTIALID()` or `INT IDENTITY` |
| Delta store large | Low row count inserts into columnstore | Batch inserts to fill row groups (min 102,400 rows) |
| `nvarchar(max)` off-row | Value exceeds 8000 bytes | Expected behavior; consider chunking large text |

## Exam Tips

- Know the difference between **clustered columnstore** (replaces rowstore) vs **non-clustered columnstore** (supplements rowstore)
- Batch mode execution is available with columnstore indexes — a key performance differentiator
- `datetime2` is preferred over `datetime` for new development (greater precision, more range)
- `INCLUDE` columns in non-clustered indexes create covering indexes without widening the key

## Key Takeaways

- Choose the smallest data type that meets requirements
- Clustered index = physical row order; only one per table
- Column store indexes enable vectorized batch execution for analytics
- Non-clustered columnstore can be added to OLTP tables for hybrid workloads

## Related Topics

- [02-Specialized Tables](./02-specialized-tables.md)
- [04-Constraints & Sequences](./04-constraints-sequences.md)
- [05-Partitioning](./05-partitioning.md)

## Official Documentation

- [Tables (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/tables/tables)
- [Columnstore Indexes Guide](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview)
- [Index Design Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide)

---

**[↑ Back to Section](./README.md) | [Next →](./02-specialized-tables.md)**
