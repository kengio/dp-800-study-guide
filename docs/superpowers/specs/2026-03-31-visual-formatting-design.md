# DP-800 Visual Formatting & Exam-Confidence Design

**Date:** 2026-03-31  
**Exam:** Friday 2026-04-03  
**Scope:** All topic files + cheat sheets (mock exams and practice questions excluded)

---

## Goal

Make the DP-800 study guide beautiful and easy to skim in Obsidian, while adding exam-confidence content so the user feels prepared walking into the exam on Friday.

---

## Section 1: Universal Formatting Standards

Applied to every topic file and cheat sheet.

### Highlights

- `==highlight==` the single most exam-relevant term or value in each table row and inline definitions
- Not every term — only the one the exam would focus on in a question

### Abstract callout

- Every topic file gets a `[!abstract]` callout near the top (after YAML frontmatter, before or replacing the plain overview paragraph)
- 2–4 bullets summarising what the file covers and what the exam specifically tests

### Horizontal rules

- `---` separator between every major `##` section for visual breathing room

### Bold key phrases inline

- Critical terms bolded in prose so scanning eyes catch them (e.g. "The **delta rowstore** absorbs new inserts before compression")

### Callout type enforcement

| Callout | Usage |
| :--- | :--- |
| `[!info]` | Context / what-this-is |
| `[!tip] Exam Tips` | Exam-specific advice (bottom of file) |
| `[!warning] Common Mistake` | Traps, gotchas, "don't confuse X with Y" — placed inline near relevant content |
| `[!note]` | Extra detail, not critical |
| `[!abstract]` | Top-of-file summary + cheat sheet quick-reference |

---

## Section 2: Exam-Confidence Content Additions

### `[!tip] What the Exam Tests` callout

- Added near the top of every topic file, after the `[!abstract]`, before the first `##` section
- 2–4 bullets in exam language: "The exam will ask you to choose between X and Y when the scenario says Z"
- Distinct from the existing `## Exam Tips` section at the bottom — this is a fast orientation before reading

### Enriched `## Exam Tips` sections

- Existing Exam Tips sections get additional bullets for any testable fact not currently covered
- No restructuring — additive only

### Inline `[!warning] Common Mistake` callouts

- Added near the content they relate to (not only at the end of the file)
- 1–3 sentences: what the mistake is and why the correct answer differs

---

## Section 3: Cheat Sheet Enhancements

Two new sections added to the bottom of all 6 cheat sheets (before Official Documentation if present):

### Files

- `certification/resources/cheat-sheets/security-quick-ref.md`
- `certification/resources/cheat-sheets/vector-ai-quick-ref.md`
- `certification/resources/cheat-sheets/tsql-core-commands.md`
- `certification/resources/cheat-sheets/json-functions-quick-ref.md`
- `certification/resources/cheat-sheets/performance-dmvs-quick-ref.md`
- `certification/resources/cheat-sheets/azure-sql-config-quick-ref.md`

### `## Gotchas & Traps`

- 4–8 bullets of things that trip people up on the exam
- Written as "Don't confuse X with Y" or "Remember that Z only applies when…"
- Concentrated list for rapid pre-exam scanning

### `## Before the Exam, I Can…`

- 5–8 `- [ ]` checkboxes of concrete capabilities
- E.g. "Explain the difference between TDE and Always Encrypted and when to use each"
- Left unchecked in the file — user ticks them off mentally on exam morning

---

## Section 4: Section README Quick Recall Diagrams

### Mermaid `mindmap` in each section README

- Added as a `## Quick Recall` section near the top of each of the 11 section READMEs
- Shows 4–6 key concepts per section in a visual map
- Fast orientation before diving into topic files

### Section READMEs to update

- `01-database-objects/README.md`
- `02-programmability-objects/README.md`
- `03-advanced-tsql/README.md`
- `04-ai-assisted-tools/README.md`
- `05-data-security-compliance/README.md`
- `06-performance-optimization/README.md`
- `07-cicd-database-projects/README.md`
- `08-azure-services-integration/README.md`
- `09-models-embeddings/README.md`
- `10-intelligent-search/README.md`
- `11-rag/README.md`

---

## Section 5: Final Review File

**Path:** `certification/resources/final-review.md`

A single exam-morning file. Structure:

- `[!abstract]` header: "Read this in 20 minutes the morning of the exam"
- `## Domain 1: Design and Develop` — 8–12 highest-probability testable facts
- `## Domain 2: Secure, Optimize, Deploy` — 8–12 highest-probability testable facts
- `## Domain 3: AI Capabilities` — 8–12 highest-probability testable facts
- `## Last-Minute Traps` — 10 "don't confuse X with Y" bullets drawn from all domains

Deliberately short — fits on one long scroll, no deep dives.

---

## Execution Order (priority-first)

1. `final-review.md` — highest exam-day value, standalone new file
2. All 6 cheat sheets — Gotchas & Traps + Before the Exam checklist
3. Topic files (all 41) — abstract callout, What the Exam Tests callout, inline warnings, highlights
4. Section READMEs (11) — Quick Recall mindmap diagrams

---

## Out of Scope

- Mock exam files (`resources/mock-exam/`, `resources/mock-exam-2/`)
- Practice question files (`resources/practice-questions/`)
- Code example files (`resources/code-examples/`)
- Appendix files
