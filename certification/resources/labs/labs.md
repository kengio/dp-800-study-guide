---
title: DP-800 Hands-on Labs
type: lab-index
tags:
  - dp-800
  - hands-on
  - labs
  - vector-search
  - rag
  - full-text-search
  - mcp
status: complete
---

# DP-800 Hands-on Labs

A small, runnable lab pack for the AI-heavy Domain 3 of the DP-800 exam, plus the
adjacent security/REST endpoint material from Domain 2. Each lab is a single
T-SQL script you can paste into SSMS, Azure Data Studio, or sqlcmd and watch
behave the way the exam expects.

> [!abstract]
>
> - Four labs covering ==vector search==, ==RAG==, ==full-text + hybrid search==, and ==MCP server endpoints==
> - All four labs share a toy `Products` catalogue so you can run them against the same database
> - Every script targets SQL Server 2025 / Azure SQL Database / SQL database in Microsoft Fabric
> - Each lab includes setup, numbered steps with expected output, cleanup, and a common-issues table

> [!tip] What the Exam Tests
>
> - Knowing the SQL feels different from reciting it — the labs train your fingers on `CREATE VECTOR INDEX`, `WITH APPROXIMATE`, `sp_invoke_external_rest_endpoint`, `CONTAINSTABLE`, and `$.result.choices[0].message.content`
> - The exam questions assume you have actually run RAG against an LLM — the labs build that intuition
> - Hands-on practice surfaces the gotchas that pure reading misses (metric mismatch fallback, JSON envelope, stop-list suppression)
> - Lab 4 is also valuable as architectural scaffolding even on instances where MCP-server endpoints are still preview

---

## Lab catalogue

| Lab | Topic | DP-800 domain | Estimated time | Skill level |
| :--- | :--- | :--- | :--- | :--- |
| [01-Vector Search](./01-vector-search-lab.md) | `VECTOR` + DiskANN index + ANN vs ENN | Domain 3 (Intelligent Search) | 25 min | Intermediate |
| [02-RAG](./02-rag-lab.md) | Chunk → embed → retrieve → call LLM → parse | Domain 3 (RAG) | 35 min | Intermediate |
| [03-Full-text + Hybrid](./03-fulltext-search-lab.md) | Full-text catalog + `CONTAINS` + RRF hybrid | Domain 3 (Intelligent Search) | 25 min | Beginner |
| [04-MCP Server](./04-mcp-lab.md) | MCP server endpoint config + Copilot integration | Domain 1 (AI-assisted tools) / Domain 2 (Endpoints) | 30 min | Intermediate |

---

## Prerequisites for all labs

You need **one** of the following SQL engines:

- **SQL Server 2025 CU1+** with `PREVIEW_FEATURES = ON` at the instance level
- **Azure SQL Database** with the `VECTOR` data type enabled (default in the preview region)
- **SQL database in Microsoft Fabric** (current preview includes the vector and external-model surface)

You also need:

- An **Azure OpenAI** (or Microsoft Foundry) resource in the same region/tenant, with two deployments:
  - `text-embedding-3-small` (1536-dim) — used by labs 1 and 2
  - `gpt-4o-mini` (or any chat completion model) — used by lab 2
- The endpoint URL and an API key for the resource (Lab 2 walks through storing it as a database-scoped credential)
- A SQL login that holds `db_owner` on the lab database (the labs create credentials, external models, and indexes — none of which are grantable to non-owners in the current previews)
- `sqlcmd`, **SSMS 20+**, or **Azure Data Studio** for running the scripts

Optional for Lab 4:

- **VS Code** with the GitHub Copilot extension, or **Copilot in Fabric** chat
- Node.js 20+ on PATH if you want to launch the `@modelcontextprotocol/server-mssql` package locally

---

## How to run

Pick your client and paste the lab's **Setup** block first, then each numbered
step in order. The labs are written to be re-runnable: every `CREATE` is
guarded, and a `Cleanup` block tears the database back down.

### sqlcmd

```bash
# Run a single lab end-to-end against Azure SQL Database
sqlcmd -S myserver.database.windows.net \
       -d master \
       -U myadmin -P 'YourStrongPassword!' \
       -G \
       -i 01-vector-search-lab.sql
```

Tip: you can save each fenced ```sql block to a `.sql` file with your editor of
choice; the `.md` files here are the source of truth so they stay in the study
guide.

### SSMS / Azure Data Studio

1. Connect to your SQL Server 2025 / Azure SQL / Fabric SQL instance
2. Open a new query window pointing at the **master** database (the lab creates its own database)
3. Paste the Setup block, then F5
4. Step through each subsequent step — each is independent, so you can stop and resume

### Lab order

Run the labs in the order listed. Lab 1 creates the shared `Lab01_Products`
schema that Labs 2 and 3 extend. Lab 4 is independent — it walks through MCP
configuration on the same database but does not require any extra schema.

---

## Troubleshooting common across labs

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `Msg 49981 — VECTOR data type is not supported` | Preview features not enabled | Run `EXEC sp_configure 'preview features', 1; RECONFIGURE;` on SQL Server 2025, or move to a region where Azure SQL has VECTOR enabled |
| `Msg 42274 — VECTOR_SEARCH TVF is not supported on the current index version` | Using the legacy TVF against a new-style DiskANN index | Switch to `SELECT TOP (N) ... ORDER BY VECTOR_DISTANCE(...) WITH APPROXIMATE` |
| `Msg 33177 — sp_invoke_external_rest_endpoint is not enabled` | Feature flag off on Azure SQL | `EXEC sp_configure 'external rest endpoint enabled', 1; RECONFIGURE;` |
| DiskANN index silently slow | Metric mismatch — query uses `cosine`, index built with `euclidean` | The engine logs a warning and falls back to exact kNN. Drop and recreate the index with the metric you actually query |
| `Msg 15247 — User does not have permission to perform this action` | Trying to create credentials without `CONTROL DATABASE` | Run as `db_owner`, or have an admin create the credential and `GRANT REFERENCES` |

---

## Related Topics

- [02-Vector Search](../../10-intelligent-search/02-vector-search.md)
- [03-Hybrid Search & RRF](../../10-intelligent-search/03-hybrid-search-rrf.md)
- [01-RAG Use Cases](../../11-rag/01-rag-use-cases.md)
- [03-MCP Server Endpoints](../../04-ai-assisted-tools/03-mcp-server-endpoints.md)
- [End-to-End RAG Walkthrough](../code-examples/tsql/rag-end-to-end-walkthrough.md)
- [Vector Search Patterns](../code-examples/tsql/vector-search-patterns.md)

---

## Official Documentation

- <https://learn.microsoft.com/en-us/sql/t-sql/data-types/vector-data-type>
- <https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-invoke-external-rest-endpoint-transact-sql>
- <https://learn.microsoft.com/en-us/sql/relational-databases/search/full-text-search>
- <https://learn.microsoft.com/en-us/azure/azure-sql/database/ai-artificial-intelligence-intelligent-applications>
- <https://modelcontextprotocol.io/>

---

**[↑ Back to overview](../../dp-800-overview.md)**
