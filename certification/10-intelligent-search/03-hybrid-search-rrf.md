---
title: Hybrid Search and Reciprocal Rank Fusion
type: study-material
tags:
  - dp-800
  - hybrid-search
  - rrf
  - reciprocal-rank-fusion
---

# Hybrid Search and Reciprocal Rank Fusion

## Overview

Hybrid search combines full-text search (keyword matching) with vector search (semantic similarity) to produce better results than either alone. The challenge is merging two ranked lists with different scoring scales. **Reciprocal Rank Fusion (RRF)** is the standard algorithm for combining ranked lists without needing to normalize scores — it uses only the rank position, not the score values.

> [!abstract]
> - Covers hybrid search: combining full-text and vector search results using Reciprocal Rank Fusion (RRF)
> - Hybrid search improves over either method alone by capturing both keyword precision and semantic recall
> - Key exam topics: RRF formula, k parameter, how to combine result sets, when hybrid outperforms single-method

> [!tip] What the Exam Tests
> - **RRF formula**: `score = Σ 1/(k + rank)` for each result set; `k = 60` default; higher score = more relevant
> - RRF is a **rank-combination algorithm** — it combines the ranks of results from multiple sources, not their raw scores
> - Hybrid search outperforms single-method when queries mix exact keywords and semantic meaning

## When to Use Each Search Type

| Scenario | Best Approach |
| :--- | :--- |
| Exact product code search (SKU-123) | Full-text (keyword) only |
| Natural language query, vague intent | Vector only |
| Short query with specific terms and semantic meaning | Hybrid (both) |
| Known acronym expansion | Full-text (FORMSOF) |
| Multi-lingual search | Vector (embeddings handle translation) |
| High-recall requirement (don't miss relevant) | Hybrid |

## Reciprocal Rank Fusion Algorithm

RRF combines ranked lists by assigning each document a score based on its rank in each list:

```
RRF_score(doc) = Σ  1 / (k + rank_in_list_i)
```

Where `k` is a constant (typically 60) that reduces the impact of very high ranks.

**Example:**

| Document | FTS Rank | Vector Rank | RRF Score (k=60) |
| :--- | :--- | :--- | :--- |
| Product A | 1 | 3 | 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = **0.0323** |
| Product B | 5 | 1 | 1/(60+5) + 1/(60+1) = 0.0154 + 0.0164 = **0.0318** |
| Product C | 2 | 50 | 1/(60+2) + 1/(60+50) = 0.0161 + 0.0091 = **0.0252** |
| Product D | 100 | 2 | 1/(60+100) + 1/(60+2) = 0.0063 + 0.0161 = **0.0224** |

Documents appearing in both lists score higher than those in only one list. The `k=60` constant prevents a rank-1 result in one list from completely dominating if it scores poorly in the other.

## Implementing Hybrid Search with RRF in T-SQL

```sql
CREATE OR ALTER PROCEDURE dbo.HybridSearch
    @query_text   NVARCHAR(500),
    @top_n        INT = 10,
    @rrf_k        INT = 60
AS
BEGIN
    SET NOCOUNT ON;

    -- Step 1: Generate query embedding
    DECLARE @query_vector VECTOR(1536);
    SELECT @query_vector = CAST(
        PREDICT(MODEL = [MyEmbeddingModel],
                DATA = (SELECT @query_text AS input_text)) AS VECTOR(1536));

    -- Step 2: Full-text search results with rank
    WITH FTSResults AS (
        SELECT
            p.[KEY]   AS ProductId,
            p.[RANK]  AS FTSScore,
            ROW_NUMBER() OVER (ORDER BY p.[RANK] DESC) AS FTSRank
        FROM FREETEXTTABLE(dbo.Products, (ProductName, Description), @query_text, 50) AS p
    ),

    -- Step 3: Vector search results with rank
    VectorResults AS (
        SELECT
            vs.ProductId,
            vs.distance AS VectorDistance,
            ROW_NUMBER() OVER (ORDER BY vs.distance ASC) AS VectorRank
        FROM VECTOR_SEARCH(
            TABLE = dbo.Products AS p,
            COLUMN = DescriptionVector,
            SIMILAR_TO = @query_vector,
            METRIC = 'cosine',
            TOP_N = 50
        ) AS vs
    ),

    -- Step 4: Combine with RRF
    RRFScores AS (
        SELECT
            COALESCE(f.ProductId, v.ProductId) AS ProductId,
            -- RRF formula: sum of 1/(k + rank) across all lists
            COALESCE(1.0 / (@rrf_k + f.FTSRank), 0) +
            COALESCE(1.0 / (@rrf_k + v.VectorRank), 0) AS RRFScore,
            f.FTSScore,
            f.FTSRank,
            v.VectorDistance,
            v.VectorRank
        FROM FTSResults f
        FULL OUTER JOIN VectorResults v ON f.ProductId = v.ProductId
    )

    -- Step 5: Return top N results
    SELECT TOP (@top_n)
        r.ProductId,
        p.ProductName,
        p.Description,
        r.RRFScore,
        r.FTSRank,
        r.VectorRank,
        r.VectorDistance
    FROM RRFScores r
    JOIN dbo.Products p ON p.ProductId = r.ProductId
    ORDER BY r.RRFScore DESC;
END;
```

```sql
-- Usage
EXEC dbo.HybridSearch @query_text = 'comfortable wireless headphones for work', @top_n = 10;
```

## Simplified RRF Without Vector Index

For smaller tables where full vector scan is acceptable:

```sql
DECLARE @query_text   NVARCHAR(500) = 'ergonomic keyboard for developers';
DECLARE @query_vector VECTOR(1536);
DECLARE @rrf_k        INT = 60;
DECLARE @top_n        INT = 10;

-- Generate embedding
SELECT @query_vector = CAST(
    PREDICT(MODEL = [MyEmbeddingModel],
            DATA = (SELECT @query_text AS input_text)) AS VECTOR(1536));

WITH FTSResults AS (
    SELECT
        [KEY] AS ProductId,
        ROW_NUMBER() OVER (ORDER BY [RANK] DESC) AS FTSRank
    FROM FREETEXTTABLE(dbo.Products, *, @query_text, 50)
),
VectorResults AS (
    SELECT
        ProductId,
        ROW_NUMBER() OVER (ORDER BY VECTOR_DISTANCE('cosine', DescriptionVector, @query_vector) ASC) AS VectorRank
    FROM dbo.Products
    WHERE DescriptionVector IS NOT NULL
),
RRF AS (
    SELECT
        COALESCE(f.ProductId, v.ProductId) AS ProductId,
        ISNULL(1.0 / (@rrf_k + f.FTSRank), 0) +
        ISNULL(1.0 / (@rrf_k + v.VectorRank), 0) AS RRFScore
    FROM FTSResults f
    FULL OUTER JOIN VectorResults v ON f.ProductId = v.ProductId
)
SELECT TOP (@top_n)
    r.ProductId,
    p.ProductName,
    r.RRFScore
FROM RRF r
JOIN dbo.Products p ON p.ProductId = r.ProductId
ORDER BY r.RRFScore DESC;
```

## Evaluating Search Performance

### Recall

Recall measures how many relevant items are returned out of all relevant items that exist:

```
Recall@K = |Relevant items in top K| / |Total relevant items|
```

- Higher is better
- Hybrid search typically improves recall over either approach alone

### Precision

Precision measures how many returned items are actually relevant:

```
Precision@K = |Relevant items in top K| / K
```

- Higher is better
- Keyword search may have high precision but low recall for semantic queries

### Mean Reciprocal Rank (MRR)

```
MRR = (1/|Q|) × Σ (1 / rank_of_first_relevant_result)
```

- Measures how quickly the first relevant result appears

### Evaluating with Ground Truth

```sql
-- Create a test set with known relevant products for queries
CREATE TABLE dbo.SearchEvaluation (
    EvalId      INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
    QueryText   NVARCHAR(500) NOT NULL,
    RelevantIds NVARCHAR(MAX) NOT NULL  -- JSON array of relevant ProductIds
);

INSERT INTO dbo.SearchEvaluation (QueryText, RelevantIds) VALUES
('wireless noise cancelling headphones', '[1, 7, 23, 45]'),
('ergonomic mechanical keyboard', '[12, 88, 91]');

-- Evaluate: for each test query, measure Precision@10
-- (Compare returned top-10 ProductIds against RelevantIds)
```

### Latency Measurement

```sql
-- Measure hybrid search latency
DECLARE @start DATETIME2 = SYSDATETIME();
EXEC dbo.HybridSearch @query_text = 'wireless audio', @top_n = 10;
SELECT DATEDIFF(MILLISECOND, @start, SYSDATETIME()) AS LatencyMs;
```

**Performance optimization levers:**

| Lever | Impact |
| :--- | :--- |
| Vector index (DiskANN) | Major — milliseconds vs seconds for ANN |
| FTS index | Major — instant vs full table scan |
| Reduce TOP_N in VECTOR_SEARCH | Minor — fewer candidates |
| Reduce FTS result limit | Minor — faster FTS evaluation |
| Pre-normalize embeddings | Minor — skip VECTOR_NORMALIZE at query time |

## Tuning RRF — Adjusting k

The `k` constant controls how much high-rank positions matter:

```sql
-- k=60 (default): standard, reduces impact of top ranks
-- k=1: top rank dominates (extreme weighting to rank 1)
-- k=100: more uniform scoring across ranks

-- Experiment with different k values to tune for your dataset
EXEC dbo.HybridSearch @query_text = 'wireless headphones', @top_n = 10, @rrf_k = 60;
EXEC dbo.HybridSearch @query_text = 'wireless headphones', @top_n = 10, @rrf_k = 20;
```

Smaller k → top-ranked results get more weight
Larger k → more uniform distribution across ranks

## Use Cases

- **E-commerce product search**: Users type short, keyword-rich queries but may use different terminology than product descriptions — hybrid handles both
- **Knowledge base search**: Technical articles have specific terminology (FTS) but users often paraphrase (vector)
- **Customer support**: Hybrid search finds the best FAQ match even when the user's phrasing differs from the FAQ question
- **RAG document retrieval**: Ensures both keyword matches and semantically similar chunks are considered

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| One list always dominates | k too small; one list much larger | Increase k; ensure both lists return similar numbers of candidates |
| FTS returns nothing | Stop words removed all query terms | Add fallback: if FTS empty, use vector-only |
| NULL RRFScore | FULL OUTER JOIN with no FTS result | Use `ISNULL(..., 0)` around RRF score components |
| Slow hybrid search | No vector index | Create DiskANN index; use `VECTOR_SEARCH` |
| Poor recall | TOP_N too small in each search | Increase candidate pool (e.g., TOP_N = 100) before final top-10 |

## Exam Tips

- RRF uses **ranks**, not raw scores — this makes it scale-invariant and robust to different scoring systems
- `k=60` is the standard RRF constant; lower k weights top ranks more heavily
- `FULL OUTER JOIN` is essential — a document may appear in only one of the two result sets
- Hybrid search improves **recall** (finds more relevant items) compared to using only one approach
- Vector search handles semantic similarity; full-text handles exact keywords — neither alone is optimal for production search

## Key Takeaways

- Hybrid search = full-text search + vector search, merged with RRF
- RRF formula: `1 / (k + rank)` summed across all result lists — higher score = better combined rank
- Use `FULL OUTER JOIN` to merge the two lists so documents appearing in only one list are still included
- Measure recall, precision, and latency to evaluate and tune the hybrid search pipeline

## Related Topics

- [01-Full-Text Search](./01-fulltext-search.md)
- [02-Vector Search](./02-vector-search.md)
- [01-RAG Use Cases](../11-rag/01-rag-use-cases.md)

## Official Documentation

- [Hybrid Search in Azure AI Search](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview)
- [Reciprocal Rank Fusion](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)
- [VECTOR_SEARCH](https://learn.microsoft.com/en-us/sql/t-sql/functions/vector-search-transact-sql)

---

**[← Previous](./02-vector-search.md) | [↑ Back to Section](./README.md)**
