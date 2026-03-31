---
title: Partitioning for Tables and Indexes
type: study-material
tags:
  - dp-800
  - partitioning
  - partition-function
  - partition-scheme
---

# Partitioning for Tables and Indexes

## Overview

Table and index partitioning divides large tables into smaller, manageable chunks based on a partition key — typically a date column. This enables partition elimination, efficient data archiving (partition switching), and parallel operations across partitions.

> [!abstract]
> - Covers table and index partitioning: partition functions, partition schemes, and partition switching
> - Partitioning improves manageability and query performance on large tables by physically separating data ranges
> - Key exam topics: function vs scheme (two separate objects), $PARTITION, partition switching for bulk operations

> [!tip] What the Exam Tests
> - **Partition function** defines value boundaries (ranges); **partition scheme** maps those ranges to filegroups — they are two distinct objects
> - `$PARTITION.FunctionName(column)` returns the partition number for a given value
> - **Partition switching** (`ALTER TABLE … SWITCH`) moves an entire partition instantly — used for bulk load staging and archiving

---

## Partitioning Components

Partitioning requires three objects:

1. **Partition Function** — defines boundary values and range direction
2. **Partition Scheme** — maps partitions to filegroups
3. **Partitioned Table/Index** — table or index created `ON` the partition scheme

### Partition Function

A **partition function** defines the boundary values and direction (RANGE LEFT or RANGE RIGHT) that determine which rows go into each partition.

```sql
-- RANGE LEFT: boundary value belongs to the LEFT partition
-- RANGE RIGHT: boundary value belongs to the RIGHT partition (typical for dates)
CREATE PARTITION FUNCTION PF_SalesByMonth (date)
AS RANGE RIGHT FOR VALUES (
    '2025-01-01', '2025-02-01', '2025-03-01',
    '2025-04-01', '2025-05-01', '2025-06-01',
    '2025-07-01', '2025-08-01', '2025-09-01',
    '2025-10-01', '2025-11-01', '2025-12-01',
    '2026-01-01'
);
-- Creates 14 partitions: 1 before Jan 2025, 12 monthly, 1 after Jan 2026
```

> [!warning] Common Mistake
> Creating a partition function is not enough — you must also create a partition scheme that maps the function's ranges to filegroups, then create the table ON that scheme. The exam may ask you to identify which step is missing.

**RANGE LEFT vs RANGE RIGHT:**

| Direction | Boundary value belongs to | Typical use |
| :--- | :--- | :--- |
| `RANGE LEFT` | Left (lower) partition (≤ boundary) | Numeric ranges |
| `RANGE RIGHT` | ==Right (upper) partition (≥ boundary)== | Date ranges — boundary starts the new period |

### Partition Scheme

```sql
-- Map all partitions to PRIMARY (simple setup)
CREATE PARTITION SCHEME PS_SalesByMonth
AS PARTITION PF_SalesByMonth ALL TO ([PRIMARY]);

-- Or map to specific filegroups for I/O separation
CREATE PARTITION SCHEME PS_SalesByMonth
AS PARTITION PF_SalesByMonth
TO (FG_Archive, FG_2025_Jan, FG_2025_Feb, FG_2025_Mar,
    FG_2025_Apr, FG_2025_May, FG_2025_Jun,
    FG_2025_Jul, FG_2025_Aug, FG_2025_Sep,
    FG_2025_Oct, FG_2025_Nov, FG_2025_Dec,
    FG_Future);
```

### Partitioned Table

```sql
CREATE TABLE dbo.Sales (
    SaleId      int             NOT NULL,
    SaleDate    date            NOT NULL,
    CustomerId  int             NOT NULL,
    Amount      decimal(10,2)   NOT NULL,
    CONSTRAINT PK_Sales PRIMARY KEY CLUSTERED (SaleDate, SaleId)
) ON PS_SalesByMonth (SaleDate);  -- partitioned on SaleDate
```

---

## Partition Switching

Partition switching is a near-instant metadata-only operation — SQL Server reassigns the data pages from one table to another without physically moving any rows.

**SWITCH OUT** moves a partition from the main table to an archive table. **SWITCH IN** loads a staged partition into the main table.

**Requirements:**

- Source and target tables must have identical structure (same columns, data types, constraints)
- Source and target must be on the same filegroup
- Target partition must be empty when switching IN

```sql
-- Switch partition 1 (oldest month) out to archive table
ALTER TABLE Orders
SWITCH PARTITION 1 TO OrdersArchive;

-- Switch staged data into main table's latest partition
ALTER TABLE OrdersStaging
SWITCH TO Orders PARTITION 12;

-- Verify partition contents before/after
SELECT partition_number, rows
FROM sys.partitions
WHERE object_id = OBJECT_ID('Orders') AND index_id <= 1;
```

---

## Sliding Window Pattern

The sliding window pattern continuously adds new partitions for incoming data and removes old ones, keeping a rolling window (e.g., last 12 months) without unbounded table growth.

**Steps for each cycle:**

1. Add a new boundary value with `SPLIT RANGE` (creates a new empty partition for the next period)
2. Switch the oldest partition out to an archive table
3. Merge the old boundary with `MERGE RANGE` (removes the now-empty partition)

```sql
-- Step 1: Add new boundary for next month
ALTER PARTITION FUNCTION pf_OrdersByMonth()
SPLIT RANGE ('2025-02-01');

-- Step 2: Switch oldest partition to archive
ALTER TABLE Orders SWITCH PARTITION 1 TO OrdersArchive;

-- Step 3: Merge old boundary (removes empty partition)
ALTER PARTITION FUNCTION pf_OrdersByMonth()
MERGE RANGE ('2024-01-01');
```

**Key tip:** Always SPLIT before loading new data, and always switch out the old partition before merging its boundary. SPLIT on an empty partition is instantaneous; SPLIT on a populated partition causes data movement.

---

## Managing Partitions

```sql
-- Add a new partition for future data
ALTER PARTITION SCHEME PS_SalesByMonth NEXT USED [PRIMARY];
ALTER PARTITION FUNCTION PF_SalesByMonth()
SPLIT RANGE ('2026-02-01');

-- Merge two adjacent partitions (consolidate old data)
ALTER PARTITION FUNCTION PF_SalesByMonth()
MERGE RANGE ('2025-01-01');

-- Check partition info
SELECT $PARTITION.PF_SalesByMonth('2025-06-15') AS PartitionNumber;

-- Row counts per partition
SELECT
    p.partition_number,
    p.rows,
    prv.value AS boundary_value
FROM sys.partitions p
JOIN sys.partition_functions pf ON pf.function_id = p.function_id
LEFT JOIN sys.partition_range_values prv
    ON prv.function_id = pf.function_id
    AND prv.boundary_id = p.partition_number
WHERE pf.name = 'PF_SalesByMonth'
ORDER BY p.partition_number;
```

---

## Partition Elimination

**Partition elimination** is the optimizer behavior of skipping partitions that cannot contain rows matching the query's WHERE clause. It is one of the primary performance benefits of partitioning.

**Requirement:** The query filter must reference the partition column directly. Implicit conversions or computed expressions on the column can prevent elimination.

**Verifying elimination:** In the execution plan, select the Clustered Index Seek or Scan operator and inspect "Partitions Accessed" in the properties pane. A range like `[6, 6]` means only partition 6 was scanned.

```sql
-- This query eliminates most partitions (filter on partition column)
SELECT OrderID, TotalAmount
FROM Orders
WHERE OrderDate >= '2024-06-01' AND OrderDate < '2024-07-01';
-- ^ Execution plan: accesses only partition 6

-- This query does NOT eliminate partitions (filter on non-partition column)
SELECT OrderID, TotalAmount
FROM Orders
WHERE CustomerID = 12345;
-- ^ Execution plan: scans all partitions

-- Check partitions accessed in sys.dm_exec_query_stats
```

If your queries commonly filter on a column other than the partition key, partitioning on that key provides no elimination benefit and may add overhead.

---

## Aligned vs Non-Aligned Indexes

An **aligned index** uses the same partition function as the base table, so each index partition maps to the same rows as the corresponding table partition.

A **non-aligned index** has a different partitioning scheme (or is not partitioned at all) from the base table.

**Why it matters:**

- Partition switching requires that all indexes on the table are aligned with the table's partition scheme
- Non-aligned indexes block SWITCH operations
- The optimizer can leverage aligned indexes for partition elimination on index seeks

**Recommendation:** Always create indexes using the same partition scheme as the base table. When designing a partitioned table, define the partition scheme first, then all indexes on it.

---

## Use Cases

- **Date-based tables**: Orders, transactions, logs — partition by month or year
- **Fast archiving**: Switch old partitions to archive table in milliseconds
- **Parallel operations**: Maintenance tasks (rebuild, statistics) run per partition
- **Data lifecycle**: Drop old data by switching out a partition then truncating it

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Switch fails: not on same filegroup | Partition scheme maps to different FG | Use `ALL TO [PRIMARY]` for simplicity |
| Switch fails: target not empty | Staging/archive partition has rows | ==Truncate or move target partition first== |
| No partition elimination | WHERE clause doesn't use partition key | Ensure filter is on the partition column directly |
| SPLIT/MERGE slow | Large data movement between partitions | Keep the new/merged partition empty before SPLIT |
| Switch fails: non-aligned index | Table has an index on a different scheme | Rebuild the index ON the same partition scheme |

---

## Best Practices

- Use `RANGE RIGHT` for date-based partition functions — the boundary value becomes the first date of the new partition, which maps naturally to month or year boundaries.
- Always `SPLIT RANGE` before the new period's data arrives; the new partition must be empty at split time to avoid data movement.
- Map all partitions to `[PRIMARY]` during development; introduce separate filegroups for I/O separation only when storage architecture justifies it.
- Align all indexes (clustered and nonclustered) with the table's partition scheme so that `SWITCH` operations succeed without rebuilding indexes.
- Automate the sliding window cycle (SPLIT → SWITCH → MERGE) in a stored procedure or SQL Agent job to ensure consistent execution each period.

---

## Exam Tips

> [!tip] Exam Tips
> - **Partition function** defines the rules; **partition scheme** maps to filegroups
> - `RANGE RIGHT` is standard for date partitioning — boundary value starts the new partition
> - Partition switching is a **metadata-only operation** — extremely fast even for billions of rows
> - Adding a new partition requires `ALTER PARTITION SCHEME ... NEXT USED` first, then `SPLIT`
> - Partition elimination only occurs when the WHERE clause filters **directly on the partition column**
> - All indexes must be **aligned** (same partition scheme) for `SWITCH` to succeed

---

## Key Takeaways

- Three objects needed: partition function → partition scheme → table/index on scheme
- Partition elimination improves performance only when filtering on the partition key
- SPLIT and MERGE modify partition boundaries; SWITCH moves data between tables
- The sliding window pattern (SPLIT → SWITCH → MERGE) manages a rolling data window efficiently
- Aligned indexes are required for partition switching and enable partition elimination on index seeks

---

## Practice Question

You need to archive last month's orders from a partitioned Orders table to an archive table with zero downtime. Which operation achieves this?

A. INSERT INTO OrdersArchive SELECT ... followed by DELETE FROM Orders
B. ALTER TABLE Orders SWITCH PARTITION n TO OrdersArchive
C. CREATE TABLE OrdersArchive AS SELECT * FROM Orders WHERE OrderDate < ...
D. ALTER PARTITION FUNCTION MERGE RANGE on the oldest boundary

> [!success]- Answer
> **B — ALTER TABLE Orders SWITCH PARTITION n TO OrdersArchive**
>
> Partition SWITCH is a metadata-only operation that completes near-instantly with minimal locking — it simply reassigns the partition's data pages to the target table. INSERT/DELETE (A) physically moves data and holds locks. CREATE TABLE AS SELECT (C) is not valid T-SQL syntax. MERGE RANGE (D) removes a boundary but doesn't move data to an archive.

---

## Related Topics

- [01-Tables & Indexes](./01-tables-indexes.md)
- [06-Performance Optimization](../06-performance-optimization/README.md)

---

## Official Documentation

- [Partitioned Tables and Indexes](https://learn.microsoft.com/en-us/sql/relational-databases/partitions/partitioned-tables-and-indexes)
- [Partition Function (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-partition-function-transact-sql)

---

**[← Previous](./04-constraints-sequences.md) | [↑ Back to Section](./README.md)**
