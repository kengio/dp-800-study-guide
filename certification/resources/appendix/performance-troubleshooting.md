---
title: Performance Troubleshooting Guide
tags:
  - dp-800
  - performance
  - troubleshooting
  - reference
---

# Performance Troubleshooting Guide

A systematic reference for diagnosing and resolving SQL Server and Azure SQL performance issues.

> [!abstract] TL;DR
> - Follow the 7-step diagnosis workflow to systematically narrow down performance problems
> - Key DMV reference table and ready-to-run diagnostic queries for each category
> - Focus on wait stats analysis, execution plan warnings, and blocking chain resolution — these dominate performance questions on the exam

---

## Table of Contents

- [[#Slow Query Diagnosis Workflow]]
- [[#Key DMVs Reference Table]]
- [[#Wait Stats Analysis]]
  - [[#Wait Type Reference]]
  - [[#Top Wait Stats Query]]
- [[#Execution Plan Warning Signs]]
- [[#Index Usage Analysis]]
  - [[#Unused Indexes]]
  - [[#Missing Indexes]]
  - [[#Duplicate and Overlapping Indexes]]
  - [[#Index Fragmentation]]
- [[#Memory Grant Issues]]
  - [[#Active Memory Grants]]
  - [[#Common Fixes]]
- [[#Blocking Chain Resolution]]
  - [[#Find the Blocking Chain]]
  - [[#Identify the Head Blocker]]
  - [[#Resolution Options]]
  - [[#Read Committed Snapshot Isolation (RCSI)]]

---

## Slow Query Diagnosis Workflow

> [!tip] Quick Win
> Start with wait stats — they immediately tell you the category of problem (CPU, I/O, locks, memory) and prevent wasted time investigating the wrong area.

Follow these steps in order. Each step narrows the cause before moving to the next.

1. **Check wait stats** — Identify what the server is waiting on; this points to the category of problem (CPU, I/O, locks, memory).
2. **Check the execution plan** — Retrieve the actual or estimated plan for the slow query; look for warnings, thick arrows, and missing index hints.
3. **Check indexes** — Verify that supporting indexes exist, are not fragmented, and are actually being used.
4. **Check statistics** — Confirm statistics are current; stale stats cause bad cardinality estimates and poor plans.
5. **Check parameter sniffing** — Determine whether the cached plan was compiled for an atypical parameter value, leading to a plan that is inefficient for the current input.
6. **Check blocking** — Look for sessions waiting on locks held by another session; blocking appears as `LCK_M_*` waits.
7. **Check memory grants** — Verify that sort and hash operations are getting adequate memory; spills to `tempdb` signal under-grants.

```sql
-- Step 1: snapshot current wait stats
SELECT TOP 20
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    max_wait_time_ms,
    signal_wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'SLEEP_TASK','BROKER_TO_FLUSH','BROKER_TASK_STOP',
    'CLR_AUTO_EVENT','DISPATCHER_QUEUE_SEMAPHORE',
    'FT_IFTS_SCHEDULER_IDLE_WAIT','HADR_WORK_QUEUE',
    'ONDEMAND_TASK_QUEUE','REQUEST_FOR_DEADLOCK_SEARCH',
    'RESOURCE_QUEUE','SERVER_IDLE_CHECK','SLEEP_DBSTARTUP',
    'SLEEP_DBRECOVER','SLEEP_MASTERDBREADY','SLEEP_MASTERMDREADY',
    'SLEEP_MASTERUPGRADED','SLEEP_MSDBSTARTUP','SLEEP_TEMPDBSTARTUP',
    'SNI_HTTP_ACCEPT','SP_SERVER_DIAGNOSTICS_SLEEP',
    'SQLTRACE_BUFFER_FLUSH','WAITFOR','XE_DISPATCHER_WAIT',
    'XE_TIMER_EVENT'
)
ORDER BY wait_time_ms DESC;
```

---

## Key DMVs Reference Table

> [!info] These 8 DMVs are the most commonly referenced in performance troubleshooting scenarios on the DP-800 exam.

| DMV | Purpose | Key Columns |
|-----|---------|-------------|
| `sys.dm_exec_query_stats` | Aggregate CPU, I/O, and elapsed time per cached plan | `total_worker_time`, `total_elapsed_time`, `execution_count`, `plan_handle` |
| `sys.dm_exec_requests` | Currently executing requests | `session_id`, `wait_type`, `wait_time`, `blocking_session_id`, `sql_handle` |
| `sys.dm_exec_sql_text` | Retrieve SQL text from a handle | `text`, `dbid`, `objectid` |
| `sys.dm_os_wait_stats` | Cumulative waits since last restart or reset | `wait_type`, `waiting_tasks_count`, `wait_time_ms` |
| `sys.dm_db_index_usage_stats` | Index seek/scan/lookup/update counts since restart | `user_seeks`, `user_scans`, `user_lookups`, `user_updates` |
| `sys.dm_db_missing_index_details` | Indexes the optimizer would have used | `equality_columns`, `inequality_columns`, `included_columns`, `statement` |
| `sys.dm_exec_query_memory_grants` | Active and pending memory grants | `requested_memory_kb`, `granted_memory_kb`, `used_memory_kb`, `queue_id` |
| `sys.dm_db_stats_properties` | Statistics metadata per object | `last_updated`, `rows`, `rows_sampled`, `modification_counter` |

```sql
-- Top 10 queries by total CPU time
SELECT TOP 10
    qs.total_worker_time / qs.execution_count          AS avg_cpu_us,
    qs.total_elapsed_time / qs.execution_count         AS avg_elapsed_us,
    qs.execution_count,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
          END - qs.statement_start_offset)/2)+1)        AS query_text
FROM sys.dm_exec_query_stats AS qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) AS st
ORDER BY qs.total_worker_time DESC;
```

---

## Wait Stats Analysis

### Wait Type Reference

| Wait Type | Category | Indicates | Action |
|-----------|----------|-----------|--------|
| `CXPACKET` | Parallelism | Threads waiting on parallel partner; skewed work distribution | Reduce MAXDOP; add `MAXDOP` hint; fix skewed data |
| `LCK_M_X` | Locking | Exclusive lock contention | Investigate blocking chain; consider RCSI |
| `PAGEIOLATCH_SH` | I/O | Reading pages from disk into buffer pool | Add indexes; increase memory; check I/O subsystem |
| `SOS_SCHEDULER_YIELD` | CPU | Query voluntarily yielding CPU; high CPU load | Tune expensive queries; check for runaway loops |
| `WRITELOG` | I/O | Log write latency; transaction log bottleneck | Move log to faster disk; reduce log writes; check VLFs |
| `RESOURCE_SEMAPHORE` | Memory | Query waiting for a memory grant | Fix bad cardinality estimates; add `OPTION (RECOMPILE)` |
| `LATCH_EX` | Latch | In-memory structure contention (e.g., PFS, GAM pages) | Enable trace flag 1118/1117; use multiple data files |

### Top Wait Stats Query

```sql
-- Cumulative wait stats, excluding benign idles
-- Run twice with a gap and diff the results for interval analysis
WITH waits AS (
    SELECT
        wait_type,
        wait_time_ms,
        waiting_tasks_count,
        100.0 * wait_time_ms / SUM(wait_time_ms) OVER () AS pct
    FROM sys.dm_os_wait_stats
    WHERE wait_type NOT IN (
        'SLEEP_TASK','BROKER_TO_FLUSH','BROKER_TASK_STOP',
        'CLR_AUTO_EVENT','DISPATCHER_QUEUE_SEMAPHORE',
        'FT_IFTS_SCHEDULER_IDLE_WAIT','HADR_WORK_QUEUE',
        'ONDEMAND_TASK_QUEUE','REQUEST_FOR_DEADLOCK_SEARCH',
        'RESOURCE_QUEUE','SERVER_IDLE_CHECK','SLEEP_DBSTARTUP',
        'SLEEP_DBRECOVER','SLEEP_MASTERDBREADY','SLEEP_MASTERMDREADY',
        'SLEEP_MASTERUPGRADED','SLEEP_MSDBSTARTUP','SLEEP_TEMPDBSTARTUP',
        'SNI_HTTP_ACCEPT','SP_SERVER_DIAGNOSTICS_SLEEP',
        'SQLTRACE_BUFFER_FLUSH','WAITFOR','XE_DISPATCHER_WAIT',
        'XE_TIMER_EVENT'
    )
)
SELECT TOP 15
    wait_type,
    wait_time_ms,
    waiting_tasks_count,
    CAST(pct AS DECIMAL(5,2)) AS pct_total
FROM waits
ORDER BY wait_time_ms DESC;
```

---

## Execution Plan Warning Signs

> [!tip] Quick Win
> Key Lookups are the most common plan problem — adding INCLUDE columns to a nonclustered index often eliminates them with minimal effort.

| Warning | What It Means | Fix |
|---------|--------------|-----|
| **Key Lookup** | Clustered index lookup after nonclustered seek; extra I/O per row | Add needed columns to nonclustered index as `INCLUDE` columns |
| **Table Scan** | No usable index; all rows examined | Create a covering index on the filtered/joined columns |
| **Sort spill** | Sort operator overflowed to `tempdb` | Improve cardinality estimate; increase memory grant via `MIN_GRANT_PERCENT` |
| **Hash Match spill** | Hash join/aggregate overflowed to `tempdb` | Same as sort spill; also consider indexed alternatives to hash joins |
| **Missing Index hint** | Optimizer found a potentially beneficial index | Evaluate and create the suggested index; validate with testing |
| **Row estimate mismatch** | Estimated rows far from actual rows | Update statistics; use `OPTION (RECOMPILE)`; check for parameter sniffing |

```sql
-- Find plans with warnings in the plan cache
SELECT
    qp.query_plan,
    qs.execution_count,
    qs.total_worker_time,
    SUBSTRING(st.text, 1, 200) AS query_snippet
FROM sys.dm_exec_query_stats AS qs
CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle)  AS qp
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle)     AS st
WHERE CAST(qp.query_plan AS NVARCHAR(MAX)) LIKE '%<Warnings%'
ORDER BY qs.total_worker_time DESC;
```

---

## Index Usage Analysis

### Unused Indexes

> [!warning] Common Mistake
> `dm_db_index_usage_stats` resets on service restart — don't drop indexes based solely on zero reads if the server recently restarted. Collect data over a full business cycle.

Unused indexes consume write overhead and storage without benefiting reads.

```sql
-- Indexes with no user reads since last restart
SELECT
    OBJECT_SCHEMA_NAME(i.object_id)   AS schema_name,
    OBJECT_NAME(i.object_id)          AS table_name,
    i.name                            AS index_name,
    i.type_desc,
    ISNULL(s.user_seeks,  0)          AS user_seeks,
    ISNULL(s.user_scans,  0)          AS user_scans,
    ISNULL(s.user_lookups,0)          AS user_lookups,
    ISNULL(s.user_updates,0)          AS user_updates
FROM sys.indexes AS i
LEFT JOIN sys.dm_db_index_usage_stats AS s
    ON s.object_id  = i.object_id
    AND s.index_id  = i.index_id
    AND s.database_id = DB_ID()
WHERE i.type_desc <> 'HEAP'
  AND i.is_primary_key = 0
  AND i.is_unique_constraint = 0
  AND ISNULL(s.user_seeks,0) + ISNULL(s.user_scans,0) + ISNULL(s.user_lookups,0) = 0
ORDER BY ISNULL(s.user_updates,0) DESC;
```

### Missing Indexes

```sql
-- Missing index suggestions sorted by estimated impact
SELECT TOP 20
    ROUND(migs.avg_total_user_cost
        * migs.avg_user_impact
        * (migs.user_seeks + migs.user_scans), 0)     AS estimated_improvement,
    migs.user_seeks,
    migs.user_scans,
    mid.statement                                       AS table_name,
    mid.equality_columns,
    mid.inequality_columns,
    mid.included_columns
FROM sys.dm_db_missing_index_groups  AS mig
JOIN sys.dm_db_missing_index_group_stats AS migs
    ON migs.group_handle = mig.index_group_handle
JOIN sys.dm_db_missing_index_details AS mid
    ON mid.index_handle  = mig.index_handle
WHERE mid.database_id = DB_ID()
ORDER BY estimated_improvement DESC;
```

### Duplicate and Overlapping Indexes

```sql
-- Indexes with identical leading columns (potential duplicates)
SELECT
    OBJECT_NAME(i1.object_id)   AS table_name,
    i1.name                     AS index1,
    i2.name                     AS index2,
    COL_NAME(ic1.object_id, ic1.column_id) AS leading_column
FROM sys.indexes        AS i1
JOIN sys.indexes        AS i2
    ON  i1.object_id = i2.object_id
    AND i1.index_id  < i2.index_id
JOIN sys.index_columns  AS ic1
    ON  ic1.object_id   = i1.object_id
    AND ic1.index_id    = i1.index_id
    AND ic1.key_ordinal = 1
JOIN sys.index_columns  AS ic2
    ON  ic2.object_id   = i2.object_id
    AND ic2.index_id    = i2.index_id
    AND ic2.key_ordinal = 1
    AND ic2.column_id   = ic1.column_id
WHERE i1.type_desc <> 'HEAP'
ORDER BY table_name, leading_column;
```

### Index Fragmentation

```sql
-- Fragmentation for indexes with > 1000 pages
SELECT
    OBJECT_SCHEMA_NAME(ips.object_id)           AS schema_name,
    OBJECT_NAME(ips.object_id)                  AS table_name,
    i.name                                       AS index_name,
    ips.index_type_desc,
    CAST(ips.avg_fragmentation_in_percent AS DECIMAL(5,1)) AS frag_pct,
    ips.page_count,
    CASE
        WHEN ips.avg_fragmentation_in_percent < 5  THEN 'None needed'
        WHEN ips.avg_fragmentation_in_percent < 30 THEN 'REORGANIZE'
        ELSE 'REBUILD'
    END AS recommended_action
FROM sys.dm_db_index_physical_stats(
    DB_ID(), NULL, NULL, NULL, 'LIMITED') AS ips
JOIN sys.indexes AS i
    ON i.object_id = ips.object_id
    AND i.index_id = ips.index_id
WHERE ips.page_count > 1000
  AND ips.index_id > 0
ORDER BY ips.avg_fragmentation_in_percent DESC;
```

---

## Memory Grant Issues

Memory grant problems manifest as `RESOURCE_SEMAPHORE` waits (query queued waiting for a grant) or sort/hash spills in execution plans (granted memory was insufficient). Both stem from inaccurate row estimates.

### Active Memory Grants

```sql
-- Queries currently holding or waiting for memory grants
SELECT
    r.session_id,
    r.status,
    r.command,
    mg.requested_memory_kb,
    mg.granted_memory_kb,
    mg.used_memory_kb,
    mg.ideal_memory_kb,
    mg.queue_id,                        -- non-NULL = still waiting
    mg.wait_order,
    SUBSTRING(st.text, 1, 200)          AS query_snippet
FROM sys.dm_exec_query_memory_grants AS mg
JOIN sys.dm_exec_requests            AS r
    ON r.session_id = mg.session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS st
ORDER BY mg.requested_memory_kb DESC;
```

### Common Fixes

| Symptom | Fix |
|---------|-----|
| Spill to `tempdb` (sort/hash) | Update statistics; use `OPTION (RECOMPILE)` to get per-execution grant |
| Query stuck in `RESOURCE_SEMAPHORE` | Reduce parallelism; use Resource Governor to cap per-query memory |
| Consistently over-granted memory | Use `OPTION (MAX_GRANT_PERCENT = n)` hint to cap the grant |
| Bad estimate causing under-grant | Add or update statistics; consider filtered statistics for skewed data |

```sql
-- Force fresh compilation and accurate grant for a single execution
SELECT *
FROM dbo.LargeTable
WHERE StatusCode = @status
OPTION (RECOMPILE);
```

---

## Blocking Chain Resolution

### Find the Blocking Chain

```sql
-- Full blocking chain with wait type and SQL text
SELECT
    r.session_id                                    AS blocked_session,
    r.blocking_session_id                           AS blocking_session,
    r.wait_type,
    r.wait_time / 1000                              AS wait_sec,
    r.status,
    SUBSTRING(bt.text, 1, 300)                      AS blocked_sql,
    SUBSTRING(ht.text, 1, 300)                      AS blocker_sql,
    s_blocked.login_name                            AS blocked_login,
    s_head.login_name                               AS blocker_login,
    s_head.program_name                             AS blocker_program,
    s_head.host_name                                AS blocker_host
FROM sys.dm_exec_requests        AS r
JOIN sys.dm_exec_sessions        AS s_blocked
    ON s_blocked.session_id = r.session_id
JOIN sys.dm_exec_sessions        AS s_head
    ON s_head.session_id    = r.blocking_session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle)      AS bt
CROSS APPLY sys.dm_exec_sql_text(
    (SELECT sql_handle
     FROM sys.dm_exec_requests AS r2
     WHERE r2.session_id = r.blocking_session_id))  AS ht
WHERE r.blocking_session_id > 0
ORDER BY r.wait_time DESC;
```

### Identify the Head Blocker

The head blocker is the session that appears in `blocking_session_id` but does not itself appear in `session_id` of `dm_exec_requests` with a non-zero blocker. It is typically idle (not currently executing) yet holds open transactions.

```sql
-- Sessions that are blocking but not themselves blocked
SELECT
    s.session_id,
    s.status,
    s.login_name,
    s.program_name,
    s.host_name,
    s.last_request_start_time,
    t.open_transaction_count,
    SUBSTRING(st.text, 1, 300) AS last_sql
FROM sys.dm_exec_sessions   AS s
JOIN sys.dm_exec_connections AS c
    ON c.session_id = s.session_id
LEFT JOIN sys.dm_tran_session_transactions AS t
    ON t.session_id = s.session_id
CROSS APPLY sys.dm_exec_sql_text(c.most_recent_sql_handle) AS st
WHERE s.session_id IN (
    SELECT blocking_session_id
    FROM sys.dm_exec_requests
    WHERE blocking_session_id > 0
)
AND s.session_id NOT IN (
    SELECT session_id
    FROM sys.dm_exec_requests
    WHERE blocking_session_id > 0
);
```

### Resolution Options

| Option | When to Use | Notes |
|--------|------------|-------|
| `KILL <session_id>` | Emergency; long-running blocker | Rolls back the blocker's transaction; use with caution |
| Shorten transactions | Design fix | Move non-DB work outside `BEGIN TRAN`; commit early |
| Add or tune indexes | Reduce lock duration | Faster queries hold locks for less time |
| Enable RCSI | Sustained read/write contention | Readers no longer block writers; enable per-database |
| Use `NOLOCK` / `READ UNCOMMITTED` | Reporting queries where dirty reads are acceptable | Not suitable for transactional workloads |

### Read Committed Snapshot Isolation (RCSI)

RCSI eliminates most reader/writer blocking by using row versioning in `tempdb`. It is the recommended baseline for Azure SQL Database (enabled by default) and should be evaluated for on-premises workloads with high read/write contention.

```sql
-- Enable RCSI (Azure SQL: on by default; on-prem SQL Server: requires exclusive database access)
ALTER DATABASE [YourDatabase]
SET READ_COMMITTED_SNAPSHOT ON;

-- Verify
SELECT name, is_read_committed_snapshot_on
FROM sys.databases
WHERE name = DB_NAME();
```

---

**[← Back to Appendix](./appendix.md)**
