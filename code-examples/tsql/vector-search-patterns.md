---
title: Vector Search Patterns
type: code-examples
tags:
  - dp-800
  - tsql
  - code-examples
  - vector-search
  - hybrid-search
---

# Vector Search Patterns

T-SQL patterns for vector storage, similarity search, DiskANN indexing, and hybrid search with Reciprocal Rank Fusion (RRF). Relevant to DP-800 Domain 3 (AI capabilities).

## Vector Data Type and Storage

```sql
-- Create a table with a VECTOR column for storing embeddings
-- VECTOR(n) where n = number of dimensions (e.g., 1536 for text-embedding-ada-002)
CREATE TABLE Documents (
    doc_id      INT IDENTITY(1,1) PRIMARY KEY,
    title       NVARCHAR(500)     NOT NULL,
    content     NVARCHAR(MAX)     NOT NULL,
    embedding   VECTOR(1536)      NULL  -- stores a 1536-dimension float32 vector
);

-- Insert a vector by passing a JSON array of floats
-- In practice, the array comes from an embedding model (Azure OpenAI, etc.)
INSERT INTO Documents (title, content, embedding)
VALUES (
    N'Introduction to Machine Learning',
    N'Machine learning is a subset of artificial intelligence...',
    '[0.012, -0.034, 0.078, ...]'  -- truncated; real arrays have 1536 values
);

-- VECTOR_NORMALIZE: returns a unit-length (L2-normalized) copy of the vector
-- Required before using dot-product distance as a cosine equivalent
UPDATE Documents
SET embedding = VECTOR_NORMALIZE(embedding)
WHERE doc_id = 1;

-- VECTORPROPERTY: inspect metadata about a vector column
-- Returns the number of dimensions configured for the column
SELECT VECTORPROPERTY(embedding, 'Dimensions') AS dimensions  -- 1536
FROM Documents
WHERE doc_id = 1;

-- Returns 1 if the vector is L2-normalized (norm ≈ 1.0), else 0
SELECT VECTORPROPERTY(embedding, 'IsNormalized') AS is_normalized
FROM Documents
WHERE doc_id = 1;
```

## Vector Distance Functions

```sql
-- VECTOR_DISTANCE(metric, vector1, vector2) — returns a FLOAT distance value
-- Lower values = more similar (except dot product, which is inverted)

DECLARE @query VECTOR(1536) = '[0.021, -0.015, 0.093, ...]';

-- 1. Cosine distance — measures angle between vectors; ignores magnitude
--    Range: 0 (identical direction) to 2 (opposite direction)
--    Best for: text embeddings, semantic similarity
SELECT doc_id, title,
       VECTOR_DISTANCE('cosine', embedding, @query) AS cosine_dist
FROM Documents
ORDER BY cosine_dist ASC;

-- 2. Dot product distance — equivalent to cosine when vectors are normalized
--    Use on pre-normalized vectors for faster computation (avoids square-root)
--    Range: -1 (opposite) to 0 (identical) — lower = more similar
SELECT doc_id, title,
       VECTOR_DISTANCE('dot', embedding, @query) AS dot_dist
FROM Documents
ORDER BY dot_dist ASC;

-- 3. Euclidean distance — straight-line distance in vector space
--    Range: 0 (identical) to ∞
--    Best for: image embeddings, spatial data where magnitude matters
SELECT doc_id, title,
       VECTOR_DISTANCE('euclidean', embedding, @query) AS euclidean_dist
FROM Documents
ORDER BY euclidean_dist ASC;
```

| Metric | Best For | Notes |
|---|---|---|
| `cosine` | Text / semantic search | Default choice; magnitude-independent |
| `dot` | Pre-normalized vectors | Same result as cosine, slightly faster |
| `euclidean` | Image / spatial data | Sensitive to vector magnitude |

```sql
-- Full example: exact nearest neighbor (ENN) — top-5 most similar documents
-- ENN performs a full table scan; accurate but slow on large tables
DECLARE @query_vector VECTOR(1536) = '[0.021, -0.015, 0.093, ...]';

SELECT TOP 5
    d.doc_id,
    d.title,
    VECTOR_DISTANCE('cosine', d.embedding, @query_vector) AS distance
FROM Documents d
ORDER BY distance ASC;
-- Note: no WHERE clause needed; ORDER BY + TOP gives nearest neighbors
```

## Approximate Nearest Neighbor (ANN) with DiskANN

```sql
-- DiskANN is a disk-resident ANN index optimized for large vector datasets
-- Trades a small amount of accuracy for dramatically faster query times

-- Create a DiskANN vector index on the embedding column
CREATE INDEX ix_documents_embedding
ON Documents (embedding)
USING DISKANN;
-- Optional hints: WITH (max_degree = 64, l_value_build = 100)
-- max_degree: graph connectivity (higher = better recall, more storage)
-- l_value_build: build-time search list size (higher = better quality index)

-- VECTOR_SEARCH: ANN search using the DiskANN index
-- Returns doc_id + distance for the top_n approximate nearest neighbors
SELECT v.doc_id, v.distance, d.title
FROM VECTOR_SEARCH(
    Documents,          -- table
    embedding,          -- vector column (must have DiskANN index)
    @query_vector,      -- query vector
    top_n => 10         -- number of results to return
) v
JOIN Documents d ON v.doc_id = d.doc_id
ORDER BY v.distance ASC;

-- ANN vs ENN comparison
-- ┌─────────────────────┬──────────────┬───────────────┐
-- │ Method              │ Speed        │ Accuracy      │
-- ├─────────────────────┼──────────────┼───────────────┤
-- │ ENN (VECTOR_DISTANCE│ O(n) — slow  │ 100% exact    │
-- │ + ORDER BY)         │              │               │
-- │ ANN (VECTOR_SEARCH  │ O(log n)     │ ~95–99%       │
-- │ + DiskANN index)    │ — very fast  │ approximate   │
-- └─────────────────────┴──────────────┴───────────────┘
-- Use ANN for production; ENN only for small datasets or ground-truth testing

-- ANN search with a JOIN to retrieve full document data
DECLARE @query_vector VECTOR(1536) = '[0.021, -0.015, 0.093, ...]';

SELECT TOP 10
    d.doc_id,
    d.title,
    d.content,
    v.distance AS cosine_distance
FROM VECTOR_SEARCH(Documents, embedding, @query_vector, top_n => 20) v
JOIN Documents d ON v.doc_id = d.doc_id
ORDER BY v.distance ASC;
```

## Full-Text Search Setup

```sql
-- Full-text search (FTS) is required for the text leg of hybrid search
-- Must create a catalog and an index before using CONTAINS / FREETEXT

-- Step 1: create a full-text catalog (logical container for FTS indexes)
CREATE FULLTEXT CATALOG ft_catalog AS DEFAULT;

-- Step 2: create a full-text index on the content column
--   KEY INDEX specifies the unique index FTS uses to map rows
--   ON ft_catalog links it to the catalog created above
CREATE FULLTEXT INDEX ON Documents (content)
    KEY INDEX PK_Documents    -- must be a unique, single-column index
    ON ft_catalog;

-- CONTAINS — boolean keyword search (exact or prefix match)
SELECT doc_id, title
FROM Documents
WHERE CONTAINS(content, '"machine learning"');  -- exact phrase

SELECT doc_id, title
FROM Documents
WHERE CONTAINS(content, 'database AND vector');  -- boolean AND

-- FREETEXT — natural-language search (inflectional forms, synonyms)
SELECT doc_id, title
FROM Documents
WHERE FREETEXT(content, 'machine learning algorithms');

-- CONTAINSTABLE — returns a table with KEY (doc_id) and RANK (0–1000)
-- Used in hybrid search to get numeric relevance scores
SELECT ct.[KEY] AS doc_id, ct.RANK AS fts_rank, d.title
FROM CONTAINSTABLE(Documents, content, 'vector search') ct
JOIN Documents d ON ct.[KEY] = d.doc_id
ORDER BY ct.RANK DESC;
```

## Hybrid Search with Reciprocal Rank Fusion (RRF)

Hybrid search combines vector similarity (semantic) with full-text keyword search. Vector search captures meaning; full-text catches exact terms that embeddings may miss. **Reciprocal Rank Fusion (RRF)** merges the two ranked lists without needing to normalize raw scores.

**RRF formula:** `score = SUM(1 / (k + rank))` where `k = 60` (dampens the influence of high-rank outliers).

```sql
-- Full hybrid search example using RRF
DECLARE @query_vector VECTOR(1536) = '[0.021, -0.015, 0.093, ...]';
DECLARE @query_text   NVARCHAR(500) = N'machine learning database';
DECLARE @k            INT = 60;  -- RRF constant; 60 is the standard default

WITH VectorResults AS (
    -- ANN search: returns doc_id + approximate cosine distance
    -- ROW_NUMBER ranks from 1 (closest) to top_n (furthest)
    SELECT
        v.doc_id,
        ROW_NUMBER() OVER (ORDER BY v.distance ASC) AS vector_rank
    FROM VECTOR_SEARCH(Documents, embedding, @query_vector, top_n => 20) v
),

TextResults AS (
    -- Full-text search: CONTAINSTABLE returns RANK 0–1000 (higher = better)
    -- ROW_NUMBER ranks from 1 (most relevant) to n (least relevant)
    SELECT
        d.doc_id,
        ROW_NUMBER() OVER (ORDER BY ct.RANK DESC) AS text_rank
    FROM CONTAINSTABLE(Documents, content, @query_text) ct
    JOIN Documents d ON ct.[KEY] = d.doc_id
),

RRF AS (
    -- FULL OUTER JOIN so documents found by only one method are still included
    -- ISNULL(..., 0) gives zero RRF contribution when a method missed the doc
    SELECT
        COALESCE(v.doc_id, t.doc_id)                   AS doc_id,
        ISNULL(1.0 / (@k + v.vector_rank), 0) +
        ISNULL(1.0 / (@k + t.text_rank),   0)          AS rrf_score
    FROM VectorResults v
    FULL OUTER JOIN TextResults t ON v.doc_id = t.doc_id
)

-- Final result: top-10 documents by combined RRF score
SELECT TOP 10
    d.doc_id,
    d.title,
    d.content,
    r.rrf_score
FROM RRF r
JOIN Documents d ON r.doc_id = d.doc_id
ORDER BY r.rrf_score DESC;
```

```sql
-- Weighted RRF variant: boost vector or text leg independently
-- Multiply each term's contribution by a weight (must sum to 1.0 ideally)
DECLARE @vector_weight FLOAT = 0.7;
DECLARE @text_weight   FLOAT = 0.3;

-- Replace the RRF score expression with:
--   @vector_weight * ISNULL(1.0 / (@k + vector_rank), 0) +
--   @text_weight   * ISNULL(1.0 / (@k + text_rank),   0)
```

## Similarity Score Conversion

```sql
-- Raw VECTOR_DISTANCE values are distances (lower = closer).
-- Convert to similarity scores (higher = closer) for intuitive thresholding.

DECLARE @query VECTOR(1536) = '[0.021, -0.015, 0.093, ...]';

-- Cosine similarity = 1 - cosine distance
-- Valid only when vectors are L2-normalized; range [−1, 1], typically [0, 1]
SELECT
    doc_id,
    title,
    VECTOR_DISTANCE('cosine', embedding, @query)       AS cosine_distance,
    1.0 - VECTOR_DISTANCE('cosine', embedding, @query) AS cosine_similarity
FROM Documents
WHERE 1.0 - VECTOR_DISTANCE('cosine', embedding, @query) >= 0.75  -- threshold
ORDER BY cosine_similarity DESC;

-- Euclidean similarity: no universal formula; common approach uses 1 / (1 + d)
-- Maps distance 0 → similarity 1.0; distance ∞ → similarity 0.0
SELECT
    doc_id,
    title,
    VECTOR_DISTANCE('euclidean', embedding, @query)              AS euclidean_distance,
    1.0 / (1.0 + VECTOR_DISTANCE('euclidean', embedding, @query)) AS euclidean_similarity
FROM Documents
WHERE 1.0 / (1.0 + VECTOR_DISTANCE('euclidean', embedding, @query)) >= 0.5
ORDER BY euclidean_similarity DESC;

-- Summary of distance → similarity conversions
-- ┌──────────────┬──────────────────────────────────────┬───────────────────┐
-- │ Metric       │ Similarity formula                   │ Range             │
-- ├──────────────┼──────────────────────────────────────┼───────────────────┤
-- │ cosine       │ 1 - distance  (normalized vectors)   │ [−1, 1] → [0, 1]  │
-- │ dot          │ -distance     (lower dot = closer)   │ depends on norms  │
-- │ euclidean    │ 1 / (1 + distance)                   │ (0, 1]            │
-- └──────────────┴──────────────────────────────────────┴───────────────────┘
```

---

**[← Back to Code Examples](./README.md) | [↑ Back to Certification](../../certification/README.md)**
