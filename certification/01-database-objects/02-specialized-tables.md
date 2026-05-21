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

> [!abstract]
>
> - Covers temporal tables (system-versioned history), ledger tables (tamper-evident), and memory-optimized tables
> - Each has distinct syntax and distinct exam scenarios
> - Key exam topics: temporal query syntax, ledger append-only behavior, memory-optimized DURABILITY options

> [!tip] What the Exam Tests
>
> - `FOR SYSTEM_TIME AS OF 'datetime'` is the correct temporal point-in-time syntax — not a WHERE clause on SysStartTime
> - Ledger tables are **append-only** — no UPDATE or DELETE; `GENERATED ALWAYS AS ROW START/END` columns are system-managed
> - Memory-optimized `DURABILITY = SCHEMA_ONLY` means data is lost on restart; `SCHEMA_AND_DATA` survives

---

## In-Memory (Memory-Optimized) Tables

**Memory-optimized tables** are stored in memory and use optimistic concurrency without locking for ultra-high-throughput OLTP workloads.

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

---

## Memory-Optimized Table Durability Options

The `DURABILITY` option controls whether data survives a server restart.

| Durability | Survives Restart | Transaction Log | Best For |
| :--- | :--- | :--- | :--- |
| `SCHEMA_AND_DATA` | Yes (data + structure) | Yes — fully logged | Orders, financial data, anything requiring persistence |
| `SCHEMA_ONLY` | ==Structure only (data lost)== | No logging | Session state, caches, temp aggregations |

```sql
-- SCHEMA_AND_DATA: durable (default) — data persists through restart
CREATE TABLE dbo.HotOrders (
    OrderID     INT             NOT NULL PRIMARY KEY NONCLUSTERED,
    CustomerID  INT             NOT NULL,
    TotalAmount DECIMAL(18,2)   NOT NULL,
    INDEX IX_HotOrders_Customer NONCLUSTERED (CustomerID)
) WITH (MEMORY_OPTIMIZED = ON, DURABILITY = SCHEMA_AND_DATA);

-- SCHEMA_ONLY: data lost on restart, fastest writes — no transaction log overhead
CREATE TABLE dbo.SessionState (
    SessionID   NVARCHAR(100)   NOT NULL PRIMARY KEY NONCLUSTERED,
    CachedData  NVARCHAR(MAX)   NOT NULL,
    ExpiresAt   DATETIME2       NOT NULL
) WITH (MEMORY_OPTIMIZED = ON, DURABILITY = SCHEMA_ONLY);
```

**Memory-optimized table variables** (declared with `DECLARE @t <type>`) are always in-memory with no durability option — they are scoped to the batch and never persisted.

---

## Temporal Tables (System-Versioned)

**Temporal tables** automatically maintain a history of all row changes, enabling time-travel queries.

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
| `AS OF <date>` | ==Row state at exactly that point in time== |
| `FROM <start> TO <end>` | Rows active during any part of the range |
| `BETWEEN <start> AND <end>` | Inclusive of the end boundary |
| `CONTAINED IN (<start>, <end>)` | Rows that started AND ended within the range |
| `ALL` | All current and historical rows |

---

## Temporal Table — Versioning Queries

Each `FOR SYSTEM_TIME` clause has distinct boundary semantics — these differences are exam-tested.

**AS OF** — Point-in-time snapshot. Returns the row version that was active at the exact moment specified.

**FROM...TO** — Open interval (exclusive on both ends). Returns any row whose active period overlapped with `[start, end)`.

**BETWEEN...AND** — Closed interval (inclusive end). Returns rows active during `[start, end]` — includes rows active exactly at the end boundary.

**CONTAINED IN** — Returns only rows whose entire lifetime (start AND end) falls within the specified window. Useful for finding records created and deleted within a period.

**ALL** — Returns every row from both the current table and the history table. Ideal for full audit trails.

> [!warning] Common Mistake
> `FOR SYSTEM_TIME AS OF` and `FOR SYSTEM_TIME ALL` are different: AS OF returns the point-in-time snapshot; ALL returns all rows including history. Don't confuse temporal tables (audit history) with ledger tables (tamper evidence) — they solve different problems.

```sql
-- Point-in-time snapshot: row state as it existed at exactly midnight Jan 1
SELECT * FROM dbo.Employees
FOR SYSTEM_TIME AS OF '2024-01-01T00:00:00';

-- All changes within a period (exclusive boundaries)
SELECT *, ValidFrom, ValidTo
FROM dbo.Employees
FOR SYSTEM_TIME FROM '2024-01-01' TO '2024-07-01';

-- Rows entirely within a period (started AND ended inside the window)
SELECT * FROM dbo.Employees
FOR SYSTEM_TIME CONTAINED IN ('2024-01-01', '2024-07-01');

-- Full audit trail for a specific employee across all history
SELECT *, ValidFrom, ValidTo
FROM dbo.Employees
FOR SYSTEM_TIME ALL
WHERE EmployeeId = 42
ORDER BY ValidFrom;
```

---

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

---

## Ledger Tables

Ledger tables provide tamper-evident, cryptographically verified audit trails using a blockchain-style linked hash chain built directly into SQL.

**Two types of ledger tables:**

- **Updatable ledger tables** — support INSERT, UPDATE, DELETE; maintain a separate history table; each transaction is recorded with a cryptographic hash linking to the previous transaction
- **Append-only ledger tables** — support INSERT only; rows cannot be updated or deleted; ideal for immutable audit logs

**Auto-generated columns** (updatable ledger): `ledger_transaction_id`, `ledger_sequence_number`, `ledger_operation_type`, `ledger_operation_type_desc`

```sql
-- Updatable ledger table: supports all DML, maintains full change history
CREATE TABLE dbo.Salaries (
    EmployeeID  INT             NOT NULL,
    Salary      DECIMAL(18,2)   NOT NULL,
    CONSTRAINT PK_Salaries PRIMARY KEY (EmployeeID)
) WITH (LEDGER = ON);

-- Append-only ledger table: INSERT only — UPDATE and DELETE are blocked
CREATE TABLE dbo.FinancialTransactions (
    TransactionID   INT IDENTITY PRIMARY KEY,
    Amount          DECIMAL(18,2),
    Description     NVARCHAR(500)
) WITH (LEDGER = ON, APPEND_ONLY = ON);

-- Verify ledger integrity: confirms no tampering since creation
EXEC sp_verify_database_ledger;

-- View the auto-created ledger history view for an updatable ledger table
SELECT * FROM dbo.MSSQL_LedgerHistoryFor_Salaries;
```

**Ledger verification** (`sp_verify_database_ledger`) recomputes the hash chain and compares it to stored digests. Any out-of-band modification — even by a DBA — breaks the chain and causes verification to fail, providing cryptographic proof of tampering.

---

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

---

## Use Cases

| Table Type | Best For |
| :--- | :--- |
| **In-Memory** | Session state, shopping carts, real-time counters |
| **Temporal** | Audit history, slowly changing dimensions, compliance |
| **External** | Data virtualization, querying data lake files |
| **Ledger** | ==Financial records, regulated audit trails, cryptographic proof== |
| **Graph** | Social networks, fraud detection, recommendation engines |

---

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Memory-optimized table creation fails | No MEMORY_OPTIMIZED_DATA filegroup | Add filegroup before creating table |
| Temporal history table growing large | High update frequency | Add retention policy: `HISTORY_RETENTION_PERIOD = 1 YEAR` |
| External table slow | File format mismatch or no statistics | Use `CREATE STATISTICS` on external tables |
| Ledger verify fails | File tampering or corruption | ==Report to compliance; evidence of tampering== |
| `CONTAINED IN` returns no rows | Period wider than any row's lifetime | Check ValidFrom/ValidTo range; rows must start AND end inside the window |

---

## Best Practices

- Use `SCHEMA_ONLY` durability for memory-optimized tables that hold transient state (sessions, caches) — it eliminates transaction log overhead and delivers maximum throughput
- Always specify a `HISTORY_TABLE` name when creating temporal tables; letting SQL auto-generate it makes schema management harder
- Prefer `CONTAINED IN` when auditing completed transactions within a reporting window; use `FROM...TO` when you need any overlap
- Store ledger database digests in Azure Confidential Ledger or Azure Blob Storage immutable containers so `sp_verify_database_ledger` can use external digests as a trust anchor
- Use append-only ledger tables for event logs and financial transactions where immutability is a compliance requirement; reserve updatable ledger for master data that legitimately changes

---

## Exam Tips

> [!tip] Exam Tips
>
> - **Temporal** tables need two `datetime2` columns with `PERIOD FOR SYSTEM_TIME` — the database tracks them automatically
> - **In-memory** tables require a `MEMORY_OPTIMIZED_DATA` filegroup first
> - **`CONTAINED IN`** vs **`FROM...TO`**: `CONTAINED IN` requires both ValidFrom and ValidTo to be within the window; `FROM...TO` only requires overlap
> - **Ledger** append-only tables prevent UPDATE and DELETE — useful for immutable audit logs; updatable ledger tables still allow DML but record it all
> - **Graph** tables use `$node_id` and `$edge_id` system columns automatically
> - **`sp_verify_database_ledger`** is the key verb for proving tamper-evidence — know it by name

---

## Key Takeaways

- Each specialized table type solves a specific problem: throughput, history, virtualization, tamper-evidence, or relationships
- Temporal tables automatically version history — no application code changes needed
- Ledger tables can be verified cryptographically with `sp_verify_database_ledger`; even DBAs cannot modify data without detection
- `SCHEMA_ONLY` memory-optimized tables trade durability for maximum write speed — appropriate for ephemeral data

---

**Practice Question**

An auditor asks for proof that no one has modified the salary records table since it was created. Which table type provides cryptographic proof of data integrity?

A. Temporal table with SYSTEM_TIME versioning
B. Ledger table with APPEND_ONLY = ON
C. Updatable ledger table with sp_verify_database_ledger
D. Memory-optimized table with DURABILITY = SCHEMA_AND_DATA

> [!success]- Answer
> **C — Updatable ledger table with sp_verify_database_ledger**
>
> Ledger tables maintain a cryptographic hash chain over all transactions. `sp_verify_database_ledger` checks this chain to prove that no rows have been tampered with outside of the normal transactional path — even a DBA cannot modify data without detection. Temporal tables (A) record history but don't prevent or detect tampering. APPEND_ONLY ledger (B) prevents updates but the question asks about an existing salary table that needs updates. Memory-optimized tables (D) provide durability, not tamper-evidence.

---

## Related Topics

- [01-Tables & Indexes](./01-tables-indexes.md)
- [04-Graph Queries](../03-advanced-tsql/04-graph-queries.md)
- [04-Auditing](../05-data-security-compliance/04-auditing.md)

---

## Official Documentation

- [In-Memory OLTP Overview](https://learn.microsoft.com/en-us/sql/relational-databases/in-memory-oltp/overview-and-usage-scenarios)
- [Temporal Tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables)
- [Ledger Tables](https://learn.microsoft.com/en-us/sql/relational-databases/security/ledger/ledger-overview)
- [Graph Tables](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-overview)

---

**[← Previous](./01-tables-indexes.md) | [↑ Back to Section](./database-objects.md) | [Next →](./03-json-columns.md)**
