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
| **Key Lookup** | Fetches extra columns from clustered index | Add INCLUDE columns to covering index |
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

## Statistics and Cardinality Estimation

Poor statistics = bad execution plans:

```sql
-- Update statistics for a table
UPDATE STATISTICS dbo.Orders WITH FULLSCAN;

-- Update all statistics in the database
EXEC sp_updatestats;

-- Check statistics last updated
SELECT
    OBJECT_NAME(s.object_id) AS TableName,
    s.name AS StatName,
    sp.last_updated,
    sp.rows,
    sp.rows_sampled
FROM sys.stats s
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE OBJECT_NAME(s.object_id) = 'Orders'
ORDER BY sp.last_updated;
```

## Use Cases

- **DMVs**: Ad-hoc investigation of current performance issues
- **Query Store**: Track plan changes after upgrades; force good plans
- **Query Performance Insight**: Regular performance reviews in Azure SQL
- **Execution plans**: Understand specific query behavior and identify bottlenecks

## Exam Tips

- **Key Lookup** = missing INCLUDE columns in non-clustered index (adds a second lookup to clustered index)
- Query Store `FORCE_LAST_GOOD_PLAN` is an automatic tuning feature; manual `sp_query_store_force_plan` is manual
- `sys.dm_db_missing_index_details` provides index recommendations — not always accurate, use as a hint
- Stale statistics → bad cardinality estimates → bad plan choices → update with `UPDATE STATISTICS` or auto-update

## Key Takeaways

- Execution plans show WHERE the query spends its cost — look for scans that should be seeks
- DMVs provide current runtime data; Query Store provides historical trend data
- Query Performance Insight (Azure SQL) is the easiest way to identify top resource consumers

## Related Topics

- [01-Database Configurations](./01-database-configurations.md)
- [02-Transaction Isolation & Concurrency](./02-transaction-isolation-concurrency.md)
- [01-Tables & Indexes](../01-database-objects/01-tables-indexes.md)

## Official Documentation

- [Execution Plans (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/performance/execution-plans)
- [Query Store (SQL Server)](https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store)
- [Query Performance Insight (Azure SQL)](https://learn.microsoft.com/en-us/azure/azure-sql/database/query-performance-insight-use)

---

**[← Previous](./02-transaction-isolation-concurrency.md) | [↑ Back to Section](./README.md)**
