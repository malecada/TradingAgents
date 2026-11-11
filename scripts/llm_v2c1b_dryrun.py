"""Charter 1b dry run of the evaluation tail on SYNTHETIC outcomes.

Loads and verifies every input of the planned registration exactly as the run script does (dossiers, call cache,
kline and funding stores), builds the forecast rows and books of the frozen weeks, and then replaces every
forward return and every funding payment by seeded synthetic values before anything is joined with a forecast.
Real returns are used for their missingness and delisting pattern only; no statistic of a real outcome is
computed, printed or stored. Scenarios: pure noise, a planted signal and degenerate panels. Every output is
encoded the way the run helper encodes it (sorted keys, allow_nan=False). Nothing is written to research_runs/.
Usage: llm_v2c1b_dryrun.py [--out research/multiagent-v2/charter1b_dryrun.json] [--fast]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_v2c1b_register import INPUTS  # noqa: E402
from llm_v2c1b_run import OUTPUTS, prepare  # noqa: E402
from tradingagents.agents_v2.charter1b import BOOK_KEYS, BOOTSTRAP_DRAWS, PLACEBO_DRAWS, asset_rows, finalize  # noqa: E402
from tradingagents.agents_v2.portfolio_eval import realized_funding  # noqa: E402
from tradingagents.dossier.quant_forecast import forward_returns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261111


def _rank_signal(rows: pd.DataFrame, col: str) -> pd.Series:
    """Within-week percentile rank of a forecast column, centred, 0 where the forecast is missing."""
    return (pd.to_numeric(rows[col], errors="coerce").groupby(rows["date"]).rank(pct=True) - 0.5).fillna(0.0)


def synthetic_returns(fwd: pd.DataFrame, rows: pd.DataFrame, scenario: str, rng) -> pd.DataFrame:
    """Same keys, delisting flags and missing cells as the real frame; every value replaced."""
    out = fwd[["date", "symbol", "delisted"]].copy()
    present = fwd["fwd_ret"].notna().to_numpy()
    noise = rng.normal(0.0, 0.08, len(out))
    if scenario == "planted":
        key = pd.DataFrame({"date": pd.to_datetime(rows["date"], utc=True), "symbol": rows["symbol"],
                            "signal": (_rank_signal(rows, "p_hybrid") + _rank_signal(rows, "p_judge")).to_numpy()})
        sig = out.assign(date=pd.to_datetime(out["date"], utc=True)).merge(key, on=["date", "symbol"], how="left")["signal"].fillna(0.0)
        values = 0.10 * sig.to_numpy() + 0.5 * noise
    elif scenario == "zero":
        values = np.zeros(len(out))
    else:
        values = noise
    out["fwd_ret"] = np.where(present, values, np.nan)
    return out


def run_scenario(name: str, rows: list[dict], books: dict, fwd: pd.DataFrame, funding: pd.DataFrame, ctx: dict,
                 n_placebo: int, n_boot: int) -> dict:
    t0 = time.time()
    weeks = {"completed": sorted({r["date"] for r in rows}), "n_completed": len({r["date"] for r in rows}),
             "n_frozen": len(ctx["frozen"]), "n_new": 0, "n_manifested": len(ctx["by_day"]), "truncated_at": None}
    outputs = finalize(rows, books, fwd, funding, ctx["cards"], ctx["quant"], ctx["flags"], weeks, n_placebo=n_placebo, n_boot=n_boot)
    outputs["cost.json"] = {"calls": 0, "spent_usd": 0.0, "dry_run": True}
    sizes = {n: len((json.dumps(outputs[n], sort_keys=True, indent=2, allow_nan=False) + "\n").encode()) for n in OUTPUTS}
    v, panel = outputs["verdict.json"], outputs["evaluation.json"]["panel"]
    return {"scenario": name, "outcomes": "SYNTHETIC", "weeks": weeks["n_completed"], "seconds": round(time.time() - t0, 1),
            "verdict": v["verdict"], "failed_gates": v["failed_gates"], "portfolio_gates_evaluated": v["portfolio_gates_evaluated"],
            "descriptive_errors": v["descriptive_errors"], "output_bytes": sizes,
            "panel_structure": {k: panel[k] for k in ("rows", "failed", "abstain", "debated", "debate_failed", "missing_fwd_ret",
                                                      "delisted_rows", "primary_provider_rows", "deployed_equals_hybrid")},
            "identified": {k: outputs["evaluation.json"]["identified_subsets"][k] for k in ("flagged_rows", "identified_rows")},
            "funding_coverage": outputs["portfolio.json"]["funding_coverage"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--fast", action="store_true", help="fewer placebo and bootstrap draws (structure check only)")
    args = ap.parse_args()
    n_placebo, n_boot = (50, 200) if args.fast else (PLACEBO_DRAWS, BOOTSTRAP_DRAWS)
    t0 = time.time()
    ctx = prepare(lambda name: (ROOT / INPUTS[name]).read_bytes(), ROOT, 0.0)
    t_prepare = time.time() - t0
    rows, books = [], {name: {} for name in BOOK_KEYS}
    for day in sorted(ctx["frozen"], reverse=True):
        out = ctx["frozen_weeks"][day]
        rows += asset_rows(day, out["results"], ctx["by_day"][day])
        for name, key in BOOK_KEYS.items():
            books[name][pd.Timestamp(day, tz="UTC")] = out["portfolio"][key]
    fridays = [pd.Timestamp(day, tz="UTC") for day in sorted(ctx["frozen"])]
    symbols = sorted({r["symbol"] for r in rows})
    t0 = time.time()
    real = forward_returns(symbols, fridays, klines_dir=ctx["klines_dir"])           # structure only, values replaced below
    funding = realized_funding(symbols, fridays, funding_dir=ctx["funding_dir"])
    t_sources = time.time() - t0
    settlements = funding["n_settlements"].value_counts().sort_index().to_dict()
    funding = funding.assign(funding_week=1e-4 * funding["n_settlements"])            # synthetic: constant rate per settlement
    frame = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED)
    results = []
    for scenario in ("noise", "planted", "zero"):
        fwd = synthetic_returns(real, frame, scenario, rng)
        results.append(run_scenario(scenario, rows, books, fwd, funding, ctx, n_placebo, n_boot))
    newest = set(sorted(ctx["frozen"], reverse=True)[:3])
    few_rows = [r for r in rows if r["date"] in newest]
    few_books = {name: {d: w for d, w in book.items() if d.strftime("%Y-%m-%d") in newest} for name, book in books.items()}
    results.append(run_scenario("three_weeks_noise", few_rows, few_books, synthetic_returns(real, frame, "noise", rng), funding, ctx,
                                n_placebo, n_boot))
    del real
    report = {"outcomes": "SYNTHETIC (no real forward return or funding payment was joined with a forecast)",
              "placebo_draws": n_placebo, "bootstrap_draws": n_boot, "frozen_weeks": len(ctx["frozen"]), "rows": len(rows),
              "symbols": len(symbols), "seconds_prepare": round(t_prepare, 1), "seconds_return_and_funding_sources": round(t_sources, 1),
              "funding_rows": int(len(funding)), "funding_settlements_per_week_histogram": {str(k): int(v) for k, v in settlements.items()},
              "scenarios": results}
    text = json.dumps(report, indent=1, sort_keys=True, allow_nan=False) + "\n"
    print("SYNTHETIC OUTCOMES ONLY")
    print(text)
    if args.out:
        (ROOT / args.out).write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
