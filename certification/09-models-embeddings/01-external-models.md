---
title: External Models in SQL Database
type: study-material
tags:
  - dp-800
  - external-models
  - azure-openai
  - model-management
---

# External Models in SQL Database

## Overview

SQL Database in Microsoft Fabric and Azure SQL support calling AI models directly from T-SQL using external model definitions. An external model is a reference to an endpoint (such as Azure OpenAI) that is registered in the database and callable via T-SQL functions. This enables embedding generation, text completion, classification, and other AI operations alongside SQL queries.

## Evaluating Models

Choosing the right model for a task depends on several dimensions:

### Model Capability Dimensions

| Dimension | Considerations | Examples |
| :--- | :--- | :--- |
| **Multimodal** | Can process images, audio, or video in addition to text | GPT-4o, GPT-4 Vision |
| **Multilanguage** | Quality of non-English language understanding and generation | GPT-4, text-embedding-3-large |
| **Structured output** | Reliable JSON/schema-formatted output (function calling) | GPT-4o, GPT-3.5-turbo |
| **Embedding dimension** | Higher dims = more semantic precision; more storage | 1536 (ada-002), 3072 (3-large) |
| **Context window** | Max tokens in/out; affects chunk size and conversation length | 8k, 128k tokens |
| **Latency** | Time per request; smaller models are faster | Ada < GPT-3.5 < GPT-4 |
| **Cost** | Token-based pricing; smaller/older models are cheaper | ada-002 << gpt-4 |

### Common Models and Their Use Cases

| Model | Type | Best For |
| :--- | :--- | :--- |
| `text-embedding-ada-002` | Embedding | General-purpose embeddings; low cost |
| `text-embedding-3-small` | Embedding | Better accuracy than ada-002; efficient |
| `text-embedding-3-large` | Embedding | Highest quality embeddings; 3072 dims |
| `gpt-35-turbo` | Chat completion | Low-latency Q&A, summarization, classification |
| `gpt-4o` | Chat completion | Complex reasoning, multimodal, structured output |
| `gpt-4o-mini` | Chat completion | Cost-effective, fast; good for most tasks |

### Size vs. Accuracy Tradeoffs

```text
Embedding models:
text-embedding-ada-002   → 1536 dims, 1x cost, baseline accuracy
text-embedding-3-small   → 1536 dims, 0.5x cost, better accuracy
text-embedding-3-large   → 3072 dims, 2x cost, best accuracy

Tradeoff: larger embedding models produce more discriminative vectors
at the cost of storage (3072 floats × 4 bytes = 12KB per row) and
slightly higher API latency.

Chat models:
gpt-4o-mini → fastest, lowest cost, sufficient for most RAG generation
gpt-4o      → best quality, supports images, higher cost and latency
gpt-35-turbo → legacy, very fast, limited context
```

## CREATE EXTERNAL MODEL Syntax

In SQL Database in Fabric, register an external model to enable T-SQL calls:

```sql
-- Create a DATABASE SCOPED CREDENTIAL for the Azure OpenAI endpoint
CREATE DATABASE SCOPED CREDENTIAL [MyAzureOpenAICredential]
WITH IDENTITY = 'HTTPEndpointHeaders',
SECRET = '{"api-key": "your-azure-openai-api-key"}';

-- Create the external model (embedding model)
CREATE EXTERNAL MODEL [MyEmbeddingModel]
WITH (
    LOCATION = 'https://myopenai.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings',
    API_FORMAT = 'Azure_OpenAI',
    MODEL_TYPE = EMBEDDINGS,
    CREDENTIAL = [MyAzureOpenAICredential]
);

-- Create a chat completion model
CREATE EXTERNAL MODEL [MyChatModel]
WITH (
    LOCATION = 'https://myopenai.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions',
    API_FORMAT = 'Azure_OpenAI',
    MODEL_TYPE = COMPLETIONS,
    CREDENTIAL = [MyAzureOpenAICredential]
);
```

Key parameters:
- `LOCATION`: The full REST endpoint URL of the model deployment
- `API_FORMAT`: `Azure_OpenAI` or `OpenAI` depending on the provider
- `MODEL_TYPE`: `EMBEDDINGS` or `COMPLETIONS`
- `CREDENTIAL`: References the credential that holds the API key

## Managing External Models

```sql
-- List all external models in the database
SELECT
    name,
    model_type_desc,
    location,
    create_date,
    modify_date
FROM sys.external_models;

-- Check model details
SELECT * FROM sys.external_models WHERE name = 'MyEmbeddingModel';

-- Drop an external model
DROP EXTERNAL MODEL [MyEmbeddingModel];

-- Alter an external model (change credential or location)
ALTER EXTERNAL MODEL [MyEmbeddingModel]
WITH (
    CREDENTIAL = [UpdatedCredential]
);
```

## Calling External Models in T-SQL

### Generating Embeddings with PREDICT

```sql
-- Generate an embedding for a single text value
SELECT PREDICT(MODEL = [MyEmbeddingModel],
               DATA = (SELECT 'Azure SQL Database is a fully managed cloud database' AS input_text))
AS embedding;

-- Generate embeddings for all products
SELECT
    ProductId,
    ProductName,
    Description,
    PREDICT(MODEL = [MyEmbeddingModel],
            DATA = (SELECT Description AS input_text)) AS DescriptionEmbedding
FROM dbo.Products;
```

### Storing Generated Embeddings

```sql
-- Add a vector column to store embeddings
ALTER TABLE dbo.Products
ADD DescriptionEmbedding VECTOR(1536);  -- 1536 dims for text-embedding-3-small

-- Generate and store embeddings for all products
UPDATE p
SET DescriptionEmbedding = CAST(
    PREDICT(MODEL = [MyEmbeddingModel],
            DATA = (SELECT p2.Description AS input_text)
           ) AS VECTOR(1536))
FROM dbo.Products p
CROSS APPLY (SELECT p.Description) p2(Description)
WHERE p.DescriptionEmbedding IS NULL;
```

### Calling Chat Completions via External Model

```sql
-- Format a prompt as JSON for the chat model
DECLARE @messages NVARCHAR(MAX) = N'[
    {"role": "system", "content": "You are a helpful assistant that classifies customer feedback."},
    {"role": "user", "content": "Classify this feedback as Positive, Negative, or Neutral: Great product, arrived fast!"}
]';

-- Call the chat model
DECLARE @result NVARCHAR(MAX);
SELECT @result = PREDICT(
    MODEL = [MyChatModel],
    DATA = (SELECT @messages AS messages)
);

-- Extract the response text
SELECT JSON_VALUE(@result, '$.choices[0].message.content') AS Classification;
```

## Permissions

```sql
-- Grant a user or role permission to use an external model
GRANT EXECUTE ON EXTERNAL MODEL [MyEmbeddingModel] TO [DataScienceRole];

-- Revoke access
REVOKE EXECUTE ON EXTERNAL MODEL [MyEmbeddingModel] FROM [DataScienceRole];
```

## Model Selection Decision Framework

```text
For embedding generation:
├── High accuracy needed? → text-embedding-3-large (3072 dims)
├── Balanced accuracy/cost? → text-embedding-3-small (1536 dims)
└── Legacy/existing systems? → text-embedding-ada-002 (1536 dims)

For text generation (RAG):
├── Fastest, cheapest, good quality? → gpt-4o-mini
├── Best quality, structured JSON output? → gpt-4o
├── Need image analysis? → gpt-4o (multimodal)
└── Very high volume, lowest cost? → gpt-35-turbo

For classification or extraction:
├── Structured JSON output required? → gpt-4o or gpt-4o-mini (JSON mode)
└── Simple binary/multi-class? → Fine-tuned gpt-35-turbo (if available)
```

## Use Cases

- **Product search**: Generate embeddings for product descriptions; store in vector column; enable semantic search
- **Document classification**: Use a completions model to classify incoming documents without custom ML models
- **Customer feedback analysis**: Batch-process feedback rows to generate sentiment scores using T-SQL
- **RAG grounding**: Embed user queries at query time to find similar documents in the database

## Common Issues & Errors

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `Invalid API key` | Wrong secret in credential | Update DATABASE SCOPED CREDENTIAL with correct API key |
| `Model not found` | Wrong deployment name in LOCATION URL | Verify deployment name in Azure OpenAI Studio |
| `Dimension mismatch` | Embedding model returns different dims than VECTOR column | Match VECTOR(n) to the model's actual output dimensions |
| `Rate limit exceeded` | Too many API calls/minute | Implement batching; increase Azure OpenAI quota |
| `PREDICT syntax error` | Wrong column alias (`input_text` required for embeddings) | Use `input_text` as the alias for embedding input column |

## Exam Tips

- `CREATE EXTERNAL MODEL` requires a `DATABASE SCOPED CREDENTIAL` — the API key is stored in the credential, not the model definition
- `MODEL_TYPE = EMBEDDINGS` vs `COMPLETIONS` — different model types have different calling conventions
- `PREDICT` is the T-SQL function for calling external models — used for both embeddings and completions
- Embedding dimension must match the `VECTOR(n)` column size — `text-embedding-3-small` = 1536, `text-embedding-3-large` = 3072
- External models are database-scoped objects — viewable in `sys.external_models`

## Key Takeaways

- External models register AI endpoints as database objects — callable via T-SQL without custom code
- `CREATE EXTERNAL MODEL` + `DATABASE SCOPED CREDENTIAL` is the setup pattern
- `PREDICT(MODEL = ..., DATA = ...)` calls the model and returns results inline with SQL queries
- Match the model type (`EMBEDDINGS` vs `COMPLETIONS`) to the use case

## Related Topics

- [02-Embedding Maintenance](./02-embedding-maintenance.md)
- [03-Chunking & Generation](./03-chunking-generation.md)
- [02-Prompts & Responses](../11-rag/02-prompts-and-responses.md)

## Official Documentation

- [External Models in Fabric SQL](https://learn.microsoft.com/en-us/fabric/database/sql/ai-external-model)
- [CREATE EXTERNAL MODEL](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-external-model-transact-sql)
- [Azure OpenAI Models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)

---

**[↑ Back to Section](./README.md) | [Next →](./02-embedding-maintenance.md)**
