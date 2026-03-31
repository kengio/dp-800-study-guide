---
title: DP-800 Cheat Sheets
type: resources
tags:
  - dp-800
  - cheat-sheets
  - quick-reference
aliases:
  - Cheat Sheets Index
---

# DP-800 — Cheat Sheets

Quick-reference guides for high-frequency exam topics. Each sheet is designed for fast lookup during study sessions — not a substitute for the full topic files, but a compact refresher.

## Available Cheat Sheets

| Cheat Sheet | Domain | Description |
| :--- | :--- | :--- |
| [T-SQL Core Commands](./tsql-core-commands.md) | 1 | DDL, DML, query patterns, control flow, session, metadata |
| [JSON Functions](./json-functions-quick-ref.md) | 1 | All JSON functions with syntax and examples |
| [Security](./security-quick-ref.md) | 2 | TDE, Always Encrypted, masking, RLS, permissions, auditing |
| [Vector & AI](./vector-ai-quick-ref.md) | 3 | VECTOR type, distance functions, DiskANN, full-text, hybrid, RAG |
| [Performance & DMVs](./performance-dmvs-quick-ref.md) | 2 | DMV reference, copy-paste diagnostic queries |
| [Azure SQL Config](./azure-sql-config-quick-ref.md) | 2 | Database configs, Query Store, DAB, sqlpackage |

## How to Use

- **Before a study session** — skim the relevant sheet to activate prior knowledge
- **After completing a topic** — use the sheet to self-test recall
- **Final review** — read all sheets end-to-end as a refresher

> [!tip] Study Tip
> Print these cheat sheets or keep them open on a second screen during practice questions. Active recall works best when you attempt the answer first, then check the cheat sheet — avoid reading passively.

## Key Numbers to Remember

| Item | Value |
| :--- | :--- |
| NVARCHAR(MAX) size | ~2 GB |
| Max columns per table | 1,024 |
| Max index key size (nonclustered) | 1,700 bytes |
| Max partitions per table | 15,000 |
| Max parameters per stored procedure | 2,100 |
| VECTOR max dimensions | 1,998 |
| DiskANN max dimensions | 1,998 |
| sp_invoke_external_rest_endpoint timeout | 30 seconds |
| Query Store MAX_STORAGE_SIZE_MB default | 100 MB |
| Dynamic Data Masking function count | 4 (default, email, random, partial) |
| Always Encrypted column master key locations | 3 (cert store, Azure Key Vault, CNG) |

---

**[← Back to Resources](../exam-resources.md)**
