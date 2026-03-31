---
title: T-SQL Code Examples
type: code-examples
tags:
  - dp-800
  - tsql
  - code-examples
---

# T-SQL Code Examples

This folder contains standalone T-SQL code examples referenced throughout the DP-800 study guide. Each file focuses on a specific pattern or feature area and includes working, exam-relevant examples with inline explanations.

These examples complement the study notes in `certification/` and are particularly useful for hands-on practice against an Azure SQL Database instance.

> [!tip] How to Practice
> Run these examples against an **Azure SQL Database** (free tier works) or a **Fabric SQL analytics endpoint**. Most patterns also work in SQL Server 2022+ where noted.

---

## Code Example Files

| File | Description |
|------|-------------|
| [window-functions.md](./window-functions.md) | Window function patterns: ROW_NUMBER, RANK, DENSE_RANK, LAG/LEAD, running totals, moving averages, and ROWS vs RANGE framing |
| [json-patterns.md](./json-patterns.md) | JSON construction and parsing patterns: FOR JSON PATH/AUTO, OPENJSON, JSON_VALUE, JSON_QUERY, JSON_MODIFY, JSON_OBJECT, JSON_ARRAYAGG |
| [rag-patterns.md](./rag-patterns.md) | `sp_invoke_external_rest_endpoint` patterns for RAG: building prompts, calling Azure OpenAI chat completion, parsing responses, and database scoped credential setup |
| [vector-search-patterns.md](./vector-search-patterns.md) | Vector search and hybrid search queries: VECTOR_DISTANCE, VECTOR_SEARCH with DiskANN, CONTAINSTABLE, and Reciprocal Rank Fusion (RRF) combining both |
| [security-patterns.md](./security-patterns.md) | Security implementation patterns: Row-Level Security (filter and block predicates), Dynamic Data Masking (all masking functions), and permission management (GRANT/DENY/REVOKE examples) |

---

**[← Back to Resources](../../dp-800-overview.md) | [↑ Back to Certification](../../../dp-800-overview.md)**
