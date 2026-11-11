"""Charter 1b lifecycle runner (one registered experiment, replacement of the Charter 1 dev run).

The weeks completed by the first attempt are read from the registered call cache without any call; older weeks
are run newest first with the registered agent system under the remaining spend cap. A week is excluded and the
run ends when the cap is reached, when the week raises, or when more than MAX_FAILED_NEW_WEEK of its assets
fail. The forecast and portfolio gates are then computed on the completed weeks and a verdict is written by
code. All inputs are registered by hash; outputs are written through ResearchRun.
Usage: llm_v2c1b_run.py --registration research/llm-v2-charter1b-<date>/gates.json --experiment <id> --cost-cap 10.43
       (--no-new-weeks evaluates the frozen weeks only and makes no call)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tradingagents.agents_v2.charter1b import (BOOK_KEYS, MAX_FAILED_NEW_WEEK, asset_rows, finalize, json_safe,  # noqa: E402
                                                load_cached_week, load_dossiers, verify_cache, verify_store)
from tradingagents.agents_v2.graph import config_sha  # noqa: E402
from tradingagents.agents_v2.portfolio_eval import realized_funding  # noqa: E402
from tradingagents.agents_v2.runner import run_week  # noqa: E402
from tradingagents.dossier.or_client import SpendCapError, StructuredClient  # noqa: E402
from tradingagents.dossier.quant_forecast import forward_returns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("forecasts.json", "evaluation.json", "portfolio.json", "books.json", "cost.json", "verdict.json")
CELLS = ("agent-run", "forecast-gates", "portfolio-gates", "identified-subsets")


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _week_digest(day_dir: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(day_dir.glob("*.json")):
        h.update(f.name.encode() + b"\0" + hashlib.sha256(f.read_bytes()).hexdigest().encode() + b"\n")
    return h.hexdigest()


def prepare(read, root: Path, cost_cap: float) -> dict:
    """Load and verify every registered input. ``read(name)`` returns the bytes of a registered input. Called once
    before the run is claimed (a defect then stops the process without consuming the attempt) and again through
    the run helper."""
    manifest = json.loads(read("dossier_manifest"))
    cfg = json.loads(read("agent_config"))
    if cfg["config_sha"] != config_sha():
        raise SystemExit("agent config differs from the registered freeze")
    cache = json.loads(read("cache_manifest"))
    if cost_cap > cache["attempt1"]["process_cap_usd"] + 1e-9:
        raise SystemExit("cost cap exceeds the registered remainder of the Charter 1 spend cap")
    by_day = load_dossiers(root, manifest)
    runs_dir = root / cache["runs_dir"]
    frozen = verify_cache(runs_dir, cache, by_day, cfg["config_sha"])
    return {"config": cfg["config_sha"], "cache": cache, "by_day": by_day, "runs_dir": runs_dir, "frozen": frozen,
            "cards": pd.read_parquet(io.BytesIO(read("cards"))),
            "quant": pd.read_parquet(io.BytesIO(read("quant_forecasts"))),
            "flags": pd.read_parquet(io.BytesIO(read("reid_flags"))),
            # forward-return and funding sources must be the registered stores
            "klines_dir": verify_store(root, json.loads(read("klines_digest")), "kline store"),
            "funding_dir": verify_store(root, json.loads(read("funding_digest")), "funding store"),
            "frozen_weeks": {day: load_cached_week(day, by_day[day], runs_dir, cfg["config_sha"]) for day in sorted(frozen)}}


def main(argv: list[str] | None = None, root: Path | None = None, client=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--cost-cap", type=float, required=True, help="spend cap of this process (new calls only)")
    ap.add_argument("--no-new-weeks", action="store_true", help="evaluate the frozen weeks only; no call is made")
    args = ap.parse_args(argv)
    root = Path(root) if root else ROOT
    from tradingagents.research import ResearchRun
    if client is None and not args.no_new_weeks:
        from llm_v2c0_client import load_api_key
        client = StructuredClient.pinned("pro", load_api_key(), cost_cap_usd=args.cost_cap)
    registered = json.loads((root / args.registration).read_text())["experiments"][args.experiment]["inputs"]
    prepare(lambda name: (root / registered[name]["path"]).read_bytes(), root, args.cost_cap)      # pre-flight, no claim yet
    with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=_head(root)) as run:
        ctx = prepare(run.read_input, root, args.cost_cap)
        by_day, runs_dir, frozen, cache = ctx["by_day"], ctx["runs_dir"], ctx["frozen"], ctx["cache"]
        rows, books, completed, new_weeks, truncated_at = [], {name: {} for name in BOOK_KEYS}, [], {}, None
        for day in sorted(by_day, reverse=True):
            if day in frozen:
                out = ctx["frozen_weeks"][day]
            else:
                if args.no_new_weeks:
                    truncated_at = {"week": day, "reason": "no new weeks requested: frozen weeks evaluated without calls"}
                    break
                calls0, spent0 = client.calls, client.spent_usd
                try:
                    out = run_week(pd.Timestamp(day, tz="UTC"), by_day[day], client, runs_dir=runs_dir)
                except SpendCapError as exc:
                    truncated_at = {"week": day, "reason": str(exc)}
                    print(f"{day}: spend cap reached, week excluded; stopping", flush=True)
                    break
                except Exception as exc:                                # noqa: BLE001
                    truncated_at = {"week": day, "reason": f"week raised {type(exc).__name__}: {exc}"}
                    print(f"{day}: {truncated_at['reason']}, week excluded; stopping", flush=True)
                    break
                n_failed = sum(bool(r.get("failed")) for r in out["results"].values())
                if n_failed > MAX_FAILED_NEW_WEEK:
                    truncated_at = {"week": day, "reason": f"{n_failed} failed assets (limit {MAX_FAILED_NEW_WEEK})"}
                    print(f"{day}: {truncated_at['reason']}, week excluded; stopping", flush=True)
                    break
                new_weeks[day] = {"calls": client.calls - calls0, "spent_usd": client.spent_usd - spent0, "failed": n_failed,
                                  "cache_digest": _week_digest(runs_dir / day)}
                print(f"{day}: calls {client.calls} spent ${client.spent_usd:.2f}", flush=True)
            rows += asset_rows(day, out["results"], by_day[day])
            for name, key in BOOK_KEYS.items():
                books[name][pd.Timestamp(day, tz="UTC")] = out["portfolio"][key]      # keyed by symbol
            completed.append(day)
        fridays = [pd.Timestamp(day, tz="UTC") for day in sorted(completed)]
        symbols = sorted({r["symbol"] for r in rows})
        fwd = forward_returns(symbols, fridays, klines_dir=ctx["klines_dir"])
        funding = realized_funding(symbols, fridays, funding_dir=ctx["funding_dir"])
        weeks = {"completed": sorted(completed), "n_completed": len(completed), "n_frozen": len(frozen), "n_new": len(new_weeks),
                 "n_manifested": len(by_day), "truncated_at": truncated_at}
        outputs = finalize(rows, books, fwd, funding, ctx["cards"], ctx["quant"], ctx["flags"], weeks)
        spent = float(client.spent_usd) if client is not None else 0.0
        outputs["cost.json"] = json_safe({
            "calls": int(client.calls) if client is not None else 0, "spent_usd": spent, "process_cap_usd": args.cost_cap,
            "no_new_weeks": bool(args.no_new_weeks), "config_sha": config_sha(), "weeks_completed": len(completed),
            "weeks_frozen": len(frozen), "new_weeks": new_weeks, "truncated_at": truncated_at, "runs_dir": cache["runs_dir"],
            "attempt1": cache["attempt1"],
            "cumulative_recorded_spend_usd": cache["attempt1"]["recorded_spend_usd"] + spent})
        for name in OUTPUTS:
            run.write_json(name, outputs[name])
        run.finish([{"id": c, "status": "complete"} for c in CELLS])
        print(json.dumps(outputs["verdict.json"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
