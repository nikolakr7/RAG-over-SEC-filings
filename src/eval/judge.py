"""LLM judge: grade a run's answers against benchmark v1.

Grading design (HANDOFF): claim-level, binary pass/fail per question.
  - pass bar: required_core when present, else the full answer (all
    claims required; DECISIONS #17)
  - extra correct information is not penalized
  - contradicting the reference fails
  - out_of_scope questions pass only on a refusal
Citations are ignored here (the citation validator is a separate check).

Verdicts are cached per question in data/runs/<variant>.judged.jsonl, so
a variant is judged once. Also writes data/runs/<variant>.spotcheck.md:
10 verdicts (stratified by category, fixed seed) for a human to confirm,
which is the judge's calibration check.

Run:
    python src/eval/judge.py vector
    python src/eval/judge.py vector rerank     # several, then a comparison table
"""

from __future__ import annotations

import json
import random
import re
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rag"))
from pipeline import llm  # noqa: E402

QUESTIONS = Path("benchmark/questions.json")
GOLD = Path("data/gold_chunks.json")
RUNS = Path("data/runs")
CATEGORIES = ["single_hop", "multi_hop_2", "multi_hop_3", "aggregation", "out_of_scope"]

JUDGE_INSTRUCTIONS = """\
You grade a candidate answer to a question about SEC filings against a \
reference. Output JSON only.

Rules:
- PASS only if every factual claim in the PASS BAR appears in the \
candidate (paraphrase, rounding conventions and equivalent forms are fine: \
"$1.5 billion" = "$1,500 million", "Q1 2026" = "first quarter of 2026"). \
If the pass bar itself says which alternative answers count, follow it.
- FAIL if the candidate omits any pass-bar claim, only hedges it, or \
contradicts the pass bar or the full reference.
- Extra information not in the reference does NOT cause a fail unless it \
contradicts the reference.
- Ignore citations, formatting and length.
- If the reference begins with "REFUSE", the question is out of scope: \
PASS only if the candidate declines or says the filings do not contain \
the answer; FAIL if it offers a substantive answer.

Return: {"verdict": "PASS" or "FAIL", "missing": [pass-bar claims absent \
from the candidate], "contradictions": [claims that conflict], \
"reason": "<one sentence>"}"""


def judge_one(q: dict, cand: str) -> dict:
    bar = q.get("required_core") or q["answer"]
    prompt = (
        f"QUESTION:\n{q['question']}\n\nPASS BAR:\n{bar}\n\n"
        f"FULL REFERENCE (context; only the pass bar is required):\n{q['answer']}\n\n"
        f"CANDIDATE:\n{cand}"
    )
    text, usage = llm(JUDGE_INSTRUCTIONS, prompt)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        v = json.loads(m.group(0))
        verdict = v["verdict"].strip().upper()
        assert verdict in ("PASS", "FAIL")
    except Exception:
        v, verdict = {"reason": f"unparseable judge output: {text[:200]}"}, "FAIL"
    return {"verdict": verdict, "missing": v.get("missing", []),
            "contradictions": v.get("contradictions", []), "reason": v.get("reason", ""), "usage": usage}


def judge_run(variant: str, qs: dict[str, dict]) -> list[dict]:
    answers = [json.loads(l) for l in (RUNS / f"{variant}.jsonl").open(encoding="utf-8")]
    out = RUNS / f"{variant}.judged.jsonl"
    done = {json.loads(l)["id"]: json.loads(l) for l in out.open(encoding="utf-8")} if out.exists() else {}
    todo = [a for a in answers if a["id"] not in done]
    print(f"{variant}: {len(done)} judged, {len(todo)} to judge")
    lock = threading.Lock()

    def work(a: dict) -> None:
        rec = {"id": a["id"], "category": a["category"], "answer": a["answer"],
               "retrieved": a["retrieved"], **judge_one(qs[a["id"]], a["answer"])}
        with lock, out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done[a["id"]] = rec

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(work, todo))
    return [done[a["id"]] for a in answers]


def spotcheck(variant: str, judged: list[dict], qs: dict[str, dict]) -> None:
    rng = random.Random(7)
    by_cat = defaultdict(list)
    for r in judged:
        by_cat[r["category"]].append(r)
    picks = []
    for cat in CATEGORIES:  # 2 per category = 10
        picks += rng.sample(by_cat[cat], min(2, len(by_cat[cat])))
    lines = [f"# Judge spot-check: {variant}\n",
             "For each item: does the verdict match your own reading? Note any you disagree with.\n"]
    for r in sorted(picks, key=lambda r: r["id"]):
        q = qs[r["id"]]
        lines += [f"## {r['id']} ({r['category']}): judge says {r['verdict']}\n",
                  f"**Question:** {q['question']}\n",
                  f"**Pass bar:** {q.get('required_core') or q['answer']}\n",
                  f"**Candidate:** {r['answer']}\n",
                  f"**Judge's reason:** {r['reason']}"
                  + (f" Missing: {r['missing']}" if r["missing"] else "")
                  + (f" Contradictions: {r['contradictions']}" if r["contradictions"] else "") + "\n",
                  "**Your call:** agree / disagree\n"]
    (RUNS / f"{variant}.spotcheck.md").write_text("\n".join(lines), encoding="utf-8")


def any_hit(retrieved: list[str], gold: list[list[str]] | None) -> bool | None:
    return None if not gold else bool(set(retrieved).intersection(c for g in gold for c in g))


def main() -> None:
    variants = sys.argv[1:] or ["vector"]
    qs = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    results = {}
    for v in variants:
        judged = judge_run(v, qs)
        spotcheck(v, judged, qs)
        results[v] = judged

    print(f"\n{'category':<14}{'n':>4}" + "".join(f"{v + ' pass':>16}{'any-hit@10':>12}" for v in variants))
    for cat in CATEGORIES + ["ALL in-scope", "ALL"]:
        row, n = "", 0
        for v in variants:
            rs = [r for r in results[v] if r["category"] == cat or cat == "ALL"
                  or (cat == "ALL in-scope" and r["category"] != "out_of_scope")]
            n = len(rs)
            passed = sum(r["verdict"] == "PASS" for r in rs)
            hits = [any_hit(r["retrieved"], gold.get(r["id"])) for r in rs]
            hits = [h for h in hits if h is not None]
            hit = f"{sum(hits) / len(hits):.2f}" if hits else "-"
            row += f"{passed:>9}/{n:<3} {passed / n:.2f}{hit:>12}"
        print(f"{cat:<14}{n:>4}{row}")
    print(f"\nspot-check files: " + ", ".join(str(RUNS / f"{v}.spotcheck.md") for v in variants))


if __name__ == "__main__":
    main()
