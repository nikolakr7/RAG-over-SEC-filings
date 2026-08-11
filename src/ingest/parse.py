"""Convert downloaded filing HTML into plain text.

Kept separate from download.py on purpose. Downloading is slow, rate-limited,
and hits someone else's server; parsing is fast, local, and something you will
redo many times as you improve it. Bundling them would mean re-downloading
every time you change how parsing works.

This is deliberately crude. Phase 2 replaces it with real chunking that
preserves section structure ("Item 1A Risk Factors" and so on), because
section path becomes chunk metadata. Right now the only goal is text you can
read with your own eyes.

Run:
    python src/ingest/parse.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")
TEXT_DIR = Path("data/text")
MANIFEST_PATH = RAW_DIR / "manifest.json"


def html_to_text(html: bytes) -> str:
    """Strip HTML down to readable text.

    Modern SEC filings are 'inline XBRL' -- ordinary HTML with thousands of
    invisible <ix:...> tags carrying machine-readable financial data. Those
    tags hold no display text, so extracting text ignores them for free. We
    are throwing away structured financial data here; that is fine, because
    this project reasons over relationships, not over numbers.
    """
    soup = BeautifulSoup(html, "lxml")

    # Scripts and styles contain text that is not content.
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Filings are full of layout whitespace and non-breaking spaces.
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit("No manifest found. Run src/ingest/download.py first.")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    for filing in manifest:
        # Primary document plus any exhibits (e.g. Exhibit 21 subsidiary
        # lists) that the downloader attached to this filing.
        paths = [Path(filing["raw_path"])]
        paths += [Path(ex["raw_path"]) for ex in filing.get("exhibits", [])]

        for raw_path in paths:
            if not raw_path.exists():
                print(f"  ! missing {raw_path}")
                continue

            out_dir = TEXT_DIR / filing["ticker"]
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / (raw_path.stem + ".txt")
            if out_path.exists():
                continue

            text = html_to_text(raw_path.read_bytes())
            out_path.write_text(text, encoding="utf-8")

            raw_kb = raw_path.stat().st_size // 1024
            txt_kb = len(text.encode("utf-8")) // 1024
            print(f"{filing['ticker']:<6} {raw_path.stem:<45} {raw_kb:>6} KB -> {txt_kb:>5} KB")

    print(f"\nText written to {TEXT_DIR}")


if __name__ == "__main__":
    main()
