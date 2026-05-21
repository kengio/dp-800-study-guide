---
title: Mock Exam 2 — Debrief
type: debrief
tags:
  - dp-800
  - mock-exam
  - debrief
  - study-plan
---

# Mock Exam 2 — Debrief

> [!abstract]
> - Use this **after** completing Mock Exam 2 and checking your answers
> - Every question maps to a topic file + cheat sheet + key concept
> - The "If you missed N+ in domain X" section at the bottom turns your score into a study plan

> [!tip] How to use this debrief
> 1. List the question numbers you got wrong
> 2. For each, look up the row below — re-read the topic file and the cheat-sheet section it points to
> 3. If you missed **3 or more questions in the same domain**, jump to the **Study Plan** section
> 4. Anything wrong on both Mock 1 and Mock 2 goes on a focused flashcard list before exam day

---

## Question-by-question map

### Domain 1 — Design and develop (Qs 1–17)

| # | Topic | Key concept tested | Re-read | Cheat sheet |
| :---: | :--- | :--- | :--- | :--- |
| 1 | Non-Clustered Columnstore | NCCI on rowstore for hybrid OLTP/analytics | [01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) | [azure-sql-config](../cheat-sheets/azure-sql-config-quick-ref.md) |
| 2 | Temporal Table — BETWEEN Syntax | `FOR SYSTEM_TIME BETWEEN ... AND ...` (inclusive both ends) | [02-specialized-tables.md](../../01-database-objects/02-specialized-tables.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 3 | OPENJSON with Schema | `WITH (col type 'path')` explicit schema | [02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) | [json-functions](../cheat-sheets/json-functions-quick-ref.md) |
| 4 | LAG and LEAD | Prior/next row access without self-join | [01-ctes-window-functions.md](../../03-advanced-tsql/01-ctes-window-functions.md) | [tsql-core-commands](../cheat-sheets/tsql-core-commands.md) |
| 5 | Table Partitioning — Partition Elimination | Optimizer prunes partitions on predicate | [05-partitioning.md](../../01-database-objects/05-partitioning.md) | — |
| 6 | Graph Tables — SHORTEST_PATH | `MATCH (...)->()...` with shortest-path operator | [04-graph-queries.md](../../03-advanced-tsql/04-graph-queries.md) | — |
| 7 | Inline TVF vs Scalar UDF | Inline TVF inlined by optimizer; scalar UDF blocks parallelism | [02-functions.md](../../02-programmability-objects/02-functions.md) | — |
| 8 | JSON_MODIFY | Update a JSON path in place; `lax` vs `strict` | [02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) | [json-functions](../cheat-sheets/json-functions-quick-ref.md) |
| 9 | Heap vs Clustered Table | Heap = no clustered index; RID lookups | [01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) | — |
| 10 | EXCEPT vs NOT IN | Set difference vs row predicate; NULL handling | [05-correlated-queries-error-handling.md](../../03-advanced-tsql/05-correlated-queries-error-handling.md) | — |
| 11 | Batch Mode on Row Store | Available without columnstore (SS2019+) | [01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) | — |
| 12 | FOR JSON — WITH_WRAPPER | `WITH ARRAY_WRAPPER` adds enclosing array | [02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) | [json-functions](../cheat-sheets/json-functions-quick-ref.md) |
| 13 | Columnstore — Batch Mode Operators | `Hash Match`, `Sort`, etc. run in batches | [01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) | — |
| 14 | Ledger — Verification | `sp_verify_database_ledger` | [02-specialized-tables.md](../../01-database-objects/02-specialized-tables.md) | — |
| 15 | PIVOT Operator | Rotate rows to columns | [01-ctes-window-functions.md](../../03-advanced-tsql/01-ctes-window-functions.md) | — |
| 16 | sp_describe_first_result_set | Inspect first result set of a procedure | [03-stored-procedures.md](../../02-programmability-objects/03-stored-procedures.md) | — |
| 17 | STRING_SPLIT — Ordered | `STRING_SPLIT(string, sep, 1)` — preserves order (SQL Server 2022+) | [01-ctes-window-functions.md](../../03-advanced-tsql/01-ctes-window-functions.md) | — |

### Domain 2 — Secure, optimize, deploy (Qs 18–32)

| # | Topic | Key concept tested | Re-read | Cheat sheet |
| :---: | :--- | :--- | :--- | :--- |
| 18 | Always Encrypted — Client Driver | Client SDK encrypts/decrypts; server never sees plaintext | [01-encryption.md](../../05-data-security-compliance/01-encryption.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 19 | DDM — Partial Mask | `partial(prefix,"mask",suffix)` | [02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 20 | RLS — BLOCK Predicate | AFTER INSERT/UPDATE; BEFORE UPDATE/DELETE | [02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 21 | Contained Database User | Authentication scoped to the database | [03-permissions-access.md](../../05-data-security-compliance/03-permissions-access.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 22 | Snapshot Isolation — Write Conflicts | Error 3960; SI detects conflicts, RCSI does not | [02-transaction-isolation-concurrency.md](../../06-performance-optimization/02-transaction-isolation-concurrency.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 23 | Wait Statistics Analysis | `sys.dm_os_wait_stats` cumulative waits | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 24 | Query Hints — NOLOCK | Dirty reads; `READUNCOMMITTED` equivalent | [02-transaction-isolation-concurrency.md](../../06-performance-optimization/02-transaction-isolation-concurrency.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 25 | Execution Plan — Hash Match | Join algorithm choice; memory-bound | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 26 | Query Store — Automatic Plan Correction | `FORCE_LAST_GOOD_PLAN` | [03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) | [performance-dmvs](../cheat-sheets/performance-dmvs-quick-ref.md) |
| 27 | dacpac — Drift Report | `SqlPackage /Action:DriftReport` | [02-sql-database-projects.md](../../07-cicd-database-projects/02-sql-database-projects.md) | — |
| 28 | Auditing — Server vs Database | Server-level catches all DBs; database-level scoped | [04-auditing.md](../../05-data-security-compliance/04-auditing.md) | — |
| 29 | Azure AD External Authentication | Entra ID identities; `FROM EXTERNAL PROVIDER` | [03-permissions-access.md](../../05-data-security-compliance/03-permissions-access.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 30 | Change Tracking — Sync Version | `CHANGE_TRACKING_CURRENT_VERSION()`; watermark pattern | [04-change-event-handling.md](../../08-azure-services-integration/04-change-event-handling.md) | — |
| 31 | DAB — REST CRUD | `permissions` array maps role to actions | [01-data-api-builder.md](../../08-azure-services-integration/01-data-api-builder.md) | — |
| 32 | Key Vault — Managed Identity | App Service MI grants → vault `Get` policy | [05-secure-endpoints.md](../../05-data-security-compliance/05-secure-endpoints.md) | [security](../cheat-sheets/security-quick-ref.md) |
| 33 | Schema Drift — CI Pipeline | `/Action:DeployReport` in PR check | [04-deployment-pipelines.md](../../07-cicd-database-projects/04-deployment-pipelines.md) | — |
| 34 | sp_set_session_context Security | `@read_only = 1` to prevent client tampering | [02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) | [security](../cheat-sheets/security-quick-ref.md) |

### Domain 3 — AI capabilities (Qs 35–45)

| # | Topic | Key concept tested | Re-read | Cheat sheet |
| :---: | :--- | :--- | :--- | :--- |
| 35 | External Model — Structured Output | `response_format = json_schema` | [01-external-models.md](../../09-models-embeddings/01-external-models.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 36 | DiskANN with `dot` Metric | Pre-normalization required for `dot`-as-cosine; NOT for `cosine` | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 37 | Full-Text Index — FREETEXTTABLE | Returns RANK score; inflectional matching | [01-fulltext-search.md](../../10-intelligent-search/01-fulltext-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 38 | Chunking — Semantic | Paragraph/sentence boundaries for legal/technical text | [03-chunking-generation.md](../../09-models-embeddings/03-chunking-generation.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 39 | VECTOR_SEARCH — Current Syntax | `SELECT TOP (N) ... WITH APPROXIMATE` (TOP_N deprecated) | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 40 | RAG — FOR JSON in Payload | `JSON_OBJECT`/`JSON_ARRAY` for safe escaping | [02-prompts-and-responses.md](../../11-rag/02-prompts-and-responses.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 41 | Hybrid Search — Implementation | Vector + FTS unioned then RRF-fused | [03-hybrid-search-rrf.md](../../10-intelligent-search/03-hybrid-search-rrf.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 42 | Embedding Model — Dimensions | text-embedding-3-small (1536) vs -large (3072) trade-off | [01-external-models.md](../../09-models-embeddings/01-external-models.md), [03-chunking-generation.md](../../09-models-embeddings/03-chunking-generation.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 43 | sp_invoke_external_rest_endpoint — Status | `@response_status_code` OUTPUT param | [02-prompts-and-responses.md](../../11-rag/02-prompts-and-responses.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 44 | CREATE EXTERNAL MODEL — Credential | `CREDENTIAL = [name]` references DSC | [01-external-models.md](../../09-models-embeddings/01-external-models.md), [05-secure-endpoints.md](../../05-data-security-compliance/05-secure-endpoints.md) | [security](../cheat-sheets/security-quick-ref.md), [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |
| 45 | Vector Search — Combining with WHERE | Pre-filter subquery passed to TVF, or `WHERE` outside `TOP (N) ... WITH APPROXIMATE` | [02-vector-search.md](../../10-intelligent-search/02-vector-search.md) | [vector-ai](../cheat-sheets/vector-ai-quick-ref.md) |

---

## Study plan by miss count

> [!tip] Triage rule
> If you took Mock 1 first, focus on items you missed on **both** mocks — that's where the real weaknesses are.

### If you missed 3+ in Domain 1

Re-read **in this order**:

1. [01-database-objects/01-tables-indexes.md](../../01-database-objects/01-tables-indexes.md) — columnstore (clustered, non-clustered, batch mode)
2. [01-database-objects/02-specialized-tables.md](../../01-database-objects/02-specialized-tables.md) — temporal `BETWEEN` vs `AS OF`, ledger verification
3. [03-advanced-tsql/04-graph-queries.md](../../03-advanced-tsql/04-graph-queries.md) — MATCH patterns including SHORTEST_PATH
4. [03-advanced-tsql/02-json-functions.md](../../03-advanced-tsql/02-json-functions.md) — `JSON_MODIFY`, `OPENJSON WITH (...)`, `FOR JSON WITH_WRAPPER`

### If you missed 3+ in Domain 2

Re-read in this order:

1. [06-performance-optimization/02-transaction-isolation-concurrency.md](../../06-performance-optimization/02-transaction-isolation-concurrency.md) — Snapshot Isolation error 3960 (this exam tests it directly)
2. [06-performance-optimization/03-query-performance-troubleshooting.md](../../06-performance-optimization/03-query-performance-troubleshooting.md) — DMVs, Query Store, plan choices
3. [07-cicd-database-projects/04-deployment-pipelines.md](../../07-cicd-database-projects/04-deployment-pipelines.md) — schema drift detection in CI
4. [05-data-security-compliance/02-dynamic-data-masking-rls.md](../../05-data-security-compliance/02-dynamic-data-masking-rls.md) — `@read_only = 1` on `sp_set_session_context`

### If you missed 3+ in Domain 3

Re-read in this order:

1. [10-intelligent-search/02-vector-search.md](../../10-intelligent-search/02-vector-search.md) — current syntax (`SELECT TOP (N) … WITH APPROXIMATE`), DiskANN metric specifics
2. [11-rag/02-prompts-and-responses.md](../../11-rag/02-prompts-and-responses.md) — `JSON_OBJECT`/`JSON_ARRAY` payload construction, `@response_status_code`
3. [09-models-embeddings/01-external-models.md](../../09-models-embeddings/01-external-models.md) — structured output, `MODEL_TYPE`, `CREDENTIAL`
4. [10-intelligent-search/03-hybrid-search-rrf.md](../../10-intelligent-search/03-hybrid-search-rrf.md) — combining vector + FTS

### If your overall score is below 700

- Take Mock 1 first if you haven't ([Mock Exam 1 →](../mock-exam/mock-exam-1.md))
- Read [final-review.md](../final-review.md) the morning of the exam
- Re-attempt this mock after a week of focused study on your weak domain

---

**[← Back to Mock Exam 2](./mock-exam-2.md)** | **[Mock Exam 1](../mock-exam/mock-exam-1.md)** | **[Final Review](../final-review.md)**
