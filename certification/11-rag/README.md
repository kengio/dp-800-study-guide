---
title: Design and Implement Retrieval-Augmented Generation (RAG)
type: category
tags:
  - dp-800
  - rag
  - llm
  - sp-invoke-external-rest-endpoint
  - ai
status: draft
---

# Design and Implement Retrieval-Augmented Generation (RAG) (Domain 3 — 25–30%)

Building RAG pipelines that convert structured data to JSON, retrieve relevant context via vector search, and send prompts to language models using `sp_invoke_external_rest_endpoint`.

## Topics Overview

```mermaid
flowchart TD
    RAG[RAG Pipeline] --> UseCases[Use Cases]
    RAG --> Prompts[Prompts & REST Calls]
    Prompts --> Convert[Convert Data to JSON]
    Prompts --> Send[Send to LLM]
    Prompts --> Extract[Extract Responses]
```

## Section Contents

| File | Topic | Priority |
| :--- | :--- | :--- |
| [01-rag-use-cases.md](01-rag-use-cases.md) | RAG use cases and architecture patterns | High |
| [02-prompts-and-responses.md](02-prompts-and-responses.md) | sp_invoke_external_rest_endpoint, JSON conversion, LLM responses | High |

## Key Concepts

- **RAG (Retrieval-Augmented Generation)**: Augments LLM prompts with retrieved context to reduce hallucinations
- **sp_invoke_external_rest_endpoint**: SQL Server stored procedure for calling external REST APIs (including AI model endpoints)
- **FOR JSON**: T-SQL clause to convert relational data to JSON for LLM processing
- **Grounding**: Providing factual context from the database in the prompt
- **Prompt Engineering**: Structuring system and user prompts for reliable model responses
- **Structured Output Extraction**: Parsing JSON responses from language models back into SQL

## Related Resources

- [10-Intelligent Search](../10-intelligent-search/README.md)
- [09-Models & Embeddings](../09-models-embeddings/README.md)
- [Official: sp_invoke_external_rest_endpoint](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-invoke-external-rest-endpoint-transact-sql)

---

**[← Back to Intelligent Search](../10-intelligent-search/README.md) | [↑ Back to Certification](../README.md)**
