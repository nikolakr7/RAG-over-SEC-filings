"""Phase 2 embeddings primer: fetch vectors for 20 hand-picked sentences.

Infrastructure only -- the similarity math is the user's exercise (see
README.md in this folder). Sentences are drawn from the corpus and
grouped so the similarity structure has something to teach: near-duplicate
auditor sign-offs, a paraphrase pair, a negation pair, a "Merck" keyword
trap (same word, different entities), topical families, and unrelated
boilerplate.

Run:
    python src/primers/embed_primer_sentences.py

Writes:
    data/primer/sentences.json   (id, group, text)
    data/primer/embeddings.npy   (20 x 1536, float32, row i = sentence i)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

SENTENCES = [
    # A: near-duplicate auditor sign-offs
    ("A1", "auditor", "We have served as the Company's auditor since 2002. San Mateo, California"),
    ("A2", "auditor", "We have served as the Company's auditor since 1992. San Diego, California"),
    ("A3", "auditor", "KPMG LLP We have served as the Company's auditor since 2024. San Diego, California"),
    # B: paraphrase pair
    ("B1", "paraphrase", "At closing, on February 7, 2025, we paid Arrowhead an up-front payment of $500.0 million in cash."),
    ("B2", "paraphrase", "Arrowhead received a $500.0 million upfront cash payment from Sarepta when their collaboration agreement closed."),
    # C: negation pair (identical but for did/did not)
    ("C1", "negation", "The CARDIO-TTRansform Phase 3 trial for eplontersen in patients with ATTR-CM did not meet the primary efficacy endpoint of the composite outcome of CV mortality and recurrent CV clinical events."),
    ("C2", "negation", "The CARDIO-TTRansform Phase 3 trial for eplontersen in patients with ATTR-CM met the primary efficacy endpoint of the composite outcome of CV mortality and recurrent CV clinical events."),
    # D: "Merck" keyword trap -- same word, different legal entities and topics
    ("D1", "merck", "In October 2024, we announced our entry into a clinical development collaboration with MSD International Business GmbH, known as Merck within the United States and Canada."),
    ("D2", "merck", "We announced that a German court had granted our request for a preliminary injunction ordering Merck Sharp & Dohme Corp. to refrain from distributing and offering Keytruda SC in Germany."),
    # E: royalty family -- same topic, different deals and wording
    ("E1", "royalty", "We are required to pay a 3% royalty to Royalty Pharma on total net sales of any product containing cabozantinib."),
    ("E2", "royalty", "We sold a minority interest in our future SPINRAZA and pelacarsen royalties to Royalty Pharma for a $500 million upfront payment."),
    ("E3", "royalty", "Jazz receives a royalty of 3.85% on net sales of LUMRYZ sold for narcolepsy."),
    # F: acquisition family
    ("F1", "acquisition", "The Company completed the acquisition of Soleno on May 18, 2026, by causing Purchaser to merge with and into Soleno."),
    ("F2", "acquisition", "On February 12, 2026, the Company successfully completed the Avadel Acquisition, adding LUMRYZ to the Company's portfolio of proprietary commercial products."),
    # G: clinical/science
    ("G1", "clinical", "ELEVIDYS, an AAV-based gene therapy, was approved by the FDA in June 2024 for the treatment of ambulatory patients at least four years old with Duchenne."),
    ("G2", "clinical", "Crysvita is a fully human monoclonal antibody administered via subcutaneous injection that targets fibroblast growth factor 23."),
    # H: unrelated boilerplate / filler
    ("H1", "filler", "The Company has open purchase orders for plant and equipment as part of its normal course of business."),
    ("H2", "filler", "Schizophrenia is a serious brain disorder marked by positive symptoms and negative symptoms."),
    ("H3", "filler", "As of January 22, 2026, the record date for the Annual Meeting, the Company had 140,010,690 shares of its common stock outstanding and entitled to vote."),
    ("H4", "filler", "Helen Torley has served as President and Chief Executive Officer of Halozyme since January 2014."),
]


def main() -> None:
    load_dotenv()
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    client = OpenAI(
        base_url=f"{endpoint}/openai/v1/",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )
    deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    texts = [t for _, _, t in SENTENCES]
    # One call for all 20: the API accepts a list and returns vectors in
    # input order (each item also carries .index; we sort on it anyway).
    response = client.embeddings.create(model=deployment, input=texts)
    data = sorted(response.data, key=lambda item: item.index)
    matrix = np.array([item.embedding for item in data], dtype=np.float32)

    out = Path("data/primer")
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "embeddings.npy", matrix)
    (out / "sentences.json").write_text(
        json.dumps(
            [{"id": i, "group": g, "text": t} for i, g, t in SENTENCES],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"embedded {matrix.shape[0]} sentences -> {matrix.shape} at {out}/")
    print(f"tokens billed: {response.usage.total_tokens}")


if __name__ == "__main__":
    main()
