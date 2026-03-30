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

## Partitioning Components

Partitioning requires three objects:

1. **Partition Function** — defines boundary values and range direction
2. **Partition Scheme** — maps partitions to filegroups
3. **Partitioned Table/Index** — table or index created `ON` the partition scheme

### Partition Function

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

**RANGE LEFT vs RANGE RIGHT:**
- `RANGE LEFT`: boundary value is the last value in the left partition (≤ boundary)
- `RANGE RIGHT`: boundary value is the first value in the right partition (≥ boundary)
- For date ranges, `RANGE RIGHT` is more intuitive (e.g., `'2025-01-01'` starts the January partition)

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

## Partition Switching

Partition switching moves an entire partition atomically (metadata-only operation) — used for fast archiving or loading:

```sql
-- Archive January 2025: switch partition 2 to archive table
ALTER TABLE dbo.Sales
SWITCH PARTITION 2 TO dbo.Sales_Archive PARTITION 2;

-- Load new data: switch from staging to main table
ALTER TABLE dbo.Sales_Staging
SWITCH TO dbo.Sales PARTITION 14;
```

**Requirements for partition switch:**
- Both tables must have identical structure (same columns, data types, constraints)
- Target partition must be empty (when switching IN)
- Both must be on the same filegroup (when on different filegroups)

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

## Partition Elimination

The optimizer skips irrelevant partitions when the WHERE clause filters on the partition key:

```sql
-- Query only scans partition(s) for June 2025 — others eliminated
SELECT SUM(Amount) FROM dbo.Sales
WHERE SaleDate >= '2025-06-01' AND SaleDate < '2025-07-01';
```

## Use Cases

- **Date-based tables**: Orders, transactions, logs — partition by month or year
- **Fast archiving**: Switch old partitions to archive table in milliseconds
- **Parallel operations**: Maintenance tasks (rebuild, statistics) run per partition
- **Data lifecycle**: Drop old data by switching out a partition then truncating it

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Switch fails: not on same filegroup | Partition scheme maps to different FG | Use `ALL TO [PRIMARY]` for simplicity |
| Switch fails: target not empty | Staging/archive partition has rows | Truncate or move target partition first |
| No partition elimination | WHERE clause doesn't use partition key | Ensure filter is on the partition column directly |
| SPLIT/MERGE slow | Large data movement between partitions | Keep the new/merged partition empty before SPLIT |

## Exam Tips

- **Partition function** defines the rules; **partition scheme** maps to filegroups
- `RANGE RIGHT` is standard for date partitioning — boundary value starts the new partition
- Partition switching is a **metadata-only operation** — extremely fast even for billions of rows
- Adding a new partition requires `ALTER PARTITION SCHEME ... NEXT USED` first, then `SPLIT`

## Key Takeaways

- Three objects needed: partition function → partition scheme → table/index on scheme
- Partition elimination improves performance only when filtering on the partition key
- SPLIT and MERGE modify partition boundaries; SWITCH moves data between tables

## Related Topics

- [01-Tables & Indexes](./01-tables-indexes.md)
- [06-Performance Optimization](../06-performance-optimization/README.md)

## Official Documentation

- [Partitioned Tables and Indexes](https://learn.microsoft.com/en-us/sql/relational-databases/partitions/partitioned-tables-and-indexes)
- [Partition Function (Transact-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-partition-function-transact-sql)

---

**[← Previous](./04-constraints-sequences.md) | [↑ Back to Section](./README.md)**
