"""Pre-registration smoke test on invented headlines (never corpus text).

Prints resolved model ID, provider and answer shapes; writes nothing into the
repository. Spend capped at USD 0.10.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_extract import anonymize  # noqa: E402
from llm_jev_client import JevClient, load_api_key  # noqa: E402
from llm_jev_questions import build_questions, build_state, candidates  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INVENTED = (
    {"store": "gdelt", "summary": "",
     "headline": "Fictional exchange Zetrix halts withdrawals after $40 million exploit"},
    {"store": "gdelt", "summary": "",
     "headline": "Regulator fines imaginary token issuer Quarkcoin Labs over unregistered sale"},
    {"store": "alpaca", "summary": "", "symbols": "NMBUSD",
     "headline": "Invented protocol Nimbus Chain completes mainnet launch"},
)
PREFLIGHT_ROWS = (
    {"store": "gdelt",
     "headline": "Fiktivní burza Zetrix – ünïcødé test ✓ halts withdrawals",
     "summary": " and ".join(f"Qorvant{i}" for i in range(32)),
     "content": ("Vymyšlený obsah č. 7 — ünïcødé ✓ Zetrix exploit report. " * 120)},
)


def preflight(client) -> None:
    """Exercise E1's worst-case request shapes before any run claim.

    Invented text only, never corpus text. Any JevError propagates.
    """
    for row in PREFLIGHT_ROWS:
        cands = candidates(row)
        client.decide(build_state(row), build_questions(cands, reverse=False))
        client.decide(build_state(row, anonymize),
                      build_questions([], reverse=False, with_asset=False))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="typesafe/jev-1.13")
    parser.add_argument("--expect-model", default=None)
    args = parser.parse_args(argv)
    client = JevClient(api_key=load_api_key(ROOT / ".env"), model=args.model,
                       expected_model=args.expect_model, expected_provider=None,
                       cost_cap_usd=0.10)
    for reverse in (False, True):
        for row in INVENTED:
            cands = candidates(row)
            resp = client.decide(build_state(row), build_questions(cands, reverse=reverse))
            print(json.dumps({"reverse": reverse, "headline": row["headline"],
                              "candidates": cands, "id": resp.get("id"),
                              "model": resp.get("model"), "provider": resp.get("provider"),
                              "usage": resp.get("usage"),
                              "latency_s": round(resp["_latency_s"], 3),
                              "answers": resp["answers"]}, indent=1))
    preflight(client)
    print(f"calls={client.calls} spent_usd={client.spent_usd:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
