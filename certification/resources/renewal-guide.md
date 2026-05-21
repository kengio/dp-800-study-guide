---
title: "DP-800 Renewal Guide"
type: resource
tags:
  - dp-800
  - renewal
  - certification
---

# DP-800 Renewal Guide

> [!abstract]
>
> - Microsoft Certified: Developing AI-Enabled Database Solutions Associate **expires annually** — you renew with a **free, unproctored, open-book online assessment** on Microsoft Learn during your six-month renewal window
> - The renewal assessment is **shorter than the original exam** and focuses on **what's changed in the blueprint since you passed** — not the full skills-measured list
> - You can **retake as many times as you need** until you pass, as long as you finish before the certification expires
> - **Fundamentals certifications never expire** — only associate, expert, and specialty (DP-800 is associate, so it does expire)

> [!tip] What the renewal tests
>
> Microsoft says renewal assessments focus on **"recent technological and industry updates"** — i.e., the diff between the blueprint version current at your original exam and the blueprint as of your renewal attempt. Translating that to DP-800: if Microsoft promotes DiskANN or half-precision vectors from preview to GA, adds a new T-SQL function, or replaces an AI integration pattern, **that's what you study**.

---

## How renewal works

| What | Detail |
| :--- | :--- |
| **Validity** | 1 year from the date you earn (or last renew) the certification. Fundamentals (DP-900, AZ-900, etc.) are exempt and never expire. |
| **Renewal window** | The six-month period **before** your certification's expiration date. Microsoft emails you when you become eligible. |
| **Cost** | Free. |
| **Where** | Microsoft Learn, via your [certification profile](https://learn.microsoft.com/en-us/users/) → the "Renew" button next to your DP-800 credential. |
| **Format** | Online, **unproctored**, **open-book**. No camera, no proctor lockdown — Microsoft trusts the open-book format. |
| **Length** | Shorter than the original ~120-minute, 50-question exam. Expect a focused subset of questions aligned to the most recent blueprint changes. |
| **Retake policy** | Take it **as many times as you need** until you pass, as long as the final passing attempt lands before your expiration date. No 24-hour cooldown like the original exam. |
| **Pass mark** | Same 700/1000 scaled score as the original. |
| **Outcome** | Passing extends your certification **1 year from the current expiration date** (not from the day you pass), so you don't lose time by renewing early in the window. |
| **What if you don't renew** | The certification expires. You can no longer claim it on your transcript, and the only path back is **retaking the full DP-800 exam** at the current ($165 USD as of 2026) price. |

Source: [Microsoft Certification Renewal](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification) and [renewal FAQ](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification-faq).

---

## How to prepare

Because the renewal assessment focuses on **what's new**, the prep cycle is the inverse of the original exam:

1. **Note the blueprint date your original exam covered.** The official skills-measured page shows the current "Skills measured as of …" date at the top. Compare it to the version that was current when you sat the exam. (If you don't remember, your Microsoft Learn certificate PDF lists the exam date — the page at that time is in the [GitHub history of the study-guide markdown](https://github.com/MicrosoftDocs/learn-certs-pr/commits/live/learn-certs-pr/certifications/resources/study-guides/dp-800.md).)
2. **Read the "Change log" or "What's new" section** on the current DP-800 skills-measured page. Microsoft is generally good about flagging what changed.
3. **Cross-reference with this study guide's [`CHANGELOG.md`](../../CHANGELOG.md)** — the maintainer tracks blueprint refreshes, currency-policy updates, and the highest-leverage facts that moved. The most-recent entries are usually the most-likely renewal-assessment material.
4. **Re-read the [final-review file](./final-review.md)** for the current blueprint date. The "20XX Updates" section is the highest-yield digest.
5. **Skim only the topic files for the domains where the blueprint moved** — don't re-read everything. If only Domain 3 (AI capabilities) changed since you sat the exam, skip Domains 1 and 2.

### Specific things to watch between blueprint refreshes (DP-800)

The features below were "preview" as of the 2026-03-12 blueprint that the original exam tracked. When Microsoft promotes any of these to GA, expect them to appear on the renewal:

- **DiskANN** — currently public preview across SS2025, Azure SQL Database, Azure SQL Managed Instance, and SQL database in Microsoft Fabric. A GA announcement is the most-likely renewal question
- **Half-precision (`float16`) vectors** — currently preview. GA would mean the deployment story changes (storage halves at same dimension count; cap stays 1 998 dimensions)
- **`VECTOR_SEARCH`, `VECTOR_NORMALIZE`, `VECTORPROPERTY`** — these are public preview as of 2026-03-12. Only `VECTOR` and `VECTOR_DISTANCE` are GA. Watch for promotion
- **Microsoft Foundry as an embedding-maintenance method** — newly added to the 2026-03-12 blueprint. Renewal questions will likely probe its trigger model, mirroring relationship, and contrast vs CES/CDC
- **MCP** (Model Context Protocol) endpoints — relatively new in the 2026 blueprint. Watch for additional endpoint types, security postures, or new server-side patterns

### What renewal does *not* re-test (typically)

- T-SQL syntax foundations (CTEs, window functions, JSON functions). Once on the blueprint, these stay stable.
- Encryption fundamentals (Always Encrypted DETERMINISTIC vs RANDOMIZED + BIN2). Stable since SQL Server 2016.
- Long-standing isolation level + concurrency behavior (RCSI/SI semantics, blocking, deadlocks).
- SQL Database Projects core flow (dacpac, SDK-style, schema drift).

If you nailed these on the original exam, don't burn time re-drilling them for the renewal.

---

## Renewal cadence + workflow

The optimal cadence:

```text
Original exam pass             →  certification valid 1 year
+10 to +12 months              →  renewal window opens (Microsoft emails you)
+11 months                     →  read the current skills-measured "Change log"
+11 months + 1 day             →  re-skim the corresponding final-review section
+11 months + 2 days            →  take the renewal assessment
+11 months + 2 days (if pass)  →  certification extended +1 year from original expiration
```

If you renew at the very start of the window (month 10), you only "gain" 2 months — but you also leave 4 months of buffer to retake if you fail. **Renew earlier in the window unless you have a strong reason to delay.**

---

## If you fail or miss the window

- **Fail attempts** don't have a cooldown — re-prep and try again within the same window.
- **Missing the window** means the certification expires; the only path back is **retaking the full DP-800 exam** at the current price. There is no extended grace period and no "lapsed but recoverable" status — once it's expired, your transcript no longer shows the cert as active.
- If you've moved to a related role, consider whether **another active certification** (e.g., [DP-700 Fabric Data Engineer](./companion-exams.md) or AI-102 successor) better represents your current work before reactivating DP-800.

---

## Quick checklist — the morning of your renewal

- [ ] Open [`final-review.md`](./final-review.md) and re-read the "20XX Updates" section
- [ ] Open the current [DP-800 skills-measured page](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800) and scan its **Change log** table at the bottom
- [ ] Have the [cheat sheets](./cheat-sheets/cheat-sheets.md) open in another tab — it's open book, use them
- [ ] Note the time; the assessment is shorter than the original exam but still time-bounded
- [ ] Sign in to [your Microsoft Learn profile](https://aka.ms/ManageCerts) and click **Renew** next to DP-800
- [ ] Pass. Your certification is extended +1 year from the existing expiration date

---

## Use Cases

- **DP-800 holders renewing for the first time** — most readers
- **Hiring managers** verifying that a candidate's DP-800 credential is current (renewals show on the Microsoft Learn transcript)
- **Forks of this study guide** maintained for a different blueprint year — the workflow generalises; only the "specific things to watch" section is DP-800-specific

## Exam Tips

> [!tip] Exam Tips for renewal
>
> - **Treat it as open-book, not no-effort.** You can use Microsoft Learn while taking it, but every minute you spend searching is a minute lost. Pre-read the change log first.
> - **Don't binge the whole study guide** the night before — the renewal is a diff, not a re-cert. Time spent re-reading Domain 1 fundamentals is time wasted.
> - **Renew early in your window.** If you fail in month 11 with 30 days left, you have a stress sprint. If you fail in month 7 with 5 months left, you have plenty of time.
> - **If the blueprint moved a feature from preview → GA**, expect at least one question on the GA-specific behavior (deployment surface, supported regions, new syntax).

## Related Topics

- [Final Review](./final-review.md) — 20-minute exam-morning scan, updated when the blueprint changes
- [Exam Tips](./exam-tips.md) — strategies and common traps from the original exam (some still applicable)
- [Companion Exams](./companion-exams.md) — DP-700, AI-102, and how they relate
- [Official Links](./official-links.md) — Microsoft Learn entry points

## Official Documentation

- [Microsoft Certification Renewal](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification) — overview page
- [Certification Renewal FAQ](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification-faq) — edge cases, accommodations, what-ifs
- [DP-800 Skills Measured](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-800) — current blueprint, with change log
- [Manage Your Certifications](https://aka.ms/ManageCerts) — direct link to the renewal dashboard

---

**[← Back to resources](./exam-resources.md)** | **[↑ Back to overview](../dp-800-overview.md)**
