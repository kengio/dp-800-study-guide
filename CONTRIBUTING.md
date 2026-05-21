# Contributing to the DP-800 Study Guide

Thanks for being here. This guide exists because someone open-sourced their exam notes — every PR you send keeps it useful for the next reader.

## Ground rules

- **The official Microsoft skills-measured page is the source of truth.** If a claim in this guide conflicts with the current [DP-800 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800), Microsoft wins. Always link the source for factual changes.
- **Be kind in reviews and issues.** This is a study aid for people about to take a stressful exam.
- **Small PRs are easier to merge than big ones.** If you're rewriting a whole section, open an issue first.

## What kinds of contributions are welcome

| Type | How to contribute |
| :--- | :--- |
| **Typo / link rot fix** | Open a PR directly. No issue needed. |
| **Factual correction** | Open a PR. Cite the Microsoft Learn page in the description. |
| **New practice question** | Open a PR adding it under the matching domain in `certification/resources/practice-questions/` (or, for the timed-exam-feel version, in `certification/resources/mock-exam/questions.md` / `mock-exam-2/questions.md`). Follow the existing format (see [conventions](#conventions) below). The [live practice quiz](https://kengio.github.io/dp-800-study-guide/) re-deploys automatically on merge — see [`practice/format.md`](./practice/format.md) for the exact markdown contract the converter expects. |
| **Topic-file expansion** | Open an issue first to align scope, then PR. |
| **New cheat sheet or worked example** | Open an issue first — these are higher-effort additions and we want to keep the set focused. |
| **Blueprint refresh** | When Microsoft updates the skills-measured page, follow the [Currency Policy](#currency-policy) below. |
| **Translation** | Read [`TRANSLATING.md`](./TRANSLATING.md) for the layout (`i18n/<locale>/` mirror), priority order, and conventions. Open an issue titled `i18n: <locale name>` first to coordinate. |

## How to contribute

1. **Fork** the repo and clone your fork
2. **Create a branch** off `main` — name it descriptively (e.g., `fix/q42-json-path`, `feat/case-study-mock-1`)
3. **Make the change.** Run `markdownlint` on any file you touch (see [conventions](#conventions))
4. **Commit** with a clear message. We use loose conventional-commit prefixes: `docs:`, `fix:`, `feat:`, `chore:`, `review(roundN):` for review passes
5. **Open a PR** against `main`. The PR template will prompt you for the relevant details
6. **Respond to review feedback** — most PRs land within a few days

## Currency Policy

When Microsoft updates the official skills-measured list:

- Update the **"What's New for the YYYY Exam"** callout at the top of `certification/dp-800-overview.md`
- Update the **"YYYY Updates"** section in `certification/resources/final-review.md`
- Update the **blueprint-date badge** in `README.md`
- Mark new questions targeting the updated skills with a `*(YYYY update)*` suffix in the question heading
- Move features from "Preview" to "GA" labelling as their status changes — verify against the [VECTOR_SEARCH docs](https://learn.microsoft.com/en-us/sql/t-sql/functions/vector-search-transact-sql) and the [Azure SQL Dev Corner blog](https://devblogs.microsoft.com/azure-sql/)
- Add an entry to [`CHANGELOG.md`](./CHANGELOG.md) describing the refresh

## Conventions

All conventions are documented in [`CLAUDE.md`](./CLAUDE.md). The highest-impact ones:

### File layout

- Topic files live under `certification/NN-topic-name/NN-sub-topic.md`
- Code examples are `.md` files under `certification/resources/code-examples/tsql/` — never `.sql`
- Topic index files are named after the folder (e.g., `database-objects.md`), not `README.md`

### File structure

Every topic file opens with this pattern:

1. YAML frontmatter
2. `# Title`
3. `## Overview` (1–3 sentences)
4. `> [!abstract]` callout (2–4 bullets)
5. `> [!tip] What the Exam Tests` callout (2–4 bullets)
6. `---` separator
7. First `##` content section

And ends with these terminal sections in this exact order:

1. `## Use Cases`
2. `## Common Issues & Errors`
3. `## Best Practices` *(optional)*
4. `## Exam Tips`
5. `## Key Takeaways`
6. `## Related Topics`
7. `## Official Documentation`
8. `---` separator + navigation link

### Practice questions

- A/B/C/D on separate lines (no bullets), two trailing spaces for line breaks
- Answer in an Obsidian foldable `> [!success]- Answer` callout
- Explanation teaches the **why**, not just confirms the letter
- Mark questions targeting the latest blueprint refresh with `*(YYYY update)*` in the heading
- Per-domain target: 15–20 questions; difficulty mix: ~30 % Easy, ~50 % Medium, ~20 % Hard

### Callouts

Use Obsidian-flavoured callouts (also render on GitHub). Standard types:

| Callout | Usage |
| :--- | :--- |
| `> [!info]` | Section intros, neutral context |
| `> [!tip] What the Exam Tests` | Top-of-file orientation |
| `> [!tip] Exam Tips` | Exam advice in the terminal Exam Tips section |
| `> [!warning] Common Mistake` | Gotchas |
| `> [!note]` | Extra detail, caveats |
| `> [!success]- Answer` | Foldable practice-question answers |
| `> [!abstract]` | Top-of-file summary |

### Diagrams

- Architecture and flow → Mermaid (`sequenceDiagram`, `flowchart`, `graph`)
- Directory trees → ASCII text (not Mermaid)
- Both GitHub and Obsidian render Mermaid natively

### Links

- Link to **files**, not folders: `path/to/database-objects.md`, not `path/to/`
- Always use `./filename.md` for same-folder links — bare names resolve ambiguously in Obsidian
- Verify target files exist after edits

### Markdown

- Run `markdownlint` on every modified file
- Blank lines before/after headings (MD022)
- Language tags on all code blocks (`sql`, `tsql`, `json`, `yaml`, `bash`)

## What to do if you find a bug in the practice questions

This is the most exam-impactful category. Please:

1. **Cite the Microsoft Learn page** that supports your correction
2. **Note any cheat-sheet / topic-file / mock-exam locations** that contain the same error (we want them all fixed in one PR)
3. **Re-frame the question** if possible — sometimes a wrong answer is salvageable by reframing the scenario, which preserves the question variety

## Reviews

- One or two-line PRs (typos, link fixes) typically merge same-day
- Larger PRs receive at least one review
- We optimise for **factual accuracy** and **exam relevance** over stylistic preference

## Code of conduct

Be kind, assume good intent, focus on the work. No tolerance for harassment of any kind.

## License

By contributing, you agree your contribution is released under the [MIT License](./LICENSE) that covers the rest of the project.

---

If something is unclear about contributing, [open an issue](https://github.com/kengio/dp-800-study-guide/issues/new) and we'll iterate on this guide.
