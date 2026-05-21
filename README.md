---
title: DP-800 Study Guide
type: project
tags:
  - dp-800
  - microsoft
  - azure
  - sql
  - ai
  - certification
  - vector-search
  - rag
---

<p align="center">
  <a href="https://learn.microsoft.com/en-us/credentials/certifications/developing-ai-enabled-database-solutions/">
    <img src="https://learn.microsoft.com/en-us/media/logos/logo-ms-social-default.png" alt="Microsoft" height="60">
  </a>
</p>

<h1 align="center">DP-800: Developing AI-Enabled Database Solutions</h1>
<h3 align="center">Open-source community study guide for the Microsoft DP-800 certification</h3>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://learn.microsoft.com/en-us/credentials/certifications/developing-ai-enabled-database-solutions/"><img src="https://img.shields.io/badge/Microsoft-DP--800-0078D4?logo=microsoft&logoColor=white" alt="Microsoft DP-800"></a>
  <a href="https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800"><img src="https://img.shields.io/badge/Blueprint-March%202026-success" alt="Blueprint: March 2026"></a>
  <a href="https://learn.microsoft.com/en-us/sql/sql-server/"><img src="https://img.shields.io/badge/SQL%20Server-2025-CC2927?logo=microsoftsqlserver&logoColor=white" alt="SQL Server 2025"></a>
  <a href="https://azure.microsoft.com/en-us/products/azure-sql"><img src="https://img.shields.io/badge/Azure-SQL-0078D4?logo=microsoftazure&logoColor=white" alt="Azure SQL"></a>
  <a href="https://www.microsoft.com/microsoft-fabric"><img src="https://img.shields.io/badge/Microsoft-Fabric-742774?logo=microsoft&logoColor=white" alt="Microsoft Fabric"></a>
  <br>
  <a href="#"><img src="https://img.shields.io/badge/T--SQL-Language-336791?logo=microsoftsqlserver&logoColor=white" alt="T-SQL"></a>
  <a href="#"><img src="https://img.shields.io/badge/Vector%20Search-DiskANN-FF6F00" alt="Vector Search"></a>
  <a href="#"><img src="https://img.shields.io/badge/RAG-Retrieval%20Augmented-4B0082" alt="RAG"></a>
  <a href="#"><img src="https://img.shields.io/badge/MCP-Model%20Context%20Protocol-2D2D2D" alt="MCP"></a>
  <a href="#"><img src="https://img.shields.io/badge/Obsidian-compatible-7C3AED?logo=obsidian&logoColor=white" alt="Obsidian compatible"></a>
  <a href="#"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs welcome"></a>
</p>

<p align="center">
  <i>A community-maintained study guide for the <b>Microsoft DP-800: Developing AI-Enabled Database Solutions</b> certification.<br>
  Aligned to the official skills-measured list updated <b>March 12, 2026</b>.</i>
</p>

> [!NOTE]
> **I used this guide to pass DP-800.** ✅ These are the exact notes, cheat sheets, practice questions, and mock exams I built while preparing — refined while studying, hardened on the actual exam, and now open-sourced under MIT so you can pass too. Every section is mapped 1:1 to the official Microsoft skills-measured list. If it helped you, ⭐ the repo and pass it on.

---

## Why this guide exists

The DP-800 is Microsoft's first certification focused on building **AI-enabled database solutions** — vector search, embeddings, RAG, and intelligent search inside SQL Server, Azure SQL, and SQL databases in Microsoft Fabric. The official skills list is broad and changes quickly. Public study resources are scarce.

This repo is the notes that got me through it. Now it's yours.

## Who this is for

- **Database developers / DBAs** moving into AI-augmented workloads
- **Data engineers** who want to add vector search and RAG to relational platforms
- **AI / app developers** who need to talk fluently about Azure SQL, Fabric SQL, and T-SQL AI functions
- **Exam takers** preparing for DP-800 specifically — every topic file maps 1:1 to the official blueprint
- **Anyone curious** about how Microsoft is bringing GenAI into the database layer

You don't need to be taking the exam to get value — the guide doubles as a reference for SQL Server 2025 vector features, MCP server integration, Data API Builder, and embedding maintenance patterns.

## What's covered

- **11 topic sections** mapped 1:1 to the official skills measured list
- **7 cheat sheets** for fast review (security, vector/AI, JSON, performance, T-SQL, Azure SQL config)
- **50+ practice questions** with full explanations across all three domains
- **2 full-length mock exams** (45 questions each, timed)
- **Final review** designed to read in 20 minutes the morning of the exam
- **T-SQL code examples** covering vector search, RAG, full-text, and AI integration

## Exam at a glance

| Detail | Information |
| --- | --- |
| **Exam ID** | DP-800 |
| **Full Name** | Developing AI-Enabled Database Solutions |
| **Credential** | Microsoft Certified: SQL AI Developer Associate |
| **Passing Score** | 700 / 1000 |
| **Question Count** | 40–60 |
| **Duration** | ~100 minutes (varies by language) |
| **Cost (USD)** | $165 (varies by region) |
| **Renewal** | Annual (free Microsoft Learn assessment) |
| **Platforms tested** | SQL Server (incl. 2025), Azure SQL, SQL databases in Microsoft Fabric |
| **Language** | T-SQL |
| **Blueprint date** | March 12, 2026 |
| **Format** | Multiple choice, case studies, interactive scenarios |

### Domain weights

```text
Domain 1: Design and develop database solutions             ████████████████  35–40 %
Domain 2: Secure, optimize, and deploy database solutions   ████████████████  35–40 %
Domain 3: Implement AI capabilities in database solutions   ███████████       25–30 %
```

### Skills measured (high level)

**Domain 1 — Design and develop**
Tables · indexes · columnstore · specialized tables (in-memory, temporal, external, ledger, graph) · JSON columns and indexes · constraints · sequences · partitioning · views · functions · stored procedures · triggers · CTEs · window functions · JSON functions · regex (`REGEXP_LIKE`, `REGEXP_MATCHES`, `REGEXP_SPLIT_TO_TABLE`, etc.) · fuzzy matching (`EDIT_DISTANCE`, `JARO_WINKLER_DISTANCE`) · graph queries with `MATCH` · GitHub Copilot · MCP server endpoints

**Domain 2 — Secure, optimize, deploy**
Always Encrypted · column encryption · Dynamic Data Masking · Row-Level Security · object-level permissions · passwordless access · auditing · Managed Identity for model endpoints · secure GraphQL/REST/MCP endpoints · isolation levels · DMVs · Query Store · Query Performance Insight · blocking and deadlocks · SQL Database Projects (SDK-style) · schema drift detection · CI/CD pipelines · Data API Builder · Azure Monitor · CDC · Change Tracking · CES · Azure Functions SQL trigger · Logic Apps

**Domain 3 — AI capabilities**
External models · embedding maintenance (triggers, CT, CDC, CES, Azure Functions, Logic Apps, Microsoft Foundry) · chunking · embedding generation · full-text search · `VECTOR` data type · `VECTOR_DISTANCE` · `VECTOR_SEARCH` · `VECTOR_NORMALIZE` · `VECTORPROPERTY` · DiskANN indexes · ANN vs ENN · hybrid search · RRF (Reciprocal Rank Fusion) · RAG with `sp_invoke_external_rest_endpoint`

## 2026 updates you should know

> [!IMPORTANT]
> Microsoft refreshed the DP-800 skills measured on **March 12, 2026**. Highlights:

- **SQL Server 2025 is GA.** The `VECTOR` data type, `VECTOR_DISTANCE`, `VECTOR_SEARCH`, `VECTOR_NORMALIZE`, and `VECTORPROPERTY` are now generally available in SQL Server 2025 and Azure SQL Database.
- **DiskANN vector indexes** are in public preview for SQL Server 2025 (private preview in Azure SQL).
- **Half-precision (16-bit) vectors** are in preview — half the storage, roughly twice the dimensions per row (~4 000).
- **MCP server endpoints** (SQL Server + Fabric lakehouse) are explicitly tested.
- **Microsoft Foundry** is named as a valid embedding-maintenance method alongside CDC, Change Tracking, and CES.
- **Change Event Streaming (CES)** in Fabric is now in the blueprint.
- **Passwordless DB access** and **Managed Identity for model endpoints** are explicit security requirements.
- **Schema drift detection** in SQL Database Projects is now an explicit skill.

The [main overview](./certification/dp-800-overview.md) opens with the full "What's New" callout.

## How to use this guide

1. **Start at the [main overview](./certification/dp-800-overview.md)** — it has the full study path and a progress tracker.
2. **Work through the 11 topic sections in order** — each topic file is 300–600 lines with examples, comparison tables, common-mistake callouts, and exam tips.
3. **Hit the [cheat sheets](./certification/resources/cheat-sheets/cheat-sheets.md)** after each domain to consolidate.
4. **Take the [practice questions](./certification/resources/practice-questions/practice-questions.md)** — aim for 70 %+ per domain before moving on.
5. **Sit the two [mock exams](./certification/resources/mock-exam/mock-exam-1.md) under timed conditions** when you think you're close.
6. **Read [`final-review.md`](./certification/resources/final-review.md) the morning of the exam** — it's the 20-minute scan.

> The guide works in any Markdown viewer. It's also optimized for **Obsidian** — wikilinks, callouts, Mermaid diagrams, and Graph View all render correctly.

## Quick navigation

| Resource | Description |
| :--- | :--- |
| [Start Studying →](./certification/dp-800-overview.md) | Main index with all 11 study sections and progress tracker |
| [Cheat Sheets](./certification/resources/cheat-sheets/cheat-sheets.md) | Seven quick-reference guides for exam day |
| [Practice Questions](./certification/resources/practice-questions/practice-questions.md) | 50+ domain-specific questions with explanations |
| [Mock Exam 1](./certification/resources/mock-exam/mock-exam-1.md) | Full 45-question timed practice exam |
| [Mock Exam 2](./certification/resources/mock-exam-2/mock-exam-2.md) | Second full 45-question practice exam |
| [Final Review](./certification/resources/final-review.md) | 20-minute exam-morning scan |
| [Exam Tips](./certification/resources/exam-tips.md) | Time management, common traps, and strategy |
| [Appendix](./certification/resources/appendix/appendix.md) | Glossary, comparison tables, error reference |
| [T-SQL Code Examples](./certification/resources/code-examples/tsql/tsql-code-examples.md) | Standalone runnable T-SQL snippets |

## Repository layout

```text
dp-800-study-guide/
├── certification/
│   ├── dp-800-overview.md           # main entry point — start here
│   ├── 01-database-objects/         # tables, indexes, JSON, partitioning
│   ├── 02-programmability-objects/  # views, functions, procedures, triggers
│   ├── 03-advanced-tsql/            # CTEs, window functions, regex, graph
│   ├── 04-ai-assisted-tools/        # GitHub Copilot, MCP server endpoints
│   ├── 05-data-security-compliance/ # encryption, RLS, DDM, secure endpoints
│   ├── 06-performance-optimization/ # configs, isolation, plans, DMVs
│   ├── 07-cicd-database-projects/   # SQL DB Projects, schema drift
│   ├── 08-azure-services-integration/ # DAB, REST/GraphQL, CDC/CT/CES
│   ├── 09-models-embeddings/        # external models, embedding maintenance
│   ├── 10-intelligent-search/       # full-text, vector, hybrid (RRF)
│   ├── 11-rag/                      # RAG, sp_invoke_external_rest_endpoint
│   └── resources/
│       ├── cheat-sheets/            # quick-reference for exam day
│       ├── practice-questions/      # per-domain Q&A
│       ├── mock-exam/               # mock exam 1
│       ├── mock-exam-2/             # mock exam 2
│       ├── code-examples/tsql/      # standalone T-SQL examples
│       ├── appendix/                # glossary, comparisons, error reference
│       ├── final-review.md          # 20-minute exam-morning scan
│       ├── exam-tips.md             # strategy and time management
│       └── official-links.md        # Microsoft docs and exam registration
├── LICENSE                          # MIT
└── README.md                        # this file
```

## Official Microsoft resources

### Exam and certification

- [DP-800 skills measured (official study guide)](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800)
- [DP-800 certification page](https://learn.microsoft.com/en-us/credentials/certifications/developing-ai-enabled-database-solutions/)
- [Schedule the exam (Pearson VUE)](https://learn.microsoft.com/en-us/credentials/certifications/exams/dp-800/)
- [Free Microsoft Learn practice assessment](https://learn.microsoft.com/en-us/credentials/certifications/azure-administrator/practice/assessment?assessment-type=practice&assessmentId=1704375541&practice-assessment-type=certification)
- [Exam sandbox (try the testing UI)](https://aka.ms/examdemo)
- [Request accommodations](https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations)

### Documentation by topic

- [SQL Server documentation](https://learn.microsoft.com/en-us/sql/?view=sql-server-ver17)
- [SQL Server 2025 — announcement](https://www.microsoft.com/en-us/sql-server/blog/2025/05/19/announcing-sql-server-2025-preview-the-ai-ready-enterprise-database-from-ground-to-cloud/)
- [Azure SQL documentation](https://learn.microsoft.com/en-us/azure/azure-sql/)
- [SQL database in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/database/sql/)
- [VECTOR data type](https://learn.microsoft.com/en-us/sql/t-sql/data-types/vector-data-type)
- [VECTOR_DISTANCE](https://learn.microsoft.com/en-us/sql/t-sql/functions/vector-distance-transact-sql)
- [VECTOR_SEARCH](https://learn.microsoft.com/en-us/sql/t-sql/functions/vector-search-transact-sql)
- [Vector indexes (DiskANN)](https://learn.microsoft.com/en-us/azure/azure-sql/database/vector-index)
- [sp_invoke_external_rest_endpoint](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-invoke-external-rest-endpoint-transact-sql)
- [CREATE EXTERNAL MODEL](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-external-model-transact-sql)
- [Data API Builder (DAB)](https://learn.microsoft.com/en-us/azure/data-api-builder/)
- [SQL Database Projects](https://learn.microsoft.com/en-us/sql/azure-data-studio/extensions/sql-database-project-extension)
- [Change Data Capture](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-data-capture-sql-server)
- [Change Tracking](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-tracking-sql-server)
- [Change Event Streaming (CES) in Fabric](https://learn.microsoft.com/en-us/fabric/database/sql/change-event-streaming)
- [Always Encrypted](https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine)
- [Row-Level Security](https://learn.microsoft.com/en-us/sql/relational-databases/security/row-level-security)
- [Dynamic Data Masking](https://learn.microsoft.com/en-us/sql/relational-databases/security/dynamic-data-masking)
- [Microsoft Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Model Context Protocol (MCP) spec](https://modelcontextprotocol.io/)
- [GitHub Copilot in VS Code](https://docs.github.com/en/copilot)
- [Copilot in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/fundamentals/copilot-fabric-overview)

### Community and learning paths

- [Microsoft Learn — DP-800 learning path](https://learn.microsoft.com/en-us/training/courses/dp-800t00)
- [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/products/)
- [SQL Server Tech Community](https://techcommunity.microsoft.com/category/sql-server/blog/sqlserver)
- [Microsoft Fabric Blog](https://blog.fabric.microsoft.com/)
- [Azure SQL Dev Corner](https://devblogs.microsoft.com/azure-sql/)
- [Data Exposed (video series)](https://learn.microsoft.com/en-us/shows/data-exposed/)
- [Exam Readiness Zone](https://learn.microsoft.com/en-us/shows/exam-readiness-zone/)

## Contributing

Found an error, a stale link, or a topic that needs deeper coverage? PRs are welcome.

- **Small fixes** (typos, link rot, factual corrections) — open a PR directly
- **New practice questions or topic expansions** — open an issue first to discuss scope
- **Blueprint changes** — Microsoft updates DP-800 periodically; PRs that bring sections in line with the latest skills-measured list are especially appreciated

Please keep the existing structure: each topic file follows the conventions in [`CLAUDE.md`](./CLAUDE.md), and code examples live in `certification/resources/code-examples/tsql/`.

## License

Released under the [MIT License](./LICENSE). Use, fork, remix, redistribute — just keep the copyright notice.

---

<p align="center">
  <i>This guide is a community resource. It is <b>not</b> affiliated with, endorsed by, or sponsored by Microsoft.<br>
  "Microsoft", "Azure", "SQL Server", and "Microsoft Fabric" are trademarks of Microsoft Corporation.<br>
  Always verify against the official <a href="https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800">DP-800 skills measured</a> page — it is the source of truth.</i>
</p>

<p align="center"><b>Good luck on the exam. You've got this. ⭐ this repo if it helped you pass.</b></p>
