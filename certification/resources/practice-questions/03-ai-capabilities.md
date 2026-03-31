---
title: "Practice Questions: Implement AI Capabilities"
type: practice-questions
tags:
  - dp-800
  - practice-questions
  - ai-capabilities
---

# Practice Questions: Implement AI Capabilities

Domain 3 covers 20–25% of the DP-800 exam.

---

## Question 1: CREATE EXTERNAL MODEL Syntax

**Question** *(Medium)*:

A developer wants to call Azure OpenAI's `text-embedding-3-small` model from T-SQL to generate embeddings. Which statement correctly registers this model in Azure SQL Database?

A. `CREATE MODEL EmbeddingModel TYPE = AZURE_OPENAI WITH (MODEL = 'text-embedding-3-small')`
B. `CREATE EXTERNAL MODEL EmbeddingModel WITH (LOCATION = '...', CREDENTIAL = ..., TASK = EMBEDDINGS, MODEL = 'text-embedding-3-small')`
C. `CREATE EXTERNAL MODEL EmbeddingModel WITH (ENDPOINT = '...', KEY = '...', TYPE = 'OpenAI')`
D. `EXEC sp_create_external_model 'EmbeddingModel', 'text-embedding-3-small'`

> [!success]- Answer
> **B. `CREATE EXTERNAL MODEL EmbeddingModel WITH (LOCATION = '...', CREDENTIAL = ..., TASK = EMBEDDINGS, MODEL = 'text-embedding-3-small')`**
>
> The full `CREATE EXTERNAL MODEL` syntax requires:
> - `LOCATION`: The Azure OpenAI endpoint URL
> - `CREDENTIAL`: A database-scoped credential holding the API key
> - `TASK`: The model's task type (e.g., `EMBEDDINGS`, `CHAT_COMPLETION`, `CLASSIFICATION`)
> - `MODEL`: The deployment name in Azure OpenAI
>
> Once created, the model is invoked with `SELECT * FROM PREDICT(MODEL = EmbeddingModel, ...)`.

---

## Question 2: External Model — Multimodal Task

**Question** *(Easy)*:

A developer registers an external model with `TASK = CHAT_COMPLETION` pointing to a GPT-4o deployment. Which capability does this enable that a text-only model does not support?

A. Generating SQL queries from natural language
B. Accepting image inputs alongside text prompts
C. Producing structured JSON output exclusively
D. Running entirely within the SQL Server process

> [!success]- Answer
> **B. Accepting image inputs alongside text prompts**
>
> **Multimodal** models (like GPT-4o) can process both text and images in a single prompt. This enables scenarios such as analyzing product photos stored in Azure Blob Storage or extracting data from document images.
>
> Text-only models handle natural language and can produce JSON output — these are not exclusive to multimodal models. All external models call remote APIs; they do not run inside SQL Server.

---

## Question 3: VECTOR Data Type

**Question** *(Easy)*:

A developer creates a column to store embeddings from `text-embedding-ada-002`, which produces 1536-dimensional vectors. Which column definition is correct?

A. `EmbeddingVector varbinary(max)`
B. `EmbeddingVector float NOT NULL`
C. `EmbeddingVector VECTOR(1536)`
D. `EmbeddingVector nvarchar(max)`

> [!success]- Answer
> **C. `EmbeddingVector VECTOR(1536)`**
>
> The `VECTOR` data type in Azure SQL Database (preview) is purpose-built for storing dense float vectors. `VECTOR(1536)` declares a 1536-dimensional vector, matching the output of `text-embedding-ada-002`.
>
> `varbinary(max)` could store raw bytes but does not support vector operations (`VECTOR_DISTANCE`, `VECTOR_SEARCH`). Storing embeddings as `nvarchar(max)` (JSON array string) is a legacy workaround that is far less efficient.

---

## Question 4: VECTOR_DISTANCE — Interpreting Results

**Question** *(Medium)*:

A developer runs a similarity search using `VECTOR_DISTANCE('cosine', queryEmbedding, docEmbedding)`. Two documents return distances of 0.12 and 0.87. Which document is more semantically similar to the query?

A. The document with distance 0.87, because higher values mean greater similarity
B. The document with distance 0.12, because lower cosine distance means greater similarity
C. They cannot be compared without normalization
D. The document with distance 0.87, because cosine distance ranges from 0 to 1 and 0.87 is closer to 1

> [!success]- Answer
> **B. The document with distance 0.12, because lower cosine distance means greater similarity**
>
> `VECTOR_DISTANCE` returns a distance metric — **lower values indicate greater similarity** regardless of the metric used (`cosine`, `euclidean`, or `dot`). A cosine distance of 0 means identical vectors; 1 means completely orthogonal (unrelated) vectors.
>
> Sort results `ORDER BY distance ASC` and take `TOP N` to get the most similar documents.

---

## Question 5: VECTOR_DISTANCE — Metric Selection

**Question** *(Medium)*:

A developer must choose between `cosine`, `euclidean`, and `dot` distance metrics for a semantic search application. The embedding vectors are already normalized (unit vectors). Which metric is equivalent to cosine similarity for normalized vectors?

A. euclidean
B. cosine
C. dot (dot product)
D. All three are equivalent for normalized vectors

> [!success]- Answer
> **C. dot (dot product)**
>
> For **unit-normalized vectors** (magnitude = 1), the dot product is mathematically equivalent to cosine similarity. Since `VECTOR_NORMALIZE` or the embedding model has already normalized the vectors, using `dot` is computationally cheaper than `cosine` (fewer operations).
>
> `euclidean` distance is not equivalent to cosine similarity even for normalized vectors. This is why `VECTOR_NORMALIZE` is often applied before indexing — it unlocks the use of the faster `dot` metric.

---

## Question 6: VECTOR_NORMALIZE Purpose

**Question** *(Easy)*:

What is the primary purpose of `VECTOR_NORMALIZE(vector)` in Azure SQL Database?

A. To compress the vector to reduce storage size
B. To scale the vector to unit length (magnitude = 1) to enable dot-product-based similarity
C. To round float values to 4 decimal places
D. To convert the vector from VECTOR type to varbinary for storage

> [!success]- Answer
> **B. To scale the vector to unit length (magnitude = 1) to enable dot-product-based similarity**
>
> `VECTOR_NORMALIZE` divides each element of the vector by the vector's Euclidean magnitude, producing a unit vector. This enables using the cheaper dot product metric as a substitute for cosine similarity, and is a prerequisite for building a DiskANN index (which requires normalized vectors for accurate inner-product search).

---

## Question 7: Embedding Maintenance — Change Tracking vs CDC

**Question** *(Hard)*:

A production table `dbo.Articles` has an embedding column that must stay synchronized whenever the `BodyText` column is updated. The team wants minimal overhead and does not need before-images of changed rows — only the current content. Which approach is most appropriate?

A. CDC (Change Data Capture) — because it captures all column changes
B. A DML trigger on `dbo.Articles` that calls `sp_invoke_external_rest_endpoint` inline
C. Change Tracking with a background job that queries `CHANGETABLE` and re-generates embeddings for changed PKs
D. An Azure Function with a SQL trigger binding monitoring the change table

> [!success]- Answer
> **C. Change Tracking with a background job that queries `CHANGETABLE` and re-generates embeddings for changed PKs**
>
> **Change Tracking** records which rows changed (by PK) with minimal overhead — no full row images stored. A background job uses `CHANGETABLE(CHANGES dbo.Articles, @lastSyncVersion)` to find changed rows, retrieves current `BodyText`, generates new embeddings via the external model, and updates the embedding column.
>
> Triggers calling REST endpoints inline (option B) add latency to every write and can cause timeouts. CDC is heavier than needed when you only need current values. Azure Functions are valid but add external infrastructure complexity.

---

## Question 8: Chunking Strategy — Fixed-Size vs Sentence-Based

**Question** *(Medium)*:

A developer is preparing legal contract documents for RAG (Retrieval Augmented Generation). The documents have complex sentence structures and paragraph-level semantics. Which chunking strategy best preserves semantic context?

A. Fixed-size chunking with no overlap — simplest and most consistent
B. Fixed-size chunking with 10–20% overlap — prevents context loss at chunk boundaries
C. Sentence-based or paragraph-based chunking — preserves natural semantic units
D. Single-token chunking — maximum granularity

> [!success]- Answer
> **C. Sentence-based or paragraph-based chunking — preserves natural semantic units**
>
> For documents with rich semantic structure (legal contracts, technical documentation), **sentence-based or paragraph-based chunking** ensures that each chunk contains a complete thought. Fixed-size chunking can split sentences mid-clause, degrading retrieval quality.
>
> Fixed-size with overlap (option B) is a reasonable compromise for less structured text. Single-token chunking is impractical for semantic search. The best strategy depends on document structure, but for legal text, semantic chunking is preferred.

---

## Question 9: VECTORPROPERTY Usage

**Question** *(Easy)*:

A developer needs to determine the number of dimensions in a `VECTOR` column before performing operations. Which function returns this metadata?

A. `DATALENGTH(EmbeddingVector)`
B. `VECTORPROPERTY(EmbeddingVector, 'Dimensions')`
C. `COLUMNPROPERTY(OBJECT_ID('dbo.Articles'), 'EmbeddingVector', 'Dimensions')`
D. `LEN(EmbeddingVector)`

> [!success]- Answer
> **B. `VECTORPROPERTY(EmbeddingVector, 'Dimensions')`**
>
> `VECTORPROPERTY` is a scalar function that returns metadata about a VECTOR value. The `'Dimensions'` property returns the number of elements (dimensions) in the vector. Other valid properties include `'BaseType'` (returns the underlying numeric type, e.g., `'float32'`).
>
> `DATALENGTH` returns bytes; `LEN` is for strings; `COLUMNPROPERTY` is for general column metadata and does not expose vector dimensions.

---

## Question 10: VECTOR_SEARCH — ANN vs ENN

**Question** *(Hard)*:

A developer is building a real-time product search for an e-commerce site with 50 million product embeddings. They choose `VECTOR_SEARCH` with `METRIC = 'cosine'` and `WITH (index_type = 'DISKANN')`. What tradeoff does ANN (Approximate Nearest Neighbor) search make compared to ENN (Exact Nearest Neighbor)?

A. ANN is slower but always returns the mathematically closest vectors
B. ANN is faster but may occasionally miss some of the true nearest neighbors
C. ANN requires more memory but uses less CPU
D. ANN and ENN produce identical results; ANN is just the newer algorithm name

> [!success]- Answer
> **B. ANN is faster but may occasionally miss some of the true nearest neighbors**
>
> **ANN (Approximate Nearest Neighbor)** uses index structures (like DiskANN) to find results that are *approximately* the closest vectors, dramatically reducing search time from O(n) to O(log n) or better. In practice, the top results are highly accurate (>95% recall) for most similarity search applications.
>
> **ENN (Exact Nearest Neighbor)** performs a full scan and is guaranteed correct but does not scale to tens of millions of vectors. For production semantic search, the speed gains of ANN far outweigh the marginal accuracy loss.

---

## Question 11: Full-Text Search — CONTAINS vs FREETEXT

**Question** *(Medium)*:

A developer needs to search a `Description` column for rows where the word "running" appears, including its inflectional forms like "run", "ran", and "runs". Which full-text predicate should they use?

A. `WHERE CONTAINS(Description, '"running"')` — for exact phrase matching
B. `WHERE FREETEXT(Description, 'running')` — for linguistic inflectional matching
C. `WHERE Description LIKE '%running%'` — for pattern matching
D. `WHERE CONTAINS(Description, 'running*')` — for prefix matching

> [!success]- Answer
> **B. `WHERE FREETEXT(Description, 'running')` — for linguistic inflectional matching**
>
> `FREETEXT` performs linguistic analysis including inflectional matching (run/ran/runs/running), synonym expansion, and thesaurus lookup — ideal for natural language search.
>
> `CONTAINS` with `"running"` matches the exact word only. `CONTAINS` with `running*` matches prefixes like "running", "runner" but not "ran". `LIKE '%running%'` cannot use a full-text index and does not do linguistic matching.

---

## Question 12: CONTAINSTABLE — RANK Column

**Question** *(Medium)*:

A developer uses `CONTAINSTABLE(dbo.Articles, BodyText, 'database')` and joins the result to `dbo.Articles`. What does the `RANK` column in the CONTAINSTABLE result represent?

A. The row number in the result set
B. A relevance score (higher = more relevant) used to sort results by match quality
C. The number of times the search term appears in the column
D. The full-text index key value

> [!success]- Answer
> **B. A relevance score (higher = more relevant) used to sort results by match quality**
>
> `CONTAINSTABLE` (and `FREETEXTTABLE`) return a result set with `KEY` (the full-text key column value) and `RANK` (an integer relevance score from 0–1000, higher is more relevant). This enables ranked results:
> ```sql
> SELECT a.Title, ct.[RANK]
> FROM CONTAINSTABLE(dbo.Articles, BodyText, 'database') ct
> JOIN dbo.Articles a ON ct.[KEY] = a.ArticleId
> ORDER BY ct.[RANK] DESC
> ```

---

## Question 13: Hybrid Search — Reciprocal Rank Fusion

**Question** *(Hard)*:

A developer implements hybrid search combining full-text search results and vector search results. They use Reciprocal Rank Fusion (RRF) to merge the ranked lists. What is the purpose of RRF?

A. To eliminate duplicate documents from both result sets
B. To combine ranked lists from multiple retrieval methods into a single unified ranking without requiring score normalization
C. To re-rank results using a cross-encoder language model
D. To weight keyword matches higher than semantic matches

> [!success]- Answer
> **B. To combine ranked lists from multiple retrieval methods into a single unified ranking without requiring score normalization**
>
> **Reciprocal Rank Fusion** computes a combined score as the sum of `1 / (k + rank_i)` across all retrieval methods, where `k` is a constant (typically 60) and `rank_i` is the document's rank in each method's result list. This works without needing to normalize scores across different methods (BM25 scores vs. cosine distances have different scales).
>
> RRF consistently outperforms simple score fusion in retrieval benchmarks. It does not use cross-encoders (that is re-ranking) or eliminate duplicates (those appear as the same document ranked in both lists and receive a boosted combined score).

---

## Question 14: RAG — sp_invoke_external_rest_endpoint

**Question** *(Hard)*:

A developer uses `sp_invoke_external_rest_endpoint` to call Azure OpenAI's chat completion API from T-SQL. The payload must be valid JSON. Which T-SQL clause correctly builds the messages array in the request body?

A. `'{"messages": [{"role": "user", "content": "' + @question + '"}]}'`
B. `JSON_OBJECT('messages': JSON_ARRAY(JSON_OBJECT('role': 'user', 'content': @question)))`
C. `(SELECT 'user' AS role, @question AS content FOR JSON PATH)`
D. `CONCAT('{"messages":[{"role":"user","content":', @question, '}]}')`

> [!success]- Answer
> **B. `JSON_OBJECT('messages': JSON_ARRAY(JSON_OBJECT('role': 'user', 'content': @question)))`**
>
> SQL Server 2022 / Azure SQL introduced `JSON_OBJECT` and `JSON_ARRAY` functions that safely construct JSON without string concatenation. They properly escape special characters in variable values, preventing JSON injection.
>
> String concatenation (options A and D) breaks if `@question` contains quotes or backslashes. `FOR JSON PATH` (option C) works but returns a JSON array, not the full messages object structure.

---

## Question 15: RAG — DATABASE SCOPED CREDENTIAL

**Question** *(Medium)*:

A developer needs `sp_invoke_external_rest_endpoint` to authenticate to Azure OpenAI using an API key. The key must not appear in the T-SQL code. What is the correct approach?

A. Pass the API key in the `@headers` parameter as a plain text string
B. Store the key in a SQL Server Agent job step and retrieve it at runtime
C. Create a DATABASE SCOPED CREDENTIAL with the API key and reference it in the `@credential` parameter
D. Encrypt the key using `ENCRYPTBYPASSPHRASE` and store it in a table

> [!success]- Answer
> **C. Create a DATABASE SCOPED CREDENTIAL with the API key and reference it in the `@credential` parameter**
>
> `sp_invoke_external_rest_endpoint` accepts an `@credential` parameter (a `NVARCHAR` name referencing a DATABASE SCOPED CREDENTIAL). The credential stores the API key in the encrypted credential store and is referenced without exposing the key in code:
>
> ```sql
> CREATE DATABASE SCOPED CREDENTIAL OpenAICredential
>   WITH IDENTITY = 'HTTPEndpointHeaders',
>   SECRET = '{"api-key": "your-key-here"}';
> ```
>
> This keeps secrets out of source code and T-SQL scripts. The `IDENTITY = 'HTTPEndpointHeaders'` tells the procedure to inject the SECRET as HTTP headers.

---

**[← Back to Practice Questions](./practice-questions.md)**
