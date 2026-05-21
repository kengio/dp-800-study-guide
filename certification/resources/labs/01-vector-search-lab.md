---
title: Vector Search Lab — VECTOR + DiskANN + ANN vs ENN
type: lab
tags:
  - dp-800
  - hands-on
  - lab
  - vector-search
  - diskann
  - ann
  - enn
status: complete
---

# Lab 01 — Vector Search with DiskANN

## Overview

A runnable walkthrough of the SQL Server 2025 / Azure SQL / Fabric SQL vector
search surface: the `VECTOR` data type, a DiskANN index, and a side-by-side
comparison of approximate (ANN) and exact (ENN) k-nearest-neighbour queries
against a small product catalogue.

> [!abstract]
>
> - Create a `Products` table with a `VECTOR(1536)` column and insert 12 sample rows
> - Build a DiskANN vector index with `CREATE VECTOR INDEX ... WITH (METRIC = 'cosine', TYPE = 'diskann')`
> - Run ANN queries with `SELECT TOP (N) ... WITH APPROXIMATE` and ENN queries without it, then compare the two result sets
> - Reproduce the DiskANN ==metric-mismatch== silent-fallback gotcha — the exam's favourite vector trap

> [!tip] What you'll do
>
> 1. Create the `Lab01_Products` database and seed 12 product rows with deterministic embeddings
> 2. Build a DiskANN vector index keyed on cosine distance
> 3. Inspect the index with `sys.indexes` and `VECTORPROPERTY`
> 4. Run an ANN query (`WITH APPROXIMATE`) and an ENN query (plain `ORDER BY`) and diff the rows
> 5. Force a metric mismatch and observe the silent fallback to exact kNN
> 6. Convert distance to similarity (`1 - cosine_distance`) and apply a threshold

## Prerequisites

- **SQL Server 2025 CU1+** with `PREVIEW_FEATURES = ON`, **Azure SQL Database** in a region with `VECTOR` enabled, or **SQL database in Microsoft Fabric**
- DiskANN vector index is **public preview** as of the March 2026 blueprint — fully testable on the exam, but flag enablement varies by surface
- A SQL login holding `db_owner` on the lab database (required to create vector indexes)
- 12 rows × 6 KB = ~72 KB of storage — fits anywhere

> [!warning] Preview surface
> If your engine errors on `CREATE VECTOR INDEX`, fall back to the legacy form
> `CREATE INDEX IX_... ON ... (col) USING DISKANN WITH (METRIC = 'cosine');`
> — both surfaces exist in the field today; the `CREATE VECTOR INDEX` form is
> the current documented syntax.

---

## Setup

```sql
-- Create the lab database
CREATE DATABASE Lab01_Products;
GO
USE Lab01_Products;
GO

-- Shared product catalogue used by Labs 1, 2, and 3.
-- Embedding dimensions = 1536 to match text-embedding-3-small.
CREATE TABLE dbo.Products (
    ProductId         INT            NOT NULL IDENTITY(1,1) PRIMARY KEY,
    ProductName       NVARCHAR(200)  NOT NULL,
    Category          NVARCHAR(100)  NOT NULL,
    Description       NVARCHAR(MAX)  NOT NULL,
    DescriptionVector VECTOR(1536)   NULL
);
GO

-- Insert 12 rows. Embeddings are placeholders — replace the VECTOR(1536) cast
-- with real embeddings from text-embedding-3-small in production.
-- For lab reproducibility we use a deterministic dummy vector built from the
-- product id, so the same query returns the same ranking on every run.
DECLARE @i INT = 1;
DECLARE @rows TABLE (Name NVARCHAR(200), Category NVARCHAR(100), Descr NVARCHAR(MAX));
INSERT INTO @rows (Name, Category, Descr) VALUES
('Wireless Noise-Cancelling Headphones', 'Audio',     'Over-ear Bluetooth headphones with active noise cancellation, 30 hour battery, ideal for long meetings.'),
('In-Ear Sport Earbuds',                 'Audio',     'Sweat-resistant wireless earbuds with secure fit, designed for running and the gym.'),
('Conference-Room Speakerphone',         'Audio',     '360-degree microphone array for hybrid meeting rooms, certified for Teams.'),
('Studio Monitor Headphones',            'Audio',     'Wired closed-back studio headphones with flat frequency response for mixing.'),
('Ultra-thin Mechanical Keyboard',       'Peripherals','Low-profile mechanical keyboard with hot-swappable switches and RGB lighting.'),
('Vertical Ergonomic Mouse',             'Peripherals','Vertical handshake-grip mouse that reduces wrist pronation during long coding sessions.'),
('USB-C Docking Station',                'Peripherals','Triple-display docking station with 100W power delivery and 2.5 Gb Ethernet.'),
('27-inch 4K Monitor',                   'Displays',  '27-inch IPS panel with USB-C input, 95% DCI-P3 colour coverage, and built-in KVM.'),
('Adjustable Standing Desk',             'Furniture', 'Electric sit-stand desk with memory presets and an anti-collision sensor.'),
('Ergonomic Mesh Office Chair',          'Furniture', 'Breathable mesh back with lumbar support, 4D armrests, and forward-tilt seat.'),
('USB-A Webcam 1080p',                   'Video',     'Plug-and-play 1080p webcam with stereo mics and a privacy shutter.'),
('External SSD 2 TB',                    'Storage',   'USB-C portable SSD, 1050 MB/s read, fits in a coin pocket.');

INSERT INTO dbo.Products (ProductName, Category, Description)
SELECT Name, Category, Descr FROM @rows;
GO

-- Deterministic dummy embeddings — build a 1536-dim JSON array from each ProductId.
-- In real life you would call PREDICT(MODEL = [your-embedding-model], DATA = ...).
WITH Vals AS (
    SELECT
        p.ProductId,
        '[' + STRING_AGG(CAST(ROUND(SIN(p.ProductId * 0.13 + n.n * 0.007), 5) AS NVARCHAR(20)), ',')
            WITHIN GROUP (ORDER BY n.n) + ']' AS json_vec
    FROM dbo.Products p
    CROSS JOIN (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) n
    GROUP BY p.ProductId
)
UPDATE p
SET p.DescriptionVector = CAST(v.json_vec AS VECTOR(1536))
FROM dbo.Products p
JOIN Vals v ON v.ProductId = p.ProductId;
GO

-- Sanity check
SELECT TOP 3 ProductId, ProductName,
       VECTORPROPERTY(DescriptionVector, 'Dimensions') AS Dims
FROM dbo.Products
ORDER BY ProductId;
GO
```

**Expected output**

| ProductId | ProductName                          | Dims |
| :-------- | :----------------------------------- | :--- |
| 1         | Wireless Noise-Cancelling Headphones | 1536 |
| 2         | In-Ear Sport Earbuds                 | 1536 |
| 3         | Conference-Room Speakerphone         | 1536 |

> [!note] Replace dummy vectors in production
> The deterministic sine-based vectors give the lab a reproducible ranking, but
> they are not semantically meaningful. Swap to real embeddings (Lab 2 shows
> the `PREDICT` / `sp_invoke_external_rest_endpoint` pattern) before drawing
> conclusions about relevance.

---

## Steps

### Step 1: Create a DiskANN vector index keyed on cosine

DiskANN is the only vector index type supported in the current preview. The
index `METRIC` is sticky — queries that pass a different metric silently fall
back to exact kNN. Build the index for the metric you actually plan to query.

```sql
CREATE VECTOR INDEX IX_Products_DescriptionVector
ON dbo.Products (DescriptionVector)
WITH (METRIC = 'cosine', TYPE = 'diskann');
GO

-- Verify
SELECT name, type_desc, is_disabled
FROM sys.indexes
WHERE object_id = OBJECT_ID('dbo.Products')
  AND name = 'IX_Products_DescriptionVector';
```

**Expected output**

| name                            | type_desc | is_disabled |
| :------------------------------ | :-------- | :---------- |
| IX_Products_DescriptionVector   | VECTOR    | 0           |

**Why this matters** — the DP-800 blueprint lists DiskANN as a named feature in
the "implement vector search" objective. Knowing the syntax and that `METRIC`
is index-level (not query-level) is the most-tested vector indexing detail.

---

### Step 2: Run an exact-kNN (ENN) baseline

Plain `ORDER BY VECTOR_DISTANCE(...)` without `WITH APPROXIMATE` always
performs an exact scan. Use it as the ground-truth comparison for ANN.

```sql
-- Query vector built the same deterministic way as ProductId = 1's vector,
-- shifted by 0.001 so it is not literally identical.
DECLARE @q VECTOR(1536) = (
    SELECT CAST(
        '[' + STRING_AGG(CAST(ROUND(SIN(1 * 0.13 + n * 0.007) + 0.001, 5) AS NVARCHAR(20)), ',')
              WITHIN GROUP (ORDER BY n) + ']' AS VECTOR(1536))
    FROM (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) AS s
);

SELECT TOP (5)
    ProductId, ProductName, Category,
    VECTOR_DISTANCE('cosine', DescriptionVector, @q) AS CosineDistance
FROM dbo.Products
WHERE DescriptionVector IS NOT NULL
ORDER BY VECTOR_DISTANCE('cosine', DescriptionVector, @q) ASC;
```

**Expected output** (distances will vary slightly; ordering is stable)

```text
ProductId  ProductName                            CosineDistance
---------  -------------------------------------  --------------
1          Wireless Noise-Cancelling Headphones   0.0000xx
2          In-Ear Sport Earbuds                   0.0001xx
3          Conference-Room Speakerphone           0.0003xx
4          Studio Monitor Headphones              0.0007xx
5          Ultra-thin Mechanical Keyboard         0.0013xx
```

**Why this matters** — ENN is what `VECTOR_DISTANCE` in `ORDER BY` always does.
The exam tests the distinction between this and ANN, and which clause forces
which path.

---

### Step 3: Run an ANN query with `WITH APPROXIMATE`

Add `WITH APPROXIMATE` to the same query. On a matching DiskANN index, the
optimizer uses the index and returns approximate results — much faster on
large tables.

```sql
DECLARE @q VECTOR(1536) = (
    SELECT CAST(
        '[' + STRING_AGG(CAST(ROUND(SIN(1 * 0.13 + n * 0.007) + 0.001, 5) AS NVARCHAR(20)), ',')
              WITHIN GROUP (ORDER BY n) + ']' AS VECTOR(1536))
    FROM (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) AS s
);

SELECT TOP (5)
    ProductId, ProductName, Category,
    VECTOR_DISTANCE('cosine', DescriptionVector, @q) AS CosineDistance
FROM dbo.Products
WHERE DescriptionVector IS NOT NULL
ORDER BY VECTOR_DISTANCE('cosine', DescriptionVector, @q) ASC
WITH APPROXIMATE;
```

**Expected output** — on 12 rows ANN and ENN return the same set; on a million
rows ANN may skip one of the close neighbours. Confirm the plan uses the
DiskANN index:

```sql
SET STATISTICS PROFILE ON;
-- re-run the query above
SET STATISTICS PROFILE OFF;
-- Look for "Index Scan" on IX_Products_DescriptionVector with operator label "Vector Index Scan"
```

**Why this matters** — `WITH APPROXIMATE` is the current ANN clause. The legacy
`VECTOR_SEARCH(...) TVF` raises `Msg 42274` on the newest index versions, so
the exam now tests this syntax exclusively.

---

### Step 4: Reproduce the metric-mismatch silent fallback

The DiskANN index in Step 1 was built with `METRIC = 'cosine'`. Issue a query
that asks for `'euclidean'`. The engine does **not** error — it logs a warning
to `sys.dm_exec_query_diagnostics` and silently runs an exact kNN.

```sql
-- Same query, but asking for euclidean distance on a cosine-only index
DECLARE @q VECTOR(1536) = (
    SELECT CAST(
        '[' + STRING_AGG(CAST(ROUND(SIN(1 * 0.13 + n * 0.007) + 0.001, 5) AS NVARCHAR(20)), ',')
              WITHIN GROUP (ORDER BY n) + ']' AS VECTOR(1536))
    FROM (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) AS s
);

SELECT TOP (5)
    ProductId, ProductName,
    VECTOR_DISTANCE('euclidean', DescriptionVector, @q) AS EuclideanDistance
FROM dbo.Products
WHERE DescriptionVector IS NOT NULL
ORDER BY VECTOR_DISTANCE('euclidean', DescriptionVector, @q) ASC
WITH APPROXIMATE;  -- ignored; engine falls back to exact scan
```

**Expected output**

```text
ProductId  ProductName                            EuclideanDistance
---------  -------------------------------------  -----------------
1          Wireless Noise-Cancelling Headphones    0.038xx
2          In-Ear Sport Earbuds                    0.041xx
3          Conference-Room Speakerphone            0.045xx
...
-- Warning in query log: "Vector index not used; metric mismatch."
```

**Why this matters** — silent fallback is the exam's favourite DiskANN trap.
Symptoms: ANN-shaped query, ENN-shaped latency. To support multiple metrics,
build one DiskANN index per metric.

---

### Step 5: Convert distance to similarity and threshold

Distances are inconvenient for product surfaces (lower = better, no obvious
floor). Convert to a similarity score and filter rows above a threshold.

```sql
DECLARE @q VECTOR(1536) = (
    SELECT CAST(
        '[' + STRING_AGG(CAST(ROUND(SIN(1 * 0.13 + n * 0.007) + 0.001, 5) AS NVARCHAR(20)), ',')
              WITHIN GROUP (ORDER BY n) + ']' AS VECTOR(1536))
    FROM (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) AS s
);

SELECT TOP (10)
    ProductId, ProductName, Category,
    1.0 - VECTOR_DISTANCE('cosine', DescriptionVector, @q) AS CosineSimilarity
FROM dbo.Products
WHERE DescriptionVector IS NOT NULL
  AND 1.0 - VECTOR_DISTANCE('cosine', DescriptionVector, @q) >= 0.95
ORDER BY 1.0 - VECTOR_DISTANCE('cosine', DescriptionVector, @q) DESC
WITH APPROXIMATE;
```

**Expected output**

| ProductId | ProductName                          | Category    | CosineSimilarity |
| :-------- | :----------------------------------- | :---------- | :--------------- |
| 1         | Wireless Noise-Cancelling Headphones | Audio       | 0.999xx          |
| 2         | In-Ear Sport Earbuds                 | Audio       | 0.999xx          |
| 3         | Conference-Room Speakerphone         | Audio       | 0.999xx          |

**Why this matters** — the exam tests the conversion `similarity = 1 - cosine_distance`
and the fact that `VECTOR_DISTANCE` returns a distance, not a similarity.

---

### Step 6: Inspect vector properties

Useful for ad-hoc checks (and for confirming that `VECTOR_NORMALIZE` actually
ran when you wired up dot-product retrieval).

```sql
SELECT TOP 1
    ProductId,
    VECTORPROPERTY(DescriptionVector, 'Dimensions')   AS Dims,
    VECTORPROPERTY(DescriptionVector, 'BaseType')     AS BaseType
FROM dbo.Products
ORDER BY ProductId;
```

**Expected output**

| ProductId | Dims | BaseType |
| :-------- | :--- | :------- |
| 1         | 1536 | float32  |

**Why this matters** — `VECTORPROPERTY` is the canonical way to verify a
column's storage layout. Watch for `BaseType = float16` once half-precision
vectors leave preview — same dimensions, half the storage.

---

## Cleanup

```sql
USE master;
GO
DROP DATABASE IF EXISTS Lab01_Products;
GO
```

If you plan to run Labs 2 or 3 next, **skip the DROP** — those labs build on
the `dbo.Products` table you just populated.

---

## Common Issues & Errors

| Error / symptom | Cause | Fix |
| :--- | :--- | :--- |
| `Msg 42274 — VECTOR_SEARCH TVF is not supported on the current index version` | Using the legacy table-valued function against a new-style DiskANN index | Switch to `SELECT TOP (N) ... ORDER BY VECTOR_DISTANCE(...) WITH APPROXIMATE` |
| ANN query has ENN latency (slow on large tables) | DiskANN metric mismatch — index built for one metric, query asks for another | Drop and recreate the index for the metric you actually query, or build one index per metric |
| `Msg 49981 — VECTOR data type is not supported` | `PREVIEW_FEATURES` not enabled (SQL Server 2025) or region without VECTOR (Azure SQL) | `EXEC sp_configure 'preview features', 1; RECONFIGURE;` or move database |
| `Msg 41750 — Vector dimension mismatch` | Query vector dimension ≠ column dimension | Always cast to the same `VECTOR(N)` as the column. Embeddings from `text-embedding-3-large` need `VECTOR(3072)`, not `VECTOR(1536)` |
| `Cannot create vector index — column is nullable and contains NULL rows` | `CREATE VECTOR INDEX` requires non-null vectors | Either backfill all rows before creating the index, or filter and rebuild after |

---

## Exam Tips

> [!tip] Exam Tips
>
> - `WITH APPROXIMATE` is the current ANN clause. The legacy `VECTOR_SEARCH(... TOP_N=N)` TVF is being retired and raises `Msg 42274` on new indexes
> - The DiskANN `METRIC` is index-level. To support multiple metrics, build multiple indexes — there is no "default metric" that adapts
> - Metric mismatch is **silent** — query still returns rows, just from an exact scan. Look for the warning event, not an error
> - `VECTOR_DISTANCE` returns a distance (lower = closer); compute `1 - cosine_distance` when the UI needs a similarity score
> - DiskANN is **public preview** in SQL Server 2025 and Azure SQL as of the March 2026 blueprint — still fully testable on the exam

---

## Key Takeaways

- `VECTOR(N)` stores the embedding inline; `VECTORPROPERTY` and `VECTOR_NORMALIZE` are the inspection / preparation primitives
- `CREATE VECTOR INDEX ... WITH (METRIC = 'cosine', TYPE = 'diskann')` is the current syntax; the index metric must match query metric
- `WITH APPROXIMATE` → ANN via DiskANN; plain `ORDER BY VECTOR_DISTANCE` → ENN exact scan
- Silent fallback on metric mismatch is the most common production performance regression — and a frequent exam trap

---

## Related Topics

- [02-Vector Search](../../10-intelligent-search/02-vector-search.md)
- [03-Hybrid Search & RRF](../../10-intelligent-search/03-hybrid-search-rrf.md)
- [Vector Search Patterns](../code-examples/tsql/vector-search-patterns.md)
- [End-to-End RAG Walkthrough](../code-examples/tsql/rag-end-to-end-walkthrough.md)

---

## Official Documentation

- <https://learn.microsoft.com/en-us/sql/t-sql/data-types/vector-data-type>
- <https://learn.microsoft.com/en-us/sql/t-sql/functions/vector-distance-transact-sql>
- <https://learn.microsoft.com/en-us/azure/azure-sql/database/vector-index>
- <https://learn.microsoft.com/en-us/sql/t-sql/functions/vectorproperty-transact-sql>

---

**[← Back to lab index](./labs.md) | [↑ Back to overview](../../dp-800-overview.md)**
