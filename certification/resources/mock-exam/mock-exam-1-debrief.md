---
title: Mock Exam 1 — Debrief
type: debrief
tags:
  - dp-800
  - mock-exam
  - debrief
  - study-plan
---

# Mock Exam 1 — Debrief

> [!abstract]
> - Use this **after** completing Mock Exam 1 and checking your answers
> - Every question maps to a topic file + cheat sheet + key concept
> - The "If you missed N+ in domain X" section at the bottom turns your score into a study plan

> [!tip] How to use this debrief
> 1. List the question numbers you got wrong
> 2. For each, look up the row below — re-read the topic file and the cheat-sheet section it points to
> 3. If you missed **3 or more questions in the same domain**, jump to the **Study Plan** section
> 4. Re-take Mock 1 after a week. Anything wrong twice goes on a focused flashcard list before exam day

---

## Question-by-question map

### Domain 1 — Design and develop (Qs 1–17)

| # | Topic | Key concept tested | Re-read | Cheat sheet |
| :---: | :--- | :--- | :--- | :--- |
| 1 | Columnstore Index for Analytics | Clustered columnstore for analytics-only tables; batch mode | [01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) | [azure-sql-config](../cheat-sheets/azure-sql-config-quick-ref.md) |
| 2 | Temporal Table — Point-in-Time | `FOR SYSTEM_TIME AS OF` | [02-specialized-tables.md](../../01-database-objects/02-specialized-tables.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 3 | JSON_VALUE vs JSON_QUERY | Scalar vs object/array; NULL on type mismatch | [03-json-columns.md](../../01-database-objects/03-json-columns.md), [02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) | [json-functions](../cheat-sheets/json-functions-quick-ref.md) |
| 4 | Window Function Frame | Default frame when `ORDER BY` is specified | [01-ctes-window-functions.md](../../03-advanced-tsql/01-ctes-window-functions.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 5 | Partition Function — RANGE LEFT | RANGE LEFT vs RANGE RIGHT boundary placement | [05-partitioning.md](../../01-database-objects/05-partitioning.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 6 | Recursive CTE — Termination | Anchor + recursive members; `MAXRECURSION` | [01-ctes-window-functions.md](../../03-advanced-tsql/01-ctes-window-functions.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 7 | Indexed View Requirements | `WITH SCHEMABINDING`, unique clustered index, `COUNT_BIG(*)` | [01-views.md](../../02-programmability-objects/01-views.md) | — |
| 8 | Graph Tables — MATCH Syntax | Chained `node-(edge)->node` pattern | [04-graph-queries.md](../../03-advanced-tsql/04-graph-queries.md) | — |
| 9 | NOT EXISTS vs NOT IN | NULL handling; `NOT IN` returns 0 rows when NULL in subquery | [05-correlated-queries-error-handling.md](../../03-advanced-tsql/05-correlated-queries-error-handling.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 10 | Scalar UDF Performance | Row-by-row execution; prevents parallelism | [02-functions.md](../../02-programmability-objects/02-functions.md) | — |
| 11 | Ledger Table — Append-Only | `LEDGER = ON, APPEND_ONLY = ON` | [02-specialized-tables.md](../../01-database-objects/02-specialized-tables.md) | — |
| 12 | JSON_ARRAYAGG | SQL Server 2022+ feature | [02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) | [json-functions](../cheat-sheets/json-functions-quick-ref.md) |
| 13 | MCP Server Authentication | `ActiveDirectoryManagedIdentity` connection string | [03-mcp-server-endpoints.md](../../04-ai-assisted-tools/03-mcp-server-endpoints.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 14 | Columnstore — Delta Rowstore | Delta store for new inserts; threshold for compression | [01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) | — |
| 15 | Copilot Instructions File | `.github/copilot-instructions.md` | [02-github-copilot-setup.md](../../04-ai-assisted-tools/02-github-copilot-setup.md) | — |
| 16 | FOR JSON PATH vs AUTO | Manual path control vs auto-naming | [02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) | [json-functions](../cheat-sheets/json-functions-quick-ref.md) |
| 17 | Partitioning — Sliding Window | Partition switching for archive/load | [05-partitioning.md](../../01-database-objects/05-partitioning.md) | — |

### Domain 2 — Secure, optimize, deploy (Qs 18–34)

| # | Topic | Key concept tested | Re-read | Cheat sheet |
| :---: | :--- | :--- | :--- | :--- |
| 18 | Always Encrypted — Det. vs Rand. | DETERMINISTIC enables equality; needs BIN2 collation for strings | [01-encryption.md](../../05-data-security-compliance/01-encryption.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 19 | DDM — Email Function | `email()` mask format `aXXX@XXXX.com` | [02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 20 | RLS — Inline TVF | `WITH SCHEMABINDING`, `SESSION_CONTEXT` pattern | [02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 21 | GRANT/DENY/REVOKE | DENY wins; REVOKE removes a prior grant or deny | [03-permissions-access.md](../../05-data-security-compliance/03-permissions-access.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 22 | Managed Identity — CREATE USER | `CREATE USER [name] FROM EXTERNAL PROVIDER` | [03-permissions-access.md](../../05-data-security-compliance/03-permissions-access.md), [05-secure-endpoints.md](../../05-data-security-compliance/05-secure-endpoints.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 23 | Auditing Destinations | Blob storage, Log Analytics, Event Hubs | [04-auditing.md](../../05-data-security-compliance/04-auditing.md) | — |
| 24 | RCSI — Enabling | `ALTER DATABASE ... SET READ_COMMITTED_SNAPSHOT ON` | [02-transaction-isolation-concurrency.md](../../06-performance-optimization/02-transaction-isolation-concurrency.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 25 | Deadlock — Retry Logic | Error 1205; retry with backoff | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 26 | Execution Plan — Seek vs Scan | Index seek vs scan choice; covering indexes | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 27 | Missing Index DMVs | `sys.dm_db_missing_index_*` | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 28 | Query Store — Regressed Queries | `sp_query_store_force_plan` | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 29 | SQL DB Projects — dacpac Deployment | `SqlPackage /Action:Publish` | [02-sql-database-projects.md](../../07-cicd-database-projects/02-sql-database-projects.md) | — |
| 30 | Schema Drift Detection | `SqlPackage /Action:DeployReport` (or `/Action:DriftReport`) | [02-sql-database-projects.md](../../07-cicd-database-projects/02-sql-database-projects.md), [04-deployment-pipelines.md](../../07-cicd-database-projects/04-deployment-pipelines.md) | — |
| 31 | CDC vs Change Tracking | CDC keeps before-image; CT does not | [04-change-event-handling.md](../../08-azure-services-integration/04-change-event-handling.md) | — |
| 32 | Azure Monitor KQL | `AzureDiagnostics \| where Category == 'SQLSecurityAuditEvents'` | [03-monitoring.md](../../08-azure-services-integration/03-monitoring.md) | — |
| 33 | DAB — REST and GraphQL | Single config exposes both surfaces | [01-data-api-builder.md](../../08-azure-services-integration/01-data-api-builder.md), [02-rest-graphql-endpoints.md](../../08-azure-services-integration/02-rest-graphql-endpoints.md) | — |
| 34 | Key Vault — Pipeline Secret | Azure DevOps variable group linked to Key Vault | [04-deployment-pipelines.md](../../07-cicd-database-projects/04-deployment-pipelines.md) | — |

### Domain 3 — AI capabilities (Qs 35–45)

| # | Topic | Key concept tested | Re-read | Cheat sheet |
| :---: | :--- | :--- | :--- | :--- |
| 35 | VECTOR Data Type | `VECTOR(n)`; dimension must match embedding model | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 36 | VECTOR_DISTANCE — Lower Is Similar | Distance, not similarity; `ORDER BY ... ASC` | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 37 | ANN vs ENN | DiskANN approximate vs exact `VECTOR_DISTANCE` scan | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 38 | Chunking — Overlapping | Overlap prevents context loss at boundaries | [03-chunking-generation.md](../../09-models-embeddings/03-chunking-generation.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 39 | Embedding Maintenance — Triggers | Synchronous trigger trade-offs | [02-embedding-maintenance.md](../../09-models-embeddings/02-embedding-maintenance.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 40 | Full-Text Search — CONTAINS | `CONTAINS` for exact / boolean; `FREETEXT` for inflectional | [01-fulltext-search.md](../../10-intelligent-search/01-fulltext-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 41 | Hybrid Search — RRF | `score = Σ 1/(k+rank)`; k = 60 default | [03-hybrid-search-rrf.md](../../10-intelligent-search/03-hybrid-search-rrf.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 42 | RAG — `sp_invoke_external_rest_endpoint` | Response JSON path: `$.result.choices[0].message.content` | [02-prompts-and-responses.md](../../11-rag/02-prompts-and-responses.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 43 | VECTORPROPERTY | `'Dimensions'`, `'BaseType'` | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 44 | CREATE EXTERNAL MODEL — Model Type | `MODEL_TYPE = EMBEDDINGS \| COMPLETIONS` (NOT `TASK`) | [01-external-models.md](../../09-models-embeddings/01-external-models.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 45 | DATABASE SCOPED CREDENTIAL | `IDENTITY = 'HTTPEndpointHeaders'` for API key injection | [02-prompts-and-responses.md](../../11-rag/02-prompts-and-responses.md), [05-secure-endpoints.md](../../05-data-security-compliance/05-secure-endpoints.md) | [security](../cheat-sheets/security-quick-ref.md), [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |

---

## Study plan by miss count

> [!tip] Triage rule
> Re-take the mock after focused study. Anything wrong **twice** becomes a flashcard for the morning of the exam.

### If you missed 3+ in Domain 1

Re-read **in this order** before re-attempting:

1. [01-database-objects/01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) — columnstore types, batch mode
2. [01-database-objects/05-partitioning.md](../../01-database-objects/05-partitioning.md) — RANGE LEFT vs RANGE RIGHT (highest-yield Domain 1 trap)
3. [03-advanced-tsql/02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) — `JSON_VALUE` vs `JSON_QUERY` (multiple questions test this)
4. [02-programmability-objects/02-functions.md](../../02-programmability-objects/02-functions.md) — scalar UDF performance trap

### If you missed 3+ in Domain 2

Re-read in this order:

1. [05-data-security-compliance/01-encryption.md](../../05-data-security-compliance/01-encryption.md) — Always Encrypted DETERMINISTIC vs RANDOMIZED + BIN2 collation
2. [05-data-security-compliance/02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) — FILTER vs BLOCK predicate operations
3. [06-performance-optimization/02-transaction-isolation-concurrency.md](../../06-performance-optimization/02-transaction-isolation-concurrency.md) — RCSI vs Snapshot Isolation (every exam tests this)
4. [08-azure-services-integration/04-change-event-handling.md](../../08-azure-services-integration/04-change-event-handling.md) — CDC vs Change Tracking vs CES

### If you missed 3+ in Domain 3

Re-read in this order:

1. [10-intelligent-search/02-vector-search.md](../../10-intelligent-search/02-vector-search.md) — ANN vs ENN, distance metrics, `WITH APPROXIMATE` syntax
2. [11-rag/02-prompts-and-responses.md](../../11-rag/02-prompts-and-responses.md) — the `$.result.choices[0].message.content` envelope trap
3. [09-models-embeddings/01-external-models.md](../../09-models-embeddings/01-external-models.md) — `MODEL_TYPE` (not `TASK`); model dimensions
4. [10-intelligent-search/03-hybrid-search-rrf.md](../../10-intelligent-search/03-hybrid-search-rrf.md) — RRF formula

### If your overall score is below 700

- Read the [final-review.md](../final-review.md) cold — these are the highest-probability facts
- Work through both [Mock Exam 2](../mock-exam-2/mock-exam-2.md) and re-take this Mock 1 after a week
- Focus weak-domain re-reads, then re-attempt before scheduling the real exam

---

**[← Back to Mock Exam 1](./mock-exam-1.md)** | **[Mock Exam 2 →](../mock-exam-2/mock-exam-2.md)** | **[Final Review](../final-review.md)**
