---
title: DP-800 Exam Tips
type: exam-tips
tags:
  - dp-800
  - exam-tips
  - strategy
---

# DP-800 Exam Tips

## Exam Format

| Detail | Information |
| :--- | :--- |
| **Passing Score** | 700 / 1000 |
| **Question Types** | Multiple choice, multi-select, case studies, drag-and-drop |
| **Languages** | English (and select other languages with +30 min) |
| **Environment** | Pearson VUE (online or test center) |

## Time Management

- Skip difficult questions and flag for review — don't get stuck
- Case studies at the end often take longer; budget time accordingly
- Multi-select questions: read carefully for "select all that apply" vs "select the best two"
- Aim to complete all questions with at least 5–10 minutes for review

## Domain-Specific Tips

### Domain 1: Design and Develop (35–40%)

- **Table types**: Know each specialized table (in-memory, temporal, external, ledger, graph) and its unique requirement or syntax
- **Column store indexes**: Clustered vs non-clustered; batch mode execution is the key benefit
- **JSON functions**: `JSON_VALUE` returns scalars; `JSON_QUERY` returns objects/arrays — don't mix them up
- **Regex functions**: Only available in **SQL databases in Microsoft Fabric** / newer Azure SQL — note the platform
- **MATCH operator**: Only works with graph tables (`AS NODE` / `AS EDGE`)
- **CTEs vs temp tables**: CTEs don't cache results; a temp table does
- **Inline TVF over scalar function**: Scalar functions prevent parallelism — inline TVF is always preferred

### Domain 2: Secure, Optimize, Deploy (35–40%)

- **Always Encrypted**: Client-side encryption — server never sees plaintext; DETERMINISTIC for searchable columns
- **DDM vs RLS**: DDM hides column values (row still visible); RLS hides entire rows
- **DENY always wins**: Even when inherited through a role grant, an explicit DENY on a user overrides it
- **Managed Identity**: Use `FROM EXTERNAL PROVIDER` in SQL; `Authentication=Active Directory Managed Identity` in connection strings
- **RCSI**: Enabled at database level — affects all READ COMMITTED queries; eliminates reader/writer blocking
- **Query Store**: Know `sp_query_store_force_plan` for manual plan forcing; `FORCE_LAST_GOOD_PLAN` for automatic
- **SDK-style projects**: `<Project Sdk="Microsoft.Build.Sql">` — modern format vs legacy `.sqlproj`
- **Schema drift**: Detected with `sqlpackage /Action:DeployReport` — identifies differences before deployment
- **DAB**: Config file is `dab-config.json`; entities define what's exposed; permissions control access per role

### Domain 3: AI Capabilities (25–30%)

- **Embedding types**: Deterministic (same input = same vector); key for cache efficiency
- **Chunking**: Overlapping chunks improve recall for semantic search at chunk boundaries
- **ANN vs ENN**: ANN = approximate (fast, index-accelerated); ENN = exact (slower, always accurate)
- **Vector data type**: `VECTOR(n)` where `n` = number of dimensions (e.g., `VECTOR(1536)` for text-embedding-3-small)
- **VECTOR_DISTANCE**: Returns a distance (lower = more similar for cosine/euclidean); normalize first
- **Hybrid search**: Combines keyword recall with semantic recall — RRF merges the ranked lists
- **sp_invoke_external_rest_endpoint**: Requires a DATABASE SCOPED CREDENTIAL; returns JSON response in OUTPUT parameter
- **RAG**: `FOR JSON PATH` converts query results to JSON for prompt building — key pattern

## Common Traps

| Trap | Correct Answer |
| :--- | :--- |
| "Which allows equality comparisons on Always Encrypted?" | **DETERMINISTIC** encryption (`varchar`/`nvarchar` columns also need a **BIN2** collation) |
| "Which isolation level uses row versioning?" | **Snapshot** and **RCSI** (both) |
| "How to prevent reader/writer blocking without changing app code?" | Enable **RCSI** at database level |
| "What is required before creating a memory-optimized table?" | A **MEMORY_OPTIMIZED_DATA filegroup** |
| "Best function type for set-based operations?" | **Inline TVF** (not scalar UDF) |
| "Which eliminates rows vs masking values?" | **RLS** eliminates rows; **DDM** masks values |
| "What does ANN sacrifice for speed?" | **Accuracy** (approximate, not exact) |
| "How to maintain an indexed view?" | SQL Server maintains it **automatically** on DML |
| "DiskANN index metric doesn't match the query metric — what happens?" | **Warning + silent fallback to exact kNN** (it does **not** error). Build one index per metric. |
| "`TOP_N` in `VECTOR_SEARCH` on a current Azure SQL vector index?" | **Deprecated** — raises Msg 42274. Use `SELECT TOP (N) ... WITH APPROXIMATE` |
| "`PARTITION FUNCTION ... RANGE RIGHT FOR VALUES ('2025-01-01', '2025-02-01')` — which partition holds `'2025-01-01'`?" | **Partition 2** (RANGE RIGHT puts the boundary value in the **right/newer** partition) |
| "`JSON_VALUE` returns a JSON object — what do you get?" | **NULL** (no error). Use `JSON_QUERY` for objects/arrays |
| "RLS: must INSERT also be blocked, not just SELECT filtered?" | Add a **BLOCK AFTER INSERT** predicate alongside the FILTER predicate |
| "CDC vs Change Tracking — which captures before-image of a row?" | **CDC** (CT captures only PK + operation; you must join to the source table for current values) |
| "`SqlPackage /Action:Extract` vs `/Publish` — which deploys?" | **Publish** (Extract creates a dacpac **from** an existing DB) |
| "`WHERE col NOT IN (SELECT ...)` returns zero rows" | The subquery contains a **NULL**. Use `NOT EXISTS` instead |
| "Snapshot Isolation gives 3960 — what is it?" | **Update conflict** detected by SI (not RCSI). Retry the transaction |
| "Connection string for passwordless Azure SQL from App Service?" | `Authentication=Active Directory Managed Identity` + `CREATE USER [name] FROM EXTERNAL PROVIDER` in the DB |
| "`sp_invoke_external_rest_endpoint` response JSON path?" | `$.result.choices[0].message.content` (the proc wraps the API response under `result`) |

## Case-Study Playbook

DP-800 includes interactive case studies — a multi-paragraph scenario with several linked questions. Get this format right and you bank easy points.

- **Read the scenario once, end to end, before opening the first question** — the requirements at the bottom often reframe earlier details
- **You can jump between questions inside a case study, but you cannot return to the case study after you submit it.** Use the **Review** button inside the case to flag answers
- **Tabs/exhibits matter** — case studies expose architecture, code, and requirements on separate tabs; you'll lose points by missing a constraint that lives on a different tab
- **Budget about 25 minutes per case-study block** out of your 120-minute total (the exam is ~50 questions; case study counts as a single block but contains 4–6 sub-questions)
- **The "best" answer is the one that satisfies every stated constraint** — eliminate options that fail any single requirement before comparing the remainder
- **If two answers both satisfy the constraints, pick the one with the lowest operational cost / least new infrastructure** — Microsoft consistently rewards the more managed option (e.g., DAB over a custom API, Managed Identity over API keys, CES over polling)

## Time Budget (120 min / ~50 questions)

| Block | Allocation |
| :--- | :--- |
| Standalone questions (~45) | ~85 min · ≈ 1:50 per question |
| Case-study block | ~25 min |
| Final review of flagged questions | ~10 min |

## Scoring Strategy

- All questions are equal weight — don't overthink any single question
- For multi-select: usually 2–3 correct answers; more than that is rare
- "BEST" answer questions: eliminate clearly wrong answers first, then choose between remaining
- Platform-specific features: always check if a feature applies to SQL Server, Azure SQL, or Fabric SQL specifically

---

**[← Back to Resources](./exam-resources.md)**
