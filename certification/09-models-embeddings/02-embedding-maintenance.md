---
title: Embedding Maintenance
type: study-material
tags:
  - dp-800
  - embeddings
  - change-tracking
  - embedding-maintenance
---

# Embedding Maintenance

## Overview

Embeddings stored in a vector column go stale when the source text changes. Maintaining embeddings means detecting when source data changes, re-generating embeddings for affected rows, and updating the vector column. Several approaches exist — each with different tradeoffs in complexity, latency, cost, and infrastructure requirements.

## Embedding Maintenance Methods Comparison

| Method | Latency | Complexity | Infrastructure | Best For |
| :--- | :--- | :--- | :--- | :--- |
| Table Triggers | Near real-time | Low | None (in-DB) | Small tables, low write volume |
| Change Tracking | Low (polling) | Medium | SQL Agent or scheduler | Moderate volume, batch-friendly |
| CDC | Medium (polling) | Medium | SQL Agent (on-prem) | Audit trail needed with embeddings |
| CES (Fabric) | Near real-time | Low | Fabric only | Fabric SQL, cloud-native |
| Azure Functions SQL Trigger | Near real-time | Medium | Azure Functions | Any Azure SQL, event-driven |
| Azure Logic Apps | Minutes | Low | Logic Apps | Low-code, low-volume |
| Microsoft Foundry | Configurable | Low | Fabric/Foundry | Declarative AI pipeline |

## Method 1: Table Triggers

Triggers fire synchronously on INSERT/UPDATE, calling the embedding model immediately.

```sql
-- Requires an external model already registered
-- CREATE EXTERNAL MODEL [MyEmbeddingModel] ...

CREATE OR ALTER TRIGGER trg_Products_EmbedDescription
ON dbo.Products
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Only regenerate if the Description actually changed
    IF UPDATE(Description)
    BEGIN
        UPDATE p
        SET DescriptionEmbedding = CAST(
            PREDICT(MODEL = [MyEmbeddingModel],
                    DATA = (SELECT i.Description AS input_text)) AS VECTOR(1536))
        FROM dbo.Products p
        INNER JOIN inserted i ON p.ProductId = i.ProductId;
    END;
END;
```

**Tradeoffs:**
- Simple — no external infrastructure
- Adds latency to every INSERT/UPDATE (synchronous API call)
- If the AI endpoint is unavailable, the write transaction fails
- Not suitable for high-volume write tables (each row = one API call)

## Method 2: Change Tracking (Batch Polling)

Change Tracking records which rows changed; a background job re-embeds them in batches.

```sql
-- Enable Change Tracking on the database and table
ALTER DATABASE MyDB SET CHANGE_TRACKING = ON
    (CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

ALTER TABLE dbo.Products
ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);

-- Watermark table
CREATE TABLE dbo.EmbeddingWatermark (
    TableName    NVARCHAR(100) PRIMARY KEY,
    SyncVersion  BIGINT NOT NULL
);
INSERT INTO dbo.EmbeddingWatermark VALUES ('Products', CHANGE_TRACKING_CURRENT_VERSION());
```

```sql
-- Embedding maintenance job (runs on a schedule via SQL Agent or App Service)
DECLARE @last_version BIGINT;
SELECT @last_version = SyncVersion FROM dbo.EmbeddingWatermark WHERE TableName = 'Products';

-- Find products whose Description changed since last run
UPDATE p
SET DescriptionEmbedding = CAST(
    PREDICT(MODEL = [MyEmbeddingModel],
            DATA = (SELECT p2.Description AS input_text)) AS VECTOR(1536))
FROM dbo.Products p
INNER JOIN CHANGETABLE(CHANGES dbo.Products, @last_version) AS ct
    ON p.ProductId = ct.ProductId
CROSS APPLY (SELECT p.Description) p2(Description)
WHERE ct.SYS_CHANGE_COLUMNS IS NULL  -- all columns changed (no column tracking)
   OR CHANGE_TRACKING_IS_COLUMN_IN_MASK(
        COLUMNPROPERTY(OBJECT_ID('dbo.Products'), 'Description', 'ColumnId'),
        ct.SYS_CHANGE_COLUMNS) = 1;  -- specifically Description changed

-- Update watermark
UPDATE dbo.EmbeddingWatermark
SET SyncVersion = CHANGE_TRACKING_CURRENT_VERSION()
WHERE TableName = 'Products';
```

**Tradeoffs:**
- Decouples write performance from embedding generation
- Latency = polling interval (seconds to minutes)
- Resilient to AI endpoint failures (retry at next poll)
- Requires a scheduler (SQL Agent, Azure Automation, App Service WebJob)

## Method 3: CDC (Change Data Capture)

CDC captures before/after values; useful when you need to know what changed before updating the embedding.

```sql
-- After enabling CDC on the database and Products table...
DECLARE @from_lsn BINARY(10);
DECLARE @to_lsn   BINARY(10) = sys.fn_cdc_get_max_lsn();

SELECT @from_lsn = LastLSN FROM dbo.EmbeddingCDCWatermark WHERE TableName = 'dbo_Products';

-- Get only changed rows (net changes — final state)
WITH ChangedProducts AS (
    SELECT ProductId
    FROM cdc.fn_cdc_get_net_changes_dbo_Products(@from_lsn, @to_lsn, 'all')
    WHERE __$operation IN (2, 5)  -- INSERT or INSERT_OR_UPDATE
)
UPDATE p
SET DescriptionEmbedding = CAST(
    PREDICT(MODEL = [MyEmbeddingModel],
            DATA = (SELECT p.Description AS input_text)) AS VECTOR(1536))
FROM dbo.Products p
INNER JOIN ChangedProducts cp ON p.ProductId = cp.ProductId;

-- Update CDC watermark
UPDATE dbo.EmbeddingCDCWatermark
SET LastLSN = @to_lsn
WHERE TableName = 'dbo_Products';
```

## Method 4: Azure Functions with SQL Trigger Binding

Azure Functions can listen for table changes and call the OpenAI API to regenerate embeddings asynchronously.

```csharp
[FunctionName("UpdateProductEmbeddings")]
public static async Task Run(
    [SqlTrigger("[dbo].[Products]", "SqlConnectionString")]
    IReadOnlyList<SqlChange<Product>> changes,
    [Sql("[dbo].[Products]", "SqlConnectionString")] IAsyncCollector<Product> productsOut,
    ILogger log)
{
    var openAiClient = new OpenAIClient(new Uri(openAiEndpoint), new AzureKeyCredential(apiKey));

    foreach (var change in changes.Where(c =>
        c.Operation == SqlChangeOperation.Insert || c.Operation == SqlChangeOperation.Update))
    {
        if (change.Item.Description == null) continue;

        var embeddings = await openAiClient.GetEmbeddingsAsync(
            new EmbeddingsOptions("text-embedding-3-small", new[] { change.Item.Description }));

        var updatedProduct = change.Item with
        {
            DescriptionEmbedding = embeddings.Value.Data[0].Embedding.ToArray()
        };

        // Write updated embedding back to SQL
        await productsOut.AddAsync(updatedProduct);
    }
}
```

**Tradeoffs:**
- Event-driven — near real-time with minimal polling overhead
- Infrastructure: requires Azure Functions deployment and configuration
- Resilient: Azure Functions handles retries on failure
- Can process changes in batches (multiple rows per trigger invocation)

## Method 5: CES (Change Event Streaming — Fabric)

In Fabric SQL Database, CES streams changes to an Eventstream, which triggers a Data Pipeline or Notebook to re-generate embeddings.

```text
Fabric SQL DB (Products table)
    → CES (Change Event Streaming)
        → Fabric Eventstream
            → Fabric Notebook (Python)
                → Azure OpenAI: generate embedding
                → Write back to SQL Database
```

```python
# Fabric Notebook: process CES events and update embeddings
import openai
import pyodbc

for event in eventstream_batch:
    product_id = event["ProductId"]
    description = event["Description"]

    # Generate embedding
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=description
    )
    embedding = response.data[0].embedding  # list of 1536 floats

    # Update the SQL Database
    cursor.execute(
        "UPDATE dbo.Products SET DescriptionEmbedding = ? WHERE ProductId = ?",
        (str(embedding), product_id)
    )
```

## Method 6: Azure Logic Apps

Logic Apps polls for changes on a schedule and calls the embedding API via an HTTP action.

```text
Logic App:
├── Trigger: Recurrence (every 5 minutes)
├── Action: SQL - Execute Stored Procedure → dbo.GetProductsNeedingEmbedding
├── For Each (products):
│   ├── Action: HTTP POST to Azure OpenAI embeddings endpoint
│   └── Action: SQL - Execute Query → UPDATE dbo.Products SET Embedding = ?
└── End
```

```sql
-- Stored procedure to find products needing embedding refresh
CREATE OR ALTER PROCEDURE dbo.GetProductsNeedingEmbedding
    @BatchSize INT = 50
AS
BEGIN
    SELECT TOP (@BatchSize)
        ProductId,
        Description
    FROM dbo.Products
    WHERE DescriptionEmbedding IS NULL
       OR DescriptionLastUpdated > EmbeddingGeneratedAt
    ORDER BY DescriptionLastUpdated ASC;
END;
```

## Method 7: Microsoft Foundry

Microsoft Foundry (AI Studio/AI Foundry in Fabric) provides a declarative AI pipeline:

```text
Foundry Data Pipeline:
├── Source: SQL Database table (Products)
├── Step: Embed column (Description) using text-embedding-3-small
├── Sink: SQL Database table (update DescriptionEmbedding column)
└── Trigger: Scheduled or event-based
```

This is the most managed option — no code required, built-in retry and monitoring.

## Choosing an Approach

```text
Decision tree:

High write volume (> 1000 rows/min)?
├── YES → Batch approach: Change Tracking or CDC
└── NO → Continue...

Fabric SQL Database?
├── YES → CES (simplest cloud-native option)
└── NO → Continue...

Real-time latency required (< 30 seconds)?
├── YES → Azure Functions SQL trigger
└── NO → Continue...

Prefer no-code/low-code?
├── YES → Logic Apps or Foundry
└── NO → Change Tracking with SQL Agent job
```

## Use Cases

- **Product catalog**: New products or description updates trigger embedding regeneration via Azure Functions
- **Document library**: Daily batch job using Change Tracking re-embeds documents modified since last run
- **Fabric data platform**: CES-driven pipeline automatically keeps Lakehouse embeddings in sync with SQL source

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| Trigger causes timeouts on bulk loads | Trigger fires per-row for large imports | Disable trigger during bulk load; use batch re-embedding afterward |
| Change Tracking min version exceeded | Sync version older than retention period | Do a full re-embed of all rows; reset watermark |
| Embedding drift undetected | Source text updated without regenerating embedding | Add `EmbeddingGeneratedAt` column and compare to `UpdatedAt` |
| Azure Functions not firing | Change Tracking not enabled on table | SQL trigger binding auto-enables CT; verify `db_owner` permission |

## Exam Tips

- **Triggers**: Simplest but synchronous — adds AI API latency to every write; risky if endpoint is down
- **Change Tracking**: Best for batch scenarios — decouple embedding from write path
- **Azure Functions SQL trigger**: Event-driven alternative to polling — uses Change Tracking internally
- **CES**: Fabric-native, zero-infrastructure — only available in SQL Database in Fabric
- Always maintain a watermark (version or timestamp) to know which rows have been embedded

## Key Takeaways

- No single embedding maintenance method suits all scenarios — choose based on volume, latency, and infrastructure
- Synchronous approaches (triggers) have simplicity but risk tightly coupling writes to AI API availability
- Asynchronous batch approaches (Change Tracking, CDC) are more resilient but have higher embedding latency
- CES is the preferred Fabric-native approach when using SQL Database in Fabric

## Related Topics

- [01-External Models](./01-external-models.md)
- [03-Chunking & Generation](./03-chunking-generation.md)
- [04-Change & Event Handling](../08-azure-services-integration/04-change-event-handling.md)

## Official Documentation

- [Azure Functions SQL Trigger](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-azure-sql-trigger)
- [Change Tracking](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-tracking-sql-server)
- [Fabric Change Event Streaming](https://learn.microsoft.com/en-us/fabric/database/sql/change-event-streaming)

---

**[← Previous](./01-external-models.md) | [↑ Back to Section](./README.md) | [Next →](./03-chunking-generation.md)**
