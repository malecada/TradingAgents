"""D1 dev grid: F&G sentiment-beta standalone middle-quintile portfolio.

gates.json fg_beta_d1: exactly 2 configs — (a) standalone (this script) and
(b) overlay wrapping the P1 dev-selected config. P1's dev grid
(data/rebuild/xs_mom/dev_results.json) selected NONE, so per the frozen
grid_desc ("if P1 selects NONE, only (a) runs") this script runs ONLY
variant (a).

Reuses the Task-4 (xs_mom_p1) fast vectorized portfolio engine
(`scripts.xs_mom_dev._fast_portfolio` / `_build_fast_arrays`) for speed — same
documented mechanics as `tradingagents.xsect.portfolio.run_weekly_portfolio`
(weekly EW rebalance, t+1 return application, turnover costs on the first
accrual day, missing-kline members contribute 0). Correctness is verified at
runtime by diffing the fast engine's THIS-CONFIG series against the reference
`run_weekly_portfolio()` bar-for-bar before results are trusted.

Benchmark: reuses the already-ledgered EW-full-eligible-universe benchmark
metrics from data/rebuild/xs_mom/dev_results.json (not recomputed as a
number), but paired_bootstrap needs the benchmark SERIES, so that series is
recomputed here with identical mechanics and its SR checked against the
committed value to 1e-6 before anything downstream is trusted.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.xs_mom_dev import _build_fast_arrays, _fast_portfolio  # noqa: E402
from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.fgbeta import (  # noqa: E402
    exclude_extreme_quintiles, fg_beta, fng_daily_series, middle_quintile,
)
from tradingagents.xsect.portfolio import (  # noqa: E402
    maxdd, paired_bootstrap, rank_placebo_pvalue, run_weekly_portfolio, sr,
)
from tradingagents.xsect.universe import eligibility, load_klines, weekly_rebalance_dates  # noqa: E402

DEV = ("2021-01-01", "2025-03-31")
GATE = {"net_sr_min": 0.8, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85,
        "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/fg_beta")
P1_RESULTS = Path("data/rebuild/xs_mom/dev_results.json")
N_PLACEBO = 500
COST_BPS = 10.0
KLINE_DIR = Path("data/xsect/klines")
FNG_PATH = Path("data/sentiment/fng/fng.parquet")
BETA_WINDOW = 90
BETA_MIN_OBS = 60


def _unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """Count UNIQUE config_hash rows across ALL experiments in the ledger
    (house convention for DSR n_trials — reproduced from scripts/xs_mom_dev.py
    to avoid importing a private helper by underscore name across modules)."""
    seen: set[str] = set()
    with open(ledger_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            seen.add(json.loads(line)["config_hash"])
    return len(seen)


def _sanitize(obj):
    """Recursively replace NaN/inf with None so json.dump(allow_nan=False)
    never sees a non-finite float."""
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def _blocked(reason: str, diagnostics: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = _sanitize({"blocked": True, "reason": reason, "diagnostics": diagnostics})
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(payload, f, indent=1, allow_nan=False, default=str)
    print(f"\nBLOCKED: {reason}")
    print(json.dumps(_sanitize(diagnostics), indent=1, default=str))


def main() -> None:
    t_start = time.time()

    # ── P1 winner check — frozen grid_desc: overlay (b) only if P1 selected a config ──
    p1 = json.loads(P1_RESULTS.read_text())
    p1_selected = p1.get("selected")
    print(f"[p1] selected: {p1_selected!r} -> "
          f"{'variant (b) would run' if p1_selected else 'variant (b) SKIPPED (P1 selected NONE)'}")

    klines = load_klines(KLINE_DIR)
    reb = weekly_rebalance_dates(*DEV)
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")

    all_days, day_pos, R, sym_idx = _build_fast_arrays(klines)
    print(f"[precompute] fast arrays: all_days={len(all_days)} symbols={len(sym_idx)} "
          f"nominal_rebalances={len(reb)} ({time.time() - t_start:.1f}s)")

    # ── Precompute #1: eligibility per rebalance date (same universe rule as P1) ──
    t0 = time.time()
    elig_by_t = {t: eligibility(klines, t) for t in reb}
    n_elig = [len(v) for v in elig_by_t.values()]
    print(f"[precompute] eligibility x{len(reb)} dates done ({time.time() - t0:.1f}s); "
          f"n_elig min/median/max = {min(n_elig)}/{int(np.median(n_elig))}/{max(n_elig)}")

    # ── Benchmark: recompute the SAME series as Task 4, check SR vs committed value ──
    t0 = time.time()
    bench_series = _fast_portfolio(elig_by_t, reb, all_days, day_pos, R, sym_idx, COST_BPS).loc[:hi]
    bench_sr, bench_dd, bench_ndays = sr(bench_series), maxdd(bench_series), len(bench_series)
    committed_bench = p1["benchmark"]
    bench_diff = abs(bench_sr - committed_bench["sr"])
    print(f"[benchmark] SR={bench_sr:+.6f} (committed {committed_bench['sr']:+.6f}, "
          f"diff={bench_diff:.2e}) maxdd={bench_dd:.4f} n_days={bench_ndays} "
          f"({time.time() - t0:.2f}s)")
    if bench_diff > 1e-6:
        _blocked(
            f"recomputed benchmark SR diverges from committed xs_mom_p1 benchmark by {bench_diff:.3e} (> 1e-6)",
            {"recomputed_sr": bench_sr, "committed_sr": committed_bench["sr"],
             "recomputed_ndays": bench_ndays, "committed_ndays": committed_bench["n_days"]},
        )
        return

    # ── F&G store + betas per rebalance date, over the eligible universe (shared, precomputed once) ──
    t0 = time.time()
    fng = fng_daily_series(FNG_PATH)
    betas_by_t = {t: fg_beta(klines, fng, elig_by_t[t], t, window=BETA_WINDOW, min_obs=BETA_MIN_OBS) for t in reb}
    n_scored = [len(v) for v in betas_by_t.values()]
    print(f"[precompute] fg_beta x{len(reb)} dates done ({time.time() - t0:.1f}s); "
          f"n_scored min/median/max = {min(n_scored)}/{int(np.median(n_scored))}/{max(n_scored)}")

    members_by_t = {t: middle_quintile(betas_by_t[t]) for t in reb}
    n_members = [len(v) for v in members_by_t.values()]
    n_zero_weeks = sum(1 for n in n_members if n == 0)
    print(f"[sanity] middle-quintile portfolio size per rebalance: "
          f"min={min(n_members)} median={int(np.median(n_members))} max={max(n_members)} "
          f"zero_weeks={n_zero_weeks}/{len(n_members)}")

    if int(np.median(n_members)) < 5 or n_zero_weeks > 0.1 * len(n_members):
        _blocked(
            f"middle-quintile portfolio too thin: median={int(np.median(n_members))} "
            f"(<5) or zero_weeks={n_zero_weeks}/{len(n_members)} (>10%) — "
            f"F&G coverage or beta coverage problem",
            {
                "n_members_min": min(n_members), "n_members_median": int(np.median(n_members)),
                "n_members_max": max(n_members), "zero_weeks": n_zero_weeks,
                "n_scored_min": min(n_scored), "n_scored_median": int(np.median(n_scored)),
                "n_scored_max": max(n_scored),
                "fng_coverage_start": str(fng.index.min()), "fng_coverage_end": str(fng.index.max()),
            },
        )
        return

    # ── Real portfolio (fast engine) ──
    t0 = time.time()
    real_series = _fast_portfolio(members_by_t, reb, all_days, day_pos, R, sym_idx, COST_BPS).loc[:hi]
    real_sr = sr(real_series)
    n_days_cfg = len(real_series)
    print(f"[portfolio] SR={real_sr:+.4f} maxdd={maxdd(real_series):.4f} n_days={n_days_cfg} "
          f"({time.time() - t0:.2f}s)")

    # ── Correctness gate: fast engine vs reference run_weekly_portfolio on THIS config ──
    t0 = time.time()
    ref_series = run_weekly_portfolio(klines, reb, lambda t: members_by_t[t], cost_bps=COST_BPS).loc[:hi]
    j = pd.concat([real_series, ref_series], axis=1, join="outer")
    max_abs_diff = float((j.iloc[:, 0] - j.iloc[:, 1]).abs().max())
    print(f"[validate] fast engine vs reference run_weekly_portfolio (this config): "
          f"max_abs_diff={max_abs_diff:.3e}, ref_ndays={len(ref_series)} "
          f"fast_ndays={n_days_cfg} ({time.time() - t0:.1f}s)")
    if max_abs_diff > 1e-8 or len(ref_series) != n_days_cfg:
        _blocked(
            f"fast engine diverges from reference mechanics: max_abs_diff={max_abs_diff:.3e}",
            {"ref_ndays": len(ref_series), "fast_ndays": n_days_cfg},
        )
        return

    if abs(n_days_cfg - bench_ndays) > 5:
        _blocked(
            f"config n_days={n_days_cfg} vs benchmark={bench_ndays} (diff > 5)",
            {"n_days_cfg": n_days_cfg, "bench_ndays": bench_ndays},
        )
        return

    pb = paired_bootstrap(real_series, bench_series)

    # ── Placebo: 500 within-rebalance draws, uniform sample of |members(t)| from the
    # beta-SCORED symbols at t (rank-permutation equivalent), same costs ──
    t0 = time.time()
    scored_syms_by_t = {t: list(betas_by_t[t]) for t in reb}
    placebo_srs = []
    for p in range(N_PLACEBO):
        rng = np.random.default_rng(seed=p)
        pmembers = {}
        for t in reb:
            syms = scored_syms_by_t[t]
            k = min(len(members_by_t[t]), len(syms))
            pmembers[t] = list(rng.choice(syms, size=k, replace=False)) if k else []
        pseries = _fast_portfolio(pmembers, reb, all_days, day_pos, R, sym_idx, COST_BPS).loc[:hi]
        placebo_srs.append(sr(pseries))
    placebo_p = rank_placebo_pvalue(real_sr, placebo_srs)
    print(f"[placebo] N={N_PLACEBO} placebo_p={placebo_p:.4f} "
          f"({time.time() - t0:.1f}s)")

    cfg = {
        "variant": "a_standalone", "beta_window": BETA_WINDOW, "beta_min_obs": BETA_MIN_OBS,
        "cost_bps": COST_BPS, "top_n": 100, "min_mvol": 5e6,
    }
    metrics = {
        "net_sr": real_sr, "maxdd": maxdd(real_series), "total_logret": float(real_series.sum()),
        "bench_sr": bench_sr, "delta_sr": pb["delta_sr"], "p_pos": pb["p_pos"],
        "placebo_p": placebo_p, "n_days": n_days_cfg,
    }
    log_trial("fg_beta_d1", cfg, DEV, metrics)

    # ── DSR: house recipe (scripts/xs_mom_dev.py), n_trials AFTER logging this trial ──
    n_trials = _unique_config_hashes()
    var_sr = variance_of_sr(real_series.values)
    se_sr = float(np.sqrt(var_sr))
    sr_perbar = float(real_series.values.mean() / real_series.values.std(ddof=1)) if real_series.values.std(ddof=1) > 0 else 0.0
    e_max = expected_max_sharpe(n_trials, var_sr)
    dsr = deflated_sharpe_ratio(sr_perbar, e_max, se_sr)
    metrics["dsr"] = dsr
    metrics["n_trials_at_eval"] = n_trials

    gate = {
        "net_sr_ge_0.8": bool(metrics["net_sr"] >= GATE["net_sr_min"]),
        "delta_sr_gt_0": bool(metrics["delta_sr"] > GATE["delta_sr_vs_benchmark_min"]),
        "p_pos_ge_0.85": bool(metrics["p_pos"] >= GATE["p_pos_min"]),
        "placebo_p_le_0.05": bool(metrics["placebo_p"] <= GATE["placebo_p_max"]),
        "dsr_ge_0.9": bool(metrics["dsr"] >= GATE["dsr_min"]),
    }
    gate_pass = all(gate.values())
    selected = cfg if gate_pass else None

    print(f"\n[result] net_sr={metrics['net_sr']:+.4f} delta_sr={metrics['delta_sr']:+.4f} "
          f"p_pos={metrics['p_pos']:.4f} placebo_p={metrics['placebo_p']:.4f} dsr={metrics['dsr']:.4f}")
    print(f"[gate] {gate} -> {'PASS' if gate_pass else 'FAIL'}")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": committed_bench,
        "benchmark_recheck": {"recomputed_sr": bench_sr, "diff_vs_committed": bench_diff},
        "config": cfg,
        "metrics": metrics,
        "gate": gate,
        "gate_pass": gate_pass,
        "selected": selected,
        "variant_b_skipped": "P1 selected NONE",
        "portfolio_size_sanity": {
            "min": min(n_members), "median": int(np.median(n_members)), "max": max(n_members),
            "zero_weeks": n_zero_weeks, "n_weeks": len(n_members),
        },
        "n_trials_at_eval": n_trials,
        "validate_fast_engine_max_abs_diff": max_abs_diff,
        "total_runtime_sec": time.time() - t_start,
    }
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)

    print(f"\nselected: {json.dumps(selected) if selected else 'NONE'}")
    print(f"total runtime: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
