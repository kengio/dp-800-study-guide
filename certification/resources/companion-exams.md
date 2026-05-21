---
title: "DP-800 Companion Exams"
type: resource
tags:
  - dp-800
  - companion-exams
  - dp-700
  - ai-102
  - certification-path
---

# DP-800 Companion Exams

> [!abstract]
>
> - **Microsoft Certified: Fabric Data Engineer Associate (DP-700)** — natural next step for SQL/data folks; shares CI/CD, RLS, DDM, security, T-SQL transformations
> - **Microsoft Certified: Azure AI Engineer Associate (AI-102)** — natural next step for AI-focused folks; shares RAG, Azure OpenAI, vector concepts, prompt engineering. **AI-102 retires June 30, 2026** — check [Microsoft Learn](https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/) for the successor before scheduling
> - **DP-800 prep gives you a meaningful head start** on both — this guide maps the overlapping content so you know what's review vs. genuinely new

> [!tip] How to use this guide
>
> - **Already passed DP-800?** Read the "What transfers from DP-800" rows below to see which domains you can skim vs. study deeply for the next exam
> - **Deciding between DP-700 and AI-102?** The recommended paths section below picks the better fit based on your role
> - **Stacking certifications?** The exam-blueprint comparison table at the end shows the structural shape of each so you can sequence them

---

## Companion exams at a glance

| Exam | Cert | Blueprint | Format | Retirement | DP-800 overlap |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[DP-700](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)** | Fabric Data Engineer Associate | Apr 20, 2026 | ~50 q · 100 min · scaled 700/1000 | Active | **Medium** (~30% of skills overlap with DP-800 Domain 2) |
| **[AI-102](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-102)** | Azure AI Engineer Associate | Dec 23, 2025 | ~50 q · 120 min · scaled 700/1000 | ⚠️ **Jun 30, 2026** | **Medium-low** (~20% overlap, mostly DP-800 Domain 3) |

> [!warning] AI-102 retirement
> The AI-102 exam **retires June 30, 2026**. Microsoft announced this on the [skills hub blog](https://techcommunity.microsoft.com/blog/skills-hub-blog/the-ai-job-boom-is-here-are-you-ready-to-showcase-your-skills/4494128). If you're considering it, **schedule before the retirement date** or wait for the announced successor. Already-earned AI-102 credentials remain valid through their normal one-year renewal cycle even after the exam retires.

---

## DP-700 — Implementing Data Engineering Solutions Using Microsoft Fabric

**Audience.** Data engineers building Fabric analytics pipelines — Lakehouse, OneLake, Eventstreams, Spark, KQL. Sits between Power BI / data analyst work (PL-300, DP-600 retired) and platform-deep data infrastructure roles.

**Skills at a glance.**

- Implement and manage an analytics solution (30–35%)
- Ingest and transform data (30–35%)
- Monitor and optimize an analytics solution (30–35%)

### What transfers from DP-800

| DP-800 skill | DP-700 equivalent | Transfer % |
| :--- | :--- | :---: |
| Row-Level Security (RLS) — Domain 2 | "Implement row-level, column-level, object-level, and folder/file-level access controls" | 90% |
| Dynamic Data Masking — Domain 2 | "Implement dynamic data masking" | 90% |
| SQL Database Projects + CI/CD — Domain 2 | "Implement database projects" + "Create and configure deployment pipelines" | 70% |
| Source control + branching — Domain 2 | "Configure version control" | 80% |
| T-SQL fundamentals (CTEs, window functions, JSON, MATCH graph) — Domain 1 | "Transform data by using PySpark, SQL, and KQL" | 50% (DP-700 SQL is a subset; KQL/PySpark dominate) |
| Schema drift detection — Domain 2 | "Implement database projects" workflow | 50% |
| Identifying and resolving query performance issues — Domain 2 | "Identify and resolve T-SQL errors" + "Optimize query performance" | 60% |

**Net-new in DP-700** (no DP-800 prep coverage):

- OneLake architecture, OneLake shortcuts, query acceleration
- Lakehouse table optimization (V-Order, compaction, vacuum)
- Mirroring (Snowflake, Databricks, Cosmos DB, Fabric SQL DB)
- Eventstreams, Eventhouses, KQL queries, real-time intelligence
- Spark workspace settings, Spark structured streaming, Spark performance
- Dataflow Gen 2 vs notebooks vs pipelines decision logic
- Sensitivity labels, endorsement, domain workspace settings
- Pipeline orchestration patterns with parameters and dynamic expressions

**Recommended prep budget if you already have DP-800.** Roughly **40–50% less** than starting from scratch. Skip the security overlap and the SQL Database Projects work; focus your time on OneLake, Eventstreams, Spark, and KQL. Plan ~30 hours instead of the ~60 hours a cold start would need.

---

## AI-102 — Designing and Implementing a Microsoft Azure AI Solution

**Audience.** Azure AI engineers building end-to-end AI solutions across OpenAI, vision, language, speech, knowledge mining. Less about data and more about the AI stack itself.

**Skills at a glance.**

- Plan and manage an Azure AI solution (20–25%)
- Implement generative AI solutions (15–20%)
- Implement an agentic solution (5–10%)
- Implement computer vision solutions (10–15%)
- Implement natural language processing solutions (15–20%)
- Implement knowledge mining and information extraction solutions (15–20%)

### What transfers from DP-800

| DP-800 skill | AI-102 equivalent | Transfer % |
| :--- | :--- | :---: |
| RAG use cases + grounding — Domain 3 | "Implement a RAG pattern by grounding a model in your data" | 80% |
| `sp_invoke_external_rest_endpoint` calling Azure OpenAI — Domain 3 | "Use Azure OpenAI in Foundry Models to generate content" | 60% (concept transfers, but AI-102 is SDK-first, not T-SQL) |
| Prompt engineering, structured-output prompts — Domain 3 | "Apply prompt engineering techniques to improve responses" | 75% |
| External-model evaluation (multimodal, multilanguage) — Domain 3 | "Choose the appropriate AI models for your solution" | 70% |
| Vector concepts (cosine/dot/euclidean, ANN vs ENN) — Domain 3 | "Implement semantic and vector store solutions" (Azure AI Search) | 50% (DP-800 is in-database vectors; AI-102 is Azure AI Search) |
| Embedding generation + chunking — Domain 3 | "Implement a RAG pattern by grounding a model in your data" + indexer skillsets | 60% |
| Securing model endpoints (Managed Identity) — Domain 2 | "Manage authentication for a Microsoft Foundry Service resource" | 60% |

**Net-new in AI-102** (no DP-800 prep coverage):

- Microsoft Foundry service architecture (formerly Azure AI Foundry) — hubs, projects, deployment options
- Azure AI Search (index, skillset, indexer, knowledge store projections)
- Computer vision: image classification, object detection, Video Indexer, spatial analysis
- Speech: STT, TTS, SSML, custom speech, intent/keyword recognition
- Natural language: entity extraction, sentiment, PII detection, custom question answering
- Document Intelligence (formerly Form Recognizer): prebuilt + custom models
- Content Understanding: OCR pipelines, multi-modal extraction
- Agent Service + Agent Framework: multi-agent orchestration, autonomous workflows
- Responsible AI: content filters, blocklists, prompt shields, harm detection
- Container deployment for AI workloads (local + edge)

**Recommended prep budget if you already have DP-800.** Roughly **15–25% less** than starting from scratch. The AI fundamentals (RAG, embeddings, prompt engineering) transfer well but they're only ~15–20% of the AI-102 blueprint. Plan ~50 hours instead of ~60–70 hours.

> [!warning] Time pressure
> AI-102 retires June 30, 2026. If you want this credential, your prep window is **roughly 5 weeks from this guide's blueprint date**. Past the retirement, the successor exam will likely cover similar ground but with a re-blueprinted skills list.

---

## Recommended paths

### Path A: DP-800 → DP-700 (data engineering depth)

- **Best for**: SQL developers, database engineers, BI engineers who built up DP-800 and want to broaden into Fabric data engineering
- **Why**: Domain 2 of DP-800 (security, performance, CI/CD) is the bridge — DP-700 reuses the same primitives at the Fabric/Lakehouse layer
- **Sequence**: DP-800 → 3 months consolidation → DP-700
- **Total time investment**: ~90 hours (60 for DP-800, ~30 for DP-700 with overlap credit)

### Path B: DP-800 → AI-102 (AI engineering depth) — schedule before Jun 30, 2026

- **Best for**: Database engineers who want to deepen the AI stack beyond in-database vectors and RAG
- **Why**: DP-800's Domain 3 is the perfect on-ramp — you understand vectors, embeddings, RAG, and Azure OpenAI; AI-102 expands to the rest of the Azure AI surface
- **Sequence**: DP-800 → consolidate ~4 weeks → AI-102 (before retirement)
- **Total time investment**: ~110 hours (60 for DP-800, ~50 for AI-102 with overlap credit)
- **Risk**: AI-102 retires Jun 30, 2026 — if you can't make the date, wait for the successor announcement

### Path C: DP-800 standalone, then renew annually

- **Best for**: Specialists whose job is squarely "AI-enabled databases"; nothing else maps directly
- **Why**: DP-800 is the only Microsoft credential targeting this niche — neither DP-700 nor AI-102 fills the same gap
- **Sequence**: Pass DP-800 → renew annually (see [renewal-guide.md](./renewal-guide.md)) → revisit related certs when blueprints stabilise
- **Total time investment**: 60 hours initial + ~3 hours per annual renewal

### Path D: DP-800 → both DP-700 and AI-102 (full data + AI surface)

- **Best for**: Architects, platform leads, anyone whose role spans data engineering AND AI integration
- **Why**: Together these three certs cover the entire "data + AI on Microsoft" surface that platform-spanning roles require
- **Sequence**: DP-800 → AI-102 (before Jun 30, 2026 retirement) → DP-700
- **Total time investment**: ~140 hours total

---

## Exam-blueprint comparison

| Attribute | DP-800 | DP-700 | AI-102 |
| :--- | :---: | :---: | :---: |
| **Cert level** | Associate | Associate | Associate |
| **Validity** | 1 year (annual renewal) | 1 year (annual renewal) | 1 year (annual renewal) |
| **Cost** | $165 USD | $165 USD | $165 USD |
| **Duration** | ~120 min | ~100 min | ~120 min |
| **Questions** | ~50 + case study | ~40–50 + case study | ~40–60 + case study |
| **Pass score** | 700 / 1000 | 700 / 1000 | 700 / 1000 |
| **Case study?** | Yes (5-question block) | Yes | Yes |
| **Domains** | 3 | 3 | 6 |
| **Practice assessment** | Free on MS Learn | Free on MS Learn | Free on MS Learn |
| **Renewal** | Free, unproctored, open-book | Free, unproctored, open-book | Free, unproctored, open-book |

---

## Use Cases

- **Career-laddering**: pick your next exam based on where you want to specialise (data vs AI)
- **Team planning**: identify which certifications cover which gaps on a data + AI team
- **Hiring**: understand what a candidate with DP-800 knows that's transferable to a DP-700 or AI-102 role
- **Cert-stacking**: sequence multiple certifications efficiently by exploiting overlap

## Exam Tips

> [!tip] Exam Tips for stacking
>
> - **DP-700 first if your day job is data engineering**, AI-102 first if your day job is AI integration. Sequence by relevance to current work, not blueprint date
> - **Don't pay for the same skill twice.** If you've done DP-800 prep, skip the overlap rows above for the next exam — your time is better spent on net-new content
> - **AI-102 retirement is a hard deadline.** If you want the credential, schedule it now and reverse-engineer your prep timeline from the exam date, not from "when I feel ready"
> - **Renewals stack independently.** Each certification has its own 1-year renewal window. Calendar them.

## Related Topics

- [Renewal Guide](./renewal-guide.md) — DP-800-specific renewal workflow
- [Final Review](./final-review.md) — DP-800 exam-morning scan
- [Exam Tips](./exam-tips.md) — DP-800-specific strategies (some transfer to companion exams)
- [Official Links](./official-links.md) — Microsoft Learn entry points

## Official Documentation

- [DP-700 Skills Measured](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700) — current blueprint with change log
- [AI-102 Skills Measured](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-102) — current blueprint with change log + retirement notice
- [Microsoft Certification Path Browser](https://learn.microsoft.com/en-us/credentials/browse/) — full catalogue
- [Fabric Data Engineer Associate cert page](https://learn.microsoft.com/en-us/credentials/certifications/fabric-data-engineering-associate/)
- [Azure AI Engineer Associate cert page](https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/)

---

**[← Back to resources](./exam-resources.md)** | **[↑ Back to overview](../dp-800-overview.md)**
