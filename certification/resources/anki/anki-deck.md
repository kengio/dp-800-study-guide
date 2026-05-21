---
title: DP-800 Anki Deck
type: resource
tags: [dp-800, anki, spaced-repetition]
---

# DP-800 Anki Deck

A starter spaced-repetition deck generated from the six DP-800 cheat sheets. Use it to drill the highest-leverage facts — DMV names, masking functions, distance metrics, syntax keywords — that the exam expects you to recall verbatim.

> [!abstract] Quick Reference
>
> - 130 cards across six cheat-sheet topics: T-SQL core, JSON, security, performance DMVs, vector/AI, and Azure SQL config
> - Distributed as `dp-800.tsv` (tab-separated Front/Back/Tags) for one-shot import into Anki
> - Every card is tagged `dp-800` plus a topic tag and zero or more sub-topic tags for filtered study

> [!tip] What the Exam Tests
>
> - DP-800 questions hinge on recall of specific syntax (e.g., `CREATE VECTOR INDEX ... TYPE = 'diskann'`), error codes (Msg 42274), and threshold numbers (REORGANIZE 10-30%, REBUILD >30%)
> - Spaced repetition is the most efficient way to lock in this style of factual surface area
> - Use the deck in parallel with cheat-sheet review — drill recall, then revisit the cheat sheet for context when a card is wrong

---

## Import instructions

1. Open Anki desktop. Switch to the deck you want to import into (or create a new "DP-800" deck).
2. Choose **File → Import…** and select `dp-800.tsv`.
3. Set the import options:
   - **Field separator**: Tab
   - **Allow HTML in fields**: off
   - **Field mapping**: column 1 → Front, column 2 → Back, column 3 → Tags
   - **Type**: Basic note type (or any 2-field type — Anki ignores extra fields)
4. Click **Import** and confirm. Anki reports the number of new cards added.
5. Optional: use the tag filter (e.g., `tag:vector-ai`) to drill one cheat sheet at a time.

---

## Card breakdown

| Topic | Source | Card count | Tags column |
| :--- | :--- | ---: | :--- |
| T-SQL Core Commands | [tsql-core-commands.md](../cheat-sheets/tsql-core-commands.md) | 20 | `dp-800 tsql-core …` |
| JSON Functions | [json-functions-quick-ref.md](../cheat-sheets/json-functions-quick-ref.md) | 20 | `dp-800 json …` |
| Security | [security-quick-ref.md](../cheat-sheets/security-quick-ref.md) | 20 | `dp-800 security …` |
| Performance & DMVs | [performance-dmvs-quick-ref.md](../cheat-sheets/performance-dmvs-quick-ref.md) | 21 | `dp-800 performance …` |
| Vector & AI | [vector-ai-quick-ref.md](../cheat-sheets/vector-ai-quick-ref.md) | 24 | `dp-800 vector-ai …` |
| Azure SQL Config | [azure-sql-config-quick-ref.md](../cheat-sheets/azure-sql-config-quick-ref.md) | 25 | `dp-800 azure-sql-config …` |
| **Total** |  | **130** |  |

Sub-topic tags include `encryption`, `rls`, `dmv`, `waits`, `query-store`, `cdc`, `diskann`, `embeddings`, `rag`, `dab`, `sqlpackage`, and others. Filter with `tag:dp-800 tag:diskann` to drill a single concept.

---

## Maintenance

The deck mirrors facts already documented in the six cheat sheets — every card's back is verbatim or near-verbatim from the source. If a cheat sheet is updated (e.g., a metric range changes, a new mask function is added, a Microsoft preview feature graduates to GA), the corresponding rows in `dp-800.tsv` should be reviewed and edited by hand. There is no automation script — the deck is intentionally simple to keep the contribution surface small.

When updating, prefer editing existing rows over inserting new ones, so anyone who has already imported the deck does not get duplicates. If you do add new rows, append them at the end of the file and call out the addition in `CHANGELOG.md`.

---

## Related Topics

- [T-SQL Core Commands](../cheat-sheets/tsql-core-commands.md)
- [JSON Functions](../cheat-sheets/json-functions-quick-ref.md)
- [Security](../cheat-sheets/security-quick-ref.md)
- [Performance & DMVs](../cheat-sheets/performance-dmvs-quick-ref.md)
- [Vector & AI](../cheat-sheets/vector-ai-quick-ref.md)
- [Azure SQL Config](../cheat-sheets/azure-sql-config-quick-ref.md)
- [Cheat Sheets Index](../cheat-sheets/cheat-sheets.md)

## Official Documentation

- DP-800 skills measured: <https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800>

---

**[↑ Back to resources](../../dp-800-overview.md)**
