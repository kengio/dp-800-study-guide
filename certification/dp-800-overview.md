---
title: DP-800 Developing AI-Enabled Database Solutions
type: certification
aliases:
  - DP-800
tags:
  - dp-800
  - microsoft
  - azure
  - sql
  - ai
  - certification
---

# Microsoft DP-800: Developing AI-Enabled Database Solutions

## How to Use This Guide

1. **Topic files** (`01-topic-name.md`) — core study material with SQL examples, comparison tables, and practice questions. Start here.
2. **Section READMEs** — overview flowcharts and topic indexes. Use to orient before diving into a section.
3. **Cheat sheets** (`resources/cheat-sheets/`) — compact quick-reference for exam day and review. Each ends with a `## Gotchas & Traps` section and a `## Before the Exam, I Can…` checklist. Use after studying a section to reinforce.
4. **Practice questions** (`resources/practice-questions/`) — 15–20 questions per domain (Domain 2 has 20; Domains 1 and 3 have 15 each), with explanations. Use to test knowledge after each domain.
5. **Mock exams** (`resources/mock-exam/`, `resources/mock-exam-2/`) — full 45-question timed exams. Take after completing all domains.
6. **Final Review** (`resources/final-review.md`) — 20-minute exam-morning scan: highest-probability facts across all three domains and 10 last-minute traps. Read the morning of the exam.

> Study path: topic files → cheat sheets → practice questions → mock exams → **final-review.md** (exam morning)

## Exam Overview

| Detail             | Information                                               |
| ------------------ | --------------------------------------------------------- |
| **Exam**           | DP-800                                                    |
| **Full Name**      | Developing AI-Enabled Database Solutions                  |
| **Passing Score**  | 700 / 1000                                                |
| **Renewal**        | Annual (free online assessment on Microsoft Learn)        |
| **Platforms**      | SQL Server, Azure SQL, SQL databases in Microsoft Fabric  |
| **Languages**      | T-SQL                                                     |

## Exam Domain Weights

```mermaid
pie title Exam Domain Distribution
    "Design and develop database solutions" : 37
    "Secure, optimize, and deploy database solutions" : 37
    "Implement AI capabilities in database solutions" : 26
```

## Study Topics

### Domain 1: Design and Develop Database Solutions (35–40%)

| Section | Priority | Topics |
| :--- | :--- | :--- |
| [01-Database Objects](01-database-objects/database-objects.md) | High | Tables, indexes, constraints, partitioning |
| [02-Programmability Objects](02-programmability-objects/programmability-objects.md) | High | Views, functions, stored procedures, triggers |
| [03-Advanced T-SQL](03-advanced-tsql/advanced-tsql.md) | High | CTEs, window functions, JSON, regex, graph |
| [04-AI-Assisted Tools](04-ai-assisted-tools/ai-assisted-tools.md) | Medium | GitHub Copilot, MCP servers, AI security |

### Domain 2: Secure, Optimize, and Deploy (35–40%)

| Section | Priority | Topics |
| :--- | :--- | :--- |
| [05-Data Security & Compliance](05-data-security-compliance/data-security-compliance.md) | High | Encryption, masking, RLS, auditing |
| [06-Performance Optimization](06-performance-optimization/performance-optimization.md) | High | Query plans, DMVs, Query Store, blocking |
| [07-CI/CD Database Projects](07-cicd-database-projects/cicd-database-projects.md) | Medium | SQL DB Projects, source control, deployment |
| [08-Azure Services Integration](08-azure-services-integration/azure-services-integration.md) | Medium | DAB, REST/GraphQL, monitoring, CDC |

### Domain 3: Implement AI Capabilities (25–30%)

| Section | Priority | Topics |
| :--- | :--- | :--- |
| [09-Models & Embeddings](09-models-embeddings/models-embeddings.md) | High | External models, embedding maintenance |
| [10-Intelligent Search](10-intelligent-search/intelligent-search.md) | High | Full-text, vector, hybrid search |
| [11-RAG](11-rag/rag.md) | High | Retrieval-augmented generation |

### Practice & Resources

| Resource | Description |
| :--- | :--- |
| [Practice Questions](resources/practice-questions/practice-questions.md) | Domain-specific practice questions |
| [Mock Exam 1](resources/mock-exam/mock-exam-1.md) | Full-length practice exam |
| [Mock Exam 2](resources/mock-exam-2/mock-exam-2.md) | Alternative practice exam |
| [Exam Tips](resources/exam-tips.md) | Strategies and exam format guide |
| [Official Links](resources/official-links.md) | Microsoft documentation and registration |
| [Code Examples](resources/code-examples/tsql/tsql-code-examples.md) | Standalone T-SQL code example files |
| [Cheat Sheets](resources/cheat-sheets/cheat-sheets.md) | Quick-reference guides for exam topics (each includes Gotchas & Traps + Before the Exam checklist) |
| [Final Review](resources/final-review.md) | 20-minute exam-morning scan: top facts and last-minute traps for all three domains |
| [Appendix](resources/appendix/appendix.md) | Glossary, comparison tables, error messages |

## Study Progress Tracker

### Phase 1: Database Design & T-SQL

- [ ] Tables, indexes, and constraints
- [ ] Specialized tables (in-memory, temporal, external, ledger, graph)
- [ ] JSON columns and indexes
- [ ] Partitioning strategies
- [ ] Views and programmability objects
- [ ] CTEs and window functions
- [ ] JSON functions
- [ ] Regex and fuzzy string matching
- [ ] Graph queries with MATCH operator

### Phase 2: AI-Assisted Development

- [ ] GitHub Copilot setup and configuration
- [ ] MCP server endpoints
- [ ] AI security impact assessment
- [ ] Copilot instruction files

### Phase 3: Security, Performance & Deployment

- [ ] Always Encrypted and column-level encryption
- [ ] Dynamic Data Masking and Row-Level Security
- [ ] Object-level permissions and auditing
- [ ] Transaction isolation levels
- [ ] Query execution plans and DMVs
- [ ] Query Store and Query Performance Insight
- [ ] SQL Database Projects (SDK-style)
- [ ] CI/CD pipeline design
- [ ] Data API Builder configuration

### Phase 4: AI Capabilities

- [ ] External model evaluation and creation
- [ ] Embedding maintenance strategies
- [ ] Chunking and embedding generation
- [ ] Full-text search
- [ ] Vector data types and indexes
- [ ] Vector and hybrid search
- [ ] RAG implementation with sp_invoke_external_rest_endpoint

### Phase 5: Practice

- [ ] Complete practice questions (aim for 70%+)
- [ ] Take Mock Exam 1 (under timed conditions)
- [ ] Review weak areas
- [ ] Take Mock Exam 2
