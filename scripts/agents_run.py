"""Run the v2 agent system over built dossiers for a date range.

Usage: agents_run.py --start 2022-01-01 --end 2024-12-31 [--n-debate 20] [--cost-cap 100] [--no-debate]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tradingagents.agents_v2.runner import run_week  # noqa: E402
from tradingagents.dossier.builder import OUT as DOSSIERS  # noqa: E402
from tradingagents.dossier.or_client import StructuredClient  # noqa: E402
from llm_v2c0_client import load_api_key  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--n-debate", type=int, default=20)
    ap.add_argument("--cost-cap", type=float, default=100.0)
    ap.add_argument("--no-debate", action="store_true")
    ap.add_argument("--role", default="pro", choices=("pro", "flash", "chrono"))
    ap.add_argument("--provider", default=None, help="override pinned provider (pilot/diagnostics only)")
    ap.add_argument("--runs-dir", default=None, help="alternative output directory (repeat runs, ablations)")
    args = ap.parse_args()
    client = StructuredClient.pinned(args.role, load_api_key(), cost_cap_usd=args.cost_cap)
    if args.provider:
        client.provider = [p.strip() for p in args.provider.split(",")]
    from pathlib import Path as _P
    runs_dir = _P(args.runs_dir) if args.runs_dir else None
    days = sorted(p for p in DOSSIERS.iterdir() if args.start <= p.name <= args.end)
    started = time.monotonic()
    for day in days:
        dossiers = {p.stem: json.loads(p.read_text()) for p in sorted(day.glob("*.json"))}
        kwargs = {"runs_dir": runs_dir} if runs_dir else {}
        out = run_week(pd.Timestamp(day.name, tz="UTC"), dossiers, client, n_debate=args.n_debate,
                       debate=not args.no_debate, **kwargs)
        debated = sum(r.get("debated", False) for r in out["results"].values())
        failed = sum(1 for r in out["results"].values() if r.get("failed") or r.get("debate_failed"))
        print(f"{day.name}: {len(dossiers)} assets, {debated} debated, {failed} failed, calls {client.calls}, spent ${client.spent_usd:.2f}, "
              f"{(time.monotonic() - started) / 60:.1f} min", flush=True)
    print(f"done: calls {client.calls}, spent ${client.spent_usd:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
