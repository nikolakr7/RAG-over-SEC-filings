"""Everything after extraction, in order, stopping at the first failure:

  1. extract.py full     (resumes; only re-runs batches that failed or are missing)
  2. resolve.py full     -> data/graph/full.graph.json
  3. load_neo4j.py full  -> Neo4j
  4. hybrid.py           -> data/runs/hybrid.jsonl (cached per question)
  5. judge.py vector rerank hybrid
  6. citations.py vector rerank hybrid

Run:
    python src/run_graph_and_score.py
"""

from __future__ import annotations

import subprocess
import sys

PY = sys.executable
STEPS = [
    ["src/graph/extract.py", "full"],
    ["src/graph/resolve.py", "full"],
    ["src/graph/load_neo4j.py", "full"],
    ["src/rag/hybrid.py"],
    ["src/eval/judge.py", "vector", "rerank", "hybrid"],
    ["src/eval/citations.py", "vector", "rerank", "hybrid"],
]

for step in STEPS:
    print(f"\n=== {' '.join(step)} ===", flush=True)
    rc = subprocess.run([PY, "-u", *step]).returncode
    if rc:
        sys.exit(f"step failed ({rc}): {' '.join(step)}")
print("\nall steps done")
