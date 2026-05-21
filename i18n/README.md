---
title: "DP-800 Study Guide — Translations"
type: i18n-index
tags:
  - dp-800
  - i18n
  - translations
---

# Translations

Community translations of the DP-800 study guide. The English content under `certification/` is canonical; each locale's tree mirrors it.

See [`TRANSLATING.md`](../TRANSLATING.md) for the conventions, suggested priority order, and how to start a new locale.

## Available locales

<!-- Locales land here as they are PR'd. -->

*No locales yet — be the first to translate. Open an issue titled `i18n: <locale name>` to coordinate.*

## Locale structure

Each locale is a self-contained mirror of the English `certification/` tree:

```text
i18n/<locale>/
├── README.md             # locale landing — what's translated, by whom, last sync
└── certification/        # mirror of the top-level certification/ tree
    └── ...               # only the files actually translated need to exist
```

A locale does not need to be complete to be merged. A single translated file is a real contribution.

## Suggested priority order

When starting a new locale, translate in this order for the biggest reader benefit:

1. `certification/dp-800-overview.md`
2. `certification/resources/final-review.md`
3. `certification/resources/exam-tips.md`
4. `certification/resources/cheat-sheets/`
5. Section landing pages (`certification/0N-*/`)
6. AI domain topic files (`09-models-embeddings/`, `10-intelligent-search/`, `11-rag/`)
7. Mock exams + practice questions
8. Remaining topic files

See [`TRANSLATING.md`](../TRANSLATING.md#suggested-priority-order-for-a-new-locale) for the full rationale.

## Currency

When the English source is updated, translations may drift. Each locale's `README.md` should record `Last sync with English: <commit-sha>` so readers can spot stale content and translators can plan re-sync PRs.

---

**[← Back to repo root](../README.md)** | **[Translation guide](../TRANSLATING.md)** | **[Contributors](../CONTRIBUTORS.md)**
