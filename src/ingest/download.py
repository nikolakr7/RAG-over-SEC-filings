"""Download SEC filings from EDGAR.

EDGAR is free and needs no API key, but it has two rules that will get you
blocked if you ignore them:

  1. Every request must send a User-Agent identifying you, including a real
     contact address. Requests without one get 403 Forbidden.
  2. Stay under 10 requests/second. We throttle well below that; nothing here
     is urgent enough to risk an IP ban.

Endpoints used:

  https://www.sec.gov/files/company_tickers.json
      One big ticker -> CIK map. A CIK is EDGAR's permanent company id.
      Tickers change, companies rename themselves, CIKs never move.

  https://data.sec.gov/submissions/CIK##########.json
      Every filing a company has ever made. CIK is zero-padded to 10 digits
      in THIS url but not in the Archives url below. That inconsistency is
      EDGAR's, not ours.

  https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json
      Lists every file inside one filing. Used to locate Exhibit 21
      (the subsidiary list), which is a SEPARATE file from the main 10-K
      document and is invisible if you only fetch primaryDocument.

Corpus plan (default): per company, the most recent
  3x 10-K (three fiscal years), 6x 10-Q, 8x 8-K, 2x DEF 14A (proxy
  statement, where officer and director bios live).
8 companies x ~19 filings comes to roughly 150 documents, matching the
project plan.

Run:
    python src/ingest/download.py                    # full corpus plan
    python src/ingest/download.py --form 10-K=1      # override one form count
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Mid-cap biotech. Same sector on purpose: shared auditors, overlapping
# officers and directors, licensing deals with each other. That density is
# what makes multi-hop questions have answers.
TICKERS = [
    "EXEL",  # Exelixis
    "HALO",  # Halozyme
    "SRPT",  # Sarepta
    "ALKS",  # Alkermes
    "IONS",  # Ionis
    "RARE",  # Ultragenyx
    "ARWR",  # Arrowhead
    "NBIX",  # Neurocrine
]

# How many of each form type to fetch per company (most recent first).
DEFAULT_PLAN = {
    "10-K": 3,
    "10-Q": 6,
    "8-K": 8,
    "DEF 14A": 2,
}

# Only 10-Ks carry Exhibit 21 (subsidiary lists) worth fetching.
EXHIBIT_FORMS = {"10-K"}
# Exhibit 21 files have no reliable type field in index.json, but their
# filenames follow strong conventions: "...ex211.htm", "ex21_1.htm",
# "d12345dex211.htm", and some filers spell it out: "exhibit211.htm".
# Match by name. Known residual ambiguity: EX-2.1 (merger agreements) can
# also be named "ex21.htm"; acceptable here because we only harvest
# exhibits from 10-Ks, where EX-2.1 rarely appears as a document.
EXHIBIT21_PATTERN = re.compile(r"(?:ex|exhibit)[-_]?21", re.IGNORECASE)

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"

RAW_DIR = Path("data/raw")
MANIFEST_PATH = RAW_DIR / "manifest.json"

REQUEST_INTERVAL = 0.17  # ~6 req/s, well under EDGAR's 10/s limit
_last_request = 0.0


def _user_agent() -> str:
    ua = os.getenv("SEC_USER_AGENT", "").strip()
    if not ua or "example.com" in ua:
        raise SystemExit(
            "SEC_USER_AGENT is not set.\n"
            "Copy .env.example to .env and put your real email in it.\n"
            "SEC blocks requests that don't identify a contact."
        )
    return ua


def get(url: str) -> requests.Response:
    """One throttled GET. Every network call in this file goes through here,
    which is the only reliable way to be sure the rate limit is respected."""
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)
    response = requests.get(url, headers={"User-Agent": _user_agent()}, timeout=30)
    _last_request = time.monotonic()
    response.raise_for_status()
    return response


def resolve_ciks(tickers: list[str]) -> dict[str, dict]:
    """Map tickers to CIKs. Cached to disk after the first call."""
    cache = RAW_DIR / "company_tickers.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
    else:
        data = get(TICKER_MAP_URL).json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")

    wanted = {t.upper() for t in tickers}
    found = {}
    for entry in data.values():
        if entry["ticker"] in wanted:
            found[entry["ticker"]] = {"cik": entry["cik_str"], "name": entry["title"]}

    for missing in wanted - found.keys():
        print(f"  ! {missing}: no CIK found (delisted, acquired, or renamed?)")
    return found


def list_filings(cik: int, plan: dict[str, int]) -> list[dict]:
    """Recent filings for one company, up to plan[form] of each form type.

    The response stores filings as PARALLEL ARRAYS: form[i], filingDate[i],
    and accessionNumber[i] all describe the same filing. We zip it into
    dicts immediately and never think about indices again.
    """
    submissions = get(SUBMISSIONS_URL.format(cik=cik)).json()
    recent = submissions["filings"]["recent"]

    filings = []
    counts = {form: 0 for form in plan}
    for i in range(len(recent["form"])):
        form = recent["form"][i]
        if form not in plan or counts[form] >= plan[form]:
            continue
        if not recent["primaryDocument"][i]:
            continue  # rare, but some old filings lack a primary document
        counts[form] += 1
        filings.append(
            {
                "cik": cik,
                "company": submissions["name"],
                "sic": submissions.get("sic"),
                "sic_description": submissions.get("sicDescription"),
                "form": form,
                "filing_date": recent["filingDate"][i],
                "report_date": recent["reportDate"][i],
                "accession": recent["accessionNumber"][i],
                "primary_document": recent["primaryDocument"][i],
            }
        )
    return filings


def find_exhibit21(cik: int, accession_nodash: str) -> list[str]:
    """Names of Exhibit 21 files inside a filing, via the filing's index."""
    try:
        index = get(FILING_INDEX_URL.format(cik=cik, accession=accession_nodash)).json()
    except requests.HTTPError:
        return []
    items = index.get("directory", {}).get("item", [])
    return [
        item["name"]
        for item in items
        if EXHIBIT21_PATTERN.search(item.get("name", ""))
        and item["name"].lower().endswith((".htm", ".html", ".txt"))
    ]


def download_document(cik: int, accession_nodash: str, document: str, out_path: Path) -> bool:
    """Fetch one document if not already on disk. Returns True if downloaded.

    Skipping existing files makes this script safe to re-run, and is also
    what will make live corpus updates a scheduler away later: re-running
    only fetches what is new.
    """
    if out_path.exists():
        return False
    url = ARCHIVE_URL.format(cik=cik, accession=accession_nodash, document=document)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(get(url).content)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Download SEC filings from EDGAR.")
    parser.add_argument(
        "--form",
        action="append",
        default=[],
        metavar="FORM=N",
        help='Override a form count, e.g. --form 10-K=1 --form "DEF 14A=0". '
        "Repeatable. Unmentioned forms keep their defaults.",
    )
    args = parser.parse_args()

    plan = dict(DEFAULT_PLAN)
    for override in args.form:
        form, _, count = override.rpartition("=")
        plan[form] = int(count)
    plan = {form: n for form, n in plan.items() if n > 0}

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Corpus plan per company: {plan}")
    print(f"Resolving {len(TICKERS)} tickers...")
    companies = resolve_ciks(TICKERS)

    manifest = []
    downloaded = 0
    for ticker, info in sorted(companies.items()):
        filings = list_filings(info["cik"], plan)
        print(f"{ticker:<6} {info['name'][:38]:<40} {len(filings)} filings")

        for filing in filings:
            filing["ticker"] = ticker
            accession_nodash = filing["accession"].replace("-", "")
            form_slug = filing["form"].replace(" ", "")
            stem = f"{form_slug}_{filing['filing_date']}_{accession_nodash}"

            out_path = RAW_DIR / ticker / f"{stem}.htm"
            if download_document(filing["cik"], accession_nodash, filing["primary_document"], out_path):
                downloaded += 1
                print(f"       + {out_path.name}")
            filing["raw_path"] = str(out_path)

            # Exhibit 21 (subsidiary list) rides along with 10-Ks as a
            # separate file. Without this, subsidiary data does not exist
            # in the corpus at all.
            filing["exhibits"] = []
            if filing["form"] in EXHIBIT_FORMS:
                for name in find_exhibit21(filing["cik"], accession_nodash):
                    ex_path = RAW_DIR / ticker / f"{stem}_EX21_{name}"
                    if download_document(filing["cik"], accession_nodash, name, ex_path):
                        downloaded += 1
                        print(f"       + {ex_path.name}")
                    filing["exhibits"].append(
                        {"kind": "EX-21", "document": name, "raw_path": str(ex_path)}
                    )

            manifest.append(filing)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} filings in manifest, {downloaded} files newly downloaded.")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
