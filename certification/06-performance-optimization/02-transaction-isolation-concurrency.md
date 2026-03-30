---
title: Transaction Isolation Levels and Concurrency Controls
type: study-material
tags:
  - dp-800
  - isolation-levels
  - concurrency
  - blocking
  - deadlocks
  - rcsi
  - snapshot-isolation
---

# Transaction Isolation Levels and Concurrency Controls

## Overview

Transaction isolation levels control how concurrent transactions see each other's changes. Choosing the right level balances data consistency against concurrency and blocking.

## Isolation Levels Overview

```sql
-- Set isolation level for a session
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;  -- default
```

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Blocking on Reads |
| :--- | :--- | :--- | :--- | :--- |
| `READ UNCOMMITTED` | Yes | Yes | Yes | **No** |
| `READ COMMITTED` (default) | No | Yes | Yes | Yes |
| `REPEATABLE READ` | No | No | Yes | Yes |
| `SERIALIZABLE` | No | No | No | Yes (most) |
| `SNAPSHOT` | No | No | No | **No** |
| `READ COMMITTED SNAPSHOT` (RCSI) | No | Yes | Yes | **No** |

**Read phenomena:**
- **Dirty read**: Reading uncommitted changes from another transaction
- **Non-repeatable read**: The same row returns different values if re-read (another transaction committed an update)
- **Phantom read**: A re-executed range query returns new rows (another transaction committed an insert)

## Pessimistic vs Optimistic Concurrency

| Approach | Mechanism | Blocking | Best For |
| :--- | :--- | :--- | :--- |
| **Pessimistic** (default) | Shared/exclusive locks | Yes | Write-heavy, short transactions |
| **Optimistic** (Snapshot/RCSI) | Row versioning | **No** | Read-heavy, mixed OLTP |

## RCSI vs Snapshot Isolation

Both use row versioning (tempdb version store) but differ in scope:

| Aspect | RCSI | Snapshot Isolation |
| :--- | :--- | :--- |
| Scope | Database-wide (affects all READ COMMITTED) | Per-transaction (explicit `SET TRANSACTION ISOLATION LEVEL SNAPSHOT`) |
| Granularity | Statement-level snapshot | Transaction-level snapshot |
| Consistency | Statement starts — snapshot taken | Transaction starts — snapshot taken |
| Enable | `ALTER DATABASE ... SET READ_COMMITTED_SNAPSHOT ON` | `ALTER DATABASE ... SET ALLOW_SNAPSHOT_ISOLATION ON` |

```sql
-- Enable RCSI (recommended for most Azure SQL workloads)
ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON;

-- Enable Snapshot Isolation
ALTER DATABASE MyDB SET ALLOW_SNAPSHOT_ISOLATION ON;

-- Use Snapshot in a transaction
SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
BEGIN TRANSACTION;
-- Sees a consistent snapshot from transaction start
SELECT Balance FROM dbo.Accounts WHERE AccountId = 1;
COMMIT;
```

## Lock Types and Compatibility

| Lock | Abbrev | Compatible With |
| :--- | :--- | :--- |
| Shared | S | Other S locks |
| Update | U | S locks |
| Exclusive | X | **Nothing** |
| Intent Shared | IS | IS, S, IX, SIX, U |
| Intent Exclusive | IX | IS, IX |

## Blocking Analysis

```sql
-- Find blocking chains
SELECT
    r.blocking_session_id AS BlockedBy,
    r.session_id AS BlockedSession,
    r.wait_type,
    r.wait_time / 1000.0 AS WaitSeconds,
    SUBSTRING(t.text, (r.statement_start_offset/2)+1,
        ((CASE r.statement_end_offset WHEN -1 THEN DATALENGTH(t.text)
         ELSE r.statement_end_offset END - r.statement_start_offset)/2)+1) AS CurrentStatement
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.blocking_session_id > 0;

-- Find long-running transactions
SELECT
    s.session_id,
    DB_NAME(t.database_id) AS DatabaseName,
    DATEDIFF(SECOND, t.transaction_begin_time, GETDATE()) AS DurationSec,
    t.transaction_type_desc
FROM sys.dm_exec_sessions s
JOIN sys.dm_tran_session_transactions st ON s.session_id = st.session_id
JOIN sys.dm_tran_active_transactions t ON t.transaction_id = st.transaction_id
WHERE DATEDIFF(SECOND, t.transaction_begin_time, GETDATE()) > 30;
```

## Deadlock Detection

SQL Server automatically detects and resolves deadlocks by killing one transaction (the deadlock victim):

```sql
-- Capture deadlock graphs via Extended Events
-- (Deadlock graph is captured by default in the system_health session)

-- Read deadlock data
WITH CTE AS (
    SELECT CAST(target_data AS xml) AS XmlData
    FROM sys.dm_xe_session_targets t
    JOIN sys.dm_xe_sessions s ON s.address = t.event_session_address
    WHERE s.name = 'system_health'
      AND t.target_name = 'ring_buffer'
)
SELECT n.value('(value)[1]', 'nvarchar(max)') AS DeadlockReport
FROM CTE
CROSS APPLY XmlData.nodes('//RingBufferTarget/event[@name="xml_deadlock_report"]') AS XTbl(n);
```

**Deadlock prevention patterns:**
1. Access tables in the same order across all transactions
2. Keep transactions short and commit quickly
3. Use RCSI/Snapshot to eliminate read/write deadlocks
4. Index columns used in WHERE clauses to reduce lock scope

## Use Cases

- **RCSI**: Default choice for Azure SQL OLTP — eliminates reader/writer blocking
- **Serializable**: Financial operations where phantom prevention is critical
- **Snapshot**: Long-running reports that need a consistent view without blocking writers
- **NOLOCK hint**: `WITH (NOLOCK)` = READ UNCOMMITTED; use only for approximate counts/non-critical reads

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Deadlock error 1205 | Circular lock dependency | Implement retry logic; use RCSI; standardize access order |
| tempdb growth | RCSI/Snapshot version store | Monitor version store; end long-running transactions quickly |
| `WITH (NOLOCK)` returning wrong data | Reads uncommitted data | Use RCSI instead; avoid NOLOCK for critical queries |

## Exam Tips

- **RCSI** is enabled at the database level and affects all `READ COMMITTED` queries automatically — no application change needed
- **Snapshot Isolation** requires `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` in the application
- Deadlocks (error 1205) require a retry mechanism — SQL Server automatically chooses the victim
- `WITH (NOLOCK)` is `READ UNCOMMITTED` — can return dirty data, duplicates, or miss rows

## Key Takeaways

- RCSI eliminates reader/writer blocking using row versioning — highly recommended for OLTP
- Snapshot Isolation provides transaction-level consistency without blocking writes
- Always handle error 1205 (deadlock victim) with retry logic in applications

## Related Topics

- [01-Database Configurations](./01-database-configurations.md)
- [03-Query Performance Troubleshooting](./03-query-performance-troubleshooting.md)

## Official Documentation

- [Transaction Isolation Levels](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql)
- [Row Versioning-based Isolation Levels](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide)
- [Analyze and Prevent Deadlocks](https://learn.microsoft.com/en-us/azure/azure-sql/database/analyze-prevent-deadlocks)

---

**[← Previous](./01-database-configurations.md) | [↑ Back to Section](./README.md) | [Next →](./03-query-performance-troubleshooting.md)**
