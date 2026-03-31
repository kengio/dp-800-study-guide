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

> [!abstract]
> - Covers all six isolation levels, optimistic vs pessimistic concurrency, blocking, and deadlocks
> - Isolation level determines what data a transaction can see and what locks it takes
> - Key exam topics: SNAPSHOT vs RCSI distinction, which isolation level prevents which anomaly, deadlock detection

> [!tip] What the Exam Tests
> - **SNAPSHOT** = application sets per-transaction; `SET TRANSACTION ISOLATION LEVEL SNAPSHOT`; requires `ALLOW_SNAPSHOT_ISOLATION ON`
> - **RCSI** = database setting; changes default READ COMMITTED to row-versioning; `ALTER DATABASE db SET READ_COMMITTED_SNAPSHOT ON`
> - Isolation anomalies: dirty read = READ UNCOMMITTED; non-repeatable read = READ COMMITTED; phantom read = REPEATABLE READ; all prevented by SERIALIZABLE and SNAPSHOT

---

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

> [!warning] Common Mistake
> SNAPSHOT isolation and Read Committed Snapshot Isolation (RCSI) are both row-versioning but are activated differently and used differently. SNAPSHOT is an explicit isolation level set by the application. RCSI changes the behavior of the existing READ COMMITTED level transparently — the app doesn't need to change.

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

## Lock Escalation

SQL Server automatically escalates many fine-grained row/page locks to a single coarser table lock to conserve memory.

**Threshold:** approximately 5,000 locks per object, or when the lock memory threshold for the instance is reached.

**Impact:** a table-level lock blocks all other readers and writers for the duration — can cause unexpected blocking spikes on busy tables.

**LOCK_ESCALATION options:**

| Option | Behavior |
| :--- | :--- |
| `TABLE` (default) | Escalates to table-level lock |
| `AUTO` | Escalates to partition-level for partitioned tables; table-level otherwise |
| `DISABLE` | Prevents escalation entirely (uses more lock memory) |

```sql
-- Check current lock escalation setting
SELECT name, lock_escalation_desc FROM sys.tables WHERE name = 'Orders';

-- Disable lock escalation (prevents escalation but uses more lock memory)
ALTER TABLE Orders SET (LOCK_ESCALATION = DISABLE);

-- Partition-level escalation for partitioned tables (best option)
ALTER TABLE Orders SET (LOCK_ESCALATION = AUTO);

-- Monitor lock escalation events
SELECT * FROM sys.dm_os_wait_stats
WHERE wait_type LIKE 'LCK%'
ORDER BY waiting_tasks_count DESC;
```

## Rowversion-Based Optimistic Concurrency

`ROWVERSION` (also aliased as `timestamp`) is an 8-byte binary value that SQL Server automatically increments on every `UPDATE` to the row. It provides a lightweight optimistic concurrency mechanism without holding locks between read and update.

**Pattern:**

1. Read the row and capture its `ROWVERSION` value
2. Perform application logic (no lock held)
3. Update with a `WHERE RowVer = @original` predicate
4. If `@@ROWCOUNT = 0`, another session modified the row — handle the conflict

**Advantages over pessimistic locking:**

- No locks held during business logic execution
- Ideal for disconnected scenarios and long-running application workflows
- Much less blocking than `UPDLOCK` held across a delay

```sql
-- Add rowversion column
ALTER TABLE Orders ADD RowVer ROWVERSION NOT NULL;

-- Read + capture rowversion
DECLARE @rv BINARY(8);
SELECT @rv = RowVer, TotalAmount FROM Orders WHERE OrderID = 1001;

-- ... some application logic (no lock held) ...

-- Update with optimistic check (fails if another session updated)
UPDATE Orders
SET TotalAmount = @newAmount
WHERE OrderID = 1001 AND RowVer = @rv;

IF @@ROWCOUNT = 0
    THROW 50001, 'Concurrency conflict: record was modified by another user', 1;
```

## RCSI vs Snapshot Isolation Comparison

Both RCSI and Snapshot Isolation use the version store in tempdb to serve consistent reads without blocking writers. The key difference is the granularity of the snapshot.

**Enable RCSI:**

```sql
ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON;
```

**Detailed comparison:**

| Feature | RCSI | Snapshot |
| :--- | :--- | :--- |
| Scope | Database-wide default | Per-transaction opt-in |
| Consistency | Statement-level | Transaction-level |
| Overhead | Lower | Higher (longer txns hold more versions) |
| Blocking | Eliminated for readers | Eliminated for readers |
| Write conflicts | No detection | Detected (update conflict error) |

**When to choose:**

- **RCSI**: Drop-in improvement for existing READ COMMITTED workloads — no application changes required
- **Snapshot**: Reports or batch jobs that need a consistent view of data across multiple statements within one transaction

## Deadlock Analysis and Prevention

A deadlock occurs when two sessions each hold a lock the other session needs, creating a circular wait. SQL Server's lock monitor detects these automatically and kills one transaction (the **deadlock victim** — typically the least expensive to roll back).

**Deadlock victim receives error 1205** — always implement retry logic.

**Reading deadlock graphs from the system_health Extended Events session:**

```sql
-- Read recent deadlocks from system_health Extended Events
SELECT xdr.value('@timestamp', 'datetime2') AS DeadlockTime,
       xdr.query('.') AS DeadlockGraph
FROM (
    SELECT CAST(target_data AS XML) AS target_data
    FROM sys.dm_xe_session_targets t
    JOIN sys.dm_xe_sessions s ON t.event_session_address = s.address
    WHERE s.name = 'system_health'
    AND t.target_name = 'ring_buffer'
) data
CROSS APPLY target_data.nodes('//RingBufferTarget/event[@name="xml_deadlock_report"]') AS XEventData(xdr);
```

**Prevention strategies:**

1. Access tables in the same order across all transactions
2. Keep transactions short — commit as soon as possible
3. Use RCSI or Snapshot Isolation to eliminate read/write deadlocks
4. Add indexes on WHERE clause columns to reduce lock scope (fewer rows locked)
5. Avoid user interaction inside open transactions

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
- **ROWVERSION**: Disconnected update scenarios where holding locks between read and write is unacceptable
- **LOCK_ESCALATION = AUTO**: High-throughput partitioned tables where table-lock escalation causes blocking spikes

## Common Issues & Errors

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Deadlock error 1205 | Circular lock dependency | Implement retry logic; use RCSI; standardize access order |
| tempdb growth | RCSI/Snapshot version store | Monitor version store; end long-running transactions quickly |
| `WITH (NOLOCK)` returning wrong data | Reads uncommitted data | Use RCSI instead; avoid NOLOCK for critical queries |
| Unexpected blocking spikes | Lock escalation to table level | Set `LOCK_ESCALATION = AUTO` on partitioned tables or `DISABLE` with caution |
| Optimistic update silently skips | `@@ROWCOUNT = 0` not checked | Always check `@@ROWCOUNT` after ROWVERSION-based update and raise error |

## Best Practices

- Enable RCSI on Azure SQL databases by default — it eliminates the most common reader/writer blocking with minimal overhead and no application changes.
- Always implement retry logic for error 1205 (deadlock victim); deadlocks are a normal occurrence under concurrent load, not a bug to prevent entirely.
- Prefer `LOCK_ESCALATION = AUTO` over `DISABLE` on large partitioned tables — `DISABLE` conserves escalation but can exhaust lock memory under high DML.
- Use ROWVERSION-based optimistic concurrency for any workflow that holds business logic state between read and update; never hold locks across network round trips or user think time.
- Monitor `sys.dm_os_wait_stats` for `LCK%` waits and the system_health Extended Events ring buffer for deadlock graphs as part of routine performance reviews.

## Exam Tips

- **RCSI** is enabled at the database level and affects all `READ COMMITTED` queries automatically — no application change needed
- **Snapshot Isolation** requires `SET TRANSACTION ISOLATION LEVEL SNAPSHOT` in the application
- Deadlocks (error 1205) require a retry mechanism — SQL Server automatically chooses the victim
- `WITH (NOLOCK)` is `READ UNCOMMITTED` — can return dirty data, duplicates, or miss rows
- **ROWVERSION** detects write conflicts without holding any locks — `@@ROWCOUNT = 0` after the update means a conflict occurred
- **RCSI** is statement-level (each statement sees latest committed data); **Snapshot** is transaction-level (entire transaction sees same snapshot)
- Lock escalation threshold is ~5,000 locks per object; `LOCK_ESCALATION = AUTO` is the safest option for partitioned tables

## Key Takeaways

- RCSI eliminates reader/writer blocking using row versioning — highly recommended for OLTP
- Snapshot Isolation provides transaction-level consistency without blocking writes
- Always handle error 1205 (deadlock victim) with retry logic in applications
- Lock escalation can unexpectedly block entire tables — monitor and tune `LOCK_ESCALATION` on high-traffic tables
- ROWVERSION-based optimistic concurrency is the lowest-blocking pattern for disconnected update scenarios

## Practice Question

**Practice Question**

An application reads a customer record, applies business logic for 5 seconds, then updates the record. Other users occasionally overwrite the same record during those 5 seconds. Which concurrency mechanism detects this conflict with MINIMAL blocking?

A. Pessimistic locking with UPDLOCK hint during the initial read
B. ROWVERSION-based optimistic concurrency check on UPDATE
C. Serializable isolation level for the entire transaction
D. Enable RCSI and retry on deadlock

> [!success]- Answer
> **B — ROWVERSION-based optimistic concurrency check on UPDATE**
>
> ROWVERSION allows reading without holding any locks, then detecting concurrent modifications at update time by checking the stored rowversion. If another session modified the row during the business logic period, the UPDATE affects 0 rows and the application can handle the conflict. UPDLOCK (A) holds an update lock for the entire 5 seconds, blocking other readers. Serializable (C) holds range locks throughout, severely impacting concurrency. RCSI (D) prevents read blocking but doesn't detect write conflicts.

## Related Topics

- [01-Database Configurations](./01-database-configurations.md)
- [03-Query Performance Troubleshooting](./03-query-performance-troubleshooting.md)

## Official Documentation

- [Transaction Isolation Levels](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql)
- [Row Versioning-based Isolation Levels](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide)
- [Analyze and Prevent Deadlocks](https://learn.microsoft.com/en-us/azure/azure-sql/database/analyze-prevent-deadlocks)

---

**[← Previous](./01-database-configurations.md) | [↑ Back to Section](./README.md) | [Next →](./03-query-performance-troubleshooting.md)**
