---
title: Prompts and Responses in T-SQL RAG
type: study-material
tags:
  - dp-800
  - sp-invoke-external-rest-endpoint
  - rag
  - json
  - llm-response
---

# Prompts and Responses in T-SQL RAG

## Overview

`sp_invoke_external_rest_endpoint` is the T-SQL stored procedure for calling HTTP endpoints from within SQL Server and SQL Database in Fabric. It enables calling Azure OpenAI (or any REST API) directly from T-SQL, making it possible to build a complete RAG pipeline without leaving SQL. This topic covers the full workflow: retrieving context, converting to JSON, constructing prompts, calling the model, and parsing responses.

## sp_invoke_external_rest_endpoint Syntax

```sql
EXEC sp_invoke_external_rest_endpoint
    @url         = N'https://...',           -- required: endpoint URL
    @method      = N'POST',                  -- required: HTTP method
    @headers     = N'{"key":"value"}',       -- optional: JSON object of headers
    @payload     = N'{"key":"value"}',       -- optional: request body (JSON string)
    @credential  = [MyCredential],           -- optional: DATABASE SCOPED CREDENTIAL
    @response    = @response_var OUTPUT,     -- output parameter
    @timeout     = 30;                       -- optional: seconds (default 30)
```

The `@response` output parameter contains the full HTTP response as a JSON string:

```json
{
  "response": {
    "status": { "http": { "code": 200, "description": "OK" } },
    "headers": { "Content-Type": "application/json" }
  },
  "result": { ... }   // The actual API response body
}
```

## DATABASE SCOPED CREDENTIAL for OpenAI

```sql
-- Store the API key securely (never hardcode in procedure)
CREATE DATABASE SCOPED CREDENTIAL [AzureOpenAICredential]
WITH IDENTITY = 'HTTPEndpointHeaders',
SECRET = '{"api-key": "your-azure-openai-api-key-here"}';
```

The credential is referenced in `sp_invoke_external_rest_endpoint` via `@credential` — the API key header is automatically injected.

## Converting Data to JSON with FOR JSON

Before including SQL data in a prompt, convert it to a text/JSON format the LLM can understand:

```sql
-- Convert query results to JSON
DECLARE @products_json NVARCHAR(MAX);

SELECT @products_json = (
    SELECT TOP 5
        ProductId   AS id,
        ProductName AS name,
        Price       AS price,
        Description AS description
    FROM dbo.Products
    WHERE InStock = 1
    ORDER BY Price ASC
    FOR JSON PATH
);
-- Result: [{"id":1,"name":"Wireless Headphones","price":49.99,"description":"..."}]
```

```sql
-- Convert to formatted text (more readable for LLM prompts)
DECLARE @products_text NVARCHAR(MAX) = '';

SELECT @products_text = STRING_AGG(
    CONCAT('Product: ', ProductName,
           ' | Price: $', CAST(Price AS VARCHAR(20)),
           ' | ', LEFT(Description, 200)),
    CHAR(10))  -- newline between products
FROM (
    SELECT TOP 5 ProductName, Price, Description
    FROM dbo.Products WHERE InStock = 1
    ORDER BY Price ASC
) t;
```

## Constructing Prompts

The Azure OpenAI chat completions API expects a JSON array of messages with `role` and `content`:

```sql
-- Build the messages array for a RAG prompt
DECLARE @system_message NVARCHAR(MAX) = N'You are a helpful product advisor.
Answer the customer question based ONLY on the provided product information.
If the answer is not in the product list, say "I don''t have that information."
Do not make up any product details.';

DECLARE @user_question NVARCHAR(500) = N'What are your cheapest in-ear headphones?';
DECLARE @context       NVARCHAR(MAX) = @products_text;  -- from above

-- Construct the full messages JSON
DECLARE @messages NVARCHAR(MAX) = N'[
    {"role": "system", "content": ' + QUOTENAME(@system_message, '"') + '},
    {"role": "user", "content": "Context:\n' + REPLACE(@context, '"', '\"') +
    '\n\nQuestion: ' + REPLACE(@user_question, '"', '\"') + '"}
]';
```

## Full RAG Procedure — End to End

```sql
CREATE OR ALTER PROCEDURE dbo.ProductRAG
    @user_question NVARCHAR(500),
    @top_k         INT = 5
AS
BEGIN
    SET NOCOUNT ON;

    -- ── Step 1: Embed the user question ──────────────────────────────────
    DECLARE @query_vector VECTOR(1536);

    SELECT @query_vector = CAST(
        PREDICT(MODEL = [MyEmbeddingModel],
                DATA = (SELECT @user_question AS input_text)) AS VECTOR(1536));

    -- ── Step 2: Retrieve relevant products via vector search ──────────────
    DECLARE @context NVARCHAR(MAX) = '';

    SELECT @context = STRING_AGG(
        CONCAT('Product: ', p.ProductName,
               CHAR(10), 'Price: $', CAST(p.Price AS VARCHAR(20)),
               CHAR(10), 'Description: ', LEFT(p.Description, 300),
               CHAR(10), '---'),
        CHAR(10))
    FROM VECTOR_SEARCH(
        TABLE = dbo.Products AS p,
        COLUMN = DescriptionVector,
        SIMILAR_TO = @query_vector,
        METRIC = 'cosine',
        TOP_N = @top_k
    ) AS vs;

    -- ── Step 3: Construct the prompt ──────────────────────────────────────
    DECLARE @system_msg  NVARCHAR(MAX) = N'You are a helpful product advisor. '
        + 'Answer using ONLY the products listed below. '
        + 'If you cannot answer from the list, say "I don''t know."';

    DECLARE @user_msg    NVARCHAR(MAX) =
        N'Available products:' + CHAR(10) + @context
        + CHAR(10) + CHAR(10) + 'Customer question: ' + @user_question;

    DECLARE @payload NVARCHAR(MAX) = N'{
        "messages": [
            {"role": "system", "content": ' + QUOTENAME(@system_msg, '"') + '},
            {"role": "user",   "content": ' + QUOTENAME(@user_msg,   '"') + '}
        ],
        "max_tokens": 500,
        "temperature": 0
    }';

    -- ── Step 4: Call Azure OpenAI ─────────────────────────────────────────
    DECLARE @response NVARCHAR(MAX);

    EXEC sp_invoke_external_rest_endpoint
        @url        = N'https://myopenai.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-01',
        @method     = N'POST',
        @headers    = N'{"Content-Type": "application/json"}',
        @payload    = @payload,
        @credential = [AzureOpenAICredential],
        @response   = @response OUTPUT;

    -- ── Step 5: Parse and return the response ─────────────────────────────
    DECLARE @http_code INT = JSON_VALUE(@response, '$.response.status.http.code');

    IF @http_code <> 200
    BEGIN
        DECLARE @error_msg NVARCHAR(MAX) = JSON_VALUE(@response, '$.result.error.message');
        RAISERROR('OpenAI API error (HTTP %d): %s', 16, 1, @http_code, @error_msg);
        RETURN;
    END;

    SELECT
        JSON_VALUE(@response, '$.result.choices[0].message.content') AS Answer,
        JSON_VALUE(@response, '$.result.usage.total_tokens')          AS TotalTokens,
        JSON_VALUE(@response, '$.result.model')                       AS ModelUsed;
END;
```

```sql
-- Usage
EXEC dbo.ProductRAG @user_question = 'What headphones do you have under $100?';
```

## Parsing JSON Responses

### JSON_VALUE — Single Scalar Values

```sql
DECLARE @response NVARCHAR(MAX) = '{"result": {"choices": [{"message": {"content": "Answer here"}}], "usage": {"total_tokens": 123}}}';

-- Extract single values
SELECT
    JSON_VALUE(@response, '$.result.choices[0].message.content') AS Answer,
    JSON_VALUE(@response, '$.result.usage.prompt_tokens')         AS PromptTokens,
    JSON_VALUE(@response, '$.result.usage.completion_tokens')     AS CompletionTokens,
    JSON_VALUE(@response, '$.result.usage.total_tokens')          AS TotalTokens;
```

### OPENJSON — Parsing Arrays

When the LLM returns a JSON array (e.g., a list of extracted entities):

```sql
DECLARE @llm_json_response NVARCHAR(MAX) = '
{
  "result": {
    "choices": [{
      "message": {
        "content": "{\"products\": [{\"id\": 1, \"reason\": \"Best match\"}, {\"id\": 7, \"reason\": \"Good value\"}]}"
      }
    }]
  }
}';

-- First extract the content string
DECLARE @content NVARCHAR(MAX) = JSON_VALUE(@llm_json_response, '$.result.choices[0].message.content');

-- Then parse the JSON within the content
SELECT
    j.id,
    j.reason
FROM OPENJSON(@content, '$.products')
WITH (
    id     INT            '$.id',
    reason NVARCHAR(500)  '$.reason'
) AS j;
```

### JSON_QUERY — Extracting JSON Objects/Arrays

```sql
-- Extract an entire array (not a scalar)
DECLARE @choices NVARCHAR(MAX) = JSON_QUERY(@response, '$.result.choices');

-- Extract a nested object
DECLARE @usage NVARCHAR(MAX) = JSON_QUERY(@response, '$.result.usage');
```

## Structured Output — Forcing JSON Responses

Use the `response_format` parameter to ensure the LLM returns valid JSON:

```sql
DECLARE @payload NVARCHAR(MAX) = N'{
    "messages": [
        {"role": "system", "content": "Classify the sentiment and extract key topics. Return JSON with fields: sentiment (Positive/Negative/Neutral), topics (array of strings), confidence (0-1)."},
        {"role": "user",   "content": "The delivery was super fast and the product is amazing!"}
    ],
    "response_format": {"type": "json_object"},
    "max_tokens": 200,
    "temperature": 0
}';

DECLARE @response NVARCHAR(MAX);
EXEC sp_invoke_external_rest_endpoint
    @url        = N'https://myopenai.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-01',
    @method     = N'POST',
    @headers    = N'{"Content-Type": "application/json"}',
    @payload    = @payload,
    @credential = [AzureOpenAICredential],
    @response   = @response OUTPUT;

-- Parse structured JSON response
DECLARE @content NVARCHAR(MAX) = JSON_VALUE(@response, '$.result.choices[0].message.content');

SELECT
    JSON_VALUE(@content, '$.sentiment')  AS Sentiment,
    JSON_VALUE(@content, '$.confidence') AS Confidence,
    JSON_QUERY(@content, '$.topics')     AS TopicsArray;

-- Parse the topics array
SELECT value AS Topic
FROM OPENJSON(JSON_QUERY(@content, '$.topics'));
```

## Error Handling

```sql
-- Robust error handling pattern for LLM calls
DECLARE @response NVARCHAR(MAX);
DECLARE @http_code INT;
DECLARE @api_error NVARCHAR(MAX);

BEGIN TRY
    EXEC sp_invoke_external_rest_endpoint
        @url        = @endpoint_url,
        @method     = N'POST',
        @headers    = N'{"Content-Type": "application/json"}',
        @payload    = @payload,
        @credential = [AzureOpenAICredential],
        @response   = @response OUTPUT,
        @timeout    = 30;

    SET @http_code = JSON_VALUE(@response, '$.response.status.http.code');

    -- Handle different HTTP status codes
    IF @http_code = 200
    BEGIN
        -- Success: extract and use the response
        SELECT JSON_VALUE(@response, '$.result.choices[0].message.content') AS Answer;
    END
    ELSE IF @http_code = 429
    BEGIN
        -- Rate limited: log and retry
        SET @api_error = 'Rate limit exceeded. Retry after: '
            + JSON_VALUE(@response, '$.response.headers.Retry-After');
        RAISERROR(@api_error, 10, 1);  -- severity ≤10 = informational (not caught by CATCH; use 11+ to trigger CATCH)
    END
    ELSE IF @http_code = 400
    BEGIN
        -- Bad request: likely prompt too long
        SET @api_error = JSON_VALUE(@response, '$.result.error.message');
        RAISERROR('API bad request: %s', 16, 1, @api_error);
    END
    ELSE
    BEGIN
        SET @api_error = JSON_VALUE(@response, '$.result.error.message');
        RAISERROR('API error (HTTP %d): %s', 16, 1, @http_code, @api_error);
    END

END TRY
BEGIN CATCH
    -- Log errors to a table for monitoring
    INSERT INTO dbo.RAGErrorLog (ErrorMessage, ErrorTime, Payload)
    VALUES (ERROR_MESSAGE(), GETUTCDATE(), @payload);
    THROW;
END CATCH;
```

## Token Management

```sql
-- Estimate tokens to avoid exceeding context window
-- Rule of thumb: ~4 characters per token for English

DECLARE @estimated_tokens INT =
    LEN(@system_msg) / 4 +   -- system message
    LEN(@context) / 4 +       -- retrieved context
    LEN(@user_question) / 4 + -- user question
    500;                       -- reserve for response

-- Check against model limit (gpt-4o-mini = 128,000 tokens)
IF @estimated_tokens > 120000
BEGIN
    -- Truncate context to fit
    SET @context = LEFT(@context, (120000 - LEN(@system_msg)/4 - LEN(@user_question)/4 - 500) * 4);
END;
```

## Use Cases

- **In-database RAG**: Build complete RAG pipelines in T-SQL without application-layer code — useful for scheduled jobs, stored procedure-based APIs
- **Batch processing**: Process thousands of rows through an LLM in a T-SQL loop or cursor
- **Classification**: Classify customer feedback, support tickets, or products using an LLM called from a SQL UPDATE statement
- **Structured extraction**: Extract entities (dates, names, amounts) from unstructured text into structured columns

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `HTTP 401 Unauthorized` | Wrong or missing API key in credential | Recreate DATABASE SCOPED CREDENTIAL with correct key |
| `HTTP 429 Too Many Requests` | Rate limit hit | Implement retry with exponential backoff; increase quota |
| `HTTP 400 Bad Request` | Prompt too long or malformed JSON | Check token count; validate JSON payload; escape special chars |
| JSON parse error on response | Response is not valid JSON | Check `$.response.status.http.code` first; may be an HTML error page |
| `QUOTENAME` returns NULL for inputs > 128 chars | `QUOTENAME` accepts `nvarchar(128)` — returns NULL (not a truncated value) for longer input | For long strings, use `REPLACE(@text, '"', '\"')` instead |
| Inconsistent responses | Temperature > 0 | Set `"temperature": 0` for factual/deterministic output |

## Exam Tips

- `sp_invoke_external_rest_endpoint` is the T-SQL bridge to external REST APIs including Azure OpenAI
- The response JSON structure has two levels: `$.response.status` (HTTP metadata) and `$.result` (API payload)
- `DATABASE SCOPED CREDENTIAL` with `IDENTITY = 'HTTPEndpointHeaders'` injects headers (like API keys) automatically
- `FOR JSON PATH` converts query results to JSON for embedding in prompts
- `JSON_VALUE` extracts scalars; `JSON_QUERY` extracts objects/arrays; `OPENJSON` parses arrays into rows
- Always check the HTTP status code before parsing the response body — errors have different JSON structure

## Key Takeaways

- `sp_invoke_external_rest_endpoint` calls external HTTP APIs from T-SQL — no application code needed
- Prompt construction: system message (instructions) + context (retrieved data as text/JSON) + user question
- Parse LLM responses with `JSON_VALUE` for scalars and `OPENJSON` for arrays
- Always handle HTTP errors (401, 429, 400) before extracting the response content
- Use `"temperature": 0` for deterministic factual responses; `"response_format": {"type": "json_object"}` for structured output

## Related Topics

- [01-RAG Use Cases](./01-rag-use-cases.md)
- [01-External Models](../09-models-embeddings/01-external-models.md)
- [03-Hybrid Search & RRF](../10-intelligent-search/03-hybrid-search-rrf.md)

## Official Documentation

- [sp_invoke_external_rest_endpoint](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-invoke-external-rest-endpoint-transact-sql)
- [FOR JSON (T-SQL)](https://learn.microsoft.com/en-us/sql/relational-databases/json/format-query-results-as-json-with-for-json-sql-server)
- [OPENJSON (T-SQL)](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql)
- [Azure OpenAI Chat Completions API](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#chat-completions)

---

**[← Previous](./01-rag-use-cases.md) | [↑ Back to Section](./README.md)**
