---
title: Practice Question Format Spec
type: reference
tags:
  - dp-800
  - practice
  - format-spec
status: published
---

# Practice Question Format Spec

The exact markdown contract that [`build.py`](./build.py) parses. Stick to this and the converter produces clean JSON; deviate and you'll see warnings or skipped questions.

## File-level structure

Source markdown files live at:

```text
certification/resources/practice-questions/<NN>-<domain>.md   # practice bank
certification/resources/mock-exam/questions.md                # Mock Exam 1
certification/resources/mock-exam-2/questions.md              # Mock Exam 2
```

For the practice bank, the filename (with the leading numeric prefix stripped) becomes the JSON `domain.id`; the H1 (with the literal "Practice Questions: " prefix stripped) becomes the `domain.name`.

For mock exams, the file is a single bank, with intra-file HTML comments demarcating domains:

```html
<!-- DOMAIN 1: Design and Develop (~17 questions) -->
<!-- DOMAIN 2: Secure, Optimize, Deploy (~17 questions) -->
<!-- DOMAIN 3: AI Capabilities (~11 questions) -->
## Case Study: <name> *(5 linked questions, ~10 minutes)*
```

Each file contains a YAML frontmatter block, an H1 title, and a sequence of `## Question N: …` blocks separated by `---` horizontal rules. The case-study sub-questions inside mock exams use `### Question N:` (H3) instead.

```markdown
---
title: "Practice Questions: Design and Develop Database Solutions"
type: practice-questions
tags: [dp-800, practice-questions, design-develop]
---

# Practice Questions: Design and Develop Database Solutions

## Question 1: Brief Title

**Question** *(Easy|Medium|Hard)*:

Question stem text. Can span multiple lines. Markdown inline formatting (`code`, **bold**) is fine.

A. First choice
B. Second choice
C. Third choice
D. Fourth choice

> [!success]- Answer
> **B. Second choice**
>
> Short answer paragraph (typically restates the correct choice in prose).
>
> Explanation paragraph(s). Markdown inline formatting works here too.

---

## Question 2: …
```

## Parser rules

- **Question boundary**: H2 or H3 heading matching `## Question <number>: <title>` or `### Question <number>: <title>`. Sub-decimals (`## Question 5.3:`) are accepted but the JSON `id` uses only the integer prefix.
- **Difficulty**: required. Three accepted formats:
  - **Format A** (practice bank): `**Question** *(Medium)*:` on the line that introduces the stem
  - **Format B**: `## Question 5 *(Medium)*: Title`
  - **Format C** (mock exams): `## Question 5: Title *(Medium)*`
  All three reduce to lowercase `easy|medium|hard` in JSON.
- **Stem**: the text after the difficulty marker up to the first line starting with `A.` (or `A)`). Multi-line is fine.
- **Choices**: exactly four lines starting `A.`, `B.`, `C.`, `D.` (or `A)`, `B)`, `C)`, `D)` — both punctuations are tolerated). Trailing whitespace tolerated.
- **Answer callout**: starts with `> [!success]-` (with or without the literal "Answer" word). Content is blockquote text until the next non-blockquote line or `---`.
- **Correct answer**: the first `**<letter>. <full choice text>**` or `**Correct Answer: <letter>**` inside the callout. Case-insensitive.
- **Short answer**: the first paragraph (split by blank line) inside the callout *after* the correct-answer line.
- **Explanation**: every subsequent paragraph inside the callout, joined with `\n\n`.
- **Mock-exam domain**: each question inherits the domain from the most recent `<!-- DOMAIN N: <name> (...) -->` HTML comment above it. Case-study sub-questions inherit the synthetic `case-study` domain from the `## Case Study: …` H2.

## Things that cause a question to be skipped (with a warning)

| Cause | Fix |
| :--- | :--- |
| Missing difficulty marker | Add `**Question** *(Easy\|Medium\|Hard)*:` (Format A) or append `*(Medium)*` to the heading (Format C) |
| Fewer than 4 `A.`/`B.`/`C.`/`D.` choice lines | Ensure each choice is on its own line, starting with the letter + `.` |
| Missing `> [!success]-` callout | Wrap the answer in the foldable callout |
| Missing `**<letter>. …**` or `**Correct Answer: X**` inside the callout | Add this as the first line of the callout |

## JSON output schema

The converter writes one JSON file per bank at `practice/data/<bank>.json` with this shape:

```jsonc
{
  "cert": "dp-800",
  "certTitle": "DP-800: Developing AI-Enabled Database Solutions",
  "blueprintVersion": "2026-03-12",
  "generated": "2026-05-22",
  "domains": [
    {
      "id": "design-develop",
      "name": "Design and Develop Database Solutions",
      "sourceFile": "certification/resources/practice-questions/01-design-develop.md",
      "questionCount": 18
    }
    // …one entry per domain file
  ],
  "questions": [
    {
      "id": "practice-questions-01-design-develop-q001",
      "domain": "design-develop",
      "title": "Column Store Index Type",
      "difficulty": "medium",
      "question": "A data engineer is creating a table in Azure SQL…",
      "choices": {
        "A": "A clustered B-tree index on the date column",
        "B": "A non-clustered B-tree index on each aggregation column",
        "C": "A clustered columnstore index",
        "D": "A non-clustered columnstore index on the aggregation columns"
      },
      "correctAnswer": "C",
      "shortAnswer": "A clustered columnstore index is optimal for tables used exclusively for analytics.",
      "explanation": "A **clustered columnstore index (CCI)** is optimal for tables used exclusively for analytics…"
    }
    // …one entry per question
  ]
}
```

For mock-exam banks, the output adds `"kind": "mock"` and `"sourceCert": "dp-800"` at the top level.

### Schema rules

- **`id`** must be stable across rebuilds — the converter derives it from `<parent-folder>-<filename-stem>-q<zero-padded-number>` (or `<bank-id>-q<num>` for mocks) so renaming a markdown file or renumbering questions inside it will break learners' localStorage progress for the affected questions. Don't renumber unless intentional.
- **`difficulty`** is one of `easy` / `medium` / `hard` (lowercase).
- **`correctAnswer`** is one of `A` / `B` / `C` / `D`.
- **`choices`** must have all four keys A-D.

## Running the converter

```bash
# Build all banks
python3 practice/build.py

# Build only the practice bank
python3 practice/build.py --kind practice

# Build only mock exams
python3 practice/build.py --kind mock

# Parse-only, no JSON written; non-zero exit if any parse error
python3 practice/build.py --check
```

The converter is Python 3.9+ standard library only — no `pip install` needed.

## Markdown features that survive the conversion

When rendered in the quiz UI:

| Source | UI |
| :--- | :--- |
| `` `inline code` `` | `<code>` element |
| `**bold**` | `<strong>` element |
| Blank line | paragraph break |
| Single `\n` | line break within paragraph |

Anything else (lists, tables, links, images, headings) is rendered as literal text. Keep question content text-and-inline-code-only.

## Why the markdown-source / JSON-build split?

Same reasoning as the [Anki deck system](../certification/resources/anki/anki-deck.md):

- Markdown source stays human-editable and version-controlled
- JSON is what the static web app actually consumes
- The converter is the only seam — if the markdown format changes, the converter changes; the JSON schema doesn't leak into the source files

This means *correcting an answer* or *adding a new question* is a one-file edit to the relevant `.md` file. Then re-run `build.py` and commit the regenerated JSON.

## Why is JSON committed and not built in CI?

It's a static site — GitHub Pages serves `practice/data/*.json` directly. If the JSON weren't committed, GitHub Pages would have no way to produce it (we'd need a CI step + commit-back, which is overkill for a static app). The build is cheap (sub-second) and idempotent, so committing the output keeps the workflow simple.

The CI markdownlint + lychee checks ensure the source markdown stays well-formed; correctness of `build.py` itself is verified by running `python3 practice/build.py --check` before opening a PR.

---

**[← Back to practice index](./README.md)**
