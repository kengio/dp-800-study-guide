#!/usr/bin/env python3
"""Convert DP-800 practice-question + mock-exam markdown into adaptive-practice JSON banks.

Walks `certification/resources/practice-questions/*.md` for the practice bank,
and `certification/resources/mock-exam/questions.md` plus
`certification/resources/mock-exam-2/questions.md` for the two mock banks, and
emits three JSON files under `practice/data/` for the static practice frontend
to load.

Source markdown format (per question):

    ## Question 5: Title

    **Question** *(Easy|Medium|Hard)*:

    <question stem, possibly multi-line>

    A. <choice>
    B. <choice>
    C. <choice>
    D. <choice>

    > [!success]- Answer
    > **B. <full choice text>**
    >
    > <short answer paragraph>
    >
    > <explanation paragraph(s)>

    ---

Case-study questions inside mock exams use H3 (`### Question 46:`) and the
same body shape. The parser handles both H2 and H3.

Usage:
    python3 practice/build.py                       # build all banks
    python3 practice/build.py --kind practice       # practice bank only
    python3 practice/build.py --kind mock           # both mock banks only
    python3 practice/build.py --check               # parse-only, no JSON written

Dependencies: Python 3.9+ standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRACTICE_DIR = ROOT / "practice"
DATA_DIR = PRACTICE_DIR / "data"
CERT_DIR = ROOT / "certification"

CERT_ID = "dp-800"
CERT_TITLE = "DP-800: Developing AI-Enabled Database Solutions"
BLUEPRINT_VERSION = "2026-03-12"

# Three heading formats supported (same shape as the upstream databricks parser):
#   Format A: `## Question 5: Title`               (difficulty in body: `**Question** *(...)*:`)
#   Format B: `## Question 5 *(Medium)*: Title`    (difficulty between number and colon)
#   Format C: `## Question 5: Title *(Medium)*`    (difficulty appended after title)
# Case-study questions use `###` instead of `##` but otherwise follow Format C.
H_QUESTION_RE = re.compile(r"^(#{2,3}) Question (\d+)(?:\.\d+)?(.*)$")
HEADING_DIFFICULTY_RE = re.compile(r"\*\(\s*(Easy|Medium|Hard)\s*\)\*", re.IGNORECASE)
BODY_DIFFICULTY_RE = re.compile(
    r"\*\*Question\*\*\s*\*\((Easy|Medium|Hard)\)\*:\s*(.+)", re.DOTALL | re.IGNORECASE
)
BODY_QUESTION_PREFIX_RE = re.compile(r"\*\*Question\*\*:\s*(.+)", re.DOTALL)
# DP-800 uses `A.` choices (the official CLAUDE.md convention) but tolerate `A)` too.
CHOICE_RE = re.compile(r"^([A-D])[.)]\s*(.+?)\s*$")
ANSWER_CALLOUT_RE = re.compile(r"^>\s*\[!success\]-?\s*(?:Answer)?\s*$", re.IGNORECASE)
# Correct-answer markers seen in DP-800 mock + practice files:
#   **B. Always Encrypted ...**                    (canonical DP-800 form)
#   **Correct Answer: B**                          (databricks-style; tolerated)
#   **Correct Answer:** B
CORRECT_ANSWER_RE = re.compile(
    r"\*\*(?:Correct Answer:?\s*\*?\*?\s*)?([A-D])[.):\s]", re.IGNORECASE
)
# Mock-exam domain demarcation: HTML comment, e.g.
#   <!-- DOMAIN 1: Design and Develop (~17 questions) -->
DOMAIN_COMMENT_RE = re.compile(
    r"^<!--\s*DOMAIN\s+\d+:\s*(.+?)\s*(?:\(.*?\))?\s*-->", re.IGNORECASE
)
# Case-study H2 in mock exams: `## Case Study: Contoso HR Migration *(5 linked questions, ~10 minutes)*`
CASE_STUDY_H2_RE = re.compile(r"^## Case Study:\s*(.+?)\s*\*\(.*?\)\*\s*$", re.IGNORECASE)
# Lightweight Q-heading detector for the mock pre-scan (matches H2 or H3)
SIMPLE_Q_HEADING_RE = re.compile(r"^#{2,3} Question (\d+)(?:\.\d+)?")


def slugify(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", s) or "section"


def parse_heading(heading_line: str):
    """Return (qnum, title, difficulty_from_heading_or_None) or (None, None, None)."""
    m = H_QUESTION_RE.match(heading_line)
    if not m:
        return None, None, None
    qnum = m.group(2)
    rest = m.group(3)
    diff_match = HEADING_DIFFICULTY_RE.search(rest)
    difficulty = diff_match.group(1).lower() if diff_match else None
    title = HEADING_DIFFICULTY_RE.sub("", rest)
    title = title.strip().lstrip(":").strip()
    if not title:
        title = f"Question {qnum}"
    return qnum, title, difficulty


def parse_questions(md_path: Path, domain_id: str) -> list[dict]:
    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]

    # Split on H2/H3 Question headings only (not on Case Study H2, not on the
    # comments separating domains).
    blocks = re.split(r"^(#{2,3} Question .+)$", text, flags=re.MULTILINE)
    questions: list[dict] = []
    for i in range(1, len(blocks), 2):
        heading = blocks[i].strip()
        body = blocks[i + 1] if i + 1 < len(blocks) else ""

        qnum, title, heading_difficulty = parse_heading(heading)
        if qnum is None:
            continue

        if heading_difficulty:
            difficulty = heading_difficulty
            sm = BODY_QUESTION_PREFIX_RE.search(body)
            stem_block = sm.group(1) if sm else body
        else:
            dm = BODY_DIFFICULTY_RE.search(body)
            if not dm:
                print(
                    f"  ⚠ {md_path.name} Q{qnum}: no difficulty marker — skipped",
                    file=sys.stderr,
                )
                continue
            difficulty = dm.group(1).lower()
            stem_block = dm.group(2)

        # Stem ends at the first choice line
        stem_lines, rest_lines = [], []
        in_stem = True
        for line in stem_block.splitlines():
            if in_stem and CHOICE_RE.match(line.strip()):
                in_stem = False
            if in_stem:
                stem_lines.append(line)
            else:
                rest_lines.append(line)
        stem = "\n".join(stem_lines).strip()

        choices: dict[str, str] = {}
        for line in rest_lines:
            cm = CHOICE_RE.match(line.strip())
            if cm:
                choices[cm.group(1)] = cm.group(2).strip()
        if len(choices) != 4:
            print(
                f"  ⚠ {md_path.name} Q{qnum}: expected 4 choices, found {len(choices)} — skipped",
                file=sys.stderr,
            )
            continue

        callout_idx = None
        for idx, line in enumerate(rest_lines):
            if ANSWER_CALLOUT_RE.match(line):
                callout_idx = idx
                break
        if callout_idx is None:
            print(
                f"  ⚠ {md_path.name} Q{qnum}: no answer callout — skipped",
                file=sys.stderr,
            )
            continue

        callout_lines = []
        for line in rest_lines[callout_idx + 1:]:
            if line.startswith("> "):
                callout_lines.append(line[2:])
            elif line.startswith(">"):
                callout_lines.append(line[1:])
            elif line.strip() == "":
                callout_lines.append("")
            elif line.strip() == "---":
                break
            else:
                break
        callout_body = "\n".join(callout_lines).strip()

        cam = CORRECT_ANSWER_RE.search(callout_body)
        if not cam:
            print(
                f"  ⚠ {md_path.name} Q{qnum}: no correct-answer marker — skipped",
                file=sys.stderr,
            )
            continue
        correct = cam.group(1).upper()
        paragraphs = [p.strip() for p in callout_body.split("\n\n") if p.strip()]
        short_answer = paragraphs[1] if len(paragraphs) > 1 else ""
        explanation = "\n\n".join(paragraphs[2:]) if len(paragraphs) > 2 else ""

        questions.append({
            "id": f"{md_path.parent.name}-{md_path.stem}-q{qnum.zfill(3)}",
            "domain": domain_id,
            "title": title,
            "difficulty": difficulty,
            "question": stem,
            "choices": choices,
            "correctAnswer": correct,
            "shortAnswer": short_answer,
            "explanation": explanation,
        })
    return questions


def build_practice(check_only: bool = False) -> dict:
    """Build the consolidated practice bank from all practice-questions/*.md files."""
    practice_dir = CERT_DIR / "resources" / "practice-questions"
    if not practice_dir.exists():
        print(f"  No practice-questions/ at {practice_dir}", file=sys.stderr)
        return {"cert": CERT_ID, "questions": []}

    domains: list[dict] = []
    questions: list[dict] = []

    for md_path in sorted(practice_dir.glob("*.md")):
        if md_path.name == "practice-questions.md":
            # Index file — skip
            continue
        stem = md_path.stem
        m = re.match(r"^\d+-(.+)$", stem)
        domain_id = m.group(1) if m else stem
        text = md_path.read_text(encoding="utf-8")
        h1_match = re.search(r"^# (.+)$", text, re.MULTILINE)
        raw_domain_name = h1_match.group(1).strip() if h1_match else domain_id.replace("-", " ").title()
        # Strip "Practice Questions: " prefix so the picker reads cleanly
        domain_name = re.sub(r"^Practice Questions:\s*", "", raw_domain_name)

        domain_questions = parse_questions(md_path, domain_id)
        if domain_questions:
            domains.append({
                "id": domain_id,
                "name": domain_name,
                "sourceFile": str(md_path.relative_to(ROOT)),
                "questionCount": len(domain_questions),
            })
            questions.extend(domain_questions)

    bank = {
        "cert": CERT_ID,
        "certTitle": CERT_TITLE,
        "blueprintVersion": BLUEPRINT_VERSION,
        "generated": date.today().isoformat(),
        "domains": domains,
        "questions": questions,
    }

    if not check_only:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if questions:
            out_path = DATA_DIR / f"{CERT_ID}.json"
            out_path.write_text(
                json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(
                f"  {CERT_ID}: {len(questions)} questions across {len(domains)} domains "
                f"→ {out_path.relative_to(ROOT)}"
            )
        else:
            print(f"  {CERT_ID}: 0 questions — no JSON written")
    else:
        print(
            f"  {CERT_ID}: {len(questions)} questions across {len(domains)} domains (ok)"
        )

    return bank


def build_mock(exam_n: int, check_only: bool = False) -> dict:
    """Build a mock-exam bank for exam number `exam_n` (1 or 2)."""
    folder = "mock-exam" if exam_n == 1 else f"mock-exam-{exam_n}"
    md_path = CERT_DIR / "resources" / folder / "questions.md"
    bank_id = f"{CERT_ID}-mock-{exam_n}"
    cert_title = f"{CERT_TITLE} — Mock Exam {exam_n}"

    if not md_path.exists():
        print(f"  No mock-exam file at {md_path}", file=sys.stderr)
        return {"cert": bank_id, "questions": []}

    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]

    # Pre-scan for domain boundaries — DP-800 mocks use HTML comments
    #   <!-- DOMAIN N: Name (~M questions) -->
    # plus the case-study H2 that demarcates the final block.
    current_domain_id = "general"
    current_domain_name = "General"
    domain_order: list[tuple[str, str]] = []
    qnum_to_domain: dict[str, str] = {}

    def remember_domain(did: str, dname: str) -> None:
        if not any(d[0] == did for d in domain_order):
            domain_order.append((did, dname))

    for line in text.splitlines():
        dm = DOMAIN_COMMENT_RE.match(line.strip())
        if dm:
            current_domain_name = dm.group(1).strip()
            current_domain_id = slugify(current_domain_name)
            remember_domain(current_domain_id, current_domain_name)
            continue
        csm = CASE_STUDY_H2_RE.match(line.strip())
        if csm:
            current_domain_name = "Case Study"
            current_domain_id = "case-study"
            remember_domain(current_domain_id, current_domain_name)
            continue
        qm = SIMPLE_Q_HEADING_RE.match(line)
        if qm:
            qnum_to_domain[qm.group(1)] = current_domain_id

    raw_questions = parse_questions(md_path, "mock")
    for q in raw_questions:
        original_qnum = q["id"].rsplit("-q", 1)[-1]
        try:
            qnum_int = str(int(original_qnum))
        except ValueError:
            qnum_int = original_qnum
        q["id"] = f"{bank_id}-q{original_qnum}"
        q["domain"] = qnum_to_domain.get(qnum_int, "general")

    domains: list[dict] = []
    for did, dname in domain_order:
        count = sum(1 for q in raw_questions if q["domain"] == did)
        if count > 0:
            domains.append({
                "id": did,
                "name": dname,
                "sourceFile": str(md_path.relative_to(ROOT)),
                "questionCount": count,
            })

    bank = {
        "cert": bank_id,
        "certTitle": cert_title,
        "blueprintVersion": BLUEPRINT_VERSION,
        "generated": date.today().isoformat(),
        "domains": domains,
        "questions": raw_questions,
        "kind": "mock",
        "sourceCert": CERT_ID,
    }

    if not check_only:
        if not raw_questions:
            print(f"  {bank_id}: 0 questions")
            return bank
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        out_path = DATA_DIR / f"{bank_id}.json"
        out_path.write_text(
            json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(
            f"  {bank_id}: {len(raw_questions)} questions across {len(domains)} domains "
            f"→ {out_path.relative_to(ROOT)}"
        )
    else:
        print(
            f"  {bank_id}: {len(raw_questions)} questions across {len(domains)} domains (ok)"
        )

    return bank


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--kind",
        choices=["practice", "mock", "all"],
        default="all",
        help="Which question banks to build: practice-questions, mock exams, or both (default).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Parse-only; don't write JSON. Non-zero exit if any parse fails.",
    )
    args = parser.parse_args()

    total_qs = 0
    total_banks = 0

    if args.kind in ("practice", "all"):
        print("Practice question bank:")
        bank = build_practice(check_only=args.check)
        n = len(bank.get("questions", []))
        if n:
            total_qs += n
            total_banks += 1

    if args.kind in ("mock", "all"):
        print("\nMock exam banks:")
        for exam_n in (1, 2):
            bank = build_mock(exam_n, check_only=args.check)
            n = len(bank.get("questions", []))
            if n:
                total_qs += n
                total_banks += 1

    print(
        f"\n{'Checked' if args.check else 'Built'} {total_banks} bank(s), "
        f"{total_qs} question(s) total"
    )
    if not args.check:
        print(f"Output: {DATA_DIR}")
        print("Open practice/index.html (any browser) or serve via GitHub Pages to study.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
