"""Pre-registration smoke test and in-run preflight on invented text only (never corpus text).

Prints the echoed model and provider, usage and answers; writes nothing into
the repository. Spend capped at USD 0.10.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_extract import anonymize  # noqa: E402
from llm_jev_smoke import INVENTED, PREFLIGHT_ROWS  # noqa: E402
from llm_v2c0_client import MODEL, PROVIDER, OpenRouterClient, load_api_key  # noqa: E402
from llm_v2c0_prompt import article_text, prompt_sha256  # noqa: E402


def preflight(client) -> None:
    """Worst-case request shapes (non-ASCII, 4,000-char content, anonymized) on invented text."""
    for row in PREFLIGHT_ROWS:
        client.extract(article_text(row))
        client.extract(article_text(row, anonymize))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--provider", default=PROVIDER)
    args = parser.parse_args(argv)
    client = OpenRouterClient(api_key=load_api_key(), model=args.model, provider=args.provider,
                              cost_cap_usd=0.10)
    print(json.dumps({"prompt_sha256": prompt_sha256(), "model": args.model,
                      "provider": args.provider}))
    for row in INVENTED:
        out = client.extract(article_text(row))
        print(json.dumps({"headline": row["headline"], "events": out["events"],
                          "ambiguous": out["ambiguous"], "raw": out["raw"]}, indent=1))
    preflight(client)
    print(f"calls={client.calls} spent_usd={client.spent_usd:.6f} max_call_usd={client.max_call_usd:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
