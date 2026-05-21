---
title: Query Performance Troubleshooting
type: study-material
tags:
  - dp-800
  - execution-plans
  - dmv
  - query-store
  - query-performance-insight
---

# Query Performance Troubleshooting

## Overview

SQL Server provides several tools for diagnosing query performance: execution plans (estimated and actual), Dynamic Management Views (DMVs), Query Store for plan history, and Query Performance Insight in Azure SQL.

> [!abstract]
>
> - Covers execution plan analysis, Query Store usage, DMV-based diagnostics, and index tuning
> - Performance troubleshooting follows a systematic path: identify → diagnose → fix → verify
> - Key exam topics: Query Store views and forcing plans, key DMV names, index scan vs seek, blocking identification

> [!tip] What the Exam Tests
>
> - **Query Store**: `sys.query_store_query`, `sys.query_store_plan`, `sys.query_store_runtime_stats`; force plan = `sp_query_store_force_plan`; plans survive restarts
> - **Index seek vs scan**: seek = uses index to go directly to rows (efficient); scan = reads all index pages (expensive on large tables)
> - Blocking: `sys.dm_exec_requests` (blocked_by column) + `sys.dm_os_waiting_tasks` (wait_type, blocking_session_id)

---

## Execution Plans

### Viewing Execution Plans

```sql
-- Estimated plan (no execution)
SET SHOWPLAN_XML ON;
SELECT * FROM dbo.Orders WHERE CustomerId = 42;
SET SHOWPLAN_XML OFF;

-- Actual plan (requires execution)
SET STATISTICS XML ON;
SELECT * FROM dbo.Orders WHERE CustomerId = 42;
SET STATISTICS XML OFF;

-- In SSMS / Azure Data Studio: Ctrl+M enables actual plan display
```

### Key Execution Plan Operators

| Operator | What It Means | Watch For |
| :--- | :--- | :--- |
| **Index Seek** | Uses index to find specific rows | Good — efficient |
| **Index Scan** | Reads entire index | Review if large table |
| **Table Scan** (Heap) | Reads entire table | Add a clustered index |
| **Key Lookup** | Fetches extra columns from clustered index | ==Add INCLUDE columns to covering index== |
| **Hash Match** | Join/aggregation using hash table | OK for large datasets; bad with low memory |
| **Nested Loops** | Iterative join | Efficient for small outer input |
| **Merge Join** | Sorted inputs joined | Efficient for large, sorted datasets |
| **Sort** | In-memory sort | Expensive; check if an index can avoid it |
| **Spill to TempDB** | Memory grant insufficient | Check memory grant warnings |

### Reading Cost Percentages

```sql
-- High-cost operators indicate where time is spent
-- Look for:
-- 1. Table scans on large tables (add index)
-- 2. Key lookups (add INCLUDE columns)
-- 3. Sort operators (add ordered index)
-- 4. Hash match with memory grant warnings (statistics may be stale)
```

---

## Dynamic Management Views (DMVs)

### Most Expensive Queries

```sql
-- Top 10 queries by total CPU
SELECT TOP 10
    total_worker_time / execution_count AS avg_cpu_us,
    total_worker_time AS total_cpu_us,
    execution_count,
    total_elapsed_time / execution_count AS avg_duration_us,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text)
         ELSE qs.statement_end_offset END - qs.statement_start_offset)/2)+1) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY avg_cpu_us DESC;

-- Top queries by total logical reads
SELECT TOP 10
    total_logical_reads / execution_count AS avg_reads,
    total_logical_reads,
    execution_count,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1, 200) AS query_snippet
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY avg_reads DESC;
```

### Missing Index Recommendations

```sql
-- Find missing index recommendations
SELECT TOP 10
    ROUND(s.avg_total_user_cost * s.avg_user_impact * (s.user_seeks + s.user_scans), 0) AS ImpactScore,
    d.equality_columns,
    d.inequality_columns,
    d.included_columns,
    OBJECT_NAME(d.object_id) AS TableName
FROM sys.dm_db_missing_index_details d
JOIN sys.dm_db_missing_index_groups g ON g.index_handle = d.index_handle
JOIN sys.dm_db_missing_index_group_stats s ON s.group_handle = g.index_group_handle
WHERE d.database_id = DB_ID()
ORDER BY ImpactScore DESC;
```

### Wait Statistics

```sql
-- Top wait types (server-wide)
SELECT TOP 10
    wait_type,
    wait_time_ms / 1000.0 AS wait_time_sec,
    100.0 * wait_time_ms / SUM(wait_time_ms) OVER() AS pct
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN ('SLEEP_TASK','BROKER_TO_FLUSH','CLR_AUTO_EVENT',
    'DISPATCHER_QUEUE_SEMAPHORE','FT_IFTS_SCHEDULER_IDLE_WAIT',
    'HADR_WORK_QUEUE','ONDEMAND_TASK_QUEUE','REQUEST_FOR_DEADLOCK_SEARCH',
    'RESOURCE_QUEUE','SERVER_IDLE_CHECK','SLEEP_DBSTARTUP',
    'SLEEP_DCOMSTARTUP','SLEEP_MASTERDBREADY','SLEEP_MASTERMDREADY',
    'SLEEP_MASTERUPGRADED','SLEEP_MSDBSTARTUP','SLEEP_TEMPDBSTARTUP',
    'SNI_HTTP_ACCEPT','SP_SERVER_DIAGNOSTICS_SLEEP','SQLTRACE_BUFFER_FLUSH',
    'WAITFOR','XE_DISPATCHER_WAIT','XE_TIMER_EVENT')
ORDER BY wait_time_ms DESC;
```

---

## Query Store

Query Store captures query plans and performance data — enabling plan forcing and regression detection.

```sql
-- Enable Query Store
ALTER DATABASE MyDB SET QUERY_STORE = ON (
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = AUTO,
    MAX_STORAGE_SIZE_MB = 1000,
    INTERVAL_LENGTH_MINUTES = 60,
    SIZE_BASED_CLEANUP_MODE = AUTO,
    DATA_FLUSH_INTERVAL_SECONDS = 900
);

-- Find regressed queries (plan changed, performance worsened)
SELECT TOP 10
    qsq.query_id,
    qsqt.query_sql_text,
    qsp.plan_id,
    qsrs.avg_cpu_time / 1000.0 AS avg_cpu_ms,
    qsrs.avg_duration / 1000.0 AS avg_duration_ms,
    qsrs.count_executions
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsqt.query_text_id = qsq.query_text_id
JOIN sys.query_store_plan qsp ON qsp.query_id = qsq.query_id
JOIN sys.query_store_runtime_stats qsrs ON qsrs.plan_id = qsp.plan_id
ORDER BY qsrs.avg_cpu_time DESC;

-- Force a good plan (when a bad plan is being chosen)
EXEC sp_query_store_force_plan @query_id = 1, @plan_id = 3;

-- Unforce a plan
EXEC sp_query_store_unforce_plan @query_id = 1, @plan_id = 3;
```

**Query Store SSMS views:**

- **Top Resource Consuming Queries**: Quick identification of high-cost queries
- **Regressed Queries**: Queries where plan changed and performance degraded
- **Plan Summary**: All plans ever used for a query — compare execution stats

> [!warning] Common Mistake
> The plan cache (sys.dm_exec_cached_plans) is volatile — it's cleared on memory pressure and restarts. Query Store persists plans and stats permanently. If a question asks about historical plan analysis or surviving restarts, the answer is Query Store, not the plan cache.

---

## Query Performance Insight (Azure SQL)

Query Performance Insight in Azure Portal provides a graphical view of Query Store data:

```text
Azure SQL Database → Intelligent Performance → Query Performance Insight
→ View: Top CPU / Top Data IO / Top Log IO / Custom
→ Drill down to individual queries → See plans and recommendations
```

**Features:**

- Visual charts of resource consumption over time
- Automatic identification of top resource consumers
- One-click plan viewing
- Integration with Azure Advisor for index recommendations

---

## Plan Forcing and Plan Guides

When a query repeatedly gets a bad execution plan, you can force a specific plan rather than waiting for the optimizer to correct itself.

### Query Store Plan Forcing

```sql
-- Force a plan via Query Store (plan_id comes from Query Store views)
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;

-- Unforce when issue is resolved (optimizer resumes normal selection)
EXEC sp_query_store_unforce_plan @query_id = 42, @plan_id = 7;
```

Forced plans are persisted in Query Store and survive restarts. The `is_forced_plan` column in `sys.query_store_plan` shows which plans are currently forced.

### Plan Guides

Plan guides attach hints to specific query text without modifying the source — essential for queries from ORMs, third-party applications, or legacy code you cannot change.

```sql
-- Create a plan guide for an ORM query
EXEC sp_create_plan_guide
    @name = N'PG_GetOrders',
    @stmt = N'SELECT * FROM Orders WHERE CustomerID = @CustID',
    @type = N'SQL',
    @module_or_batch = NULL,
    @params = N'@CustID int',
    @hints = N'OPTION (OPTIMIZE FOR (@CustID UNKNOWN))';

-- Verify the plan guide was created
SELECT name, scope_type_desc, is_disabled
FROM sys.plan_guides
WHERE name = N'PG_GetOrders';

-- Drop a plan guide when no longer needed
EXEC sp_control_plan_guide N'DROP', N'PG_GetOrders';
```

**Plan guide types:**

| Type | Use When |
| :--- | :--- |
| `SQL` | Ad-hoc or parameterized SQL statements |
| `OBJECT` | Stored procedures or functions |
| `TEMPLATE` | ==Auto-parameterized queries (server-wide template)== |

---

## Parameter Sniffing Mitigations

**Parameter sniffing** occurs when SQL Server compiles a stored procedure or parameterized query using a specific parameter value, then reuses that plan for all future executions — even when different parameter values would benefit from a different plan.

### OPTION(RECOMPILE)

Forces a fresh plan on every execution using the current parameter values. Best for queries with highly variable data distributions.

```sql
-- Recompile every execution (no plan reuse)
CREATE PROCEDURE dbo.GetOrdersByDate
    @StartDate DATE,
    @EndDate DATE
AS
    SELECT * FROM dbo.Orders
    WHERE OrderDate BETWEEN @StartDate AND @EndDate
    OPTION (RECOMPILE);
```

### OPTION(OPTIMIZE FOR UNKNOWN)

Compiles the plan using average statistics rather than the sniffed value. Produces a single stable plan that is reasonable for most inputs.

```sql
-- Use average statistics; avoids sniffing without recompiling each time
CREATE PROCEDURE dbo.GetCustomerOrders
    @CustomerID INT
AS
    SELECT * FROM dbo.Orders
    WHERE CustomerID = @CustomerID
    OPTION (OPTIMIZE FOR (@CustomerID UNKNOWN));
```

### Local Variable Workaround

Assigning the parameter to a local variable breaks sniffing because the optimizer cannot see the value at compile time. However, it also prevents plan reuse benefits.

```sql
CREATE PROCEDURE dbo.GetOrdersByRegion
    @RegionID INT
AS
    DECLARE @LocalRegion INT = @RegionID;  -- breaks sniffing
    SELECT * FROM dbo.Orders
    WHERE RegionID = @LocalRegion;
```

### Adaptive Query Processing (SQL Server 2017+)

- **Interleaved execution**: multi-statement TVFs re-estimated at runtime
- **Batch mode adaptive joins**: switch between hash and nested loops based on actual row counts
- **Memory grant feedback**: adjusts memory grants after first execution based on actual usage

These are automatic in compatibility level 140+ and require no code changes.

---

## Statistics Maintenance

Statistics are histograms describing the distribution of data values in index and column samples. The query optimizer uses them to estimate row counts (cardinality) and choose execution plans.

### Auto-Update Thresholds

- **Small tables** (< 500 rows): triggered after 500 row changes
- **Larger tables**: triggered after approximately 20% of rows change
- **SQL Server 2016+ with trace flag 2371 / compat level 130+**: dynamic threshold — roughly `sqrt(1000 * rows)`, which scales better for very large tables

### Manual Statistics Updates

```sql
-- Check statistics freshness and sampling rate
SELECT OBJECT_NAME(s.object_id) AS TableName,
       s.name AS StatName,
       sp.last_updated,
       sp.rows,
       sp.rows_sampled,
       sp.modification_counter
FROM sys.stats s
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE OBJECT_NAME(s.object_id) = 'Orders'
ORDER BY sp.last_updated;

-- Force full scan update for accurate statistics (slower but exact)
UPDATE STATISTICS dbo.Orders WITH FULLSCAN;

-- Update all statistics in database (uses default sampling)
EXEC sp_updatestats;
```

`modification_counter` shows how many leading-column changes have occurred since the last update — a high value relative to row count signals stale statistics.

---

## Use Cases

- **DMVs**: Ad-hoc investigation of current performance issues
- **Query Store**: Track plan changes after upgrades; force good plans
- **Query Performance Insight**: Regular performance reviews in Azure SQL
- **Execution plans**: Understand specific query behavior and identify bottlenecks
- **Plan guides**: Fix bad plans from ORMs or third-party apps without code changes
- **Parameter sniffing mitigations**: Stabilize plans for stored procedures with skewed parameter distributions

---

## Common Issues & Errors

| Symptom | Likely Cause | Remedy |
| :--- | :--- | :--- |
| Query fast first run, slow after | Parameter sniffing | OPTION(RECOMPILE) or OPTIMIZE FOR UNKNOWN |
| Plan changed after index rebuild | Statistics updated with new distribution | Verify plan; force if needed |
| Plan guide not applied | Query text mismatch (whitespace, case) | ==Use `sys.fn_validate_plan_guide` to diagnose== |
| Query Store full | Max storage size reached | Increase `MAX_STORAGE_SIZE_MB` or change cleanup mode |
| Stale stats on large table | 20% threshold not reached | Manual `UPDATE STATISTICS WITH FULLSCAN` |

---

## Best Practices

- Always check `modification_counter` against row count before concluding statistics are fresh — high ratios warrant a manual `UPDATE STATISTICS WITH FULLSCAN`.
- Prefer `OPTION(OPTIMIZE FOR UNKNOWN)` over local variable tricks; it produces a reusable plan and is explicit about intent.
- Use Query Store plan forcing as a short-term fix while diagnosing root cause; do not leave plans forced indefinitely without review.
- Validate plan guides after deployment using `sys.fn_validate_plan_guide` — a silently invalid plan guide has no effect and is hard to detect.
- Avoid adding `OPTION(RECOMPILE)` to high-frequency queries; the recompilation overhead can become a CPU bottleneck under load.

---

## Exam Tips

> [!tip] Exam Tips
>
> - **Key Lookup** = missing INCLUDE columns in non-clustered index (adds a second lookup to clustered index)
> - Query Store `FORCE_LAST_GOOD_PLAN` is an automatic tuning feature; manual `sp_query_store_force_plan` is manual
> - `sys.dm_db_missing_index_details` provides index recommendations — not always accurate, use as a hint
> - Stale statistics → bad cardinality estimates → bad plan choices → update with `UPDATE STATISTICS` or auto-update
> - Plan guides require **exact query text match** — even a single space difference causes the guide to be skipped
> - `OPTION(RECOMPILE)` eliminates parameter sniffing but prevents plan caching; use on infrequent, skewed queries only

---

## Key Takeaways

- Execution plans show WHERE the query spends its cost — look for scans that should be seeks
- DMVs provide current runtime data; Query Store provides historical trend data
- Query Performance Insight (Azure SQL) is the easiest way to identify top resource consumers
- Plan guides let you inject hints into queries you cannot modify (ORMs, third-party apps)
- Parameter sniffing produces correct plans for the sniffed value but wrong plans for others — mitigate with OPTIMIZE FOR UNKNOWN or RECOMPILE

---

## Practice Questions

**Practice Question**

A third-party application sends parameterized queries that consistently get poor execution plans due to parameter sniffing. You cannot modify the application code. What is the BEST solution?

A. Use OPTION(RECOMPILE) added directly to the query
B. Create a plan guide using sp_create_plan_guide to add the OPTIMIZE FOR hint
C. Disable auto-update statistics for the affected tables
D. Force a specific plan using sp_query_store_force_plan

> [!success]- Answer
> **B — Create a plan guide using sp_create_plan_guide to add the OPTIMIZE FOR hint**
>
> When you cannot modify the application's SQL, plan guides let you attach hints to specific query patterns. A plan guide matching the ORM's query text can inject OPTION(OPTIMIZE FOR UNKNOWN) to fix parameter sniffing without application changes. OPTION(RECOMPILE) (A) can't be added without modifying the query. Disabling statistics updates (C) makes plans worse over time. Plan forcing (D) locks in a single plan that may not work for all parameter values.

---

## Related Topics

- [01-Database Configurations](./01-database-configurations.md)
- [02-Transaction Isolation & Concurrency](./02-transaction-isolation-concurrency.md)
- [01-Tables & Indexes](../01-database-objects/01-tables-indexes.md)

---

## Official Documentation

- [Execution Plans (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/performance/execution-plans)
- [Query Store (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store)
- [Query Performance Insight (Azure SQL)](https://learn.microsoft.com/en-us/azure/azure-sql/database/query-performance-insight-use)
- [Plan Guides (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/performance/plan-guides)
- [Parameter Sniffing (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/query-processing-architecture-guide#parameter-sensitivity)

---

**[← Previous](./02-transaction-isolation-concurrency.md) | [↑ Back to Section](./performance-optimization.md)**
