---
title: Specialized Tables
type: study-material
tags:
  - dp-800
  - in-memory
  - temporal
  - external-tables
  - ledger
  - graph-tables
---

# Specialized Tables

## Overview

SQL Server and Azure SQL support several specialized table types for specific scenarios: in-memory OLTP tables for high throughput, temporal tables for historical queries, external tables for accessing remote data, ledger tables for tamper-evident auditing, and graph tables for relationship data.

## In-Memory (Memory-Optimized) Tables

Memory-optimized tables are stored in memory and use optimistic concurrency without locking for ultra-high-throughput OLTP workloads.

```sql
-- Requires a MEMORY_OPTIMIZED_DATA filegroup
ALTER DATABASE MyDB
ADD FILEGROUP FG_MOT CONTAINS MEMORY_OPTIMIZED_DATA;

ALTER DATABASE MyDB
ADD FILE (NAME = 'mot_file', FILENAME = 'C:\data\mot') TO FILEGROUP FG_MOT;

-- Create memory-optimized table
CREATE TABLE dbo.SessionCache (
    SessionId   uniqueidentifier NOT NULL,
    UserId      int              NOT NULL,
    Data        nvarchar(4000)   NULL,
    ExpiresAt   datetime2(0)     NOT NULL,
    CONSTRAINT PK_SessionCache PRIMARY KEY NONCLUSTERED HASH (SessionId)
        WITH (BUCKET_COUNT = 1048576)
) WITH (MEMORY_OPTIMIZED = ON, DURABILITY = SCHEMA_AND_DATA);
```

**Key characteristics:**
- No page latches or locks — uses optimistic multi-version concurrency (MVCC)
- Indexes: HASH (for equality) or RANGE (BW-tree, for range scans)
- `DURABILITY`: `SCHEMA_AND_DATA` (persisted) or `SCHEMA_ONLY` (lost on restart)
- Natively compiled stored procedures for maximum throughput

## Temporal Tables (System-Versioned)

Temporal tables automatically maintain a history of all row changes, enabling time-travel queries.

```sql
CREATE TABLE dbo.Employees (
    EmployeeId  int             NOT NULL PRIMARY KEY,
    Name        nvarchar(100)   NOT NULL,
    Salary      decimal(10,2)   NOT NULL,
    -- System period columns (auto-managed)
    ValidFrom   datetime2(7)    GENERATED ALWAYS AS ROW START NOT NULL,
    ValidTo     datetime2(7)    GENERATED ALWAYS AS ROW END   NOT NULL,
    PERIOD FOR SYSTEM_TIME (ValidFrom, ValidTo)
) WITH (SYSTEM_VERSIONING = ON (HISTORY_TABLE = dbo.EmployeesHistory));

-- Time-travel query: what was the salary on a specific date?
SELECT EmployeeId, Name, Salary
FROM dbo.Employees
FOR SYSTEM_TIME AS OF '2025-01-01T00:00:00';

-- Show all changes for an employee
SELECT EmployeeId, Name, Salary, ValidFrom, ValidTo
FROM dbo.Employees
FOR SYSTEM_TIME ALL
WHERE EmployeeId = 42
ORDER BY ValidFrom;
```

**Temporal query clauses:**
| Clause | Returns |
| :--- | :--- |
| `AS OF <date>` | Row state at exactly that point in time |
| `FROM <start> TO <end>` | Rows active during any part of the range |
| `BETWEEN <start> AND <end>` | Inclusive of the end boundary |
| `CONTAINED IN (<start>, <end>)` | Rows that started AND ended within the range |
| `ALL` | All current and historical rows |

## External Tables

External tables allow querying data outside the database without importing it — on Azure Blob Storage, ADLS, or other SQL instances.

```sql
-- Create external data source (Azure Blob Storage)
CREATE EXTERNAL DATA SOURCE MyADLS
WITH (
    TYPE = BLOB_STORAGE,
    LOCATION = 'https://myaccount.blob.core.windows.net/mycontainer',
    CREDENTIAL = MyCredential
);

-- Create external file format
CREATE EXTERNAL FILE FORMAT ParquetFormat
WITH (FORMAT_TYPE = PARQUET);

-- Create external table
CREATE EXTERNAL TABLE dbo.ExternalSales (
    SaleId      int,
    Amount      decimal(10,2),
    SaleDate    date
)
WITH (
    LOCATION = '/sales/2025/',
    DATA_SOURCE = MyADLS,
    FILE_FORMAT = ParquetFormat
);
```

## Ledger Tables

Ledger tables provide tamper-evident, cryptographically verified audit trails — stored using a blockchain-like linked hash chain.

```sql
-- Updatable ledger table (tracks all changes)
CREATE TABLE dbo.AccountBalances (
    AccountId   int             NOT NULL PRIMARY KEY,
    Balance     decimal(18,2)   NOT NULL
) WITH (LEDGER = ON);

-- Append-only ledger table (no UPDATE/DELETE allowed)
CREATE TABLE dbo.TransactionLog (
    TransactionId   uniqueidentifier NOT NULL DEFAULT NEWID(),
    Amount          decimal(18,2)    NOT NULL,
    Timestamp       datetime2(0)     NOT NULL DEFAULT GETUTCDATE()
) WITH (LEDGER = ON, APPEND_ONLY = ON);

-- Verify ledger integrity
EXECUTE sp_verify_database_ledger;
```

**Auto-generated columns (updatable ledger):** `ledger_transaction_id`, `ledger_sequence_number`, `ledger_operation_type`, `ledger_operation_type_desc`

## Graph Tables

Graph tables store nodes (entities) and edges (relationships) for querying connected data.

```sql
-- Node table
CREATE TABLE dbo.Person (
    PersonId    int         NOT NULL PRIMARY KEY,
    Name        nvarchar(100) NOT NULL
) AS NODE;

-- Edge table
CREATE TABLE dbo.Knows AS EDGE;

-- Insert
INSERT INTO dbo.Person VALUES (1, 'Alice'), (2, 'Bob');
INSERT INTO dbo.Knows VALUES (
    (SELECT $node_id FROM dbo.Person WHERE PersonId = 1),
    (SELECT $node_id FROM dbo.Person WHERE PersonId = 2)
);

-- MATCH query: find all friends of Alice
SELECT p2.Name
FROM dbo.Person p1, dbo.Knows k, dbo.Person p2
WHERE MATCH(p1-(k)->p2)
AND p1.Name = 'Alice';
```

See [04-Graph Queries](../03-advanced-tsql/04-graph-queries.md) for advanced MATCH patterns.

## Use Cases

| Table Type | Best For |
| :--- | :--- |
| **In-Memory** | Session state, shopping carts, real-time counters |
| **Temporal** | Audit history, slowly changing dimensions, compliance |
| **External** | Data virtualization, querying data lake files |
| **Ledger** | Financial records, regulated audit trails |
| **Graph** | Social networks, fraud detection, recommendation engines |

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Memory-optimized table creation fails | No MEMORY_OPTIMIZED_DATA filegroup | Add filegroup before creating table |
| Temporal history table growing large | High update frequency | Add retention policy: `HISTORY_RETENTION_PERIOD = 1 YEAR` |
| External table slow | File format mismatch or no statistics | Use `CREATE STATISTICS` on external tables |
| Ledger verify fails | File tampering or corruption | Report to compliance; evidence of tampering |

## Exam Tips

- **Temporal** tables need two `datetime2` columns with `PERIOD FOR SYSTEM_TIME` — the database tracks them automatically
- **In-memory** tables require a `MEMORY_OPTIMIZED_DATA` filegroup first
- **Ledger** append-only tables prevent UPDATE and DELETE — useful for immutable audit logs
- **Graph** tables use `$node_id` and `$edge_id` system columns automatically

## Key Takeaways

- Each specialized table type solves a specific problem: throughput, history, virtualization, tamper-evidence, or relationships
- Temporal tables automatically version history — no application code changes needed
- Ledger tables can be verified cryptographically with `sp_verify_database_ledger`

## Related Topics

- [01-Tables & Indexes](./01-tables-indexes.md)
- [04-Graph Queries](../03-advanced-tsql/04-graph-queries.md)
- [04-Auditing](../05-data-security-compliance/04-auditing.md)

## Official Documentation

- [In-Memory OLTP Overview](https://learn.microsoft.com/en-us/sql/relational-databases/in-memory-oltp/overview-and-usage-scenarios)
- [Temporal Tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables)
- [Ledger Tables](https://learn.microsoft.com/en-us/sql/relational-databases/security/ledger/ledger-overview)
- [Graph Tables](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-overview)

---

**[← Previous](./01-tables-indexes.md) | [↑ Back to Section](./README.md) | [Next →](./03-json-columns.md)**
