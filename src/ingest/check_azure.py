"""One-off check that .env is filled in correctly and both Azure OpenAI
deployments actually respond. This is the Phase 0 finish line.

Deliberately checks the CHAT and EMBEDDING deployments separately, with
separate try/except blocks, so a failure in one doesn't hide whether the
other one works. A single try/except around both would tell you "something
broke" without telling you which deployment.

Run:
    python src/ingest/check_azure.py
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

REQUIRED = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
]


def check_env() -> dict[str, str]:
    values = {}
    missing = []
    for key in REQUIRED:
        val = os.getenv(key, "").strip()
        if not val:
            missing.append(key)
        values[key] = val

    if missing:
        print("Missing from .env:")
        for key in missing:
            print(f"  - {key}")
        sys.exit(1)

    # Common copy-paste mistake: pasting the endpoint into the key field or
    # vice versa. The endpoint always starts with https://; the key never does.
    if not values["AZURE_OPENAI_ENDPOINT"].startswith("https://"):
        print(
            "AZURE_OPENAI_ENDPOINT doesn't start with https:// -- "
            "did you paste the key and endpoint into the wrong fields?"
        )
        sys.exit(1)
    if values["AZURE_OPENAI_API_KEY"].startswith("https://"):
        print(
            "AZURE_OPENAI_API_KEY looks like a URL -- "
            "did you paste the key and endpoint into the wrong fields?"
        )
        sys.exit(1)

    print("All four .env variables are present and look plausible.\n")
    return values


def check_chat(client, deployment: str) -> None:
    print(f"Chat deployment '{deployment}'...")
    try:
        # Using the Responses API (client.responses.create), not the older
        # Chat Completions API (client.chat.completions.create). Foundry's
        # own generated sample code for this deployment used Responses --
        # some newer model deployments only support this surface, so we
        # match it exactly rather than assume the older one still works.
        response = client.responses.create(
            model=deployment,
            input="Reply with exactly the two words: Phase 0.",
        )
        text = getattr(response, "output_text", None)
        print(f"  OK -> {text!r}" if text else f"  OK -> {response.output!r}")
        try:
            print(f"  tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out")
        except AttributeError:
            pass  # usage field shape varies; the OK above is what matters
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        print(
            "  Common causes: deployment name doesn't match .env exactly, "
            "or the deployment isn't finished provisioning yet (can take a "
            "minute or two after clicking Deploy)."
        )


def check_embedding(client, deployment: str) -> None:
    print(f"\nEmbedding deployment '{deployment}'...")
    try:
        response = client.embeddings.create(
            model=deployment,
            input="Which subsidiaries share an auditor with this company's CFO's former employer?",
        )
        vector = response.data[0].embedding
        print(f"  OK -> vector of length {len(vector)}")
        print(f"  first 5 values: {[round(v, 4) for v in vector[:5]]}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")


def main() -> None:
    values = check_env()

    # Imported after the env check so a missing package doesn't mask a
    # missing .env file -- you want to see the more obvious problem first.
    from openai import OpenAI

    # Foundry's current (v1) API drops the old dated `api_version` string
    # entirely -- you just point the plain OpenAI client at a specific base
    # URL under your resource. AzureOpenAI + api_version="2024-10-21" is the
    # OLD pattern and is what caused the 404s: an outdated api_version made
    # Azure unable to resolve the deployment, which surfaces as
    # "deployment not found" even though the deployment is fine.
    endpoint = values["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    client = OpenAI(
        base_url=f"{endpoint}/openai/v1/",
        api_key=values["AZURE_OPENAI_API_KEY"],
    )

    check_chat(client, values["AZURE_OPENAI_CHAT_DEPLOYMENT"])
    check_embedding(client, values["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"])


if __name__ == "__main__":
    main()
