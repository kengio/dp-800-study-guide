---
title: "Azure SQL Config — Quick Reference"
type: cheat-sheet
tags:
  - dp-800
  - cheat-sheet
  - azure-sql
  - query-store
  - dab
  - sqlpackage
---

# Azure SQL Config — Quick Reference

Database configurations, Query Store, Data API Builder (DAB), and sqlpackage for Azure SQL Database.

---

## Database Configuration Settings

### ALTER DATABASE SCOPED CONFIGURATION

```sql
-- View current settings
SELECT * FROM sys.database_scoped_configurations;

-- MAXDOP: max parallelism per query
ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = 8;

-- Legacy cardinality estimator (for backward compat)
ALTER DATABASE SCOPED CONFIGURATION SET LEGACY_CARDINALITY_ESTIMATION = OFF;

-- Parameter sniffing
ALTER DATABASE SCOPED CONFIGURATION SET PARAMETER_SNIFFING = ON;   -- default

-- Query optimizer hotfixes
ALTER DATABASE SCOPED CONFIGURATION SET QUERY_OPTIMIZER_HOTFIXES = ON;

-- Optimize for ad hoc workloads (cache stub first)
ALTER DATABASE SCOPED CONFIGURATION SET OPTIMIZE_FOR_AD_HOC_WORKLOADS = ON;

-- Set for secondary replica only
ALTER DATABASE SCOPED CONFIGURATION FOR SECONDARY SET MAXDOP = 4;
```

### Key Settings Table

| Setting | Default | Exam Relevance |
| :--- | :--- | :--- |
| `MAXDOP` | 0 (unlimited) | Parallelism control |
| `LEGACY_CARDINALITY_ESTIMATION` | OFF | Use new CE by default |
| `PARAMETER_SNIFFING` | ON | Disable for ad-hoc workloads |
| `QUERY_OPTIMIZER_HOTFIXES` | OFF | Enable for latest optimizer fixes |
| `OPTIMIZE_FOR_AD_HOC_WORKLOADS` | OFF | Reduces plan cache bloat |
| `IDENTITY_CACHE` | ON | Turn OFF to avoid gaps on restart |
| `BATCH_MODE_ON_ROWSTORE` | ON | Batch mode without columnstore |
| `ACCELERATED_DATABASE_RECOVERY` | ON (Azure SQL) | Fast recovery, no long rollbacks |

### Compatibility Level

```sql
-- Check current level
SELECT name, compatibility_level FROM sys.databases WHERE name = DB_NAME();

-- Set compatibility level
ALTER DATABASE CURRENT SET COMPATIBILITY_LEVEL = 160;  -- SQL Server 2022
```

| Level | Version | Key Feature |
| :--- | :--- | :--- |
| 160 | SQL Server 2022 | Parameter-sensitive plan optimization, CE feedback |
| 150 | SQL Server 2019 | Batch mode on rowstore, scalar UDF inlining |
| 140 | SQL Server 2017 | Adaptive joins, interleaved execution |
| 130 | SQL Server 2016 | Batch mode for columnstore, Query Store |

---

## Query Store

### Enable / Configure

```sql
-- Enable Query Store
ALTER DATABASE CURRENT SET QUERY_STORE = ON;

-- Configure settings
ALTER DATABASE CURRENT SET QUERY_STORE (
    OPERATION_MODE = READ_WRITE,
    MAX_STORAGE_SIZE_MB = 200,
    INTERVAL_LENGTH_MINUTES = 30,        -- stats aggregation interval
    DATA_FLUSH_INTERVAL_SECONDS = 900,
    STALE_QUERY_THRESHOLD_DAYS = 30,
    QUERY_CAPTURE_MODE = AUTO,           -- AUTO, ALL, NONE, CUSTOM
    SIZE_BASED_CLEANUP_MODE = AUTO,
    MAX_PLANS_PER_QUERY = 200,
    CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30)
);
```

### Query Store Catalog Views

| View | Purpose |
| :--- | :--- |
| `sys.query_store_query` | Query metadata |
| `sys.query_store_query_text` | SQL text |
| `sys.query_store_plan` | Execution plans |
| `sys.query_store_runtime_stats` | Runtime statistics per plan per interval |
| `sys.query_store_runtime_stats_interval` | Time intervals |
| `sys.query_store_wait_stats` | Wait statistics per plan |
| `sys.database_query_store_options` | Current QS configuration |

### Find Regressed Queries

```sql
-- Queries with recent plan regression
SELECT
    q.query_id,
    qt.query_sql_text,
    p.plan_id,
    rs.avg_duration,
    rs.avg_cpu_time,
    rs.avg_logical_io_reads,
    rs.count_executions,
    rs.first_execution_time,
    rs.last_execution_time
FROM sys.query_store_runtime_stats rs
JOIN sys.query_store_plan p ON rs.plan_id = p.plan_id
JOIN sys.query_store_query q ON p.query_id = q.query_id
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
WHERE rs.last_execution_time > DATEADD(HOUR, -24, GETUTCDATE())
ORDER BY rs.avg_duration DESC;
```

### Force / Unforce a Plan

```sql
-- Force a known-good plan
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;

-- Unforce
EXEC sp_query_store_unforce_plan @query_id = 42, @plan_id = 7;

-- Remove a query from Query Store
EXEC sp_query_store_remove_query @query_id = 42;

-- Flush to disk immediately
EXEC sp_query_store_flush_db;
```

### Query Store Hints (SQL Server 2022+ / Azure SQL)

```sql
-- Apply a hint to a query without modifying application code
EXEC sp_query_store_set_hints
    @query_id = 42,
    @query_hints = N'OPTION (RECOMPILE, MAXDOP 1)';

-- Remove hint
EXEC sp_query_store_clear_hints @query_id = 42;
```

---

## Transaction Isolation Levels

```sql
-- Set at session level
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;  -- default
```

| Level | Dirty Reads | Non-Repeatable | Phantoms | Locks |
| :--- | :--- | :--- | :--- | :--- |
| READ UNCOMMITTED | Yes | Yes | Yes | None |
| READ COMMITTED | No | Yes | Yes | Shared (released after read) |
| REPEATABLE READ | No | No | Yes | Shared (held to end of txn) |
| SERIALIZABLE | No | No | No | Range locks |
| SNAPSHOT | No | No | No | Row versioning (no locks) |
| READ COMMITTED SNAPSHOT | No | Yes | Yes | Row versioning |

```sql
-- Enable SNAPSHOT isolation
ALTER DATABASE CURRENT SET ALLOW_SNAPSHOT_ISOLATION ON;

-- Enable READ_COMMITTED_SNAPSHOT (recommended for Azure SQL)
ALTER DATABASE CURRENT SET READ_COMMITTED_SNAPSHOT ON;
```

---

## Data API Builder (DAB)

REST and GraphQL API layer for Azure SQL, no custom code required.

### Configuration File (dab-config.json)

```json
{
  "data-source": {
    "database-type": "mssql",
    "connection-string": "@env('DATABASE_CONNECTION_STRING')"
  },
  "runtime": {
    "rest": { "enabled": true, "path": "/api" },
    "graphql": { "enabled": true, "path": "/graphql" }
  },
  "entities": {
    "Customer": {
      "source": { "object": "dbo.Customers", "type": "table" },
      "permissions": [
        {
          "role": "anonymous",
          "actions": [
            { "action": "read" }
          ]
        },
        {
          "role": "authenticated",
          "actions": ["create", "read", "update", "delete"]
        }
      ],
      "rest": { "path": "/customers" },
      "graphql": { "singular": "customer", "plural": "customers" }
    }
  }
}
```

### DAB CLI Commands

```bash
# Initialize config
dab init --database-type mssql --connection-string "Server=..."

# Add entity
dab add Customer --source dbo.Customers --permissions "anonymous:read"

# Add stored procedure entity
dab add GetOrders --source dbo.usp_GetOrdersByCustomer \
    --source.type "stored-procedure" \
    --source.params "CustomerId:1" \
    --permissions "authenticated:execute"

# Start DAB locally
dab start

# Validate config
dab validate
```

### DAB REST Endpoints

| Operation | HTTP Method | URL |
| :--- | :--- | :--- |
| List all | GET | `/api/customers` |
| Get by PK | GET | `/api/customers/CustomerID/42` |
| Filter | GET | `/api/customers?$filter=Name eq 'Alice'` |
| Select fields | GET | `/api/customers?$select=Name,Email` |
| Order | GET | `/api/customers?$orderby=Name asc` |
| Create | POST | `/api/customers` |
| Update | PUT/PATCH | `/api/customers/CustomerID/42` |
| Delete | DELETE | `/api/customers/CustomerID/42` |

### DAB GraphQL

```graphql
# Query
query {
  customers(filter: { Name: { eq: "Alice" } }) {
    items {
      CustomerID
      Name
      Email
    }
  }
}

# Mutation
mutation {
  createCustomer(item: { Name: "Dave", Email: "dave@example.com" }) {
    CustomerID
    Name
  }
}
```

---

## sqlpackage — Schema Deployment

### Common Actions

```bash
# Export database to BACPAC (schema + data)
sqlpackage /Action:Export \
    /TargetFile:"backup.bacpac" \
    /SourceConnectionString:"Server=myserver.database.windows.net;..."

# Import BACPAC to new database
sqlpackage /Action:Import \
    /SourceFile:"backup.bacpac" \
    /TargetConnectionString:"Server=myserver.database.windows.net;..."

# Extract schema to DACPAC (schema only)
sqlpackage /Action:Extract \
    /TargetFile:"schema.dacpac" \
    /SourceConnectionString:"Server=myserver.database.windows.net;..."

# Publish DACPAC (deploy schema changes)
sqlpackage /Action:Publish \
    /SourceFile:"schema.dacpac" \
    /TargetConnectionString:"Server=myserver.database.windows.net;..." \
    /p:BlockOnPossibleDataLoss=true

# Generate diff script (no deploy)
sqlpackage /Action:Script \
    /SourceFile:"schema.dacpac" \
    /TargetConnectionString:"Server=myserver.database.windows.net;..." \
    /OutputFile:"diff.sql"

# Drift report (compare live DB to DACPAC)
sqlpackage /Action:DeployReport \
    /SourceFile:"schema.dacpac" \
    /TargetConnectionString:"Server=myserver.database.windows.net;..." \
    /OutputFile:"report.xml"
```

### DACPAC vs BACPAC

| Feature | DACPAC | BACPAC |
| :--- | :--- | :--- |
| Contains | Schema only | Schema + data |
| Use case | CI/CD deployment | Backup / migration |
| Action: create | Extract | Export |
| Action: apply | Publish | Import |
| Incremental | Yes (diff-based) | No (full replace) |

---

## SQL Database Projects

```bash
# Build project (creates DACPAC)
dotnet build MyProject.sqlproj

# Publish to target
dotnet publish MyProject.sqlproj /p:TargetConnectionString="..."
```

### .sqlproj Key Properties

```xml
<Project Sdk="Microsoft.Build.Sql/0.2.0-preview">
  <PropertyGroup>
    <Name>MyProject</Name>
    <DSP>Microsoft.Data.Tools.Schema.Sql.SqlAzureV12DatabaseSchemaProvider</DSP>
    <ModelCollation>1033, CI</ModelCollation>
  </PropertyGroup>
</Project>
```

---

## Change Data Capture (CDC)

```sql
-- Enable CDC on database
EXEC sys.sp_cdc_enable_db;

-- Enable CDC on table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name = N'Orders',
    @role_name = N'cdc_reader';

-- Query changes
DECLARE @from_lsn BINARY(10) = sys.fn_cdc_get_min_lsn('dbo_Orders');
DECLARE @to_lsn   BINARY(10) = sys.fn_cdc_get_max_lsn();

SELECT * FROM cdc.fn_cdc_get_all_changes_dbo_Orders(
    @from_lsn, @to_lsn, 'all update old'
);

-- Net changes (latest state per row)
SELECT * FROM cdc.fn_cdc_get_net_changes_dbo_Orders(
    @from_lsn, @to_lsn, 'all'
);
```

| Operation Code (__$operation) | Meaning |
| :--- | :--- |
| 1 | Delete |
| 2 | Insert |
| 3 | Update (before) |
| 4 | Update (after) |

---

**[← Back to Cheat Sheets](./README.md)**
