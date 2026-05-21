# Changelog

Notable changes to the DP-800 study guide.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/). Dates use ISO 8601. Each section is grouped under the Microsoft blueprint date it tracks, so future readers can match guide versions to the version of the exam they were preparing for.

## [2026.05.21] — Case studies, rebalanced practice set, mental models

Still aligned to the 2026-03-12 blueprint. Follow-up additions surfaced by the senior-data-engineer review.

### Added

- **Case-study mini-block in Mock Exam 1** — Contoso HR migration scenario with 5 linked sub-questions (Qs 46–50) covering Always Encrypted (DETERMINISTIC + BIN2), RLS with SESSION_CONTEXT, passwordless model endpoints via Managed Identity, and CES → Lakehouse change feed
- **Case-study mini-block in Mock Exam 2** — Northwind RAG product catalog scenario with 5 linked sub-questions (Qs 46–50) covering chunking strategy, embedding maintenance at high write volume, DiskANN with metric matching, hybrid search with RRF, and RAG grounding + `$.result` JSON envelope
- **+2 Hard practice questions in Domain 1** — graph SHORTEST_PATH edge direction and memory-optimized table filegroup prerequisite
- **+1 REGEXP practice question in Domain 1** — `REGEXP_SPLIT_TO_TABLE`
- **+2 Easy practice questions in Domain 2** — `ALTER ROLE ... ADD MEMBER` and TDE default-on for Azure SQL
- **Mental-model callouts** in Domain 1/2 topic files:
  - RANGE LEFT vs RANGE RIGHT — person standing at a doorway (`01-database-objects/05-partitioning.md`)
  - Always Encrypted — locked briefcase the DBA holds but never opens (`05-data-security-compliance/01-encryption.md`)
  - Row versioning (RCSI vs SI) — polaroid snapshots in tempdb (`06-performance-optimization/02-transaction-isolation-concurrency.md`)
  - GRANT/DENY/REVOKE — bouncer at a club (`05-data-security-compliance/03-permissions-access.md`)
- **Mock exam landing pages updated** — 50 questions, 70-minute time limit, scoring guide and domain breakdown reflect the new case-study block
- **Mock exam debriefs updated** — new "Case Study" sub-tables added to both Mock 1 and Mock 2 debrief files
- **CLAUDE.md** — new sections documenting the mock-exam structure, case-study format, and mental-model callout pattern
- **README.md** — refreshed counts (60+ practice questions, 50-question mocks), added direct links to debrief files and the RAG walkthrough, marked completed roadmap items

### Changed

- Mock exam total: 45 → 50 questions; time limit: 60 → 70 minutes; scoring tiers updated proportionally
- `03-permissions-access.md` — added an explicit note clarifying that `REVOKE` alone does not block access (it undoes a prior GRANT or DENY)

## [2026.05] — Open-source release, aligned to 2026-03-12 blueprint

Aligned to the official Microsoft skills-measured list updated **2026-03-12**, and open-sourced under MIT.

### Added

- **MIT license** and public GitHub release at <https://github.com/kengio/dp-800-study-guide>
- **README rewrite** for a broader audience: badges, Microsoft Certified banner, exam-at-a-glance table, table of contents, expanded official resource links
- **`OBSIDIAN-SETUP.md`** referenced from a new 5-minute Obsidian onboarding section in the README
- **`CONTRIBUTING.md`** with contributor guide, currency policy, and conventions
- **GitHub issue templates** (typo, factual correction, new question/topic) and **PR template** with blueprint-alignment checklist
- **Study roadmap** in the README: 4-week sprint, 8-week balanced, and 12-week comprehensive plans plus a per-resource time budget
- **Guide-itself roadmap** (Q2/Q3 2026, Q4 2026, Q1 2027)
- **"What's New for the 2026 Exam"** callout at the top of `certification/dp-800-overview.md`
- **"2026 Updates"** section in `certification/resources/final-review.md`
- **5 new Domain 3 practice questions** covering DiskANN metric matching, half-precision vectors, Microsoft Foundry, CES, and `VECTOR_SEARCH` recall tuning
- **`exam-tips.md` "Common Traps" expansion** — 10 new high-yield rows (RANGE LEFT/RIGHT, `JSON_VALUE` on object → NULL, FILTER vs BLOCK AFTER INSERT, CDC vs CT before-image, SqlPackage Extract vs Publish, NOT IN + NULL, Snapshot error 3960, passwordless connection string, `$.result.choices[0]...` JSON path, DiskANN-mismatch, TOP_N deprecation)
- **Case-Study Playbook** in `exam-tips.md` covering reading order, navigation, tab/exhibit handling, time budget, and Microsoft's "most-managed option wins" pattern
- **120-minute time budget** in `exam-tips.md` (~85 min standalone + 25 min case study + 10 min review)
- **Mock-exam debrief files** (`mock-exam-1-debrief.md`, `mock-exam-2-debrief.md`) mapping each question to topic file + cheat sheet, with per-domain study plans by miss count
- **End-to-end RAG worked example** in `certification/resources/code-examples/tsql/rag-end-to-end-walkthrough.md` — the full chunk → embed → store → retrieve → augment → call → parse pipeline in ~80 lines of T-SQL, including a Mermaid sequence diagram
- **Mermaid diagrams in Domain 3 topic files**: RAG sequence diagram (`11-rag/01-rag-use-cases.md`), ANN vs ENN path-split flowchart (`10-intelligent-search/02-vector-search.md`), embedding-maintenance decision tree (`09-models-embeddings/02-embedding-maintenance.md`)
- **Mental-model phrasings** added in Domain 3 (e.g., "RAG = open-book exam; fine-tuning = studying")
- **Cross-link** from `10-intelligent-search/02-vector-search.md` to the RAG topic files

### Changed

- **Reclassified `VECTOR_SEARCH`, `VECTOR_NORMALIZE`, `VECTORPROPERTY`** as **public preview** (not GA) on SS2025 / Azure SQL Database / Fabric SQL. Only `VECTOR` and `VECTOR_DISTANCE` are GA. Reflected across overview, final-review, vector-search topic file, and README
- **DiskANN status** corrected to **public preview** across SQL Server 2025, Azure SQL Database, Azure SQL Managed Instance, and SQL database in Microsoft Fabric (was previously stated as "private preview in Azure SQL")
- **DiskANN metric-mismatch behaviour** corrected from "raises an error" to "logs a warning and silently falls back to exact kNN" (the more dangerous behaviour) — applied to cheat sheet, final-review, mock exam, and practice question Q16
- **Half-precision (`float16`) vector** description corrected: halves storage at the same dimension count; the `VECTOR` type documented cap remains **1 998** dimensions (was incorrectly stated as ~4 000)
- **`VECTOR_SEARCH` syntax** updated to the current `SELECT TOP (N) ... WITH APPROXIMATE` pattern. The legacy `VECTOR_SEARCH(... TOP_N = n)` TVF marked as deprecated on latest-version indexes (raises Msg 42274)
- **DiskANN DDL** updated from `CREATE NONCLUSTERED INDEX ... USING DISKANN` to `CREATE VECTOR INDEX ... WITH (METRIC=..., TYPE='diskann')` (the current syntax)
- **`CREATE EXTERNAL MODEL`** standardised on `MODEL_TYPE` keyword (not `TASK`) across topic files, practice questions, and mock exams. Mock Exam 1 Q44 rewritten — the previous `TASK = CLASSIFICATION` answer was a fabricated value
- **Mock Exam 1 Q42** corrected: JSON path is `$.result.choices[0].message.content` (the `sp_invoke_external_rest_endpoint` `result` envelope is the most-missed RAG detail) — was previously `$.choices[0].message.content`
- **Mock Exam 2 Q39** rewritten to use `SELECT TOP (N) ... WITH APPROXIMATE` (previously used the non-existent `WITH (TOP_K = 10)` parameter)
- **Mock Exam 2 Q36** corrected — DiskANN normalisation is required for the `dot` metric used as a cosine proxy, NOT for the `cosine` metric itself
- **Exam duration** corrected to 120 minutes (was "~100 minutes")
- **Replaced ASCII bar chart** in README with a Mermaid pie chart + percentage table (Unicode FULL BLOCK rendered as disjointed squares on GitHub)
- **README "Skills measured" sections** wrapped in `<details>` collapsibles; same for "Official Microsoft Resources" sub-sections, to keep the main flow scannable

### Removed

- Broken Microsoft banner image (replaced with a working shields.io "Microsoft Certified" badge)
- Three 404 official-doc links in README (replaced with current URLs)
- `docs/superpowers/` directory (internal planning artifacts, not relevant to the public guide)
- Redundant "guide works in Obsidian" note that duplicated the new Obsidian onboarding section

### Fixed

- Inconsistent callout casing and a double `---` separator in `02-dynamic-data-masking-rls.md`
- Vector-search topic file's `Related Topics` section no longer omits the RAG cross-link

## [2026.03] — Pre-release (private)

Original private notes that the author used to pass DP-800. Not publicly released; preserved here for context.

### Highlights

- 11 topic sections aligned to the 2025 blueprint
- 50+ practice questions across the three domains
- Two full-length mock exams
- Cheat sheets for the highest-volatility topics
- 20-minute exam-morning final review
