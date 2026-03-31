---
title: "Performance & DMVs — Quick Reference"
type: cheat-sheet
tags:
  - dp-800
  - cheat-sheet
  - performance
  - dmvs
  - query-tuning
---

# Performance & DMVs — Quick Reference

Key **Dynamic Management Views** (DMVs), diagnostic queries, and performance tuning patterns for Azure SQL Database.

> [!abstract] Quick Reference
> - DMV reference table for query stats, waits, indexes, locking, and Azure SQL resource usage
> - Copy-paste diagnostic queries for top CPU, I/O, blocking, and missing indexes
> - Use when practicing performance tuning scenarios or memorizing key DMV names

---

## DMV Reference Table

> [!info] DMVs expose internal engine state — memorize the category groupings to quickly find the right view on the exam.

| DMV | Category | Purpose |
| :--- | :--- | :--- |
| ==`sys.dm_exec_query_stats`== | Query | Aggregate query performance stats |
| `sys.dm_exec_query_plan` | Query | XML execution plan for a plan handle |
| `sys.dm_exec_sql_text` | Query | SQL text for a sql_handle |
| `sys.dm_exec_requests` | Session | Currently executing requests |
| `sys.dm_exec_sessions` | Session | All active sessions |
| `sys.dm_exec_connections` | Session | Connection details |
| `sys.dm_os_wait_stats` | Waits | Cumulative wait statistics |
| `sys.dm_os_waiting_tasks` | Waits | Currently waiting tasks |
| `sys.dm_db_index_usage_stats` | Index | Index read/write counts |
| `sys.dm_db_index_physical_stats` | Index | Fragmentation, page counts |
| `sys.dm_db_missing_index_details` | Index | Missing index suggestions |
| `sys.dm_db_missing_index_group_stats` | Index | Impact of missing indexes |
| `sys.dm_tran_locks` | Locking | Current locks held |
| `sys.dm_os_memory_clerks` | Memory | Memory allocation by component |
| `sys.dm_exec_cached_plans` | Plan cache | Cached execution plans |
| `sys.dm_db_resource_stats` | Azure SQL | CPU, IO, memory % (last hour) |

---

## Top Queries by CPU

> [!info] This is the single most useful diagnostic query — it identifies which statements consume the most CPU time.

```sql
SELECT TOP 20
    qs.total_worker_time / qs.execution_count AS AvgCPU_us,
    qs.execution_count,
    qs.total_worker_time AS TotalCPU_us,
    qs.total_elapsed_time / qs.execution_count AS AvgDuration_us,
    qs.total_logical_reads / qs.execution_count AS AvgReads,
    SUBSTRING(st.text,
        (qs.statement_start_offset / 2) + 1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
          END - qs.statement_start_offset) / 2) + 1
    ) AS QueryText,
    qp.query_plan
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
ORDER BY AvgCPU_us DESC;
```

---

## Top Queries by Logical Reads (I/O)

> [!info] High logical reads indicate queries scanning more data than necessary — often fixable with better indexes.

```sql
SELECT TOP 20
    qs.total_logical_reads / qs.execution_count AS AvgReads,
    qs.execution_count,
    qs.total_logical_reads,
    qs.total_logical_writes / qs.execution_count AS AvgWrites,
    SUBSTRING(st.text,
        (qs.statement_start_offset / 2) + 1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
          END - qs.statement_start_offset) / 2) + 1
    ) AS QueryText
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY AvgReads DESC;
```

---

## Currently Running Queries

> [!info] Use this query to see what is executing right now, including wait types and blocking relationships.

```sql
SELECT
    r.session_id,
    r.status,
    r.command,
    r.wait_type,
    r.wait_time,
    r.blocking_session_id,
    r.cpu_time,
    r.logical_reads,
    r.total_elapsed_time,
    st.text AS QueryText,
    qp.query_plan
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) st
CROSS APPLY sys.dm_exec_query_plan(r.plan_handle) qp
WHERE r.session_id > 50   -- exclude system sessions
ORDER BY r.total_elapsed_time DESC;
```

---

## Wait Statistics

> [!info] Wait stats reveal the bottleneck category — always check waits first before diving into individual queries.

### Top Waits (Cumulative)

```sql
SELECT TOP 15
    wait_type,
    wait_time_ms,
    signal_wait_time_ms,
    wait_time_ms - signal_wait_time_ms AS resource_wait_ms,
    waiting_tasks_count,
    CAST(100.0 * wait_time_ms / SUM(wait_time_ms) OVER () AS DECIMAL(5,2)) AS PctTotal
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'SLEEP_TASK', 'BROKER_TO_FLUSH', 'SQLTRACE_BUFFER_FLUSH',
    'CLR_AUTO_EVENT', 'CLR_MANUAL_EVENT', 'LAZYWRITER_SLEEP',
    'CHECKPOINT_QUEUE', 'WAITFOR', 'XE_TIMER_EVENT',
    'BROKER_EVENTHANDLER', 'FT_IFTS_SCHEDULER_IDLE_WAIT',
    'XE_DISPATCHER_WAIT', 'SP_SERVER_DIAGNOSTICS_SLEEP'
)
AND waiting_tasks_count > 0
ORDER BY wait_time_ms DESC;
```

### Common Wait Types

| Wait Type | Category | Indicates |
| :--- | :--- | :--- |
| `CXPACKET` / `CXCONSUMER` | Parallelism | Parallel query waits (often benign) |
| ==`PAGEIOLATCH_*`== | I/O | Reading pages from disk |
| `LCK_M_*` | Locking | Blocked by another session |
| `SOS_SCHEDULER_YIELD` | CPU | CPU pressure |
| `WRITELOG` | Transaction log | Log write latency |
| `RESOURCE_SEMAPHORE` | Memory | Waiting for memory grant |
| `ASYNC_NETWORK_IO` | Network | Client not consuming results fast enough |

> [!warning] Common Mistake
> CXPACKET waits alone do not indicate a parallelism problem. They are normal in parallel queries. Only investigate if combined with high LATCH or SOS_SCHEDULER_YIELD waits.

---

## Index Analysis

> [!info] Index DMVs help you find missing indexes, unused indexes, and fragmentation levels.

### Missing Indexes

```sql
SELECT TOP 20
    ROUND(gs.avg_total_user_cost * gs.avg_user_impact *
          (gs.user_seeks + gs.user_scans), 0) AS ImprovementScore,
    d.statement AS TableName,
    d.equality_columns,
    d.inequality_columns,
    d.included_columns,
    gs.user_seeks,
    gs.user_scans
FROM sys.dm_db_missing_index_group_stats gs
JOIN sys.dm_db_missing_index_groups g
    ON gs.group_handle = g.index_group_handle
JOIN sys.dm_db_missing_index_details d
    ON g.index_handle = d.index_handle
ORDER BY ImprovementScore DESC;
```

> [!warning] Common Mistake
> Missing index DMV suggestions are cumulative since last restart and do not account for write overhead. Always evaluate the trade-off before blindly creating suggested indexes.

### Index Usage Stats

```sql
SELECT
    OBJECT_NAME(ius.object_id) AS TableName,
    i.name AS IndexName,
    i.type_desc,
    ius.user_seeks,
    ius.user_scans,
    ius.user_lookups,
    ius.user_updates,
    ius.last_user_seek,
    ius.last_user_scan
FROM sys.dm_db_index_usage_stats ius
JOIN sys.indexes i
    ON ius.object_id = i.object_id AND ius.index_id = i.index_id
WHERE ius.database_id = DB_ID()
ORDER BY ius.user_seeks + ius.user_scans DESC;
```

### Index Fragmentation

```sql
SELECT
    OBJECT_NAME(ips.object_id) AS TableName,
    i.name AS IndexName,
    ips.index_type_desc,
    ips.avg_fragmentation_in_percent,
    ips.page_count,
    ips.avg_page_space_used_in_percent
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i
    ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10
    AND ips.page_count > 1000
ORDER BY ips.avg_fragmentation_in_percent DESC;
```

| Fragmentation | Action |
| :--- | :--- |
| 10-30% | `ALTER INDEX ... REORGANIZE` |
| > 30% | ==`ALTER INDEX ... REBUILD`== |
| < 10% | No action needed |

> [!tip] Exam Tip
> Remember the thresholds: REORGANIZE for 10-30% fragmentation, REBUILD for over 30%. In Azure SQL Database, automatic tuning can handle index management, but you still need to know the manual thresholds.

---

## Blocking & Deadlocks

> [!info] Blocking chains show which session holds the lock that other sessions are waiting on.

### Current Blocking Chain

```sql
SELECT
    r.session_id AS BlockedSession,
    r.blocking_session_id AS BlockingSession,
    r.wait_type,
    r.wait_time,
    blocked_text.text AS BlockedQuery,
    blocker_text.text AS BlockerQuery
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) blocked_text
LEFT JOIN sys.dm_exec_requests r2
    ON r.blocking_session_id = r2.session_id
OUTER APPLY sys.dm_exec_sql_text(r2.sql_handle) blocker_text
WHERE r.blocking_session_id > 0;
```

### Kill a Blocking Session

```sql
KILL 55;   -- use with caution, rolls back the blocker's transaction
```

---

## Azure SQL Resource Usage

> [!info] dm_db_resource_stats provides CPU, I/O, and memory percentages at 15-second intervals for the last hour.

```sql
-- Last hour, 15-second intervals
SELECT TOP 60
    end_time,
    avg_cpu_percent,
    avg_data_io_percent,
    avg_log_write_percent,
    avg_memory_usage_percent,
    max_worker_percent,
    max_session_percent
FROM sys.dm_db_resource_stats
ORDER BY end_time DESC;
```

---

## Execution Plan Warning Flags

> [!info] These warnings appear in actual execution plans — each one points to a specific optimization opportunity.

| Warning | Meaning | Fix |
| :--- | :--- | :--- |
| Missing index hint | Optimizer suggests an index | Evaluate and create if beneficial |
| Key Lookup | Bookmark lookup to clustered index | Add INCLUDE columns to nonclustered index |
| Sort with spill | Sort exceeded memory grant | Update statistics, increase memory grant |
| Hash match spill | Hash join exceeded memory grant | Update statistics, add index |
| ==Implicit conversion== | Data type mismatch in join/filter | Fix column types or cast explicitly |
| Parameter sniffing | Plan compiled for atypical value | OPTION (RECOMPILE), plan guides, OPTIMIZE FOR |
| Cardinality estimate warning | Row estimate far from actual | Update statistics, use query hints |

> [!tip] Exam Tip
> Implicit conversions are the most commonly missed performance issue. They occur when comparing mismatched data types (e.g., VARCHAR column filtered with NVARCHAR parameter) and prevent index seeks.

---

## Quick Tuning Checklist

> [!info] Follow this sequence to systematically diagnose and resolve performance issues.

1. **Check wait stats** — identify bottleneck category (CPU, I/O, locks, memory)
2. **Find top queries** — by CPU, reads, or duration
3. **Review execution plans** — look for scans, spills, implicit conversions
4. **Check missing indexes** — evaluate top suggestions
5. **Check unused indexes** — drop indexes with 0 seeks/scans and high updates
6. **Check fragmentation** — rebuild/reorganize as needed
7. **Review Query Store** — identify regressed queries, force good plans

---

## Gotchas & Traps

- **sys.dm_os_wait_stats is cumulative** — values accumulate since the last service restart. To trend wait stats, capture a snapshot, wait, capture again, and diff. A single reading is meaningless.
- **Query Store ≠ plan cache** — plan cache is volatile (cleared on memory pressure, restart); Query Store persists plans and stats across restarts. Forced plans survive restarts too.
- **sys.dm_exec_query_plan is the current cached plan** — not necessarily the plan that ran for a slow query. Use Query Store for historical plan analysis.
- **Missing index DMVs are suggestions, not mandates** — `sys.dm_db_missing_index_details` recommends indexes but doesn't account for write overhead or existing similar indexes. Always evaluate before creating.
- **REBUILD vs REORGANIZE** — REBUILD: offline by default (ONLINE = ON option), full rewrite, resets fragmentation to ~0%; REORGANIZE: always online, leaf-level defrag, less disruptive.
- **MAXDOP = 0 ≠ no parallelism** — MAXDOP 0 means use all available CPUs. MAXDOP 1 disables parallelism. Override per query with `OPTION (MAXDOP n)`.

---

## Before the Exam, I Can…

- [ ] Name the key DMVs for: top CPU queries, active blocking, wait stats, missing indexes, and index fragmentation
- [ ] Explain the difference between REBUILD and REORGANIZE and when to use each
- [ ] Describe Query Store's role: what it captures, how to force a plan, how to unforce it
- [ ] Explain why sys.dm_os_wait_stats requires a delta approach and what a single snapshot tells you
- [ ] Explain what MAXDOP 0, 1, and N mean in practice
- [ ] Describe how to identify a blocking chain using sys.dm_exec_requests and sys.dm_os_waiting_tasks

---

**[← Back to Cheat Sheets](./README.md)**
