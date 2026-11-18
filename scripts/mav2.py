"""Second multi-agent framework (family llm-multiagent-v2): status, pin check and offline replay. No model call.

  mav2.py status            one row per registered run: receipt, verdict, headline gate, test sample, cost
  mav2.py verify            receipt verification plus the check that no pinned file changed (exit 1 on a problem)
  mav2.py replay V2 V5      recompute the outputs of the given runs from their registered inputs and compare
  mav2.py replay all        the same for every completed run (V1b, V2-V5); tens of minutes, mostly V5
  mav2.py pinned            the files pinned by any receipt: never edit them, add new files instead

Add --json for machine-readable output. Nothing is written into research_runs/, no sealed window is read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.mav2 import pins, registry, replay


def _fmt(value, spec: str) -> str:
    return "" if value is None else format(value, spec)


def cmd_status(args) -> int:
    rows = registry.status()
    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    print(f"{'run':<4} {'receipt':<9} {'verdict':<12} {'gate':<24} {'value':>7} {'sample':<10} {'cost $':>8}")
    for r in rows:
        print(f"{r['label']:<4} {r['receipt']:<9} {r['verdict'] or '':<12} {r['gate'] or '':<24} {_fmt(r['value'], '.2f'):>7} "
              f"{r['sample'] or '':<10} {_fmt(r['cost_usd'], '.2f'):>8}")
    print("\ncost sources:")
    for r in rows:
        print(f"  {r['label']}: {r['cost_source']}")
    return 0


def cmd_verify(args) -> int:
    rows = registry.status()
    reports = pins.check_all()
    problems = [f"{r['label']}: receipt {r['receipt']}" for r in rows
                if r["receipt"] != "complete" and not (r["label"] == "V1" and r["receipt"] == "failed")]
    problems += [f"{p.label}: pinned file changed: {f}" for p in reports for f in p.drifted]
    if args.json:
        print(json.dumps({"receipts": {r["label"]: r["receipt"] for r in rows},
                          "pins": {p.label: {"pinned": p.pinned, "drifted": p.drifted, "expected": p.expected} for p in reports},
                          "problems": problems}, indent=1))
    else:
        for r, p in zip(rows, reports):
            note = f", documented changes: {len(p.expected)}" if p.expected else ""
            print(f"{r['label']:<4} receipt {r['receipt']:<9} pinned {p.pinned:>3} changed {len(p.drifted)}{note}")
        print("\nV1 is expected to be 'failed' (interrupted run); its documented changes are listed in tradingagents/mav2/pins.py.")
        print("OK" if not problems else "PROBLEMS:\n  " + "\n  ".join(problems))
    return 1 if problems else 0


def cmd_replay(args) -> int:
    labels = list(replay.ADAPTERS) if args.runs == ["all"] else args.runs
    failed, results = False, {}
    for label in labels:
        try:
            res = replay.replay(label)
        except replay.ReplayError as exc:
            failed = True
            results[label] = {"error": str(exc)}
            if not args.json:
                print(f"{label}: cannot replay: {exc}")
            continue
        failed |= not res.ok
        results[label] = {"ok": res.ok, "verdict_stored": res.verdict_stored, "verdict_replay": res.verdict_replay,
                          "differences": res.compared, "known_differences": res.known, "skipped": res.skipped}
        if not args.json:
            print(f"{label}: {'reproduced' if res.ok else 'DIFFERS'} (verdict stored {res.verdict_stored}, "
                  f"replay {res.verdict_replay}; outputs compared {len(res.compared)}, skipped {res.skipped or 'none'})")
            for d in res.compared.values():
                for line in d:
                    print(f"    {line}")
            n_known = sum(len(d) for d in res.known.values())
            if n_known:
                print(f"    {n_known} known platform-dependent differences, cause in replay.KNOWN_DIFFERENCES:")
                for reason in replay.KNOWN_DIFFERENCES[label].values():
                    print(f"      {reason}")
    if args.json:
        print(json.dumps(results, indent=1))
    return 1 if failed else 0


def cmd_pinned(args) -> int:
    paths = sorted(pins.all_pinned_paths())
    print(json.dumps(paths, indent=1) if args.json else "\n".join(paths))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    p = sub.add_parser("replay")
    p.add_argument("runs", nargs="+", help="labels (V1b V2 V3 V4 V5) or 'all'")
    p.set_defaults(fn=cmd_replay)
    sub.add_parser("pinned").set_defaults(fn=cmd_pinned)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
