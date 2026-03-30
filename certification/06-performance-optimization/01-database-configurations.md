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
| **Hyperscale** | Very large databases (up to 100 TB) | Rapid scaling, distributed architecture |

**Serverless (General Purpose only):** Auto-pause when idle, auto-scale compute — good for intermittent workloads:

```text
Azure SQL → Configure → Serverless
- Min vCores: 0.5 (minimum when active)
- Max vCores: 4
- Auto-pause delay: 60 minutes
```

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

## Use Cases

- **Business Critical tier**: Latency-sensitive workloads, In-Memory OLTP, read scale-out
- **Serverless**: Development databases, apps with unpredictable usage patterns
- **RCSI**: Multi-user OLTP workloads where reader/writer blocking is a problem
- **Query Store**: Regression detection and plan forcing after upgrades

## Exam Tips

- **RCSI** (Read Committed Snapshot Isolation) eliminates reader/writer blocking — enable for OLTP
- Compatibility level 160 enables the latest optimizer features — test before changing in production
- Azure SQL Business Critical has a **built-in read-only replica** at no extra cost
- Automatic tuning `FORCE_LAST_GOOD_PLAN` automatically reverts to previous plan on regression

## Key Takeaways

- Match service tier to workload: General Purpose for most, Business Critical for low-latency
- Enable RCSI to reduce blocking in read/write mixed workloads
- Query Store should always be enabled — it's the foundation for plan forcing and regression detection

## Related Topics

- [02-Transaction Isolation & Concurrency](./02-transaction-isolation-concurrency.md)
- [03-Query Performance Troubleshooting](./03-query-performance-troubleshooting.md)

## Official Documentation

- [Azure SQL Service Tiers](https://learn.microsoft.com/en-us/azure/azure-sql/database/service-tiers-overview)
- [ALTER DATABASE SCOPED CONFIGURATION](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-scoped-configuration-transact-sql)
- [Automatic Tuning](https://learn.microsoft.com/en-us/azure/azure-sql/database/automatic-tuning-overview)

---

**[↑ Back to Section](./README.md) | [Next →](./02-transaction-isolation-concurrency.md)**
