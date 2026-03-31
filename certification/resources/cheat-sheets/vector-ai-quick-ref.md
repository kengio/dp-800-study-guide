---
title: "Vector & AI — Quick Reference"
type: cheat-sheet
tags:
  - dp-800
  - cheat-sheet
  - vector-search
  - ai
  - rag
  - embeddings
---

# Vector & AI — Quick Reference

VECTOR type, distance functions, DiskANN indexing, full-text search, hybrid search, and RAG patterns for Azure SQL Database.

---

## VECTOR Data Type

Available in Azure SQL Database. Stores fixed-dimension float arrays.

```sql
-- Column definition
CREATE TABLE dbo.Documents (
    DocumentID   INT            NOT NULL PRIMARY KEY,
    Title        NVARCHAR(200)  NOT NULL,
    Content      NVARCHAR(MAX)  NOT NULL,
    Embedding    VECTOR(1536)   NOT NULL   -- 1536 dimensions (text-embedding-3-small)
);

-- Insert with JSON array syntax
INSERT INTO dbo.Documents (DocumentID, Title, Content, Embedding)
VALUES (1, 'Azure SQL Overview', 'Azure SQL Database is...',
        '[0.0123, -0.0456, 0.0789, ...]');   -- 1536 float values as JSON array
```

| Constraint | Value |
| :--- | :--- |
| Max dimensions | 1,998 |
| Element type | 32-bit float |
| Storage format | Binary (not JSON at rest) |
| NULL support | Yes |
| Indexing | DiskANN (native vector index) |

---

## Distance Functions

```sql
-- VECTOR_DISTANCE(metric, vector1, vector2)
SELECT
    DocumentID,
    Title,
    VECTOR_DISTANCE('cosine', Embedding, @queryVector)    AS CosineDistance,
    VECTOR_DISTANCE('dot', Embedding, @queryVector)       AS DotProduct,
    VECTOR_DISTANCE('euclidean', Embedding, @queryVector)  AS L2Distance
FROM dbo.Documents;
```

| Metric | Range | Lower = More Similar? | Best For |
| :--- | :--- | :--- | :--- |
| `cosine` | 0 to 2 | Yes (0 = identical) | Normalized embeddings (most common) |
| `dot` | Varies | No (higher = more similar) | When magnitude matters |
| `euclidean` | 0 to infinity | Yes (0 = identical) | Spatial / coordinate data |

> **Exam tip:** `cosine` distance = 1 - cosine_similarity. Distance of 0 means identical vectors.

---

## DiskANN Vector Index

Approximate Nearest Neighbor (ANN) index for fast vector search. Creates a graph-based index on disk.

```sql
-- Create DiskANN index
CREATE NONCLUSTERED INDEX IX_Documents_Embedding
    ON dbo.Documents (Embedding)
    WITH (TYPE = DISKANN);

-- With options
CREATE NONCLUSTERED INDEX IX_Documents_Embedding
    ON dbo.Documents (Embedding)
    WITH (TYPE = DISKANN, MAXDOP = 4);
```

| Feature | Detail |
| :--- | :--- |
| Max dimensions | 1,998 |
| Approximate | Yes (may miss exact nearest neighbors) |
| Updateable | Yes (inserts/updates/deletes supported) |
| Filterable | Yes (with WHERE clause) |
| Index type | Nonclustered |

---

## VECTOR_SEARCH — Native Vector Search

```sql
-- Top-K nearest neighbors using DiskANN index
SELECT vs.DocumentID, vs.Title, vs.distance
FROM VECTOR_SEARCH(
    dbo.Documents,            -- table
    'Embedding',              -- vector column
    @queryVector,             -- query vector
    'cosine',                 -- metric
    10                        -- top K
) vs;
```

### With Pre-filter

```sql
SELECT vs.DocumentID, vs.Title, vs.distance
FROM VECTOR_SEARCH(
    (SELECT * FROM dbo.Documents WHERE CategoryID = 5),
    'Embedding',
    @queryVector,
    'cosine',
    10
) vs;
```

---

## Full-Text Search

### Setup

```sql
-- 1. Create full-text catalog
CREATE FULLTEXT CATALOG ftCatalog AS DEFAULT;

-- 2. Create full-text index (one per table, on unique index)
CREATE FULLTEXT INDEX ON dbo.Documents (
    Title LANGUAGE 1033,       -- English
    Content LANGUAGE 1033
)
KEY INDEX PK_Documents
ON ftCatalog
WITH (CHANGE_TRACKING = AUTO);
```

### Query Functions

```sql
-- CONTAINS: exact word/phrase matching
SELECT * FROM dbo.Documents
WHERE CONTAINS(Content, '"Azure SQL" OR "vector search"');

-- CONTAINS with proximity
SELECT * FROM dbo.Documents
WHERE CONTAINS(Content, 'NEAR((vector, search), 5)');

-- FREETEXT: semantic/fuzzy matching (inflectional forms)
SELECT * FROM dbo.Documents
WHERE FREETEXT(Content, 'database performance optimization');

-- CONTAINSTABLE: returns rank score
SELECT d.Title, ft.RANK
FROM dbo.Documents d
INNER JOIN CONTAINSTABLE(dbo.Documents, Content, '"vector search"') ft
    ON d.DocumentID = ft.[KEY]
ORDER BY ft.RANK DESC;

-- FREETEXTTABLE: ranked semantic search
SELECT d.Title, ft.RANK
FROM dbo.Documents d
INNER JOIN FREETEXTTABLE(dbo.Documents, Content, 'AI database solutions') ft
    ON d.DocumentID = ft.[KEY]
ORDER BY ft.RANK DESC;
```

| Function | Type | Returns Rank | Use Case |
| :--- | :--- | :--- | :--- |
| `CONTAINS` | Exact / boolean | No | Precise keyword matching |
| `FREETEXT` | Semantic | No | Natural language queries |
| `CONTAINSTABLE` | Exact / boolean | Yes | Ranked keyword results |
| `FREETEXTTABLE` | Semantic | Yes | Ranked semantic results |

---

## Hybrid Search (Vector + Full-Text + RRF)

Reciprocal Rank Fusion (RRF) combines rankings from multiple search methods.

```sql
-- Step 1: Vector search results
WITH VectorResults AS (
    SELECT vs.DocumentID, vs.distance,
           ROW_NUMBER() OVER (ORDER BY vs.distance ASC) AS VectorRank
    FROM VECTOR_SEARCH(
        dbo.Documents, 'Embedding', @queryVector, 'cosine', 50
    ) vs
),

-- Step 2: Full-text search results
FullTextResults AS (
    SELECT ft.[KEY] AS DocumentID, ft.RANK AS FTRank,
           ROW_NUMBER() OVER (ORDER BY ft.RANK DESC) AS TextRank
    FROM FREETEXTTABLE(dbo.Documents, Content, @searchText) ft
),

-- Step 3: RRF fusion
Combined AS (
    SELECT
        COALESCE(v.DocumentID, f.DocumentID) AS DocumentID,
        1.0 / (60 + ISNULL(v.VectorRank, 1000)) AS VectorRRF,
        1.0 / (60 + ISNULL(f.TextRank, 1000))   AS TextRRF
    FROM VectorResults v
    FULL OUTER JOIN FullTextResults f ON v.DocumentID = f.DocumentID
)

SELECT TOP 10
    c.DocumentID,
    d.Title,
    c.VectorRRF + c.TextRRF AS RRFScore
FROM Combined c
JOIN dbo.Documents d ON c.DocumentID = d.DocumentID
ORDER BY RRFScore DESC;
```

> **RRF formula:** `1 / (k + rank)` where k is typically 60. Higher RRF score = more relevant.

---

## Generating Embeddings with sp_invoke_external_rest_endpoint

```sql
DECLARE @url NVARCHAR(4000) = 'https://my-openai.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-06-01';

DECLARE @payload NVARCHAR(MAX) = JSON_OBJECT('input': @inputText);

DECLARE @response NVARCHAR(MAX);
DECLARE @retval INT;

EXEC @retval = sp_invoke_external_rest_endpoint
    @url = @url,
    @method = 'POST',
    @payload = @payload,
    @credential = [https://my-openai.openai.azure.com],
    @response = @response OUTPUT;

-- Extract embedding vector from response
DECLARE @embedding NVARCHAR(MAX) = JSON_QUERY(
    @response, '$.result.data[0].embedding'
);
```

### Database Scoped Credential

```sql
-- Create credential for Azure OpenAI
CREATE DATABASE SCOPED CREDENTIAL [https://my-openai.openai.azure.com]
WITH IDENTITY = 'HTTPEndpointHeaders',
     SECRET = '{"api-key": "your-api-key-here"}';
```

| Constraint | Value |
| :--- | :--- |
| Timeout | 30 seconds |
| Max response size | 100 MB |
| Allowed protocols | HTTPS only |
| Auth methods | Managed Identity, API key (via credential) |

---

## RAG Pattern — End-to-End

```sql
-- 1. Generate embedding for user question
DECLARE @questionEmbedding VECTOR(1536);
-- (call sp_invoke_external_rest_endpoint to get embedding)

-- 2. Retrieve relevant documents (vector search)
DECLARE @context NVARCHAR(MAX);
SELECT @context = STRING_AGG(
    CONCAT('Title: ', Title, CHAR(10), 'Content: ', LEFT(Content, 500)),
    CHAR(10) + '---' + CHAR(10)
)
FROM (
    SELECT vs.Title, vs.Content
    FROM VECTOR_SEARCH(
        dbo.Documents, 'Embedding', @questionEmbedding, 'cosine', 5
    ) vs
) topDocs;

-- 3. Build prompt with context
DECLARE @prompt NVARCHAR(MAX) = CONCAT(
    'Answer the question based on the context below.', CHAR(10),
    'Context:', CHAR(10), @context, CHAR(10),
    'Question: ', @userQuestion
);

-- 4. Call LLM via sp_invoke_external_rest_endpoint
DECLARE @chatPayload NVARCHAR(MAX) = JSON_OBJECT(
    'messages': JSON_ARRAY(
        JSON_OBJECT('role': 'system', 'content': 'You are a helpful assistant.'),
        JSON_OBJECT('role': 'user', 'content': @prompt)
    ),
    'max_tokens': 500
);

EXEC sp_invoke_external_rest_endpoint
    @url = 'https://my-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-06-01',
    @method = 'POST',
    @payload = @chatPayload,
    @credential = [https://my-openai.openai.azure.com],
    @response = @response OUTPUT;

-- 5. Extract answer
SELECT JSON_VALUE(@response, '$.result.choices[0].message.content') AS Answer;
```

---

## Embedding Models Reference

| Model | Dimensions | Max Tokens | Use Case |
| :--- | :--- | :--- | :--- |
| text-embedding-3-small | 1536 | 8,191 | General purpose, lower cost |
| text-embedding-3-large | 3072 | 8,191 | Higher accuracy |
| text-embedding-ada-002 | 1536 | 8,191 | Legacy (still widely used) |

> **Exam tip:** Dimension count must match between stored embeddings and query vector. Mismatched dimensions cause runtime errors.

---

**[← Back to Cheat Sheets](./README.md)**
