"""P1 dev grid: 12 pre-registered configs vs EW-universe benchmark. Ledger: xs_mom_p1.

Performance note: the reference mechanics engine `run_weekly_portfolio()` in
tradingagents/xsect/portfolio.py recomputes per-symbol log-returns and the
full day-index union on every call, then walks day-by-day using pandas
label lookups — fine for a single run, far too slow for 12 configs x 500
placebos = 6000+ portfolio evaluations (~1-7s per call observed => hours).

This script therefore builds a local vectorized engine (`_fast_portfolio`)
that implements the *identical* documented mechanics (weekly EW rebalancing,
t+1 return application, turnover costs charged on the first accrual day
after rebalance, missing-kline members contribute 0) over precomputed numpy
arrays. It does NOT alter tradingagents/xsect/portfolio.py. Correctness is
verified at runtime (Step "validate") by diffing the fast engine's benchmark
series against the reference `run_weekly_portfolio()` output bar-for-bar
before any grid results are trusted; a mismatch aborts the run as BLOCKED.

Eligibility and momentum scores are also precomputed once per (t) and per
(t, L, skip) respectively (6 unique L/skip combos), shared across K and
across all 500 placebo draws per combo — they do not depend on K or on the
placebo permutation itself, only the ranking/shuffling built on top of them
does.
"""
import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.portfolio import (  # noqa: E402
    maxdd, momentum_scores, paired_bootstrap, rank_placebo_pvalue,
    run_weekly_portfolio, sr,
)
from tradingagents.xsect.universe import eligibility, load_klines, weekly_rebalance_dates  # noqa: E402

DEV = ("2021-01-01", "2025-03-31")
GRID = list(product([7, 14, 28], [0, 1], [10, 20]))  # L, skip, K — frozen, 12 configs
GATE = {"net_sr_min": 0.8, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85,
        "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/xs_mom")
N_PLACEBO = 500
COST_BPS = 10.0
KLINE_DIR = Path("data/xsect/klines")


def _unique_config_hashes(ledger_path: Path = DEFAULT_LEDGER) -> int:
    """Count UNIQUE config_hash rows across ALL experiments in the ledger
    (house convention for DSR n_trials — see scripts/exp_sizing_ablation.py
    ``_unique_config_hashes``, reproduced here to avoid importing a script
    module)."""
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
    never sees a non-finite float (a prior program shipped bare-NaN JSON)."""
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
        json.dump(payload, f, indent=1, allow_nan=False)
    print(f"\nBLOCKED: {reason}")
    print(json.dumps(_sanitize(diagnostics), indent=1))


# ── Fast vectorized portfolio engine (mechanics-identical to portfolio.py) ──

def _build_fast_arrays(klines: dict):
    all_days = pd.DatetimeIndex(sorted(set().union(*[df.index for df in klines.values()])))
    day_pos = {d: i for i, d in enumerate(all_days)}
    sym_list = sorted(klines)
    sym_idx = {s: j for j, s in enumerate(sym_list)}
    n_days, n_syms = len(all_days), len(sym_list)
    R = np.full((n_days, n_syms), np.nan)
    for s, j in sym_idx.items():
        raw = np.log(klines[s]["close"]).diff()  # identical to portfolio.py's logret[s]
        R[:, j] = raw.reindex(all_days).to_numpy()
    return all_days, day_pos, R, sym_idx


def _fast_portfolio(members_by_t: dict, reb_dates, all_days, day_pos, R, sym_idx,
                     cost_bps: float = COST_BPS) -> pd.Series:
    """Vectorized reimplementation of tradingagents.xsect.portfolio.run_weekly_portfolio.

    Same mechanics: EW over members_by_t[t] takes effect the day AFTER
    rebalance date t (positions pos_t+1 .. pos_{t+1} inclusive of the next
    rebalance day, which still books its return with the OLD weights before
    switching); turnover cost is charged once, on the first accrual day
    after each rebalance; a missing kline for a member on a given day
    contributes 0 to that day's return (weight not redistributed).
    """
    n_days = len(all_days)
    ret = np.zeros(n_days)
    events = sorted((day_pos[t], t) for t in reb_dates if t in day_pos)
    weights: dict = {}
    for i, (pos, date) in enumerate(events):
        members = members_by_t.get(date, [])
        new_w = {s: 1.0 / len(members) for s in members} if members else {}
        keys = set(new_w) | set(weights)
        turnover = sum(abs(new_w.get(k, 0.0) - weights.get(k, 0.0)) for k in keys)
        cost = cost_bps / 1e4 * turnover
        start = pos + 1
        end = events[i + 1][0] if i + 1 < len(events) else n_days - 1
        if start <= end and new_w:
            idxs = [sym_idx[s] for s in new_w]
            warr = np.array([new_w[s] for s in new_w])
            block = np.nan_to_num(R[start:end + 1, idxs], nan=0.0)
            ret[start:end + 1] = block @ warr
        if start < n_days:
            ret[start] -= cost
        weights = new_w
    port = pd.Series(ret, index=all_days)
    start_date = reb_dates[0] if len(reb_dates) else all_days[0]
    return port.loc[port.index > start_date]


def main() -> None:
    t_start = time.time()
    klines = load_klines(KLINE_DIR)
    reb = weekly_rebalance_dates(*DEV)
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")

    all_days, day_pos, R, sym_idx = _build_fast_arrays(klines)
    print(f"[precompute] fast arrays: all_days={len(all_days)} symbols={len(sym_idx)} "
          f"nominal_rebalances={len(reb)} ({time.time() - t_start:.1f}s)")

    # ── Precompute #1: eligibility per rebalance date — shared by ALL configs ──
    t0 = time.time()
    elig_by_t = {t: eligibility(klines, t) for t in reb}
    n_elig = [len(v) for v in elig_by_t.values()]
    print(f"[precompute] eligibility x{len(reb)} dates done ({time.time() - t0:.1f}s); "
          f"n_elig min/median/max = {min(n_elig)}/{int(np.median(n_elig))}/{max(n_elig)}")

    # ── Sanity gate: eligibility >= 20 symbols on all 2021 Mondays ──
    y2021 = [t for t in reb if t.year == 2021]
    bad_2021 = [(str(t.date()), len(elig_by_t[t])) for t in y2021 if len(elig_by_t[t]) < 20]
    if bad_2021:
        _blocked(
            f"eligibility < 20 symbols on {len(bad_2021)}/{len(y2021)} 2021 Mondays",
            {"bad_2021_mondays": bad_2021[:20]},
        )
        return

    # ── Benchmark: EW full eligible universe (top_n=100 default), fast engine ──
    t0 = time.time()
    bench_series = _fast_portfolio(elig_by_t, reb, all_days, day_pos, R, sym_idx, COST_BPS).loc[:hi]
    bench_sr, bench_dd, bench_ndays = sr(bench_series), maxdd(bench_series), len(bench_series)
    print(f"[benchmark] SR={bench_sr:+.4f} maxdd={bench_dd:.4f} n_days={bench_ndays} "
          f"({time.time() - t0:.2f}s)")

    # ── Sanity gates on benchmark (frozen — no rule tweaks) ──
    problems = []
    if not (1450 <= bench_ndays <= 1550):
        problems.append(f"benchmark n_days={bench_ndays} outside 1500+/-50")
    if not (-1.5 < bench_sr < 2.0):
        problems.append(f"benchmark SR={bench_sr:.4f} outside (-1.5, 2.0)")
    if problems:
        _blocked("; ".join(problems), {"bench_sr": bench_sr, "bench_ndays": bench_ndays})
        return

    # ── Correctness gate: fast engine vs reference run_weekly_portfolio on benchmark ──
    t0 = time.time()
    ref_bench = run_weekly_portfolio(klines, reb, lambda t: elig_by_t[t], cost_bps=COST_BPS).loc[:hi]
    j = pd.concat([bench_series, ref_bench], axis=1, join="outer")
    max_abs_diff = float((j.iloc[:, 0] - j.iloc[:, 1]).abs().max())
    print(f"[validate] fast engine vs reference run_weekly_portfolio (benchmark): "
          f"max_abs_diff={max_abs_diff:.3e}, ref_ndays={len(ref_bench)} "
          f"fast_ndays={len(bench_series)} ({time.time() - t0:.1f}s)")
    if max_abs_diff > 1e-8 or len(ref_bench) != len(bench_series):
        _blocked(
            f"fast engine diverges from reference mechanics: max_abs_diff={max_abs_diff:.3e}",
            {"ref_ndays": len(ref_bench), "fast_ndays": len(bench_series)},
        )
        return

    # ── Precompute #2: momentum scores per (t, L, skip) — 6 combos, shared across K & placebos ──
    t0 = time.time()
    LSKIP = sorted({(L, skip) for L, skip, _ in GRID})
    scores_by_lskip = {
        (L, skip): {t: momentum_scores(klines, elig_by_t[t], t, L, skip) for t in reb}
        for L, skip in LSKIP
    }
    print(f"[precompute] momentum_scores x{len(LSKIP)} (L,skip) combos x {len(reb)} dates "
          f"done ({time.time() - t0:.1f}s)")

    # ── Grid: 12 configs, grouped by (L, skip) so placebo shuffles are shared across K ──
    results = []
    series_by_cfg = {}  # (L, skip, K) -> daily log-return series, cached for the DSR pass below
    for L, skip in LSKIP:
        t_cfg = time.time()
        scores_t = scores_by_lskip[(L, skip)]
        scored_syms_by_t = {t: list(scores_t[t]) for t in reb}

        real_members = {
            K: {t: [s for s, _ in sorted(scores_t[t].items(), key=lambda kv: -kv[1])[:K]] for t in reb}
            for K in (10, 20)
        }
        real_series = {
            K: _fast_portfolio(real_members[K], reb, all_days, day_pos, R, sym_idx, COST_BPS).loc[:hi]
            for K in (10, 20)
        }
        real_sr = {K: sr(real_series[K]) for K in (10, 20)}
        pb = {K: paired_bootstrap(real_series[K], bench_series) for K in (10, 20)}

        placebo_srs = {10: [], 20: []}
        for p in range(N_PLACEBO):
            rng = np.random.default_rng(seed=p)  # fresh per placebo index -> reproducible per p
            shuffled_by_t = {}
            for t in reb:
                syms = scored_syms_by_t[t].copy()
                rng.shuffle(syms)
                shuffled_by_t[t] = syms
            for K in (10, 20):
                pmembers = {t: shuffled_by_t[t][:K] for t in reb}
                pseries = _fast_portfolio(pmembers, reb, all_days, day_pos, R, sym_idx, COST_BPS).loc[:hi]
                placebo_srs[K].append(sr(pseries))

        for K in (10, 20):
            placebo_p = rank_placebo_pvalue(real_sr[K], placebo_srs[K])
            series = real_series[K]
            series_by_cfg[(L, skip, K)] = series
            n_days_cfg = len(series)
            if abs(n_days_cfg - bench_ndays) > 5:
                problems.append(
                    f"L={L} skip={skip} K={K}: n_days={n_days_cfg} vs benchmark={bench_ndays} "
                    f"(diff > 5)"
                )
            cfg = {"L": L, "skip": skip, "K": K, "cost_bps": COST_BPS, "top_n": 100, "min_mvol": 5e6}
            metrics = {
                "net_sr": real_sr[K], "maxdd": maxdd(series), "total_logret": float(series.sum()),
                "bench_sr": bench_sr, "delta_sr": pb[K]["delta_sr"], "p_pos": pb[K]["p_pos"],
                "placebo_p": placebo_p, "n_days": n_days_cfg,
            }
            log_trial("xs_mom_p1", cfg, DEV, metrics)
            results.append({"config": cfg, "metrics": metrics})
            print(f"L={L} skip={skip} K={K}: SR={real_sr[K]:+.3f} dSR={pb[K]['delta_sr']:+.3f} "
                  f"p_pos={pb[K]['p_pos']:.3f} placebo_p={placebo_p:.3f} n_days={n_days_cfg}")
        print(f"  [(L={L},skip={skip}) block done in {time.time() - t_cfg:.1f}s]")

    if problems:
        _blocked("; ".join(problems), {"partial_results": [r["metrics"] for r in results]})
        return

    # ── DSR: house recipe (scripts/exp_sizing_ablation.py:452-457), n_trials AFTER logging all 12 ──
    n_trials = _unique_config_hashes()
    for r in results:
        L, skip, K = r["config"]["L"], r["config"]["skip"], r["config"]["K"]
        cand = series_by_cfg[(L, skip, K)].values
        var_sr = variance_of_sr(cand)
        se_sr = float(np.sqrt(var_sr))
        sr_perbar = float(cand.mean() / cand.std(ddof=1)) if cand.std(ddof=1) > 0 else 0.0
        e_max = expected_max_sharpe(n_trials, var_sr)
        dsr = deflated_sharpe_ratio(sr_perbar, e_max, se_sr)
        r["metrics"]["dsr"] = dsr
        r["metrics"]["n_trials_at_eval"] = n_trials
        r["gate_pass"] = bool(
            r["metrics"]["net_sr"] >= GATE["net_sr_min"]
            and r["metrics"]["delta_sr"] > GATE["delta_sr_vs_benchmark_min"]
            and r["metrics"]["p_pos"] >= GATE["p_pos_min"]
            and r["metrics"]["placebo_p"] <= GATE["placebo_p_max"]
            and r["metrics"]["dsr"] >= GATE["dsr_min"]
        )

    passing = [r for r in results if r["gate_pass"]]
    selected = (
        max(passing, key=lambda r: (r["metrics"]["dsr"], -r["metrics"]["placebo_p"]))
        if passing else None
    )

    # sort results into GRID order for a stable, readable table
    order = {cfg: i for i, cfg in enumerate(GRID)}
    results.sort(key=lambda r: order[(r["config"]["L"], r["config"]["skip"], r["config"]["K"])])

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": {"sr": bench_sr, "maxdd": bench_dd, "n_days": bench_ndays},
        "results": results,
        "selected": selected,
        "n_trials_at_eval": n_trials,
        "validate_fast_engine_max_abs_diff": max_abs_diff,
        "total_runtime_sec": time.time() - t_start,
    }
    with open(OUT / "dev_results.json", "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)

    print(f"\nselected: {json.dumps(selected['config']) if selected else 'NONE'}")
    print(f"total runtime: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
