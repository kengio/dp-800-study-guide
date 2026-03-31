---
title: Change and Event Handling
type: study-material
tags:
  - dp-800
  - cdc
  - change-tracking
  - azure-functions
  - ces
---

# Change and Event Handling

## Overview

Reacting to data changes is fundamental to building event-driven systems. SQL Server and Azure SQL offer several mechanisms at different granularities: **Change Tracking** (did a row change?), **CDC** (what did the row change from/to?), and **CES** (Change Event Streaming in Fabric — push-based streaming). These feed downstream systems via Azure Functions SQL trigger binding, Logic Apps, or direct streaming.

> [!abstract]
> - Covers Change Data Capture (CDC) and Change Tracking (CT): what changed, when, and how to consume it
> - CDC and CT both track data changes but differ in detail captured and infrastructure required
> - Key exam topics: CDC vs CT differences, CDC agent dependency, CT lightweight use cases

> [!tip] What the Exam Tests
> - **CDC**: captures full before/after row values; requires SQL Server Agent; stores changes in capture tables; used for ETL/replication
> - **Change Tracking**: captures only that a row changed (row ID + operation); no Agent required; used for sync scenarios where you only need to know *what* changed, not *how*
> - CDC has latency (agent job); CT is synchronous (committed with the transaction)

---

## Change Data Capture (CDC)

CDC captures row-level INSERT, UPDATE, and DELETE changes with before/after values. Changes are stored in system tables and can be queried.

### Enabling CDC

```sql
-- Enable CDC on the database
EXEC sys.sp_cdc_enable_db;

-- Verify
SELECT is_cdc_enabled FROM sys.databases WHERE name = DB_NAME();

-- Enable CDC on a specific table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'Orders',
    @role_name     = N'cdc_reader',  -- db_role that can read CDC tables; NULL = no role check
    @supports_net_changes = 1;       -- 1 = also capture net changes

-- Verify CDC-enabled tables
SELECT source_schema, source_name, capture_instance, has_drop_pending
FROM cdc.change_tables;
```

### Querying CDC Changes

CDC functions return the change records within an LSN (Log Sequence Number) range:

```sql
-- Get the current LSN range
DECLARE @from_lsn BINARY(10) = sys.fn_cdc_get_min_lsn('dbo_Orders');
DECLARE @to_lsn   BINARY(10) = sys.fn_cdc_get_max_lsn();

-- Query all changes (INSERT=2, UPDATE before=3, UPDATE after=4, DELETE=1)
SELECT
    sys.fn_cdc_map_lsn_to_time(__$start_lsn) AS ChangeTime,
    CASE __$operation
        WHEN 1 THEN 'DELETE'
        WHEN 2 THEN 'INSERT'
        WHEN 3 THEN 'UPDATE_BEFORE'
        WHEN 4 THEN 'UPDATE_AFTER'
    END AS Operation,
    OrderId,
    CustomerId,
    Status,
    TotalAmount
FROM cdc.fn_cdc_get_all_changes_dbo_Orders(@from_lsn, @to_lsn, 'all update old')
ORDER BY __$start_lsn;
```

```sql
-- Net changes (only the final state, even if a row was updated multiple times)
SELECT
    CASE __$operation
        WHEN 1 THEN 'DELETE'
        WHEN 5 THEN 'INSERT_OR_UPDATE'  -- net change combines updates
    END AS Operation,
    OrderId,
    Status
FROM cdc.fn_cdc_get_net_changes_dbo_Orders(@from_lsn, @to_lsn, 'all');
```

### LSN-Based Incremental Processing

```sql
-- Store the last processed LSN in a control table
CREATE TABLE dbo.CDCWatermark (
    TableName   NVARCHAR(100) PRIMARY KEY,
    LastLSN     BINARY(10)    NOT NULL
);

-- Insert initial watermark
INSERT INTO dbo.CDCWatermark VALUES ('dbo_Orders', sys.fn_cdc_get_min_lsn('dbo_Orders'));

-- Incremental processing pattern
DECLARE @last_lsn BINARY(10);
DECLARE @current_lsn BINARY(10) = sys.fn_cdc_get_max_lsn();

SELECT @last_lsn = LastLSN FROM dbo.CDCWatermark WHERE TableName = 'dbo_Orders';

-- Process only new changes since last run
SELECT * FROM cdc.fn_cdc_get_all_changes_dbo_Orders(@last_lsn, @current_lsn, 'all')
WHERE __$start_lsn > @last_lsn;  -- exclude the last processed LSN

-- Update watermark after successful processing
UPDATE dbo.CDCWatermark
SET LastLSN = @current_lsn
WHERE TableName = 'dbo_Orders';
```

---

## Change Tracking

**Change Tracking** is lighter weight than CDC — it only records which rows changed and in what direction, not the before/after values. Good for synchronization scenarios where you only need to know "what changed since my last sync."

### Enabling Change Tracking

```sql
-- Enable at database level
ALTER DATABASE MyDB SET CHANGE_TRACKING = ON
    (CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

-- Enable on specific table
ALTER TABLE dbo.Products
ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);

-- Verify
SELECT * FROM sys.change_tracking_databases;
SELECT * FROM sys.change_tracking_tables;
```

### Querying Change Tracking

```sql
-- Get initial synchronization version
DECLARE @sync_version BIGINT = CHANGE_TRACKING_CURRENT_VERSION();

-- ... (initial full load) ...

-- Later: get changes since @sync_version
SELECT
    ct.OrderId,
    ct.SYS_CHANGE_OPERATION,   -- I=Insert, U=Update, D=Delete
    ct.SYS_CHANGE_VERSION,
    o.Status,
    o.TotalAmount
FROM CHANGETABLE(CHANGES dbo.Orders, @sync_version) AS ct
LEFT JOIN dbo.Orders o ON o.OrderId = ct.OrderId  -- NULL for deletes
ORDER BY ct.SYS_CHANGE_VERSION;

-- Update the sync version after processing
SET @sync_version = CHANGE_TRACKING_CURRENT_VERSION();
```

**Change Tracking vs CDC:**

| Feature | Change Tracking | CDC |
| :--- | :--- | :--- |
| Before image (old values) | No | ==Yes== |
| After image (new values) | No (join to table) | Yes |
| Column-level granularity | Which columns (optional) | Full row |
| Storage overhead | Low | Medium |
| Retention | Configurable (days) | Until cleanup job runs |
| Use case | Sync, replication | Audit, ETL, streaming |

> [!warning] Common Mistake
> CDC and Change Tracking are often confused. CDC = captures the actual data values before and after change (heavier, requires Agent). CT = captures only that a change happened to a row (lightweight, no Agent). If the scenario requires knowing the old value of a column, the answer is CDC, not CT.

---

## Azure Functions SQL Trigger Binding

The Azure Functions SQL trigger binding monitors a SQL table and fires a function whenever rows are inserted, updated, or deleted. It uses Change Tracking internally.

### Function Definition (C#)

```csharp
// Triggered when dbo.Orders changes
[FunctionName("ProcessOrderChanges")]
public static async Task Run(
    [SqlTrigger("[dbo].[Orders]", "SqlConnectionString")]
    IReadOnlyList<SqlChange<Order>> changes,
    ILogger log)
{
    foreach (SqlChange<Order> change in changes)
    {
        Order order = change.Item;
        log.LogInformation($"Change: {change.Operation} OrderId={order.OrderId} Status={order.Status}");

        switch (change.Operation)
        {
            case SqlChangeOperation.Insert:
                await ProcessNewOrder(order);
                break;
            case SqlChangeOperation.Update:
                await ProcessOrderUpdate(order);
                break;
            case SqlChangeOperation.Delete:
                // order.OrderId is populated; other fields may be null
                await HandleOrderDeletion(order.OrderId);
                break;
        }
    }
}
```

### local.settings.json for SQL Trigger

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet",
    "SqlConnectionString": "Server=myserver.database.windows.net;Database=MyDB;Authentication=Active Directory Default;"
  }
}
```

The SQL trigger binding automatically enables Change Tracking on the target table and creates internal tracking infrastructure.

---

## Change Event Streaming (CES) in Microsoft Fabric

CES is a Fabric-native feature for SQL Database in Fabric that streams change events to downstream Fabric workloads (Eventstream, Lakehouse, Warehouse) without any polling or CDC configuration.

```text
SQL Database in Fabric → Change Event Streaming → Eventstream → Lakehouse / KQL Database

Setup in Fabric Portal:
1. SQL Database in Fabric → Settings → Change Event Streaming
2. Enable streaming for selected tables
3. Choose destination: Eventstream, Lakehouse, or KQL Database
4. Map columns and configure filters (optional)
```

CES works in near-real-time and delivers change events with:
- Table name, operation type (Insert/Update/Delete)
- Changed row values (after image)
- LSN and timestamp

---

## Azure Logic Apps for Change Handling

Logic Apps can poll for changes using a Recurrence trigger and a SQL connector:

```text
Logic App workflow:
├── Trigger: Recurrence (every 1 minute)
├── Action: SQL Server - Execute Stored Procedure
│         → dbo.GetUnprocessedChanges
│         (returns rows from a change queue table)
├── For Each: Process each changed row
│   ├── Action: Send email / HTTP POST / Service Bus message
│   └── Action: SQL Server - Execute Query (mark row as processed)
└── End
```

```sql
-- Change queue table pattern (used with Logic Apps polling)
CREATE TABLE dbo.ChangeQueue (
    ChangeId     INT          NOT NULL IDENTITY(1,1),
    TableName    NVARCHAR(100) NOT NULL,
    Operation    CHAR(1)      NOT NULL,  -- I, U, D
    RecordId     INT          NOT NULL,
    ChangedAt    DATETIME2    NOT NULL DEFAULT GETUTCDATE(),
    Processed    BIT          NOT NULL DEFAULT 0,
    ProcessedAt  DATETIME2    NULL
);

-- Trigger to populate the queue
CREATE TRIGGER trg_Orders_AfterInsertUpdate
ON dbo.Orders
AFTER INSERT, UPDATE
AS
BEGIN
    INSERT INTO dbo.ChangeQueue (TableName, Operation, RecordId)
    SELECT 'Orders',
           CASE WHEN EXISTS (SELECT 1 FROM deleted) THEN 'U' ELSE 'I' END,
           OrderId
    FROM inserted;
END;

-- Get unprocessed changes (called by Logic App)
CREATE OR ALTER PROCEDURE dbo.GetUnprocessedChanges
    @BatchSize INT = 100
AS
BEGIN
    WITH Batch AS (
        SELECT TOP (@BatchSize) ChangeId, TableName, Operation, RecordId, ChangedAt
        FROM dbo.ChangeQueue
        WHERE Processed = 0
        ORDER BY ChangeId
    )
    UPDATE Batch
    SET Processed = 1, ProcessedAt = GETUTCDATE()
    OUTPUT DELETED.ChangeId, DELETED.TableName, DELETED.Operation,
           DELETED.RecordId, DELETED.ChangedAt;
END;
```

---

## Use Cases

- **CDC for data warehouse ETL**: Capture all row changes for incremental loading into Synapse or Fabric Lakehouse
- **Change Tracking for mobile sync**: Sync only changed rows to mobile clients since their last connection
- **Azure Functions SQL trigger**: Real-time event processing — update a search index, send notifications, or trigger downstream workflows whenever orders change
- **CES in Fabric**: Stream SQL changes to Lakehouse for near-real-time analytics without infrastructure management
- **Logic Apps polling**: Low-code integration with change data for alerting and notification workflows

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| CDC capture job not running | SQL Agent not running (on-prem/MI) | ==Start SQL Agent; on Azure SQL, CDC cleanup runs automatically== |
| `@from_lsn` returns NULL | CDC not enabled or no data yet | Verify `sp_cdc_enable_db` and `sp_cdc_enable_table` ran successfully |
| Change Tracking retention exceeded | Sync version too old | Use `CHANGE_TRACKING_MIN_VALID_VERSION()` to validate; do full resync if needed |
| SQL trigger function not firing | Change Tracking not enabled | SQL trigger binding auto-enables it; check connection string permissions |
| CES not available | Not a Fabric SQL Database | CES is specific to SQL Database in Microsoft Fabric |

---

## Exam Tips

> [!tip] Exam Tips
> - **CDC**: Captures before AND after values; requires SQL Agent (on-prem) or runs automatically (Azure SQL)
> - **Change Tracking**: Only tracks that a row changed; no before image; lighter weight; requires join to get current values
> - **Azure Functions SQL trigger**: Uses Change Tracking under the hood — enables it automatically on the source table
> - **CES**: Fabric-native; no infrastructure setup required; pushes events rather than requiring polling
> - `SYS_CHANGE_OPERATION` values: `I` = Insert, `U` = Update, `D` = Delete
> - CDC `__$operation` values: `1` = Delete, `2` = Insert, `3` = Update (before), `4` = Update (after)

---

## Key Takeaways

- CDC provides full before/after audit trail; Change Tracking provides lightweight sync capability
- Azure Functions SQL trigger is the easiest way to react to SQL changes in real-time from application code
- CES in Fabric is the cloud-native zero-configuration approach for Fabric workloads
- LSN-based watermarking is the standard pattern for incremental CDC-based ETL

---

## Related Topics

- [03-Monitoring](./03-monitoring.md)
- [02-Embedding Maintenance](../09-models-embeddings/02-embedding-maintenance.md)
- [02-Transaction Isolation & Concurrency](../06-performance-optimization/02-transaction-isolation-concurrency.md)

---

## Official Documentation

- [CDC in SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-data-capture-sql-server)
- [Change Tracking](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-tracking-sql-server)
- [Azure Functions SQL Trigger Binding](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-azure-sql-trigger)
- [Fabric Change Event Streaming](https://learn.microsoft.com/en-us/fabric/database/sql/change-event-streaming)

---

**[← Previous](./03-monitoring.md) | [↑ Back to Section](./README.md)**
