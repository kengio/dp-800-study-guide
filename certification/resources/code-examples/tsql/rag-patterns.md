---
title: RAG Patterns with sp_invoke_external_rest_endpoint
type: code-examples
tags:
  - dp-800
  - tsql
  - code-examples
  - rag
  - rest-endpoint
  - azure-openai
---

# RAG Patterns with sp_invoke_external_rest_endpoint

Retrieval-Augmented Generation (RAG) in Azure SQL Database and Microsoft Fabric SQL uses
`sp_invoke_external_rest_endpoint` to call Azure OpenAI APIs directly from T-SQL.
The typical pipeline is: **embed query → vector search → retrieve context → call LLM → return answer**.

> [!abstract] What You'll Learn
> - Database scoped credential setup for Azure OpenAI REST calls
> - Generating embeddings via sp_invoke_external_rest_endpoint
> - Building RAG prompts from retrieved document context
> - End-to-end RAG stored procedure: embed, search, prompt, respond

## Table of Contents

- [[#Database Scoped Credentials Setup]]
- [[#Generating Embeddings via REST]]
- [[#Building Prompts from Retrieved Context]]
- [[#Calling Azure OpenAI Chat Completion]]
- [[#Parsing and Storing LLM Responses]]
- [[#End-to-End RAG Stored Procedure]]

---

## Database Scoped Credentials Setup

> [!info] Use database scoped credentials to securely store API keys so sp_invoke_external_rest_endpoint can authenticate to Azure OpenAI.

Before calling any external REST endpoint, the database must have a master key and a
credential that carries the API key as an HTTP header.

```sql
-- Step 1: Create the database master key (required for credential encryption)
-- Skip if it already exists
IF NOT EXISTS (
    SELECT * FROM sys.symmetric_keys
    WHERE name = '##MS_DatabaseMasterKey##'
)
    CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongPassword123!';

-- Step 2: Create a DATABASE SCOPED CREDENTIAL for the Azure OpenAI endpoint
-- IDENTITY = 'HTTPEndpointHeaders' tells SQL to pass SECRET as request headers
-- SECRET is a JSON object whose keys become HTTP header names
CREATE DATABASE SCOPED CREDENTIAL [https://myopenai.openai.azure.com]
WITH IDENTITY = 'HTTPEndpointHeaders',
     SECRET = '{"api-key": "your-api-key-here"}';

-- Required permissions:
--   CREATE MASTER KEY  → needs CONTROL on database
--   CREATE DATABASE SCOPED CREDENTIAL → needs CONTROL on database
--   EXECUTE sp_invoke_external_rest_endpoint → needs EXECUTE on the procedure

-- Verify the credential was created (key value is not exposed)
SELECT name, credential_identity, create_date
FROM sys.database_scoped_credentials
WHERE name = 'https://myopenai.openai.azure.com';
```

> [!tip] Exam Tip
> The credential name must exactly match the base URL passed to `@url` — the stored procedure resolves credentials by prefix match. A mismatched name silently fails authentication.

---

## Generating Embeddings via REST

> [!info] Use the embeddings endpoint to convert text into vectors for storage in VECTOR columns and subsequent similarity search.

Convert a text string into a vector by calling the Azure OpenAI embeddings endpoint.
The response contains a floating-point array that can be cast to a `VECTOR` column.

```sql
-- Generate an embedding for a single text string
DECLARE @text    NVARCHAR(MAX) = 'What is vector search in Azure SQL?';
DECLARE @url     NVARCHAR(MAX) = 'https://myopenai.openai.azure.com/openai/deployments/'
                                 + 'text-embedding-3-small/embeddings?api-version=2024-02-01';
DECLARE @payload  NVARCHAR(MAX);
DECLARE @response NVARCHAR(MAX);

-- Build the request body: {"input": "<text>"}
SET @payload = JSON_OBJECT('input': @text);

-- Call Azure OpenAI; response is a JSON string in @response
EXEC sp_invoke_external_rest_endpoint
    @url        = @url,
    @method     = 'POST',
    @credential = [https://myopenai.openai.azure.com],
    @payload    = @payload,
    @response   = @response OUTPUT;

-- The embedding lives at $.result.data[0].embedding (a JSON array of floats)
SELECT
    JSON_QUERY(@response, '$.result.data[0].embedding') AS embedding_json,
    JSON_VALUE(@response, '$.result.usage.total_tokens') AS tokens_used;

-- To store the result in a table with a VECTOR(1536) column:
-- CAST(JSON_QUERY(...) AS VECTOR(1536)) is supported in Azure SQL / Fabric SQL
UPDATE Documents
SET    embedding = CAST(
           JSON_QUERY(@response, '$.result.data[0].embedding') AS VECTOR(1536)
       )
WHERE  doc_id = 42;
```

### Batch embedding helper pattern

```sql
-- Process unembedded rows one at a time inside a cursor or loop
DECLARE @doc_id  INT;
DECLARE @content NVARCHAR(MAX);

DECLARE doc_cursor CURSOR FAST_FORWARD FOR
    SELECT doc_id, content
    FROM   Documents
    WHERE  embedding IS NULL;

OPEN doc_cursor;
FETCH NEXT FROM doc_cursor INTO @doc_id, @content;

WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @emb_payload  NVARCHAR(MAX) = JSON_OBJECT('input': @content);
    DECLARE @emb_response NVARCHAR(MAX);

    EXEC sp_invoke_external_rest_endpoint
        @url        = 'https://myopenai.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01',
        @method     = 'POST',
        @credential = [https://myopenai.openai.azure.com],
        @payload    = @emb_payload,
        @response   = @emb_response OUTPUT;

    UPDATE Documents
    SET    embedding = CAST(
               JSON_QUERY(@emb_response, '$.result.data[0].embedding') AS VECTOR(1536)
           )
    WHERE  doc_id = @doc_id;

    FETCH NEXT FROM doc_cursor INTO @doc_id, @content;
END;

CLOSE doc_cursor;
DEALLOCATE doc_cursor;
```

> [!warning] Watch Out
> Cursor-based embedding is slow for large datasets and may hit API rate limits. For bulk embedding, consider batching via application code with retry logic and rate-limit awareness.

---

## Building Prompts from Retrieved Context

> [!info] Use STRING_AGG to concatenate top-K document chunks into a system message that grounds the LLM response.

After a vector search returns the most relevant document chunks, concatenate them into
a context string and inject that string into the system message.

```sql
DECLARE @user_question NVARCHAR(MAX) = 'How do I configure vector indexes?';
DECLARE @context       NVARCHAR(MAX);
DECLARE @system_message NVARCHAR(MAX);

-- Retrieve top-3 document chunks by similarity score
-- (vector search result assumed to be pre-computed or in a CTE)
SELECT @context = STRING_AGG(
           CAST(d.content AS NVARCHAR(MAX)),
           CHAR(10) + '---' + CHAR(10)   -- separator between chunks
       )
FROM (
    SELECT TOP 3
           d.content,
           vs.similarity_score
    FROM   Documents       d
    JOIN   VectorSearchResults vs ON vs.doc_id = d.doc_id
    ORDER BY vs.similarity_score DESC
) top_docs;

-- Guard against empty context (no matching documents found)
IF @context IS NULL OR LEN(@context) = 0
    SET @context = 'No relevant documentation was found.';

-- Build system message with injected context
SET @system_message =
    N'You are a helpful assistant for Azure SQL Database and Microsoft Fabric SQL. '
    + N'Answer the user question using ONLY the context provided below. '
    + N'If the context does not contain enough information, say so.' + CHAR(10)
    + N'--- CONTEXT ---' + CHAR(10)
    + @context + CHAR(10)
    + N'--- END CONTEXT ---';

-- Preview the assembled prompt (useful during development)
SELECT
    LEN(@system_message) AS system_message_chars,
    LEFT(@system_message, 500)  AS system_message_preview;
```

---

## Calling Azure OpenAI Chat Completion

> [!info] Use the chat completions endpoint after assembling the context-enriched prompt to generate a natural-language answer.

Use the assembled messages to call a chat completions deployment (e.g., `gpt-4o`).

```sql
DECLARE @chat_payload  NVARCHAR(MAX);
DECLARE @chat_response NVARCHAR(MAX);

-- Build the full chat completion request payload
SET @chat_payload = JSON_OBJECT(
    'messages': JSON_ARRAY(
        JSON_OBJECT('role': 'system',  'content': @system_message),
        JSON_OBJECT('role': 'user',    'content': @user_question)
    ),
    'temperature': 0.1,       -- low temperature for factual, deterministic answers
    'max_tokens':  800        -- cap response length
);

-- Call the chat completions endpoint
EXEC sp_invoke_external_rest_endpoint
    @url        = 'https://myopenai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01',
    @method     = 'POST',
    @credential = [https://myopenai.openai.azure.com],
    @payload    = @chat_payload,
    @response   = @chat_response OUTPUT;

-- Inspect the raw response during development
SELECT @chat_response AS raw_response;
```

### Response structure (reference)

```json
{
  "result": {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "To configure a vector index in Azure SQL..."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 412,
      "completion_tokens": 95,
      "total_tokens": 507
    }
  },
  "headers": { "Content-Type": "application/json" },
  "status": { "http": { "code": 200, "description": "OK" } }
}
```

---

## Parsing and Storing LLM Responses

> [!info] Use JSON_VALUE to extract the answer, detect errors, and log the full interaction for auditing and cost tracking.

Extract the generated answer from the response JSON, handle errors, and log the
full RAG interaction for auditing.

```sql
-- Extract the assistant's answer from choices[0]
DECLARE @answer      NVARCHAR(MAX);
DECLARE @finish_reason NVARCHAR(50);
DECLARE @total_tokens  INT;

SET @answer       = JSON_VALUE(@chat_response, '$.result.choices[0].message.content');
SET @finish_reason = JSON_VALUE(@chat_response, '$.result.choices[0].finish_reason');
SET @total_tokens  = JSON_VALUE(@chat_response, '$.result.usage.total_tokens');

-- Error handling: Azure OpenAI errors appear in $.result.error
IF JSON_VALUE(@chat_response, '$.result.error.code') IS NOT NULL
BEGIN
    DECLARE @error_msg NVARCHAR(500) =
        'Azure OpenAI error '
        + JSON_VALUE(@chat_response, '$.result.error.code')
        + ': '
        + JSON_VALUE(@chat_response, '$.result.error.message');
    THROW 50001, @error_msg, 1;
END;

-- Warn if the model hit the token limit before finishing
IF @finish_reason = 'length'
    PRINT 'WARNING: Response was truncated (finish_reason = length). Increase max_tokens.';

-- Log the complete RAG interaction for auditing and cost tracking
INSERT INTO RAGLog (
    Question,
    ContextUsed,
    Answer,
    FinishReason,
    TotalTokens,
    CreatedAt
)
VALUES (
    @user_question,
    @context,
    @answer,
    @finish_reason,
    @total_tokens,
    GETUTCDATE()
);

-- Return the answer to the caller
SELECT
    @answer       AS Answer,
    @finish_reason AS FinishReason,
    @total_tokens  AS TotalTokens;
```

### RAGLog table definition

```sql
-- Recommended schema for logging RAG interactions
CREATE TABLE RAGLog (
    log_id       INT            IDENTITY(1,1) PRIMARY KEY,
    Question     NVARCHAR(MAX)  NOT NULL,
    ContextUsed  NVARCHAR(MAX)  NULL,
    Answer       NVARCHAR(MAX)  NULL,
    FinishReason NVARCHAR(50)   NULL,
    TotalTokens  INT            NULL,
    CreatedAt    DATETIME2      NOT NULL DEFAULT GETUTCDATE()
);
```

---

## End-to-End RAG Stored Procedure

> [!info] Use a single stored procedure to encapsulate the complete RAG pipeline for reuse by applications or other procedures.

A complete stored procedure that encapsulates the full RAG pipeline:
embed the query → vector search → retrieve context → call LLM → return answer.

```sql
CREATE OR ALTER PROCEDURE dbo.usp_RAGQuery
    @question NVARCHAR(MAX),   -- user's natural language question
    @top_k    INT = 3          -- number of document chunks to retrieve
AS
BEGIN
    SET NOCOUNT ON;

    -- ----------------------------------------------------------------
    -- Step 1: Embed the user question
    -- ----------------------------------------------------------------
    DECLARE @embed_payload  NVARCHAR(MAX) = JSON_OBJECT('input': @question);
    DECLARE @embed_response NVARCHAR(MAX);

    EXEC sp_invoke_external_rest_endpoint
        @url        = 'https://myopenai.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01',
        @method     = 'POST',
        @credential = [https://myopenai.openai.azure.com],
        @payload    = @embed_payload,
        @response   = @embed_response OUTPUT;

    -- Abort if the embedding call failed
    IF JSON_VALUE(@embed_response, '$.result.error.code') IS NOT NULL
        THROW 50002, 'Embedding API call failed', 1;

    DECLARE @query_vector VECTOR(1536) = CAST(
        JSON_QUERY(@embed_response, '$.result.data[0].embedding') AS VECTOR(1536)
    );

    -- ----------------------------------------------------------------
    -- Step 2: Vector search — find top-K nearest document chunks
    -- VECTOR_DISTANCE returns cosine distance (lower = more similar)
    -- ----------------------------------------------------------------
    DECLARE @context NVARCHAR(MAX);

    SELECT @context = STRING_AGG(
               CAST(d.content AS NVARCHAR(MAX)),
               CHAR(10) + '---' + CHAR(10)
           )
    FROM (
        SELECT TOP (@top_k)
               d.content,
               VECTOR_DISTANCE('cosine', d.embedding, @query_vector) AS distance
        FROM   Documents d
        WHERE  d.embedding IS NOT NULL
        ORDER BY distance ASC
    ) ranked;

    IF @context IS NULL
        SET @context = 'No relevant documents found.';

    -- ----------------------------------------------------------------
    -- Step 3: Build prompt with injected context
    -- ----------------------------------------------------------------
    DECLARE @system_message NVARCHAR(MAX) =
        N'You are an expert on Azure SQL Database and Microsoft Fabric SQL. '
        + N'Answer using only the context below.' + CHAR(10)
        + N'=== CONTEXT ===' + CHAR(10)
        + @context + CHAR(10)
        + N'=== END CONTEXT ===';

    -- ----------------------------------------------------------------
    -- Step 4: Call the LLM (chat completions)
    -- ----------------------------------------------------------------
    DECLARE @chat_payload  NVARCHAR(MAX) = JSON_OBJECT(
        'messages': JSON_ARRAY(
            JSON_OBJECT('role': 'system', 'content': @system_message),
            JSON_OBJECT('role': 'user',   'content': @question)
        ),
        'temperature': 0.1,
        'max_tokens':  800
    );
    DECLARE @chat_response NVARCHAR(MAX);

    EXEC sp_invoke_external_rest_endpoint
        @url        = 'https://myopenai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01',
        @method     = 'POST',
        @credential = [https://myopenai.openai.azure.com],
        @payload    = @chat_payload,
        @response   = @chat_response OUTPUT;

    IF JSON_VALUE(@chat_response, '$.result.error.code') IS NOT NULL
        THROW 50003, 'Chat completion API call failed', 1;

    -- ----------------------------------------------------------------
    -- Step 5: Parse response, log interaction, return answer
    -- ----------------------------------------------------------------
    DECLARE @answer       NVARCHAR(MAX) = JSON_VALUE(@chat_response, '$.result.choices[0].message.content');
    DECLARE @total_tokens INT           = JSON_VALUE(@chat_response, '$.result.usage.total_tokens');

    INSERT INTO RAGLog (Question, ContextUsed, Answer, FinishReason, TotalTokens, CreatedAt)
    VALUES (
        @question,
        @context,
        @answer,
        JSON_VALUE(@chat_response, '$.result.choices[0].finish_reason'),
        @total_tokens,
        GETUTCDATE()
    );

    -- Return the answer to the caller as a result set
    SELECT
        @answer       AS Answer,
        @total_tokens  AS TotalTokens,
        @top_k         AS ChunksRetrieved;
END;
GO

-- Usage
EXEC dbo.usp_RAGQuery
    @question = 'How do I create a vector index in Azure SQL?',
    @top_k    = 3;
```

> [!tip] Exam Tip
> `sp_invoke_external_rest_endpoint` is only available in **Azure SQL Database** and **Fabric SQL** — it does not exist in on-premises SQL Server or Azure SQL Managed Instance. The exam tests platform availability.

---

**[← Back to Code Examples](./README.md) | [↑ Back to Certification](../../../README.md)**
