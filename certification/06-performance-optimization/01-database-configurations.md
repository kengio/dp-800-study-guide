---
title: Database Configuration Recommendations
type: study-material
tags:
  - dp-800
  - performance
  - database-configuration
  - azure-sql
  - service-tiers
---

# Database Configuration Recommendations

## Overview

Database configuration choices — service tier, compatibility level, memory grants, and database-scoped options — significantly impact performance. The DP-800 exam tests recommending appropriate configurations for specific workloads.

> [!abstract]
> - Covers database-scoped configurations (MAXDOP, cost threshold, auto-stats), compatibility levels, and Query Store setup
> - Configuration changes affect all queries unless overridden at the query level with hints
> - Key exam topics: MAXDOP values, compatibility level effects, auto-create/update statistics behavior

> [!tip] What the Exam Tests
> - `MAXDOP = 0` = use all CPUs; `MAXDOP = 1` = disable parallelism; override per query with `OPTION (MAXDOP n)`
> - `ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = n` sets the database default (does not affect server default)
> - **Compatibility level** controls optimizer behavior and feature availability — independent of the SQL Server engine version

---

## Azure SQL Service Tiers

### DTU-Based (Simpler Pricing)

| Tier | Use Case | DTU Range |
| :--- | :--- | :--- |
| Basic | Dev/test, small apps | 5 DTU |
| Standard | Departmental workloads | 10–3000 DTU |
| Premium | Mission-critical, In-Memory OLTP | 125–4000 DTU |

### vCore-Based (Recommended)

| Tier | Use Case | Notes |
| :--- | :--- | :--- |
| **General Purpose** | Most business workloads | Remote storage, auto-pause option |
| **Business Critical** | Low latency, In-Memory OLTP | Local SSD, built-in HA replica |
| **Hyperscale** | Very large databases (up to 100 TB) | ==Rapid scaling, distributed architecture== |

**Serverless (General Purpose only):** Auto-pause when idle, auto-scale compute — good for intermittent workloads:

```text
Azure SQL → Configure → Serverless
- Min vCores: 0.5 (minimum when active)
- Max vCores: 4
- Auto-pause delay: 60 minutes
```

---

## Database Compatibility Level

Compatibility level controls which query optimizer features and breaking changes are active:

```sql
-- Check current compatibility level
SELECT name, compatibility_level FROM sys.databases WHERE name = DB_NAME();

-- Change compatibility level
ALTER DATABASE MyDB SET COMPATIBILITY_LEVEL = 160;  -- SQL Server 2022
```

**Compatibility levels:**

| Level | SQL Server Version | Key Features |
| :--- | :--- | :--- |
| 160 | 2022 / Azure SQL | Parameter sensitivity plan optimization, DOP feedback |
| 150 | 2019 | Scalar UDF inlining, table variable deferred compilation, batch mode on rowstore |
| 140 | 2017 | Adaptive query processing (adaptive joins, interleaved execution) |
| 130 | 2016 | Batch mode for aggregates, parallel `INSERT INTO ... SELECT` |

---

## Database-Scoped Configurations

```sql
-- Enable Read Committed Snapshot Isolation (RCSI) — recommended for Azure SQL
ALTER DATABASE MyDB SET READ_COMMITTED_SNAPSHOT ON;

-- Enable Query Store
ALTER DATABASE MyDB SET QUERY_STORE = ON (
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = AUTO,
    MAX_STORAGE_SIZE_MB = 1000
);

-- Set max degree of parallelism
ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = 4;

-- Legacy cardinality estimator (if new CE causes regressions)
ALTER DATABASE SCOPED CONFIGURATION SET LEGACY_CARDINALITY_ESTIMATION = OFF;

-- Optimize for ad hoc workloads (reduce plan cache bloat)
EXEC sp_configure 'optimize for ad hoc workloads', 1;
RECONFIGURE;
```

---

## Memory and Resource Configuration

```sql
-- View memory grants
SELECT * FROM sys.dm_exec_query_memory_grants;

-- View current server configuration
SELECT name, value_in_use
FROM sys.configurations
WHERE name IN ('max server memory (MB)', 'min server memory (MB)',
               'max degree of parallelism', 'cost threshold for parallelism');
```

**Key server-level settings:**

| Setting | Recommendation |
| :--- | :--- |
| `max server memory` | Leave 10–15% for OS; set rest to SQL |
| `MAXDOP` | Equal to physical CPU count or 8 (whichever is lower) |
| `cost threshold for parallelism` | Increase from default 5 to 25–50 to reduce unnecessary parallelism |

---

## Automatic Tuning (Azure SQL)

Azure SQL can automatically create, verify, and drop indexes based on query performance:

```sql
-- Enable automatic tuning
ALTER DATABASE MyDB SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
ALTER DATABASE MyDB SET AUTOMATIC_TUNING (CREATE_INDEX = ON);
ALTER DATABASE MyDB SET AUTOMATIC_TUNING (DROP_INDEX = ON);

-- View recommendations
SELECT * FROM sys.dm_db_tuning_recommendations;
```

---

## MAXDOP and Parallelism Settings

**MAXDOP (Maximum Degree of Parallelism)** caps the number of parallel threads SQL Server can use for a single query. Setting it appropriately prevents runaway parallelism from monopolizing CPU resources.

**Scope hierarchy** (most specific wins):

1. Query hint: `OPTION(MAXDOP n)`
2. Database-scoped: `ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = n`
3. Server-level: `sp_configure 'max degree of parallelism'`

**Cost threshold for parallelism:** The estimated query cost (in seconds on a reference machine) must exceed this threshold before SQL Server considers a parallel plan. The default of 5 is very low — most queries on modern hardware are cheap enough to go parallel unnecessarily. Raising it to 40–50 reduces context-switch overhead for OLTP workloads.

> [!warning] Common Mistake
> MAXDOP 0 does NOT disable parallelism — it means "use all available CPUs." MAXDOP 1 disables parallelism. This is a classic exam trap.

**When parallel plans hurt:**

- Short OLTP queries — thread coordination overhead exceeds query time
- High concurrent load — parallel queries steal threads from other sessions
- Single-row lookups and simple aggregations

```sql
-- Set MAXDOP at database scope (Azure SQL Database approach)
ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = 4;

-- Override at query level
SELECT CustomerID, SUM(TotalAmount) AS Total
FROM Orders
GROUP BY CustomerID
OPTION(MAXDOP 1);  -- Force serial execution

-- Set cost threshold for parallelism (server-level)
EXEC sp_configure 'cost threshold for parallelism', 50;
RECONFIGURE;

-- Check current settings
SELECT name, value_in_use
FROM sys.configurations
WHERE name IN ('max degree of parallelism', 'cost threshold for parallelism');
```

---

## Memory Grant Configuration

A **memory grant** is memory pre-allocated before a query executes to support sort and hash join operations. If the grant is too small, SQL Server spills to tempdb (hurting performance); if too large, other queries are starved.

**Memory grant feedback (adaptive query processing):** Introduced in compatibility level 140+, SQL Server tracks actual vs. granted memory across executions and adjusts future grants automatically — no manual tuning required for stable workloads.

**Manual control options:**

- `OPTION(MIN_GRANT_PERCENT = n)` — guarantee a minimum fraction of the workspace memory pool
- `OPTION(MAX_GRANT_PERCENT = n)` — cap the grant to prevent over-allocation
- Resource Governor pools: set `MIN_MEMORY_PERCENT` / `MAX_MEMORY_PERCENT` per workload group

```sql
-- Diagnose memory grant issues
SELECT session_id, granted_memory_kb, used_memory_kb,
       ideal_memory_kb, requested_memory_kb,
       wait_time_ms, queue_id
FROM sys.dm_exec_query_memory_grants;

-- Force minimum memory grant for large sort
SELECT CustomerID, SUM(TotalAmount) AS Total
FROM Orders
GROUP BY CustomerID
ORDER BY Total DESC
OPTION(MIN_GRANT_PERCENT = 10);
```

**Key columns in `sys.dm_exec_query_memory_grants`:**

| Column | Meaning |
| :--- | :--- |
| `granted_memory_kb` | Memory actually allocated |
| `ideal_memory_kb` | Memory the optimizer wanted |
| `used_memory_kb` | Memory consumed at query completion |
| `wait_time_ms` | Time spent waiting for a grant (> 0 means memory pressure) |

---

## Query Store Configuration

**Query Store** captures a history of queries, execution plans, and runtime statistics. It is the primary tool for diagnosing plan regressions, forcing good plans, and analyzing workload trends.

**What Query Store captures:**

- Query text and parameterized form
- All execution plans (including historical plans)
- Aggregated runtime stats per plan: CPU, duration, I/O, memory, row counts
- Wait statistics per query (compatibility level 140+)

**Key configuration settings:**

| Setting | Description | Recommended Value |
| :--- | :--- | :--- |
| `OPERATION_MODE` | READ_WRITE collects data; READ_ONLY stops collection | READ_WRITE |
| `MAX_STORAGE_SIZE_MB` | Max disk space for Query Store data | 1024–2048 MB |
| `INTERVAL_LENGTH_MINUTES` | Aggregation window for runtime stats | 60 minutes |
| `QUERY_CAPTURE_MODE` | ALL, AUTO (significant queries), CUSTOM, NONE | ==AUTO== |
| `SIZE_BASED_CLEANUP_MODE` | Auto-purge oldest data when near capacity | AUTO |

```sql
-- Enable and configure Query Store
ALTER DATABASE MyDatabase
SET QUERY_STORE = ON
(
    OPERATION_MODE = READ_WRITE,
    MAX_STORAGE_SIZE_MB = 1024,
    INTERVAL_LENGTH_MINUTES = 60,
    QUERY_CAPTURE_MODE = AUTO,     -- Captures significant queries only
    SIZE_BASED_CLEANUP_MODE = AUTO
);

-- Find top 10 queries by average CPU
SELECT TOP 10
    qt.query_sql_text,
    qrs.avg_cpu_time,
    qrs.avg_duration,
    qrs.count_executions
FROM sys.query_store_query_text qt
JOIN sys.query_store_query q ON qt.query_text_id = q.query_text_id
JOIN sys.query_store_plan qp ON q.query_id = qp.query_id
JOIN sys.query_store_runtime_stats qrs ON qp.plan_id = qrs.plan_id
ORDER BY qrs.avg_cpu_time DESC;

-- Force a specific plan
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 1;
```

**Query Store built-in reports (SSMS / Azure Portal):**

- Regressed Queries — plans that degraded over a time period
- Top Resource Consuming Queries — ranked by CPU, duration, I/O, or memory
- Plan Summary — all plans for a single query with performance comparison

---

## Database Compatibility Level Impact

**Compatibility level** determines which version of the query optimizer's cardinality estimator (CE) is active and which adaptive query processing features are available. It is the primary control for balancing access to new features against regression risk after an upgrade.

**Cardinality estimator versions:**

| CE Version | Compatibility Level | Notes |
| :--- | :--- | :--- |
| CE70 | 70–110 | Legacy; often produces suboptimal plans on modern schemas |
| CE120 | 120 (SQL 2014) | Major rewrite; better multi-predicate selectivity estimates |
| CE150 | 150+ (SQL 2019) | Improved row goal adjustments, adaptive joins, UDF inlining |

**Key compatibility levels for the exam:**

| Level | Version | Exam-Relevant Features |
| :--- | :--- | :--- |
| 130 | SQL 2016 | Batch mode aggregates, parallel INSERT...SELECT |
| 140 | SQL 2017 | Adaptive joins, interleaved execution, memory grant feedback |
| 150 | SQL 2019 | Scalar UDF inlining, table variable deferred compilation, batch mode on rowstore |
| 160 | SQL 2022 / Azure SQL | Parameter Sensitive Plan (PSP) optimization, DOP feedback, CE feedback |

**Recommended upgrade approach:** Enable Query Store before changing compatibility level so you have a pre-upgrade baseline. After changing, use the Regressed Queries report to identify and force any plans that degraded.

```sql
-- Check and change compatibility level
SELECT name, compatibility_level FROM sys.databases WHERE name = DB_NAME();

ALTER DATABASE MyDatabase SET COMPATIBILITY_LEVEL = 160;

-- Test with new CE without changing DB compat level
SELECT * FROM Orders WHERE CustomerID = @CustID
OPTION(USE HINT('ENABLE_QUERY_OPTIMIZER_HOTFIXES'));
```

---

## Use Cases

- **Business Critical tier**: Latency-sensitive workloads, In-Memory OLTP, read scale-out
- **Serverless**: Development databases, apps with unpredictable usage patterns
- **RCSI**: Multi-user OLTP workloads where reader/writer blocking is a problem
- **Query Store**: Regression detection and plan forcing after upgrades or compatibility level changes
- **MAXDOP 1**: Reporting queries on high-concurrency OLTP systems to limit CPU consumption

---

## Common Issues & Errors

- **Memory spills to tempdb**: `granted_memory_kb` much lower than `ideal_memory_kb` — increase grant hint or enable memory grant feedback (compat level 140+)
- **Query Store goes READ_ONLY unexpectedly**: ==Storage cap reached — increase `MAX_STORAGE_SIZE_MB` or enable `SIZE_BASED_CLEANUP_MODE = AUTO`==
- **Plan regression after compat level change**: Use Query Store Regressed Queries report and `sp_query_store_force_plan` to restore the previous good plan
- **Excessive parallelism on OLTP**: CXPACKET waits dominate — raise cost threshold for parallelism to 40–50 and consider MAXDOP 4 or lower at DB scope
- **Automatic tuning not creating indexes**: `CREATE_INDEX` must be explicitly enabled; verify the feature is ON and check `sys.dm_db_tuning_recommendations` for blocked recommendations

---

## Best Practices

- Enable Query Store on every production database before any upgrade or compatibility level change to establish a performance baseline
- Set `QUERY_CAPTURE_MODE = AUTO` to avoid storing trivial single-execution queries that inflate storage and obscure analysis
- Raise `cost threshold for parallelism` to 40–50 on OLTP workloads — the default of 5 causes unnecessary parallelism for cheap queries
- Use database-scoped `MAXDOP` settings in Azure SQL Database rather than server-level, since the instance may host multiple databases with different workload profiles
- Always test compatibility level changes in a non-production environment with a representative Query Store workload before promoting to production

---

## Exam Tips

> [!tip] Exam Tips
> - **RCSI** (Read Committed Snapshot Isolation) eliminates reader/writer blocking — enable for OLTP
> - Compatibility level 160 enables the latest optimizer features — test before changing in production
> - Azure SQL Business Critical has a **built-in read-only replica** at no extra cost
> - Automatic tuning `FORCE_LAST_GOOD_PLAN` automatically reverts to previous plan on regression
> - **Query Store is the recommended tool** for investigating plan regressions after a compatibility level upgrade — not reverting the level
> - **Memory grant feedback** (compat level 140+) self-corrects over-/under-grants automatically — prefer it over manual grant hints for stable workloads
> - `OPTION(MAXDOP 1)` is a valid query-level override and is often the right choice for long-running reports on busy OLTP systems

---

## Key Takeaways

- Match service tier to workload: General Purpose for most, Business Critical for low-latency
- Enable RCSI to reduce blocking in read/write mixed workloads
- Query Store should always be enabled — it is the foundation for plan forcing and regression detection
- MAXDOP and cost threshold for parallelism settings prevent parallelism from degrading OLTP concurrency
- Compatibility level upgrades unlock new optimizer features but carry plan regression risk — always use Query Store as a safety net

---

## Practice Question

After upgrading an Azure SQL Database compatibility level from 130 to 150, several queries start using suboptimal plans. What is the RECOMMENDED approach to investigate and fix this?

A. Revert the compatibility level to 130 permanently
B. Use Query Store to identify regressed queries and force the previous plans
C. Disable parallelism with MAXDOP 1 for all queries
D. Increase the cost threshold for parallelism to 100

> [!success]- Answer
> **B — Use Query Store to identify regressed queries and force the previous plans**
>
> Query Store captures plans before and after the compatibility level change. The Regressed Queries report shows queries whose performance degraded. You can force the previously good plan while investigating root cause. Reverting (A) gives up the benefits of the new CE. MAXDOP 1 (C) and high cost threshold (D) are blunt instruments that don't address the plan regression.

---

## Related Topics

- [02-Transaction Isolation & Concurrency](./02-transaction-isolation-concurrency.md)
- [03-Query Performance Troubleshooting](./03-query-performance-troubleshooting.md)

---

## Official Documentation

- [Azure SQL Service Tiers](https://learn.microsoft.com/en-us/azure/azure-sql/database/service-tiers-overview)
- [ALTER DATABASE SCOPED CONFIGURATION](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-scoped-configuration-transact-sql)
- [Automatic Tuning](https://learn.microsoft.com/en-us/azure/azure-sql/database/automatic-tuning-overview)
- [Query Store Overview](https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store)
- [Memory Grant Feedback](https://learn.microsoft.com/en-us/sql/relational-databases/performance/adaptive-query-processing)
- [Database Compatibility Level](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level)

---

**[↑ Back to Section](./README.md) | [Next →](./02-transaction-isolation-concurrency.md)**
