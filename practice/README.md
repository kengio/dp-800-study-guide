---
title: Adaptive Practice Questions
type: index
tags:
  - dp-800
  - practice
  - quiz
  - adaptive
status: published
---

# Adaptive Practice Questions

A browser-based quiz for the DP-800 practice + mock-exam question files in this repo. Tracks your attempts in `localStorage` and surfaces questions you've gotten wrong recently (adaptive mode), without sending anything to a server.

## What this is

- **A static web page**: `index.html` + `app.js` + `styles.css` + `data/*.json` — no backend, no build step beyond the JSON converter.
- **Adaptive**: by default the question selector weights toward never-attempted + recently-wrong questions, so re-running the quiz quickly converges on what you don't yet know.
- **Per-bank localStorage state**: your progress for each bank (practice + Mock 1 + Mock 2) is kept independently. No cross-device sync — `Export progress (JSON)` downloads it if you want to back it up or move it.
- **Source: the existing practice + mock-exam markdown files** — no parallel content to maintain. When the markdown changes, re-run the converter and the bank refreshes.

## Available banks

**3 banks · 160 questions total**

| Bank | Source | Q |
| :--- | :--- | :---: |
| Practice questions | `certification/resources/practice-questions/` | 60 |
| Mock Exam 1 | `certification/resources/mock-exam/questions.md` | 50 |
| Mock Exam 2 | `certification/resources/mock-exam-2/questions.md` | 50 |

The practice bank covers all three exam domains in a single drillable set. The two mock exams mirror the full-length 50-question / 70-minute format with a 5-question case-study block at the end of each.

## How to run

### Live version

**[https://kengio.github.io/dp-800-study-guide/](https://kengio.github.io/dp-800-study-guide/)**

Deployed automatically from `main` whenever anything in `practice/` or the source practice / mock-exam markdown changes. No install, no clone — open the link and start drilling.

### Local

```bash
# 1. Generate / refresh the JSON banks (only needed when markdown changes)
python3 practice/build.py

# 2. Serve the practice/ folder. The fetch calls require an HTTP origin,
#    not file://, so use any static server:
python3 -m http.server 8080 --directory practice
# Then open http://localhost:8080/
```

> [!tip]
> Opening `practice/index.html` directly via `file://` won't work because browsers block `fetch()` for local files. Always use a static server (or GitHub Pages).

### Deploy (for fork maintainers)

The deploy is driven by [`../.github/workflows/deploy-practice.yml`](../.github/workflows/deploy-practice.yml). It runs on every push to `main` that touches any of:

- `practice/**` — the quiz app itself
- `certification/resources/practice-questions/**` — source markdown for the practice bank
- `certification/resources/mock-exam/**` or `mock-exam-2/**` — source markdown for the mock banks
- `.github/workflows/deploy-practice.yml`

The workflow:

1. Checks out the repo
2. **Re-runs `python3 practice/build.py`** so `practice/data/*.json` is rebuilt fresh from current markdown — even if the author forgot to regenerate locally
3. Uploads `practice/` as a Pages artifact (with `.nojekyll` so HTML/JS pass through unmodified)
4. Deploys via `actions/deploy-pages@v4`

This means: edit a question in any source markdown file, commit, push to `main`, and the live site updates within ~1 minute. No need to run `build.py` locally before pushing — the committed JSON is just a convenience for local dev / quick PR review, not the source of truth at deploy time.

**First-time setup** (only needed once per fork):

1. Repo → **Settings** → **Pages**
2. **Build and deployment** → **Source: GitHub Actions**
3. Push any change under `practice/` to `main` (or trigger the workflow manually via Actions → "Deploy practice quiz to GitHub Pages" → Run workflow)
4. After ~1 minute, the live URL is shown on the workflow run page and in repo Settings → Pages

The published site lives at `https://<user>.github.io/<repo>/` (no `/practice` suffix because the workflow uploads `practice/` as the artifact root).

## Modes

| Mode | When to use |
| :--- | :--- |
| **Adaptive** (default) | Day-to-day study. The selector down-weights questions you've recently answered correctly and up-weights ones you've recently missed or never attempted. |
| **Random** | Mock-exam vibe — uniform sampling across the bank, ignoring history. Good for occasional gauges of where you stand. |
| **Sequential** | Walk through every question in source-file order. Useful when prepping a specific domain end-to-end. |

You can also filter by **Domain** and **Difficulty** in the Settings panel.

## Adaptive selector — exactly what it does

For each question in the filtered pool, the weight is:

```text
never attempted                            → 10  (highest)
last attempt CORRECT,   N days ago         → min(5, 0.5 + N * 0.3)
last attempt INCORRECT, N days ago         → max(3, 8 - N * 0.3)
```

So:

- A question you've never seen has weight `10` — it'll surface fast.
- A question you just got wrong has weight `8` — heavy priority, but decays over time so it doesn't dominate forever.
- A question you just got right has weight `0.8` — almost ignored, but rises as days pass so you do re-review eventually.

A weighted random pick chooses the next question. After a full pass through the filtered pool, the "seen this session" set clears so you don't get stuck on the same dozen questions.

## Privacy

- All state lives in your browser's `localStorage` under keys like `dp800-practice-dp-800`.
- Nothing is sent to a server — there's no server.
- Clearing browser storage or using a different browser / device wipes progress. The **Export progress (JSON)** button lets you back it up.
- Importing progress isn't built yet; if you need it, open an issue.

## Files in this folder

| File | Purpose |
| :--- | :--- |
| `index.html` | App skeleton, branded header, favicon |
| `app.js` | Quiz logic, adaptive selector, localStorage, stats, theme cycle |
| `styles.css` | Minimal styling with theme variables (auto / light / dark) |
| `favicon.svg` | Browser tab icon (also displayed in the page header) |
| `build.py` | Markdown → JSON converter (Python 3.9+ stdlib only) |
| `data/<bank>.json` | Generated question banks (committed so the static page works) |
| `format.md` | Markdown source format spec that `build.py` parses |
| `README.md` | This file |

## Theme

The page ships with three theme states: **auto** (follows your OS dark-mode preference), **light**, and **dark**. The button in the top-right of the header cycles through them. Your choice is saved in `localStorage` and applied immediately on every visit.

## Adding more questions

The parser supports three question heading formats, all with the same body shape (choices + answer callout). See [`format.md`](./format.md) for the exact spec.

To add new questions:

1. Edit the relevant markdown file (`certification/resources/practice-questions/*.md` or one of the mock-exam `questions.md` files) using the existing format with all four `A. B. C. D.` choices and a `**<letter>. <full choice text>**` line inside the `> [!success]-` callout.
2. Run `python3 practice/build.py` and check the parsed count.
3. Commit both the markdown change and the regenerated JSON.

A handful of questions where a choice contains a multi-line code block may be skipped (the parser sees the bare `A.` / `C.` line with no inline content). If that affects a question, restructure the choice to inline the code or move the code block into the answer explanation.

## Contributing

PRs welcome for: UI improvements, additional adaptive strategies (e.g., SuperMemo-style intervals), accessibility fixes, mobile polish, server-sync of progress (optional, requires a backend).

## Caveats

- This isn't an official Microsoft practice exam. It's static study material derived from the markdown files in this repo. Quality matches the quality of those files.
- The adaptive selector is a simple weighted-random heuristic, not a full spaced-repetition algorithm like SM-2 or FSRS. It's good enough for cert prep; if you want SM-2-level scheduling, use Anki (see [`../certification/resources/anki/anki-deck.md`](../certification/resources/anki/anki-deck.md)).
- The 60 practice questions live alongside, not inside, the 100 mock-exam questions. The mocks remain the canonical end-to-end exam simulation; this practice app is for between-mock drilling.

---

**[← Back to repo root](../README.md)** | **[Format spec →](./format.md)**
