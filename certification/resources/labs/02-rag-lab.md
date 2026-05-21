---
title: RAG Lab — Chunk, Embed, Retrieve, Generate
type: lab
tags:
  - dp-800
  - hands-on
  - lab
  - rag
  - embeddings
  - sp-invoke-external-rest-endpoint
status: complete
---

# Lab 02 — End-to-End RAG with `sp_invoke_external_rest_endpoint`

## Overview

A runnable, self-contained RAG pipeline built entirely in T-SQL. You chunk a
product knowledge base, embed each chunk via Azure OpenAI, store the result in
a `VECTOR(1536)` column, retrieve the top-K chunks for a user question, hand
them to a chat model, and parse the answer out of the canonical
`$.result.choices[0].message.content` JSON envelope.

> [!abstract]
>
> - Manual chunking of product policy text into 6 rows you can read in one screen
> - Calls Azure OpenAI from inside the database using `sp_invoke_external_rest_endpoint` and a database-scoped credential
> - Retrieves with `WITH APPROXIMATE` over the DiskANN index from Lab 1
> - Parses the LLM response with the **canonical** `$.result.choices[0].message.content` JSON path — the most-missed RAG detail on DP-800
> - All in ~120 lines of SQL, no application server required

> [!tip] What you'll do
>
> 1. Reuse the `Lab01_Products` database from Lab 1 (or recreate it inline)
> 2. Create a `ProductPolicies` table with chunked policy text
> 3. Register a database-scoped credential and call Azure OpenAI's embeddings endpoint to populate the `VECTOR(1536)` column
> 4. Issue a user question, embed it, retrieve the top-3 chunks with `WITH APPROXIMATE`
> 5. Build the chat completion payload with `JSON_OBJECT` and call the chat model
> 6. Parse the response with `JSON_VALUE(@resp, '$.result.choices[0].message.content')`
> 7. Wrap the whole thing in a single `dbo.AskCatalog` procedure

## Prerequisites

- **Lab 01** completed (or rerun its Setup block to recreate the `Lab01_Products` database with the `dbo.Products` table). This lab adds tables to that database.
- An **Azure OpenAI** (or Microsoft Foundry) resource with these deployments:
  - `text-embedding-3-small` (1536 dimensions)
  - `gpt-4o-mini` (or any chat-completions model)
- The resource's endpoint URL (looks like `https://<name>.openai.azure.com/`) and an API key
- The `external rest endpoint` feature enabled on your engine: `EXEC sp_configure 'external rest endpoint enabled', 1; RECONFIGURE;`
- `db_owner` on `Lab01_Products` — required to create database-scoped credentials

---

## Setup

```sql
USE Lab01_Products;
GO

-- Master key needed to encrypt the database-scoped credential at rest
IF NOT EXISTS (SELECT 1 FROM sys.symmetric_keys WHERE name = '##MS_DatabaseMasterKey##')
    CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Replace_With_StrongPassword!1';
GO

-- Database-scoped credential for Azure OpenAI. Replace <key> with your real key.
-- Note: IDENTITY = 'HTTPEndpointHeaders' tells sp_invoke_external_rest_endpoint
-- to pass SECRET as request headers. SECRET is a JSON object with header names.
CREATE DATABASE SCOPED CREDENTIAL [https://YOUR-RESOURCE.openai.azure.com]
    WITH IDENTITY = 'HTTPEndpointHeaders',
         SECRET   = '{"api-key":"YOUR_AZURE_OPENAI_KEY"}';
GO

-- Policy chunks. In real RAG you would split source documents by paragraph
-- or 400-token windows with 10–20% overlap; for the lab we hand-pick 6 chunks.
CREATE TABLE dbo.ProductPolicies (
    ChunkId      INT IDENTITY(1,1) PRIMARY KEY,
    PolicyName   NVARCHAR(200) NOT NULL,
    ChunkText    NVARCHAR(MAX) NOT NULL,
    Embedding    VECTOR(1536)  NULL
);
GO

INSERT INTO dbo.ProductPolicies (PolicyName, ChunkText) VALUES
('Electronics Returns',
 'Electronics may be returned within 30 days of delivery with the original packaging. A 15% restocking fee applies to opened items. Refunds are issued to the original payment method within 5 business days.'),
('Audio Warranty',
 'All audio products (headphones, earbuds, speakerphones) carry a 2-year manufacturer warranty covering defects in materials and workmanship. The warranty does not cover wear on ear cushions or accidental damage.'),
('Furniture Assembly',
 'Standing desks and office chairs ship with assembly instructions and a hex key. White-glove assembly is available at checkout for an additional fee. Damaged-in-transit claims must be filed within 14 days of delivery.'),
('Bulk Discount',
 'Orders of 10 or more identical items qualify for a 12% bulk discount, applied automatically at checkout. Bulk pricing does not stack with promotional codes.'),
('Shipping Zones',
 'Free standard shipping within the contiguous United States. Hawaii and Alaska add $25 per order. International shipping is calculated at checkout and excludes Australia and New Zealand due to local distributor agreements.'),
('Privacy Policy Excerpt',
 'We do not sell customer data. Order history is retained for 7 years for tax and warranty purposes. Customers may request deletion of their account and personal data at any time via the privacy portal.');
GO

SELECT ChunkId, PolicyName, LEFT(ChunkText, 60) AS Preview
FROM dbo.ProductPolicies
ORDER BY ChunkId;
```

**Expected output**

| ChunkId | PolicyName             | Preview                                                       |
| :------ | :--------------------- | :------------------------------------------------------------ |
| 1       | Electronics Returns    | Electronics may be returned within 30 days of delivery with… |
| 2       | Audio Warranty         | All audio products (headphones, earbuds, speakerphones) car… |
| 3       | Furniture Assembly     | Standing desks and office chairs ship with assembly instruc… |
| 4       | Bulk Discount          | Orders of 10 or more identical items qualify for a 12% bulk… |
| 5       | Shipping Zones         | Free standard shipping within the contiguous United States… |
| 6       | Privacy Policy Excerpt | We do not sell customer data. Order history is retained for… |

---

## Steps

### Step 1: Embed each chunk via Azure OpenAI

Loop over the rows, call the embeddings endpoint, cast the resulting JSON
array to `VECTOR(1536)`, and store it. The payload format follows the Azure
OpenAI REST contract: `{ "input": "<text>" }` for embeddings.

```sql
DECLARE @url        NVARCHAR(4000) =
    'https://YOUR-RESOURCE.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01';
DECLARE @id INT, @text NVARCHAR(MAX), @payload NVARCHAR(MAX), @response NVARCHAR(MAX);

DECLARE c CURSOR LOCAL FAST_FORWARD FOR
    SELECT ChunkId, ChunkText FROM dbo.ProductPolicies WHERE Embedding IS NULL;

OPEN c;
FETCH NEXT FROM c INTO @id, @text;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @payload = JSON_OBJECT('input': @text);

    EXEC sp_invoke_external_rest_endpoint
         @url        = @url,
         @method     = 'POST',
         @credential = [https://YOUR-RESOURCE.openai.azure.com],
         @payload    = @payload,
         @timeout    = 230,
         @response   = @response OUTPUT;

    -- Embedding lives under $.result.data[0].embedding in the wrapped response
    UPDATE dbo.ProductPolicies
    SET Embedding = CAST(
        JSON_QUERY(@response, '$.result.data[0].embedding')
        AS VECTOR(1536))
    WHERE ChunkId = @id;

    FETCH NEXT FROM c INTO @id, @text;
END;
CLOSE c; DEALLOCATE c;

SELECT ChunkId, PolicyName,
       VECTORPROPERTY(Embedding, 'Dimensions') AS Dims
FROM dbo.ProductPolicies
ORDER BY ChunkId;
```

**Expected output**

| ChunkId | PolicyName             | Dims |
| :------ | :--------------------- | :--- |
| 1       | Electronics Returns    | 1536 |
| 2       | Audio Warranty         | 1536 |
| 3       | Furniture Assembly     | 1536 |
| 4       | Bulk Discount          | 1536 |
| 5       | Shipping Zones         | 1536 |
| 6       | Privacy Policy Excerpt | 1536 |

**Why this matters** — `sp_invoke_external_rest_endpoint` wraps every API
response under `$.result`. The exam tests both the JSON path used to read the
embedding **and** the chat completion path, which is the same envelope.

---

### Step 2: Build a DiskANN index on the chunks

Same syntax as Lab 1, but on the chunks table.

```sql
CREATE VECTOR INDEX IX_ProductPolicies_Embedding
ON dbo.ProductPolicies (Embedding)
WITH (METRIC = 'cosine', TYPE = 'diskann');
GO
```

**Expected output**

```text
Command(s) completed successfully.
```

**Why this matters** — 6 rows do not need an index, but the exam expects you
to know that a vector index is part of the production RAG retrieval path.

---

### Step 3: Embed a user question and retrieve the top-3 chunks

```sql
DECLARE @question NVARCHAR(MAX) =
    N'How long is the warranty on a pair of headphones?';

DECLARE @url      NVARCHAR(4000) =
    'https://YOUR-RESOURCE.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01';
DECLARE @qPayload NVARCHAR(MAX) = JSON_OBJECT('input': @question);
DECLARE @qResp    NVARCHAR(MAX);

EXEC sp_invoke_external_rest_endpoint
     @url        = @url,
     @method     = 'POST',
     @credential = [https://YOUR-RESOURCE.openai.azure.com],
     @payload    = @qPayload,
     @response   = @qResp OUTPUT;

DECLARE @qvec VECTOR(1536) = CAST(
    JSON_QUERY(@qResp, '$.result.data[0].embedding') AS VECTOR(1536));

SELECT TOP (3)
    ChunkId, PolicyName,
    LEFT(ChunkText, 80) AS Preview,
    VECTOR_DISTANCE('cosine', Embedding, @qvec) AS Distance
INTO   #TopK
FROM   dbo.ProductPolicies
WHERE  Embedding IS NOT NULL
ORDER  BY VECTOR_DISTANCE('cosine', Embedding, @qvec) ASC
WITH APPROXIMATE;

SELECT * FROM #TopK ORDER BY Distance;
```

**Expected output**

| ChunkId | PolicyName          | Preview                                          | Distance |
| :------ | :------------------ | :----------------------------------------------- | :------- |
| 2       | Audio Warranty      | All audio products (headphones, earbuds, speak… | 0.18xx   |
| 1       | Electronics Returns | Electronics may be returned within 30 days of … | 0.34xx   |
| 6       | Privacy Policy Excerpt | We do not sell customer data. Order history… | 0.41xx   |

**Why this matters** — this is the entire **retrieve** step of RAG. The exam
asks which clause makes this ANN vs ENN and where in the pipeline retrieval
sits.

---

### Step 4: Build the chat completion payload

Use `JSON_OBJECT` / `JSON_ARRAY` so the LLM payload escapes quotes for you.
The system message constrains the model to the retrieved chunks.

```sql
DECLARE @context NVARCHAR(MAX) = (
    SELECT STRING_AGG(
        CONCAT('[', PolicyName, ']: ', ChunkText),
        CHAR(10) + CHAR(10))
    FROM #TopK
);

DECLARE @question NVARCHAR(MAX) =
    N'How long is the warranty on a pair of headphones?';

DECLARE @payload NVARCHAR(MAX) = JSON_OBJECT(
    'messages':    JSON_ARRAY(
        JSON_OBJECT('role':'system','content':
            N'Answer the user question using ONLY the provided policy excerpts. If the answer is not in the excerpts, say "I don''t know based on the provided policies." Cite the policy name in brackets.'),
        JSON_OBJECT('role':'system','content': CONCAT(N'Policy excerpts:', CHAR(10), @context)),
        JSON_OBJECT('role':'user','content': @question)),
    'temperature': 0.1,    -- low temp for grounded Q&A
    'max_tokens':  500
);

SELECT LEFT(@payload, 800) AS PayloadPreview;
```

**Expected output** (truncated)

```json
{
  "messages": [
    {"role":"system","content":"Answer the user question using ONLY ..."},
    {"role":"system","content":"Policy excerpts:\n[Audio Warranty]: All audio ..."},
    {"role":"user","content":"How long is the warranty on a pair of headphones?"}
  ],
  "temperature":0.1,
  "max_tokens":500
}
```

**Why this matters** — `JSON_OBJECT` / `JSON_ARRAY` escape quotes safely. The
exam contrasts this with naive string concatenation, which breaks the moment a
chunk contains a literal `"`.

---

### Step 5: Call the chat model and parse `$.result.choices[0].message.content`

```sql
DECLARE @chatUrl NVARCHAR(4000) =
    'https://YOUR-RESOURCE.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-01';
DECLARE @response NVARCHAR(MAX);
DECLARE @ret INT;

EXEC @ret = sp_invoke_external_rest_endpoint
     @url        = @chatUrl,
     @method     = 'POST',
     @credential = [https://YOUR-RESOURCE.openai.azure.com],
     @payload    = @payload,
     @timeout    = 230,
     @response   = @response OUTPUT;

-- *** The most-missed RAG detail on the exam ***
-- sp_invoke_external_rest_endpoint wraps every body under "result":
--   { "response": { "status": { "http": { "code": 200 } } },
--     "result":   { "choices": [ { "message": { "content": "..." } } ] } }
SELECT
    HttpCode = JSON_VALUE(@response, '$.response.status.http.code'),
    Answer   = JSON_VALUE(@response, '$.result.choices[0].message.content');
```

**Expected output** (exact text depends on the LLM)

| HttpCode | Answer                                                                                          |
| :------- | :---------------------------------------------------------------------------------------------- |
| 200      | Headphones carry a 2-year manufacturer warranty covering defects in materials and workmanship… |

**Why this matters** — this is the JSON-path question DP-800 candidates miss
most often. The OpenAI REST contract is `$.choices[0].message.content`, but
when called via `sp_invoke_external_rest_endpoint` the entire body is wrapped
under `$.result`. Always remember the `result` prefix.

---

### Step 6: Wrap it in a single procedure

```sql
CREATE OR ALTER PROCEDURE dbo.AskCatalog
    @question NVARCHAR(MAX),
    @top_n    INT = 3,
    @answer   NVARCHAR(MAX) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    -- Embed the question
    DECLARE @qPayload NVARCHAR(MAX) = JSON_OBJECT('input': @question);
    DECLARE @qResp    NVARCHAR(MAX);
    EXEC sp_invoke_external_rest_endpoint
         @url        = 'https://YOUR-RESOURCE.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01',
         @method     = 'POST',
         @credential = [https://YOUR-RESOURCE.openai.azure.com],
         @payload    = @qPayload,
         @response   = @qResp OUTPUT;

    DECLARE @qvec VECTOR(1536) = CAST(
        JSON_QUERY(@qResp, '$.result.data[0].embedding') AS VECTOR(1536));

    -- Retrieve top-K context
    DECLARE @context NVARCHAR(MAX) = (
        SELECT STRING_AGG(
            CONCAT('[', PolicyName, ']: ', ChunkText),
            CHAR(10) + CHAR(10))
        FROM (
            SELECT TOP (@top_n) PolicyName, ChunkText
            FROM   dbo.ProductPolicies
            WHERE  Embedding IS NOT NULL
            ORDER  BY VECTOR_DISTANCE('cosine', Embedding, @qvec) ASC
            WITH APPROXIMATE
        ) AS t
    );

    -- Generate the answer
    DECLARE @payload NVARCHAR(MAX) = JSON_OBJECT(
        'messages':    JSON_ARRAY(
            JSON_OBJECT('role':'system','content':
                N'Answer using ONLY the provided policy excerpts. Cite the [Policy Name]. Say "I don''t know" if unsupported.'),
            JSON_OBJECT('role':'system','content': CONCAT(N'Excerpts:', CHAR(10), @context)),
            JSON_OBJECT('role':'user','content': @question)),
        'temperature': 0.1,
        'max_tokens':  500
    );

    DECLARE @resp NVARCHAR(MAX);
    EXEC sp_invoke_external_rest_endpoint
         @url        = 'https://YOUR-RESOURCE.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-01',
         @method     = 'POST',
         @credential = [https://YOUR-RESOURCE.openai.azure.com],
         @payload    = @payload,
         @response   = @resp OUTPUT;

    SET @answer = JSON_VALUE(@resp, '$.result.choices[0].message.content');
END;
GO

-- Try it
DECLARE @ans NVARCHAR(MAX);
EXEC dbo.AskCatalog
     @question = N'Can I return an opened pair of headphones?',
     @answer   = @ans OUTPUT;
SELECT @ans AS Answer;
```

**Expected output**

| Answer                                                                                                                          |
| :------------------------------------------------------------------------------------------------------------------------------ |
| Yes — opened electronics may be returned within 30 days, but a 15% restocking fee applies. \[Electronics Returns]\[Audio Warranty] |

**Why this matters** — DP-800 expects you to recognise the full RAG pipeline
as something a database can do natively. No application server, no separate
orchestration framework.

---

## Cleanup

```sql
USE Lab01_Products;
GO
DROP PROCEDURE IF EXISTS dbo.AskCatalog;
DROP TABLE     IF EXISTS dbo.ProductPolicies;
DROP TABLE     IF EXISTS #TopK;

-- Credential and master key — drop only if you are done with Lab 2 entirely
-- (other labs may reuse the credential).
DROP DATABASE SCOPED CREDENTIAL [https://YOUR-RESOURCE.openai.azure.com];
-- DROP MASTER KEY;  -- only if no other credentials exist

USE master;
GO
-- DROP DATABASE Lab01_Products;  -- only if you are done with Labs 1–3
```

---

## Common Issues & Errors

| Error / symptom | Cause | Fix |
| :--- | :--- | :--- |
| `Msg 33177 — sp_invoke_external_rest_endpoint is not enabled` | Feature flag off on Azure SQL | `EXEC sp_configure 'external rest endpoint enabled', 1; RECONFIGURE;` |
| `HTTP 401 from Azure OpenAI` despite a valid key | Credential `IDENTITY` is `MANAGED IDENTITY` or `SHARED ACCESS SIGNATURE` instead of `HTTPEndpointHeaders` | Recreate the credential with `IDENTITY = 'HTTPEndpointHeaders'` and `SECRET = '{"api-key":"..."}'` |
| `JSON_VALUE returned NULL` on `$.choices[0].message.content` | Reading the response as if you called the API directly | `sp_invoke_external_rest_endpoint` wraps the body under `$.result`. Read `$.result.choices[0].message.content` |
| `Cannot convert JSON array to VECTOR(1536)` | Embedding model dimension does not match the column | `text-embedding-3-small` = 1536; `text-embedding-3-large` = 3072; `text-embedding-ada-002` = 1536 |
| LLM still hallucinates despite RAG | System message not strict, or retrieval missed the answer | Add "ONLY use the provided excerpts" to the system message; raise `@top_n`; consider hybrid retrieval (Lab 3) |

---

## Exam Tips

> [!tip] Exam Tips
>
> - The canonical path is `$.result.choices[0].message.content` — not `$.choices[0]`. Memorise this
> - Database-scoped credentials for Azure OpenAI use `IDENTITY = 'HTTPEndpointHeaders'` and a JSON `SECRET` containing the `api-key` header. Don't confuse this with the `MANAGED IDENTITY` or `SAS` identities used by Azure Storage credentials
> - `JSON_OBJECT` / `JSON_ARRAY` escape quotes for you. Plain string concatenation breaks the moment your chunk contains a `"` character
> - The RAG flow on the exam is always **Retrieve → Augment → Generate** — know which T-SQL primitive serves each step

---

## Key Takeaways

- A complete RAG pipeline fits in one stored procedure: embed → retrieve → augment → generate → parse
- Both the embedding response and the chat completion response are wrapped under `$.result` by `sp_invoke_external_rest_endpoint`
- The retrieve leg is just `SELECT TOP (N) ... ORDER BY VECTOR_DISTANCE(...) WITH APPROXIMATE`
- Low temperature (0.0–0.2) plus an "only use the provided excerpts" system message are the two grounding levers

---

## Related Topics

- [01-RAG Use Cases](../../11-rag/01-rag-use-cases.md)
- [02-Prompts and Responses](../../11-rag/02-prompts-and-responses.md)
- [01-External Models](../../09-models-embeddings/01-external-models.md)
- [03-Chunking & Generation](../../09-models-embeddings/03-chunking-generation.md)
- [End-to-End RAG Walkthrough](../code-examples/tsql/rag-end-to-end-walkthrough.md)

---

## Official Documentation

- <https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-invoke-external-rest-endpoint-transact-sql>
- <https://learn.microsoft.com/en-us/azure/azure-sql/database/ai-artificial-intelligence-intelligent-applications>
- <https://learn.microsoft.com/en-us/sql/t-sql/functions/json-object-transact-sql>
- <https://learn.microsoft.com/en-us/sql/t-sql/functions/json-value-transact-sql>
- <https://learn.microsoft.com/en-us/azure/ai-services/openai/reference>

---

**[← Back to lab index](./labs.md) | [↑ Back to overview](../../dp-800-overview.md)**
