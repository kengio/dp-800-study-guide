# CLAUDE.md

Study notes for the Microsoft DP-800: Developing AI-Enabled Database Solutions certification exam.

## Repository Structure

```text
dp-800-study-guide/
├── certification/
│   ├── dp-800-overview.md      # Certification index with exam overview and progress tracker
│   ├── 01-database-objects/    # Design and implement database objects
│   ├── 02-programmability-objects/ # Views, functions, stored procedures, triggers
│   ├── 03-advanced-tsql/       # CTEs, window functions, JSON, regex, graph queries
│   ├── 04-ai-assisted-tools/   # GitHub Copilot, MCP, AI security
│   ├── 05-data-security-compliance/ # Encryption, masking, RLS, auditing
│   ├── 06-performance-optimization/ # Configs, isolation levels, query plans
│   ├── 07-cicd-database-projects/   # SQL Database Projects, CI/CD, deployment
│   ├── 08-azure-services-integration/ # DAB, REST/GraphQL, monitoring, CDC
│   ├── 09-models-embeddings/   # External models, embedding generation
│   ├── 10-intelligent-search/  # Full-text, vector, and hybrid search
│   ├── 11-rag/                 # Retrieval-augmented generation
│   └── resources/              # Practice questions, mock exams, exam tips, code examples, appendix, cheat sheets
```

Each topic folder contains a named index file (e.g., `database-objects.md`, `advanced-tsql.md`) and numbered `.md` topic files.

## Content Guidelines

### Content Placement

- **Single certification** — all content lives under `certification/`
- **Code examples** go in `certification/resources/code-examples/tsql/` as `.md` files, never `.sql`

### Code Examples

- **Always `.md` files**, never `.sql` — store in `certification/resources/code-examples/tsql/`
- Fenced code blocks with language tags (`sql`, `tsql`, `json`, `yaml`)
- Group related snippets under `##` headings; add YAML frontmatter with `tags`

### File Size

- **Target: 300–600 lines**; hard limit: ~800 lines (~20–25 KB)
- **Exception:** `mock-exam/questions.md` files — do not split
- **Split** when 2+ distinct sub-topics can stand alone → `03-topic-part1.md` + `03-topic-part2.md`:
  1. Same number prefix; append `-part1` / `-part2`
  2. Each part gets own YAML frontmatter and intro
  3. Terminal sections (Use Cases → Official Docs) go in **Part 2 only**; Part 1 ends with forward link
  4. Update topic index file; delete original; fix all links repo-wide

### Markdown Conventions

- Run markdownlint on every modified file; blank lines before/after headings (MD022)
- Language tags on all code blocks (`sql`, `tsql`, `json`)
- **Practice answers:** Obsidian foldable `> [!success]- Answer` callout
- **Practice choices:** A/B/C/D on separate lines (no bullets); two trailing spaces for line breaks

### Obsidian Callouts

Use callouts to break up dense text in topic files and cheat sheets. Standard types:

| Callout | Usage |
| :--- | :--- |
| `> [!info]` | Section intros, neutral context, "what this is" |
| `> [!tip] What the Exam Tests` | Top-of-file orientation: 2–4 bullets on what the exam specifically tests in this file |
| `> [!tip] Exam Tips` | Exam-specific advice in the terminal Exam Tips section |
| `> [!warning] Common Mistake` | Frequent errors, gotchas, "don't confuse X with Y" |
| `> [!note]` | Extra detail, caveats, "worth knowing but not critical" |
| `> [!success]- Answer` | Collapsed practice question answers (foldable) |
| `> [!abstract]` | Quick-reference summaries at top of cheat sheets and topic files |

- Use `> [!tip] What the Exam Tests` immediately after the `[!abstract]` callout, before the first `##` section
- Use `> [!tip] Exam Tips` blocks instead of bare bullet lists for the **Exam Tips** section in topic files
- Use `> [!warning]` to highlight traps covered in the **Common Issues** section
- Highlight key terms in tables with `==text==` (Obsidian highlight syntax)

### Diagrams & Images

- **Architecture diagrams:** Mermaid (`flowchart`, `sequenceDiagram`, `graph`)
- **Directory trees:** ASCII text, not Mermaid
- **Screenshots:** `images/<feature>/`; standard markdown `![Alt](path)` with caption; ≤800 px wide

### Links

- **Link to files, not folders** (`path/to/database-objects.md`, not `path/to/`)
- **Topic index files** are named after their folder (e.g., `./database-objects.md`, `./advanced-tsql.md`) — never `README.md`
- **Always use `./filename.md`** for same-folder links — bare filenames resolve ambiguously in Obsidian
- Verify target files exist after edits

### Section Ordering (End of Topic Files)

Terminal sections in this exact order:

1. `## Use Cases`
2. `## Common Issues & Errors`
3. `## Best Practices` *(optional)*
4. `## Exam Tips`
5. `## Key Takeaways`
6. `## Related Topics`
7. `## Official Documentation`
8. `---` separator + navigation link (always last)

**Nav format:** `**[← Previous](./NN-prev.md) | [↑ Back to Section](./topic-index.md) | [Next →](./NN-next.md)**`

where `topic-index.md` is the folder's named index file (e.g., `./database-objects.md`, `./advanced-tsql.md`)

- Part 1 files: end with only forward link to Part 2
- Part 2 files: full three-way nav

## README Standards

### Certification Index (`certification/dp-800-overview.md`)

Required: YAML frontmatter (`title`, `type: certification`, `aliases`, `tags`), How to Use This Guide (numbered steps including `final-review.md`), Exam Overview table, Domain Weights (Mermaid pie), Study Topics table with weights, Practice & Resources table (must include `Final Review` row), Study Progress Tracker (checkboxes).

### Topic Folder Index (`<topic-folder>/<topic-name>.md`)

Required: YAML frontmatter (`title`, `type: category`, `tags`, `status`), topic title with exam weight, `## Quick Recall` Mermaid mindmap (first section, before Topics Overview), Topics Overview (Mermaid flowchart), Section Contents table, Key Concepts, Related Resources, Back/Next navigation.

- `status` field values: `draft`, `in-progress`, `complete`
- Update `status` in each topic index as sections are completed — do not leave complete sections as `draft`
- `## Quick Recall` mindmap lists the 3–6 most testable facts per section — use `mindmap` diagram type

### Topic File Structure (Top of File)

Every topic file must open with this pattern, in order, before the first `##` content section:

1. YAML frontmatter
2. `# Title`
3. `## Overview` paragraph (1–3 sentences)
4. `> [!abstract]` callout — 2–4 bullet summary of what the file covers
5. `> [!tip] What the Exam Tests` callout — 2–4 bullets on specifically what the exam tests from this file
6. `---` separator
7. First `##` content section

### Cheat Sheet Structure

Each cheat sheet (`resources/cheat-sheets/`) ends with:

1. `## Gotchas & Traps` — 4–8 bullets on common errors and exam traps specific to the topic
2. `## Before the Exam, I Can…` — 5–8 unchecked checkboxes (`- [ ]`) the reader should be able to tick before taking the exam

## Exam Domain Mapping

- **Domain 1 — Design and develop (35–40%):** 01-database-objects, 02-programmability-objects, 03-advanced-tsql, 04-ai-assisted-tools
- **Domain 2 — Secure, optimize, deploy (35–40%):** 05-data-security-compliance, 06-performance-optimization, 07-cicd-database-projects, 08-azure-services-integration
- **Domain 3 — AI capabilities (25–30%):** 09-models-embeddings, 10-intelligent-search, 11-rag
