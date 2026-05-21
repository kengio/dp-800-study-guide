# Translating the DP-800 Study Guide

Translations live under `i18n/<locale>/` and mirror the English structure under `certification/`. The English content remains canonical — translations are valued additions, not replacements.

## Why a parallel `i18n/` tree

The same reason the English content lives under `certification/`: every reader gets a complete, self-contained study guide in their language without having to mentally re-resolve cross-links. A parallel tree also makes it easy to:

- See at a glance which sections have been translated (folders that exist) vs. not yet (folders that don't)
- Diff a translation against its English source by file path
- Let a translator fork, work on a single locale, and PR it back without touching English files

## Layout

```text
i18n/
├── README.md                        # locale index — updated when a new locale lands
└── <locale>/                        # BCP-47 locale tag (e.g., th, es, es-MX, ja, vi)
    ├── README.md                    # locale landing page — what's translated, by whom
    └── certification/
        ├── dp-800-overview.md       # cert index (highest priority)
        ├── 01-database-objects/
        │   ├── database-objects.md
        │   └── 01-tables-indexes.md
        ├── ...
        └── resources/
            ├── final-review.md      # 20-minute exam-morning scan (highest priority)
            ├── exam-tips.md
            ├── cheat-sheets/
            ├── mock-exam/
            ├── mock-exam-2/
            └── practice-questions/
```

A translation does **not** need to be complete to be useful. Even a single translated file — `certification/resources/final-review.md`, for example — is a real contribution. Each locale's `README.md` should track what's translated.

## Locale codes

Use [BCP 47](https://www.rfc-editor.org/info/bcp47) tags:

- Language only: `th` (Thai), `ja` (Japanese), `vi` (Vietnamese), `pt` (Portuguese)
- Language + region when meaningful: `pt-BR` (Brazilian Portuguese), `es-MX` (Mexican Spanish), `zh-Hans` (Simplified Chinese), `zh-Hant` (Traditional Chinese)

If you're not sure which variant to use, pick the broadest one (`pt` over `pt-BR`) and we can split later if a second variant arrives.

## Suggested priority order for a new locale

If you're starting from scratch, translate in this order — the earlier items give the biggest reader benefit for the least effort:

1. `certification/dp-800-overview.md` — the cert index
2. `certification/resources/final-review.md` — exam-morning scan
3. `certification/resources/exam-tips.md` — common traps + time budget
4. `certification/resources/cheat-sheets/` — all 6 quick-references
5. `certification/dp-800-domain-mapping` — section landing pages (`01-database-objects/database-objects.md`, etc.)
6. Highest-yield topic files — start with the AI domain (`09-models-embeddings/`, `10-intelligent-search/`, `11-rag/`) since it changes fastest
7. Mock exams (`certification/resources/mock-exam*/questions.md`)
8. Everything else

## Conventions for translated files

- **Keep the file path identical** to the English source. `i18n/th/certification/09-models-embeddings/01-external-models.md` mirrors `certification/09-models-embeddings/01-external-models.md`.
- **Translate prose but keep code blocks untranslated.** SQL keywords, function names, error messages, JSON field names — leave in English. If a code comment is in English, you may translate the comment but leave the code itself unchanged.
- **Translate the YAML frontmatter `title` field; leave `tags` and `type` as-is.** Tags are used for indexing and must stay stable across locales.
- **Internal links should point within the locale tree.** `[Vector search](./02-vector-search.md)` in a translated file should resolve to the translated sibling. If the sibling isn't translated yet, link directly to the English original: `[Vector search](../../../certification/10-intelligent-search/02-vector-search.md)` — and add a note (e.g., `*(English only)*`) so the reader isn't surprised.
- **External links (Microsoft Learn, etc.) stay as-is.** Microsoft auto-redirects `/en-us/` to the user's locale where translated docs exist; trying to hardcode `/th/` or `/ja/` URLs creates 404s when Microsoft hasn't translated that page.
- **Match the English structure section-for-section.** Don't merge or split sections; future blueprint refreshes will diff translated files against English, and a structural change makes that harder.
- **Mock-exam answer callouts** keep the `> [!success]- Answer` syntax and the bold answer letter. Translate the explanation prose; leave the answer letter and code in English.

## Currency

When the English source is refreshed (blueprint update, factual correction, new content), translations will drift. We don't block English updates on translation parity — but the translator (or the maintainer) should:

1. Note the drift in the locale's `README.md` ("Last sync with English: `<commit-sha>`")
2. PR a follow-up that re-syncs the changed files
3. If a translated file is significantly out of date, add a banner at the top:

```markdown
> [!warning] Translation may be out of date
> This file was translated from the English source at commit `abc1234`. The English version has changed since then — see [original](../../../certification/path/to/file.md) for the latest.
```

## Quality bar

- **Accuracy beats fluency.** If a Microsoft technical term has no good translation in your language, leave it in English (e.g., "RAG", "Always Encrypted", "DiskANN") rather than coining an obscure native term.
- **No machine-translated PRs without human review.** Auto-translation creates plausible-sounding but subtly-wrong content. If you use a machine translator as a draft tool, that's fine — but the PR must show the translator's edits and judgement.
- **One locale per PR.** Don't bundle translations across languages in a single PR; it slows review.

## How to start

1. Open an issue titled `i18n: <locale name>` so we can coordinate (avoids two people translating the same locale in parallel without knowing)
2. Fork the repo, create a branch like `i18n/<locale>` (e.g., `i18n/th`, `i18n/es-MX`)
3. Create `i18n/<locale>/README.md` with your name as the lead translator and a status table for what's translated
4. Translate at least one file, PR it
5. Iterate — subsequent PRs add more files

You'll be listed in [`CONTRIBUTORS.md`](./CONTRIBUTORS.md) with the locale label after your first translation PR lands.

## Questions

Open an issue using the **Factual correction** template (closest fit for "translation question") and tag the issue with `i18n`. The maintainer will reply.

---

**[← Back to repo root](./README.md)** | **[Contribution guide](./CONTRIBUTING.md)** | **[Contributors](./CONTRIBUTORS.md)**
