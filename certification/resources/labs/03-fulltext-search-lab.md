---
title: Full-Text + Hybrid Search Lab
type: lab
tags:
  - dp-800
  - hands-on
  - lab
  - full-text-search
  - hybrid-search
  - rrf
status: complete
---

# Lab 03 — Full-Text Search and Hybrid Retrieval with RRF

## Overview

Stand up a full-text catalogue and index on the shared product catalogue from
Lab 1, run the four classic FTS predicates (`CONTAINS`, `FREETEXT`,
`CONTAINSTABLE`, `FREETEXTTABLE`), and then fuse the FTS results with the
vector results from Lab 1 using Reciprocal Rank Fusion (RRF).

> [!abstract]
>
> - Set up a full-text catalog and index over `dbo.Products` (Description + ProductName)
> - Run `CONTAINS`, `FREETEXT`, `CONTAINSTABLE`, `FREETEXTTABLE` queries and inspect the `RANK` column
> - Combine vector and full-text ranked lists into a single ranked result with the canonical RRF formula `score = SUM(1 / (k + rank))`
> - See ==when hybrid beats vector-only==: queries with rare technical terms (model numbers, brand names) where keywords matter

> [!tip] What you'll do
>
> 1. Reuse the `Lab01_Products` database and `dbo.Products` table
> 2. Create a full-text catalog and an index on `(ProductName, Description)`
> 3. Run `CONTAINS` and `FREETEXT` to see precision-vs-recall behaviour
> 4. Use `CONTAINSTABLE` and `FREETEXTTABLE` to get the `RANK` score
> 5. Combine vector + FTS results with RRF
> 6. Compare the three ranked lists (vector, FTS, hybrid) side-by-side

## Prerequisites

- **Lab 01** completed — this lab depends on the `dbo.Products` table created in Lab 1 (12 rows with `VECTOR(1536)` embeddings and the DiskANN index)
- A SQL engine that supports **Full-Text Search**:
  - SQL Server 2025 — included by default
  - Azure SQL Database — included on all service tiers except Hyperscale named-replica
  - SQL database in Microsoft Fabric — FTS is **public preview** as of the March 2026 blueprint; check the Fabric admin portal
- The user must hold `CREATE FULLTEXT CATALOG` permission (granted via `db_owner`)

---

## Setup

The lab assumes you still have `Lab01_Products` with `dbo.Products`. If not,
rerun Lab 1's Setup block first.

```sql
USE Lab01_Products;
GO

-- Verify the prerequisite table is there
SELECT COUNT(*) AS Products, AVG(LEN(Description)) AS AvgDescLen
FROM dbo.Products;
```

**Expected output**

| Products | AvgDescLen |
| :------- | :--------- |
| 12       | 90 (approx.) |

---

## Steps

### Step 1: Create the full-text catalog and index

A full-text index needs (a) a catalog, (b) a unique single-column key index
(usually the PK), and (c) at least one column to index. `LANGUAGE 1033` =
English.

```sql
-- Catalog (logical container)
CREATE FULLTEXT CATALOG ProductFTSCatalog AS DEFAULT;
GO

-- Index ProductName + Description, keyed off the PK on ProductId
CREATE FULLTEXT INDEX ON dbo.Products (
    ProductName LANGUAGE 1033,
    Description LANGUAGE 1033
)
KEY INDEX PK__Products__B40CC6CD  -- replace with your actual PK name
ON ProductFTSCatalog
WITH (CHANGE_TRACKING = AUTO,
      STOPLIST        = SYSTEM);
GO

-- Find the real PK name if the placeholder above does not match
-- SELECT name FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.Products') AND is_primary_key = 1;

-- Wait for the index to populate
WAITFOR DELAY '00:00:05';

SELECT FULLTEXTCATALOGPROPERTY('ProductFTSCatalog', 'PopulateStatus') AS Status;
-- 0 = Idle (populated)
```

**Expected output**

| Status |
| :----- |
| 0      |

> [!warning] PK name
> The PK name in `KEY INDEX` must match the actual primary key. The `IDENTITY`
> column in Lab 1 gives the PK an auto-generated name like
> `PK__Products__B40CC6CD`. Run the commented `SELECT` to discover yours.

**Why this matters** — the exam tests the three-part FTS prerequisite
(catalog, key index, and the full-text index itself) plus the
`CHANGE_TRACKING` options that keep the index current.

---

### Step 2: `CONTAINS` — precision search

`CONTAINS` is the precise predicate: exact terms, prefix wildcards, phrases,
Boolean operators, and `NEAR()` proximity.

```sql
-- Exact word
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, 'wireless');

-- Prefix wildcard — finds wireless, wireless-charging, wirelessly, ...
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, '"wire*"');

-- Phrase
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS(Description, '"noise cancellation"');

-- Boolean AND across both indexed columns
SELECT ProductId, ProductName
FROM dbo.Products
WHERE CONTAINS((ProductName, Description), 'wireless AND headphones');
```

**Expected output** (Boolean AND query)

| ProductId | ProductName                          |
| :-------- | :----------------------------------- |
| 1         | Wireless Noise-Cancelling Headphones |

**Why this matters** — `CONTAINS` returns a Boolean; it does not give you a
relevance score. Use it when you want a hard filter.

---

### Step 3: `FREETEXT` — natural-language search

`FREETEXT` tokenises the query, removes stop words, expands inflectional forms,
and ORs them together. Use it when the user types something conversational.

```sql
-- A natural-language style query
SELECT ProductId, ProductName, Category
FROM dbo.Products
WHERE FREETEXT(Description, 'something I can use for long video meetings');
```

**Expected output**

| ProductId | ProductName                          | Category    |
| :-------- | :----------------------------------- | :---------- |
| 1         | Wireless Noise-Cancelling Headphones | Audio       |
| 3         | Conference-Room Speakerphone         | Audio       |
| 11        | USB-A Webcam 1080p                   | Video       |

**Why this matters** — `FREETEXT` is broader-recall than `CONTAINS`. The exam
tests when to pick precision (`CONTAINS`) vs recall (`FREETEXT`).

---

### Step 4: `CONTAINSTABLE` and `FREETEXTTABLE` — ranked results

The `*TABLE` variants return a `[KEY]` column (matching your key index value)
and a `[RANK]` column (1–1000, higher = better). You join back to the source
table to project the data you actually want.

```sql
-- CONTAINSTABLE — Boolean grammar, with ranks
SELECT
    p.ProductId,
    p.ProductName,
    ct.[RANK] AS FtsRank
FROM CONTAINSTABLE(dbo.Products, (ProductName, Description),
                   'headphones OR earbuds OR "noise cancellation"') AS ct
JOIN dbo.Products p ON p.ProductId = ct.[KEY]
ORDER BY ct.[RANK] DESC;

-- FREETEXTTABLE — natural-language grammar, with ranks, capped to 5 rows
SELECT
    p.ProductId,
    p.ProductName,
    ftt.[RANK] AS FtsRank
FROM FREETEXTTABLE(dbo.Products, (ProductName, Description),
                   'comfortable audio for long meetings',
                   LANGUAGE 1033, 5) AS ftt
JOIN dbo.Products p ON p.ProductId = ftt.[KEY]
ORDER BY ftt.[RANK] DESC;
```

**Expected output** (`CONTAINSTABLE`)

| ProductId | ProductName                          | FtsRank |
| :-------- | :----------------------------------- | :------ |
| 1         | Wireless Noise-Cancelling Headphones | 96      |
| 2         | In-Ear Sport Earbuds                 | 64      |
| 4         | Studio Monitor Headphones            | 48      |
| 3         | Conference-Room Speakerphone         | 32      |

**Why this matters** — RRF needs ranks, not raw scores. `CONTAINSTABLE` and
`FREETEXTTABLE` give you the row position you can pass into `ROW_NUMBER()`.

---

### Step 5: Hybrid retrieval with Reciprocal Rank Fusion

RRF merges two ranked lists by summing `1 / (k + rank)` for each document
across both lists. `k = 60` is the canonical constant (it dampens the
influence of the top rank so a strong second-place finish in both lists beats
a single first-place finish in one list).

**RRF formula:** `score = SUM(1 / (k + rank))` summed over each retrieval leg.

```sql
DECLARE @question NVARCHAR(MAX) =
    N'noise cancelling headphones for video meetings';

-- Compute the query embedding the same way Lab 2 did (deterministic stub here
-- so the lab is reproducible without a live OpenAI call — replace with a real
-- embedding from PREDICT or sp_invoke_external_rest_endpoint in production).
DECLARE @qvec VECTOR(1536) = (
    SELECT CAST(
        '[' + STRING_AGG(CAST(ROUND(SIN(1 * 0.13 + n * 0.007) + 0.001, 5) AS NVARCHAR(20)), ',')
              WITHIN GROUP (ORDER BY n) + ']' AS VECTOR(1536))
    FROM (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) AS s
);

DECLARE @k INT = 60;

WITH VectorLeg AS (
    -- Top 10 by vector similarity
    SELECT TOP (10)
        ProductId,
        ROW_NUMBER() OVER (ORDER BY VECTOR_DISTANCE('cosine', DescriptionVector, @qvec) ASC) AS VectorRank
    FROM dbo.Products
    WHERE DescriptionVector IS NOT NULL
    ORDER BY VECTOR_DISTANCE('cosine', DescriptionVector, @qvec) ASC
    WITH APPROXIMATE
),

TextLeg AS (
    -- Top 10 by FTS rank
    SELECT TOP (10)
        ct.[KEY] AS ProductId,
        ROW_NUMBER() OVER (ORDER BY ct.[RANK] DESC) AS TextRank
    FROM CONTAINSTABLE(dbo.Products, (ProductName, Description),
                       'noise OR cancelling OR headphones OR meetings') AS ct
),

RRF AS (
    SELECT
        COALESCE(v.ProductId, t.ProductId)            AS ProductId,
        ISNULL(1.0 / (@k + v.VectorRank), 0) +
        ISNULL(1.0 / (@k + t.TextRank),   0)          AS RrfScore,
        v.VectorRank,
        t.TextRank
    FROM VectorLeg v
    FULL OUTER JOIN TextLeg t ON v.ProductId = t.ProductId
)

SELECT TOP (5)
    r.ProductId,
    p.ProductName,
    p.Category,
    r.VectorRank,
    r.TextRank,
    CAST(r.RrfScore AS DECIMAL(10,6)) AS RrfScore
FROM RRF r
JOIN dbo.Products p ON p.ProductId = r.ProductId
ORDER BY r.RrfScore DESC;
```

**Expected output**

| ProductId | ProductName                          | Category | VectorRank | TextRank | RrfScore |
| :-------- | :----------------------------------- | :------- | :--------- | :------- | :------- |
| 1         | Wireless Noise-Cancelling Headphones | Audio    | 1          | 1        | 0.032787 |
| 2         | In-Ear Sport Earbuds                 | Audio    | 2          | 2        | 0.032258 |
| 3         | Conference-Room Speakerphone         | Audio    | 3          | 3        | 0.031746 |
| 4         | Studio Monitor Headphones            | Audio    | 4          | 4        | 0.031250 |
| 5         | Ultra-thin Mechanical Keyboard       | Peripherals | 5       | NULL     | 0.015385 |

**Why this matters** — RRF is rank-based, so the two legs do not need to be on
the same score scale. The vector leg's distances and the FTS leg's RANK score
(1–1000) never get compared directly. The exam tests both the formula
(`1 / (k + rank)`) and the standard `k = 60`.

---

### Step 6: When hybrid beats vector-only

Hybrid wins when the query contains a rare exact token an embedding model is
unlikely to weight strongly — model numbers, brand names, SKU strings. Try:

```sql
-- Vector-only
DECLARE @qvec VECTOR(1536) = (
    SELECT CAST(
        '[' + STRING_AGG(CAST(ROUND(SIN(5 * 0.13 + n * 0.007), 5) AS NVARCHAR(20)), ',')
              WITHIN GROUP (ORDER BY n) + ']' AS VECTOR(1536))
    FROM (
        SELECT TOP (1536) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects a CROSS JOIN sys.all_objects b
    ) AS s
);

SELECT 'vector' AS Leg, TOP (3) ProductId, ProductName,
       VECTOR_DISTANCE('cosine', DescriptionVector, @qvec) AS Dist
FROM dbo.Products
ORDER BY VECTOR_DISTANCE('cosine', DescriptionVector, @qvec) ASC
WITH APPROXIMATE;

-- FTS-only — searches for a literal SKU-like token
SELECT 'fts' AS Leg, TOP (3) p.ProductId, p.ProductName, ct.[RANK]
FROM CONTAINSTABLE(dbo.Products, *, '"hot-swappable"') ct
JOIN dbo.Products p ON p.ProductId = ct.[KEY]
ORDER BY ct.[RANK] DESC;
```

**Expected output** (FTS-only) — picks up product 5 because of the literal
`hot-swappable` phrase that an embedding may diffuse:

| Leg | ProductId | ProductName                     | RANK |
| :-- | :-------- | :------------------------------ | :--- |
| fts | 5         | Ultra-thin Mechanical Keyboard  | 96   |

**Why this matters** — the exam tests "when do you reach for hybrid?" Answer:
when literal-token recall matters (brand, model number, error code, regulatory
identifier).

---

## Cleanup

```sql
USE Lab01_Products;
GO

DROP FULLTEXT INDEX ON dbo.Products;
DROP FULLTEXT CATALOG ProductFTSCatalog;

-- Keep the Products table if you plan to revisit Labs 1 or 2.
-- DROP DATABASE Lab01_Products;
```

---

## Common Issues & Errors

| Error / symptom | Cause | Fix |
| :--- | :--- | :--- |
| `Msg 7610 — Cannot use the column ... in a full-text index` | Column type not supported (e.g. `VARCHAR(MAX)` on certain engines, or a non-string column) | Use `NVARCHAR(MAX)` / `NVARCHAR(N)`; confirm with `SELECT * FROM sys.fulltext_indexable_types` |
| `Msg 7619 — Could not find key index 'PK_...'` in `CREATE FULLTEXT INDEX` | PK name mismatch | Look up the real PK name in `sys.indexes`; the `IDENTITY` PK is auto-named |
| `CONTAINS` returns no rows for a common word like "the" | Word is in the system stop list | Remove from a custom stoplist or use `CONTAINS(col, 'FORMSOF(INFLECTIONAL, the)')` (rarely a real fix) |
| FTS index appears empty after insert | `CHANGE_TRACKING = OFF` or `MANUAL`, or population still running | `ALTER FULLTEXT INDEX ON dbo.Products START FULL POPULATION;` and wait for `PopulateStatus = 0` |
| RRF score is dominated by the FTS leg | The FTS query matches dozens of rows; vector top-10 is smaller | Cap the FTS leg with `TOP (10)` or weight the legs with a multiplier on each `1/(k+rank)` term |

---

## Exam Tips

> [!tip] Exam Tips
>
> - `CONTAINS` and `FREETEXT` are Boolean predicates; `CONTAINSTABLE` and `FREETEXTTABLE` return ranked tables with `[KEY]` and `[RANK]` columns
> - The canonical RRF formula is `score = SUM(1 / (k + rank))` with `k = 60`. Memorise both the formula and the default constant
> - RRF needs **ranks**, not raw scores — that's why we wrap each leg in `ROW_NUMBER()` before summing
> - Hybrid retrieval wins on queries that mix semantic intent with literal exact-match tokens (SKUs, model numbers, regulatory codes)

---

## Key Takeaways

- A full-text index needs a catalog, a unique key index, and the column list
- `CONTAINS` for precision, `FREETEXT` for natural language, `*TABLE` variants when you need ranked results
- RRF fuses ranked lists without normalising scores — works because both legs produce a rank position
- The hybrid leg's win condition is literal-token recall on top of semantic similarity

---

## Related Topics

- [01-Full-Text Search](../../10-intelligent-search/01-fulltext-search.md)
- [03-Hybrid Search & RRF](../../10-intelligent-search/03-hybrid-search-rrf.md)
- [02-Vector Search](../../10-intelligent-search/02-vector-search.md)
- [Vector Search Patterns](../code-examples/tsql/vector-search-patterns.md)

---

## Official Documentation

- <https://learn.microsoft.com/en-us/sql/relational-databases/search/full-text-search>
- <https://learn.microsoft.com/en-us/sql/t-sql/queries/contains-transact-sql>
- <https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/containstable-transact-sql>
- <https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/freetexttable-transact-sql>
- <https://learn.microsoft.com/en-us/azure/azure-sql/database/hybrid-search>

---

**[← Back to lab index](./labs.md) | [↑ Back to overview](../../dp-800-overview.md)**
