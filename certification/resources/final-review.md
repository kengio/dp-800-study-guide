---
title: "DP-800 Final Review — Exam Morning"
type: study-material
tags:
  - dp-800
  - final-review
  - exam-prep
---

# DP-800 Final Review — Exam Morning

> [!abstract] Read This in 20 Minutes
> - Highest-probability testable facts across all three exam domains
> - One scroll, no deep dives — orient your brain before walking in
> - After reading: open your cheat sheets and run through the "Before the Exam, I Can…" checklists

---

## Domain 1: Design and Develop (35–40%)

- **Clustered Columnstore Index (CCI):** optimal for analytics-only workloads; batch mode execution; delta rowstore buffers inserts before compressing. For mixed OLTP+analytics, add a *non-clustered* CCI alongside the rowstore.
- **Temporal tables:** `FOR SYSTEM_TIME AS OF '2025-01-01T12:00:00'` = point-in-time query. Columns `SysStartTime`/`SysEndTime` are system-managed. History table is auto-created or user-specified.
- **Ledger tables:** append-only, blockchain-style tamper evidence. `GENERATED ALWAYS AS ROW START/END` + `LEDGER = ON`. Cannot update or delete rows in append-only mode.
- **Memory-optimized tables:** `DURABILITY = SCHEMA_AND_DATA` (survives restart) vs `SCHEMA_ONLY` (data lost on restart). Must use `MEMORY_OPTIMIZED = ON` in filegroup.
- **JSON functions:** `JSON_VALUE` = scalar; `JSON_QUERY` = object or array fragment; `OPENJSON` = table rows; `JSON_MODIFY` = update a path in place; `FOR JSON PATH` = serialize rows to JSON.
- **SEQUENCE vs IDENTITY:** `SEQUENCE` is a standalone object, shared across tables, cycles; `IDENTITY` is column-bound, table-scoped, no cycling.
- **Partitioning:** partition *function* defines value ranges → partition *scheme* maps ranges to filegroups → table uses scheme. `$PARTITION.FunctionName(col)` = partition number. Partition switching = instant bulk load/archive.
- **Recursive CTE:** anchor member `UNION ALL` recursive member. Anchor runs once; recursive runs until no rows returned. `OPTION (MAXRECURSION n)` limits depth.
- **Window functions on ties:** `ROW_NUMBER` = unique (arbitrary tie-break); `RANK` = skips numbers; `DENSE_RANK` = no skip. `NTILE(n)` = bucket.
- **Graph tables:** `CREATE TABLE … AS NODE` / `AS EDGE`. Query with `MATCH (A)-[E]->(B)`. `SHORTEST_PATH` for traversal. Edges must reference NODE tables.
- **Triggers:** `AFTER` fires after the DML; `INSTEAD OF` fires in place of it. `INSERTED` = new values; `DELETED` = old values. Both available in UPDATE triggers.
- **Inline TVF vs multi-statement TVF:** inline TVF is expanded like a view (optimizer sees through it, parallelism allowed); multi-statement TVF is a black box (no parallelism, worse cardinality estimates).

---

## Domain 2: Secure, Optimize, Deploy (35–40%)

- **TDE:** encrypts entire database at rest; transparent to app; server sees plaintext; enabled by default on Azure SQL. Does NOT protect data in transit — use TLS separately.
- **Always Encrypted:** column-level; server NEVER sees plaintext; driver handles encrypt/decrypt; CMK (Column Master Key, client-side in Key Vault) → CEK (Column Encryption Key, encrypted by CMK, stored in DB) → column data.
- **DDM (Dynamic Data Masking):** hides values from non-privileged users at query time; does NOT encrypt; `UNMASK` permission reveals full data; masks: `default()`, `email()`, `partial()`, `random()`.
- **RLS (Row-Level Security):** security predicate function returns a filter; attached to table via `CREATE SECURITY POLICY`. Transparent to the user — they don't know rows are hidden. Filter predicate (SELECT) vs block predicate (INSERT/UPDATE/DELETE).
- **Permission precedence:** `DENY` always wins over `GRANT`, even if GRANT comes through a role. `REVOKE` removes a prior GRANT or DENY — it does not itself deny.
- **Query Store:** persists query plans and runtime stats across restarts. Force a plan: `sp_query_store_force_plan`. Unforce: `sp_query_store_unforce_plan`. Detects plan regressions via Automatic Plan Correction.
- **Isolation levels:** `READ COMMITTED` = default; `READ UNCOMMITTED` = dirty reads; `REPEATABLE READ` = no phantom rows; `SERIALIZABLE` = full isolation; `SNAPSHOT` = optimistic, row versioning, per-transaction opt-in (requires `ALLOW_SNAPSHOT_ISOLATION ON`); `RCSI` (Read Committed Snapshot Isolation) = database-level setting that changes default READ COMMITTED behavior — set `READ_COMMITTED_SNAPSHOT ON`.
- **Blocking vs deadlock:** blocking = one session waits for lock held by another (resolves when lock released); deadlock = circular wait (SQL Server auto-kills one victim). Check with `sys.dm_exec_requests` and `sys.dm_os_waiting_tasks`.
- **SQL DB Projects:** `.sqlproj` file; `Build` → `.dacpac`; `Publish` (via SqlPackage.exe) → deploys diff to target. Pre/post-deployment scripts run outside the diff. `SqlPackage.exe /Action:Publish` deploys; `/Action:Extract` creates dacpac from existing DB.
- **DAB (Data API Builder):** config file maps entities to DB objects; generates REST (`/api/{Entity}`) and GraphQL (`/graphql`) endpoints; no custom code. Permissions: anonymous, authenticated, role-based.
- **Change Data Capture vs Change Tracking:** CDC = captures before/after values for each row change, requires SQL Server Agent; CT = lightweight, captures only that a change occurred (not what changed), no Agent needed.
- **Private endpoint vs service endpoint:** private endpoint = private IP in your VNet (fully private); service endpoint = routes Azure service traffic via Azure backbone but endpoint remains public-facing.

---

## Domain 3: AI Capabilities (25–30%)

- **VECTOR data type:** `VECTOR(n)` — fixed-dimension float array. `VECTOR(1536)` = text-embedding-3-small or ada-002; `VECTOR(3072)` = text-embedding-3-large.
- **VECTOR_DISTANCE:** exact nearest neighbor (ENN); syntax: `VECTOR_DISTANCE('cosine', v1, v2)`; metrics: `cosine`, `euclidean`, `dot`. Smaller value = more similar (except dot where larger = more similar).
- **VECTOR_SEARCH:** approximate nearest neighbor (ANN) via DiskANN index; faster at scale; supports `cosine`, `dot`, and `euclidean` — the **index metric must match** the metric used in `VECTOR_SEARCH`.
- **VECTOR_NORMALIZE:** normalizes to unit length (L2 norm = 1); after normalization, dot product equals cosine similarity. Required before using dot as cosine proxy.
- **Full-text search:** `CONTAINS` = precision (exact terms, proximity, weighted); `FREETEXT` = recall (natural language, broader); both require a full-text index. `CONTAINSTABLE`/`FREETEXTTABLE` return ranked results.
- **Hybrid search with RRF:** Reciprocal Rank Fusion combines FTS + vector result sets. Formula: `score = Σ 1/(k + rank)` where `k=60` by default. Higher RRF score = better. Not a score average — a rank-combination algorithm.
- **Chunking:** fixed-size (predictable) vs semantic (respects sentence/paragraph boundaries). Overlap (`overlap_tokens`) prevents losing context at chunk boundaries. Too small chunks = no context; too large = diluted relevance.
- **sp_invoke_external_rest_endpoint:** calls external REST API (e.g., Azure OpenAI). Requires `DATABASE SCOPED CREDENTIAL` for bearer token. Returns JSON response parsed with `JSON_VALUE`/`JSON_QUERY`.
- **RAG pattern:** (1) embed user query → (2) search DB with `VECTOR_SEARCH` + `CONTAINS` → (3) retrieve top-K chunks → (4) build prompt (system message + context + user question) → (5) call LLM → (6) return grounded response.
- **Grounding:** RAG provides context at *inference time* — it does NOT fine-tune the model. The LLM uses retrieved data for this one response; its weights are unchanged.
- **Prompt structure:** system message (instructions/persona) + user message (question + context). Temperature → randomness (0 = deterministic, 1 = creative). Use low temperature for RAG to reduce hallucination risk.

---

## 2026 Updates — What Microsoft Added or Emphasized

- **SQL Server 2025 GA:** `VECTOR` and `VECTOR_DISTANCE` are **GA** in SQL Server 2025 and Azure SQL Database. `VECTOR_SEARCH`, `VECTOR_NORMALIZE`, and `VECTORPROPERTY` are in **public preview** on the same platforms — fully testable per Microsoft's preview-features note.
- **DiskANN vector index:** **public preview** across SQL Server 2025, Azure SQL Database, Azure SQL Managed Instance, and SQL database in Microsoft Fabric. On SQL Server 2025 also needs `PREVIEW_FEATURES = ON`. Index `METRIC` (`cosine`/`euclidean`/`dot`) must match the metric passed to `VECTOR_SEARCH` — **a mismatch produces a warning and falls back to exact kNN**, it does not error.
- **Half-precision (`float16`) vectors:** preview; halves storage at the same dimension count. The documented `VECTOR` type cap is **1 998** dimensions — half-precision does not raise that cap.
- **MCP server endpoints:** explicitly tested. `stdio` for local, `HTTP+SSE` for remote/hosted (e.g., Fabric lakehouse). Always pass credentials through env vars, never inline in config. MCP runs with the **connection-string user's permissions** — least privilege matters.
- **Microsoft Foundry** is now a listed embedding-maintenance option alongside triggers, CT, CDC, CES, Azure Functions, and Logic Apps. Foundry = the most managed/declarative option in Fabric.
- **Change Event Streaming (CES):** push-based change stream from SQL Database in Fabric to Lakehouse/Eventstream/KQL DB. Zero-infrastructure alternative to CDC + custom consumer.
- **Schema drift detection** in SQL Database Projects is now an explicit skill — SDK-style `.sqlproj`, `SqlPackage /Action:DriftReport`, or the VS Code extension's compare view.
- **Passwordless DB access**: `Authentication=Active Directory Managed Identity` in the connection string; `CREATE USER [name] FROM EXTERNAL PROVIDER` in the database; no password rotation. Test favorite.
- **`CREATE DATABASE SCOPED CREDENTIAL ... WITH IDENTITY = 'Managed Identity'`** is the correct passwordless pattern for `sp_invoke_external_rest_endpoint` calling Azure OpenAI.
- **REGEXP family** has been expanded — `REGEXP_LIKE`, `REGEXP_REPLACE`, `REGEXP_SUBSTR`, `REGEXP_INSTR`, `REGEXP_COUNT`, `REGEXP_MATCHES`, and `REGEXP_SPLIT_TO_TABLE` are all in scope. `REGEXP_SPLIT_TO_TABLE` returns rows — useful for tokenizing.

---

## Last-Minute Traps

1. **JSON_VALUE on an object/array path returns NULL** — not an error. Use `JSON_QUERY` to extract objects or arrays.
2. **DiskANN index metric must match the query metric** — DiskANN supports `cosine`, `dot`, and `euclidean`. The metric on the index must match the metric used in the query. **A mismatch does NOT error** — it logs a warning and silently falls back to exact kNN (no index used). Build one index per metric you need.
3. **DENY always overrides GRANT** — even if the GRANT came through a role. There is no way to "un-deny" except REVOKE of the DENY.
4. **DDM ≠ encryption** — DDM hides values at display time; the data is stored in plaintext. Users with `UNMASK` or admin rights see everything.
5. **SNAPSHOT isolation ≠ RCSI** — SNAPSHOT = application sets it per transaction; RCSI = database setting that changes the *default* READ COMMITTED behavior to row-versioning.
6. **VECTOR_SEARCH / `WITH APPROXIMATE` is approximate** — it can miss the true nearest neighbor for speed. `VECTOR_DISTANCE` in `ORDER BY` without `WITH APPROXIMATE` is exact (ENN) but slower. On latest-version indexes use `SELECT TOP (N) … WITH APPROXIMATE` (the legacy `TOP_N` parameter is deprecated and raises Msg 42274).
7. **CMK stays client-side** — Always Encrypted: the Column Master Key lives in Key Vault (or cert store), never uploaded to SQL Server. The server only holds the encrypted CEK.
8. **SqlPackage /Action:Extract ≠ Publish** — Extract creates a dacpac FROM an existing database. Publish deploys a dacpac TO a database.
9. **Partition function ≠ partition scheme** — function defines value boundaries; scheme maps them to filegroups. Need both to partition a table.
10. **RAG doesn't train the model** — retrieved context is injected into the prompt for one call; the model's weights do not change.
