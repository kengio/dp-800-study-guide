---
title: RAG Use Cases and Architecture
type: study-material
tags:
  - dp-800
  - rag
  - llm
  - use-cases
  - architecture
---

# RAG Use Cases and Architecture

## Overview

Retrieval-Augmented Generation (RAG) grounds large language model (LLM) responses in data from a database, preventing **hallucinations** and providing up-to-date, accurate answers. Rather than relying on what the model "knows" from training, RAG retrieves relevant context from a trusted data source and includes it in the prompt. SQL Database in Fabric and Azure SQL are natural RAG backends because they store both structured data and embeddings in one place.

> [!abstract]
> - Covers the RAG pattern (Retrieve-Augment-Generate), use cases, and Azure SQL as a RAG backend
> - RAG grounds LLM responses in real data, preventing hallucinations and using current information
> - Key exam topics: RAG pattern steps, grounding vs fine-tuning distinction, combined vector+FTS retrieval

> [!tip] What the Exam Tests
> - RAG pattern: (1) embed user query → (2) search DB with VECTOR_SEARCH + CONTAINS → (3) retrieve top-K chunks → (4) build prompt → (5) call LLM → (6) return grounded response
> - **Grounding ≠ fine-tuning** — RAG injects context at inference time; the model's weights are not changed
> - Azure SQL is a natural RAG backend: stores both structured data AND vector embeddings in one database

---

## The RAG Pattern

```text
User Question
     │
     ▼
┌────────────────────────────────────────────────┐
│  RETRIEVE                                       │
│  1. Embed the user question (query vector)      │
│  2. Search database: vector + full-text         │
│  3. Retrieve top-K relevant chunks/records      │
└────────────────────────────────────────────────┘
     │ retrieved context (text)
     ▼
┌────────────────────────────────────────────────┐
│  AUGMENT                                        │
│  4. Construct prompt:                           │
│     - System message (instructions)             │
│     - Context (retrieved data)                  │
│     - User question                             │
└────────────────────────────────────────────────┘
     │ prompt (system + context + question)
     ▼
┌────────────────────────────────────────────────┐
│  GENERATE                                       │
│  5. Call LLM (e.g., GPT-4o-mini)               │
│  6. Return grounded response to user            │
└────────────────────────────────────────────────┘
```

---

## Grounding Benefits

| Without RAG | With RAG |
| :--- | :--- |
| LLM may hallucinate facts | ==Answers grounded in actual database records== |
| Knowledge cutoff from training | Uses current data (pricing, inventory, policies) |
| No access to proprietary data | Can reference internal documents, customer records |
| Generic responses | Specific, personalized responses |
| No citation possible | Can cite the source documents used |

---

## RAG Use Cases

### 1. Customer Support Assistant

```text
Use case: Customer asks "What is my return policy for electronics?"

Retrieve:
- Full-text search on policy documents for "electronics return"
- Vector search for semantically similar policy chunks

Augment:
- System: "Answer based only on the provided policy documents."
- Context: [3 most relevant policy chunks]
- User: "What is my return policy for electronics?"

Generate:
- "Based on our policy, electronics can be returned within 30 days
   with original packaging. Opened items incur a 15% restocking fee."
```

Database structure:
```sql
CREATE TABLE dbo.PolicyDocuments (
    PolicyId     INT           NOT NULL PRIMARY KEY,
    Title        NVARCHAR(500) NOT NULL,
    Content      NVARCHAR(MAX) NOT NULL,
    Category     NVARCHAR(100) NOT NULL,
    LastUpdated  DATE          NOT NULL
);

CREATE TABLE dbo.PolicyChunks (
    ChunkId      INT           NOT NULL PRIMARY KEY IDENTITY,
    PolicyId     INT           NOT NULL REFERENCES dbo.PolicyDocuments(PolicyId),
    ChunkText    NVARCHAR(MAX) NOT NULL,
    Embedding    VECTOR(1536)  NULL
);

CREATE FULLTEXT INDEX ON dbo.PolicyChunks (ChunkText LANGUAGE 1033)
KEY INDEX PK_PolicyChunks ON PolicyCatalog;
```

### 2. Product Search and Recommendations

```text
Use case: User types "I need headphones for long video calls"

Retrieve:
- Vector search on product descriptions
- Filter by category = 'Headphones', in_stock = 1
- Top 5 matching products

Augment:
- System: "You are a product advisor. Recommend from the provided products only."
- Context: [product names, prices, key features for top 5 results]
- User: "I need headphones for long video calls"

Generate:
- "For long video calls, I recommend the Jabra Evolve2 55. It features..."
```

### 3. Document Q&A

```text
Use case: Internal knowledge base search
"How do I configure SSO for our HR system?"

Retrieve:
- Vector search across IT documentation chunks
- Filter by doc_type = 'IT' or 'Security'

Augment:
- System: "Answer questions about IT procedures using the provided documentation."
- Context: [relevant procedure steps and configuration guides]
- User: "How do I configure SSO for our HR system?"

Generate:
- Step-by-step answer grounded in the actual IT documentation
```

### 4. Data Analysis Assistant

```text
Use case: Business user asks "Which products had the highest return rate last month?"

Retrieve:
- Structured SQL query (not vector search — this is tabular data)
- SELECT TOP 10 products by return_rate WHERE period = 'last_month'

Augment:
- System: "You are a data analyst. Summarize the provided query results."
- Context: [SQL result set as formatted text/JSON]
- User: "Which products had the highest return rate last month?"

Generate:
- "Last month, wireless earbuds had the highest return rate at 8.3%,
   followed by smart watches at 6.1%..."
```

---

## Structured vs Unstructured Data in RAG

### Unstructured Data (Documents, Articles)

```text
Source: PDF manuals, Word docs, web pages, emails
Processing:
  1. Extract text
  2. Chunk into segments
  3. Generate embeddings per chunk
  4. Store in vector table
Retrieval: Vector search + full-text search
```

### Structured Data (Tables, Reports)

```text
Source: Orders, Products, Customers tables
Processing: No chunking needed — query results are the context
Retrieval: Direct SQL query (SELECT, JOIN, aggregate)
Context format: Table → JSON (FOR JSON) or formatted text
```

### Hybrid: Structured + Unstructured

```sql
-- Example: combine structured product data with unstructured reviews
DECLARE @query_vector VECTOR(1536) = ...;

-- Structured: get product details
SELECT p.ProductId, p.ProductName, p.Price, p.Category
FROM dbo.Products p
WHERE p.Category = 'Headphones' AND p.InStock = 1

-- Unstructured: get relevant review chunks
UNION ALL
SELECT r.ProductId, r.ReviewText AS ProductName, NULL, 'review'
FROM dbo.ReviewChunks r
WHERE r.ProductId IN (1, 7, 23)
  AND VECTOR_DISTANCE('cosine', r.Embedding, @query_vector) < 0.3;
```

---

## Multi-Turn RAG (Conversational)

For multi-turn conversations, include conversation history in the prompt:

```sql
CREATE TABLE dbo.ConversationHistory (
    MessageId   INT           NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SessionId   UNIQUEIDENTIFIER NOT NULL,
    Role        NVARCHAR(20)  NOT NULL,  -- 'user' or 'assistant'
    Content     NVARCHAR(MAX) NOT NULL,
    CreatedAt   DATETIME2     NOT NULL DEFAULT GETUTCDATE()
);
```

```sql
-- Build conversation context for the prompt
DECLARE @history NVARCHAR(MAX);

SELECT @history = STRING_AGG(
    '{"role": "' + Role + '", "content": ' + QUOTENAME(Content, '"') + '}',
    ','
) WITHIN GROUP (ORDER BY CreatedAt)
FROM dbo.ConversationHistory
WHERE SessionId = @session_id
  AND CreatedAt >= DATEADD(HOUR, -1, GETUTCDATE());  -- last hour only

-- Include in message array: [system, ...history, user_current]
```

---

## Architecture Patterns

### In-Database RAG (All in SQL)

```text
SQL Database → T-SQL Procedure:
  1. PREDICT(MODEL=EmbeddingModel) → query vector
  2. VECTOR_SEARCH → relevant chunks
  3. BUILD prompt string
  4. sp_invoke_external_rest_endpoint → LLM
  5. RETURN response
```

Advantages: All processing in one place, no application code, latency in single round trip

### Application-Layer RAG

```text
Application (Python/C#):
  1. Embed user query via SDK
  2. SQL query with vector/FTS search
  3. Build prompt in application code
  4. Call OpenAI SDK
  5. Return response
```

Advantages: More flexible, easier to debug, better error handling

### Azure AI Search + SQL

```text
SQL Database → synced to Azure AI Search index
User Query → Azure AI Search (hybrid built-in) → Top results
Top results → LLM via Azure OpenAI
```

Advantages: Managed search service with built-in RRF; scales independently of database

---

## Use Cases

| Use Case | Data Type | Search Type | Latency Target |
| :--- | :--- | :--- | :--- |
| Policy/FAQ chat | Documents | Hybrid (FTS + vector) | < 3 seconds |
| Product advisor | Catalog | Vector + structured filter | < 2 seconds |
| Document Q&A | Unstructured | Vector | < 3 seconds |
| Analytics summary | Structured tables | SQL query only | < 5 seconds |
| Customer history | Structured | SQL (exact match on IDs) | < 1 second |

---

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| LLM gives wrong answer despite RAG | Retrieved wrong context | Improve retrieval (hybrid, better embeddings, chunking) |
| LLM "makes up" information | Context doesn't contain the answer | Add "Only answer from the provided context. Say I don't know if not found." |
| Slow end-to-end latency | Embedding + search + LLM in sequence | Parallelize where possible; use ANN index; use faster model (gpt-4o-mini) |
| Context too long for LLM | Too many chunks retrieved | Limit to 3–5 most relevant chunks; use smaller chunks |
| Inconsistent answers | Non-deterministic LLM | ==Set `temperature=0` for factual Q&A== |

---

## Exam Tips

> [!tip] Exam Tips
> - RAG = **Retrieve → Augment → Generate** — know each step and what SQL object is involved at each step
> - Grounding prevents hallucination — the LLM is constrained to provided context
> - Structured data uses direct SQL queries; unstructured uses vector/FTS search
> - The system message in the prompt is where you instruct the LLM to "only answer from provided context"
> - Multi-turn conversations require storing history — include recent turns in the prompt

---

## Key Takeaways

- RAG architecture: embed query → retrieve relevant data → build prompt with context → call LLM → return response
- SQL Database is a natural RAG backend: stores both structured data and vector embeddings in one place
- Different use cases need different retrieval strategies: documents use vector search, structured data uses SQL queries
- Grounding the LLM in retrieved context prevents hallucination and enables use of current proprietary data

---

## Related Topics

- [02-Prompts & Responses](./02-prompts-and-responses.md)
- [03-Hybrid Search & RRF](../10-intelligent-search/03-hybrid-search-rrf.md)
- [01-External Models](../09-models-embeddings/01-external-models.md)

---

## Official Documentation

- [RAG with Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/ai-artificial-intelligence-intelligent-applications)
- [Azure OpenAI RAG Patterns](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/retrieval-augmented-generation)
- [Fabric SQL AI Features](https://learn.microsoft.com/en-us/fabric/database/sql/ai-embedding-generation)

---

**[↑ Back to Section](./rag.md) | [Next →](./02-prompts-and-responses.md)**
