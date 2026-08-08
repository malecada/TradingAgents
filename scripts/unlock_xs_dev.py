"""unlock_xs_t1 dev runner: probes P0-P2 (STOP semantics) then the frozen grid.

Probes run to completion first and STOP the experiment on failure (exit 2 +
probes.json), so a broken data path cannot reach a publishable number.
Registered in data/rebuild/gates.json under unlock_xs_t1; this file must not
introduce any config not in that grid.

Placebo, DSR, and gate machinery are imported from scripts/value_xs_dev.py
verbatim so the two halves of lead #7 share byte-identical statistics.

P0 operationalization (concrete thresholds chosen before any probe or return
was computed; the gate registers the criterion "systematic divergence growing
toward the present = silent restatement = STOP" without numbers):

- comparable name: reconstructed and reference supply overlap >= 180 days;
- divergence growth g = median|log(recon/ref)| over the last 90 overlap days
  minus the same over the first 90 overlap days (a STABLE level offset is a
  definitional mismatch, not a restatement; growth is the discriminator);
- a name is flagged if g > 0.25;
- P0 FAILS if flagged share > 25% of comparable names, or the median g
  across comparable names exceeds 0.10, or fewer than 30 names are
  comparable (a vacuous P0 must not silently pass).
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.value_xs_dev import (  # noqa: E402  — shared frozen machinery
    GRID_GATE, circular_shift_columns, dsr_or_nan, gate_config,
    rank_shuffle_columns, run_config, unique_config_hashes,
)
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.xsect.ls_common import sharpe_365  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402
from tradingagents.xsect.unlock_xs import (  # noqa: E402
    amendment_exposure, build_matrices, load_events, mcap_control_signal,
    supply_frame,
)
from tradingagents.xsect.value_xs import (  # noqa: E402
    control_signal, membership_mask, simple_returns,
)
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EMISSIONS_DIR = ROOT / "data" / "xsect" / "emissions"
EMISSIONS_VINTAGE = ROOT / "data" / "xsect" / "emissions_vintage.json"
KLINES_DIR = ROOT / "data" / "xsect" / "klines"
UNIV_FILE = ROOT / "data" / "xsect" / "unlock_xs_universe.json"
MAP_FILE = ROOT / "data" / "xsect" / "unlock_xs_slug_map.json"
REFS_DIR = ROOT / "data" / "xsect" / "unlock_p0_refs"
REFS_STAMP = ROOT / "data" / "xsect" / "unlock_p0_refs_vintage.json"
OUT_DIR = ROOT / "data" / "rebuild" / "unlock_xs"

DEV = ("2021-01-01", "2025-03-31")
WARMUP_START = "2020-06-01"     # 30d control windows warm up before DEV[0]
MAX_LOAD_END = "2025-03-31"     # holdout starts 2025-04-01; never load past this
MIN_MEDIAN_BREADTH = 20
LEG_FRAC = {"decile": 0.1}
GRID = [(14, "decile"), (30, "decile")]   # lookahead_days x breadth — frozen
REGISTERED_N_CANDIDATES = 129   # gates.json value, recorded 2026-07-30

P0_MIN_OVERLAP_DAYS = 180
P0_WINDOW_DAYS = 90
P0_FLAG_GROWTH = 0.25
P0_MAX_FLAG_SHARE = 0.25
P0_MAX_MEDIAN_GROWTH = 0.10
P0_MIN_COMPARABLE = 30

P2_MIN_CLIFF_PCT = 0.01
P2_FWD_DAYS = 14


def _load_all():
    universe = json.loads(UNIV_FILE.read_text())
    slug_map = json.loads(MAP_FILE.read_text())
    symbols = sorted({s for v in universe.values() for s in v})
    days = pd.date_range(WARMUP_START, MAX_LOAD_END, freq="D", tz="UTC")
    klines = {s: d.loc[:MAX_LOAD_END] for s, d in load_klines(KLINES_DIR).items()
              if s in symbols}
    max_load_end_ts = pd.Timestamp(MAX_LOAD_END, tz="UTC")
    assert all(d.index.max() <= max_load_end_ts for d in klines.values() if len(d)), (
        "a klines frame exceeds MAX_LOAD_END after truncation -- the sealed "
        "holdout boundary must never be crossed, even in memory"
    )
    active_map = {slug: sym for slug, sym in slug_map.items() if sym in symbols}
    mats = build_matrices(EMISSIONS_DIR, active_map, days,
                          lookaheads=tuple(la for la, _ in GRID))
    return days, klines, universe, symbols, active_map, mats


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def _divergence_growth(recon: pd.Series, ref: pd.Series) -> dict | None:
    j = pd.concat([recon.rename("a"), ref.rename("b")], axis=1).dropna()
    j = j[(j["a"] > 0) & (j["b"] > 0)]
    if len(j) < P0_MIN_OVERLAP_DAYS:
        return None
    r = np.log(j["a"] / j["b"]).abs()
    first = float(r.iloc[:P0_WINDOW_DAYS].median())
    last = float(r.iloc[-P0_WINDOW_DAYS:].median())
    return {"overlap_days": int(len(j)), "median_absdiv_first": first,
            "median_absdiv_last": last, "growth": last - first}


def probe_p0_restatement(active_map: dict) -> dict:
    """Reconstructed supply vs the independent reference store (offline).

    The reconstruction is replayed on a full-span index reaching the
    reference stores' present frontier, purely for this comparison —
    restatement is a present-frontier property, and nothing derived from
    this frame enters a signal or portfolio computation.
    """
    if not EMISSIONS_VINTAGE.exists() or not REFS_STAMP.exists():
        return {"probe": "P0_silent_restatement", "pass": False,
                "error": "missing vintage stamp",
                "note": "emissions_vintage.json and unlock_p0_refs_vintage.json "
                        "must exist before P0 can run (offline contract)"}
    ev = json.loads(EMISSIONS_VINTAGE.read_text())
    refs_stamp = json.loads(REFS_STAMP.read_text())
    frontier = (pd.Timestamp(refs_stamp["fetched_utc"]).tz_convert("UTC")
                .normalize().tz_localize(None))
    p0_days = pd.date_range(WARMUP_START, frontier, freq="D", tz="UTC")
    supply_full = supply_frame(EMISSIONS_DIR, active_map, p0_days)

    per_name, no_ref = {}, []
    for sym in supply_full.columns:
        p = REFS_DIR / f"{sym}.parquet"
        if not p.exists():
            no_ref.append(sym)
            continue
        ref = pd.read_parquet(p)["ref_supply"]
        recon = supply_full[sym]
        d = _divergence_growth(recon, ref)
        if d is None:
            no_ref.append(sym)
            continue
        d["source"] = refs_stamp["sources"].get(sym, {}).get("source", "?")
        d["flag"] = bool(d["growth"] > P0_FLAG_GROWTH)
        per_name[sym] = d

    n = len(per_name)
    flagged = [s for s, d in per_name.items() if d["flag"]]
    med_growth = (float(statistics.median(d["growth"] for d in per_name.values()))
                  if n else float("nan"))
    checks = {
        "min_comparable": n >= P0_MIN_COMPARABLE,
        "flag_share": (len(flagged) / n <= P0_MAX_FLAG_SHARE) if n else False,
        "median_growth": (med_growth <= P0_MAX_MEDIAN_GROWTH) if n else False,
    }
    return {"probe": "P0_silent_restatement",
            "emissions_fetched_utc": ev["fetched_utc"],
            "refs_fetched_utc": refs_stamp["fetched_utc"],
            "n_comparable": n, "n_no_reference": len(no_ref),
            "no_reference_symbols": sorted(no_ref),
            "n_flagged": len(flagged), "flagged_symbols": sorted(flagged),
            "median_growth": med_growth,
            "thresholds": {"min_overlap_days": P0_MIN_OVERLAP_DAYS,
                           "window_days": P0_WINDOW_DAYS,
                           "flag_growth": P0_FLAG_GROWTH,
                           "max_flag_share": P0_MAX_FLAG_SHARE,
                           "max_median_growth": P0_MAX_MEDIAN_GROWTH,
                           "min_comparable": P0_MIN_COMPARABLE},
            "checks": checks, "per_name": per_name,
            "coingecko_truncation_note": refs_stamp.get(
                "coingecko_public_tier_note"),
            "pass": all(checks.values())}


def probe_p1_breadth(universe: dict, days: pd.DatetimeIndex, symbols,
                     mats: dict) -> dict:
    """Gated on monthly universe breadth (registered floor 20, per year).

    Signal-valid breadth (universe ∩ non-NaN burden) is reported per
    lookahead — not gated, house precedent value_xs_t1.
    """
    sizes = {m: len(v) for m, v in universe.items()}
    by_year: dict[str, list[int]] = {}
    for m, nsize in sizes.items():
        by_year.setdefault(m[:4], []).append(nsize)
    med = statistics.median(sizes.values())
    breadth_by_year = {y: statistics.median(v) for y, v in sorted(by_year.items())}

    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    M = membership_mask(days, symbols, universe)
    median_signal_valid, min_signal_valid = {}, {}
    for la, _ in GRID:
        S = mats["burden"][la].reindex(columns=list(symbols))
        sv = (M.loc[dev] & S.loc[dev].notna()).sum(axis=1)
        median_signal_valid[f"lookahead_{la}"] = float(sv.median())
        min_signal_valid[f"lookahead_{la}"] = float(sv.min())

    first_two_below = all(
        breadth_by_year.get(y, 0) < MIN_MEDIAN_BREADTH for y in ("2021", "2022"))
    return {"probe": "P1_breadth", "median_breadth": med,
            "min_breadth": min(sizes.values()),
            "breadth_by_year": breadth_by_year,
            "median_signal_valid_breadth": median_signal_valid,
            "min_signal_valid_breadth": min_signal_valid,
            "registered_n_candidates": REGISTERED_N_CANDIDATES,
            "realized_n_candidates": len(json.loads(MAP_FILE.read_text())),
            "candidate_delta_note": ("the registered recipe is the "
                                     "intersection itself; the protocol list "
                                     "and CoinGecko mapping grew between "
                                     "registration (129) and execution"),
            "dev_truncation_triggered": bool(first_two_below),
            "floor": MIN_MEDIAN_BREADTH,
            "pass": bool(med >= MIN_MEDIAN_BREADTH)}


def probe_p2_event_study(mats: dict, klines: dict, days: pd.DatetimeIndex,
                         symbols) -> dict:
    """Cliff unlocks >= 1% of supply must carry the negative forward sign."""
    dev_lo = pd.Timestamp(DEV[0], tz="UTC")
    dev_hi = pd.Timestamp(DEV[1], tz="UTC") - pd.Timedelta(days=P2_FWD_DAYS)
    rets, rows = [], []
    for sym in symbols:
        cl = mats["cliffs"].get(sym)
        df = klines.get(sym)
        if cl is None or cl.empty or df is None or df.empty:
            continue
        supply = mats["supply"][sym]
        close = df["close"]
        for _, row in cl.iterrows():
            t = row["date"]
            if not (dev_lo <= t <= dev_hi):
                continue
            sup = supply.get(t, np.nan)
            if not np.isfinite(sup) or sup <= 0:
                continue
            pct = row["amount"] / sup
            if pct < P2_MIN_CLIFF_PCT:
                continue
            if t not in close.index:
                continue
            fwd_idx = close.loc[t:t + pd.Timedelta(days=P2_FWD_DAYS)]
            if len(fwd_idx) < P2_FWD_DAYS + 1:
                continue    # incomplete forward window (gap/delist)
            fwd_ret = float(fwd_idx.iloc[-1] / fwd_idx.iloc[0] - 1.0)
            rets.append(fwd_ret)
            rows.append({"symbol": sym, "date": str(t.date()),
                         "pct_of_supply": float(pct), "fwd_ret": fwd_ret})
    n = len(rets)
    mean_ret = float(np.mean(rets)) if n else float("nan")
    tstat = (float(np.mean(rets) / (np.std(rets, ddof=1) / np.sqrt(n)))
             if n > 2 and np.std(rets, ddof=1) > 0 else float("nan"))
    by_year: dict[str, int] = {}
    for r in rows:
        by_year[r["date"][:4]] = by_year.get(r["date"][:4], 0) + 1
    return {"probe": "P2_event_study", "n_events": n,
            "events_by_year": dict(sorted(by_year.items())),
            "min_cliff_pct": P2_MIN_CLIFF_PCT, "fwd_days": P2_FWD_DAYS,
            "mean_fwd_ret": mean_ret,
            "median_fwd_ret": float(np.median(rets)) if n else float("nan"),
            "tstat_informational": tstat,
            "events": rows,
            "pass": bool(n > 0 and mean_ret < 0.0)}


def verdict_from_probes(p0: dict, p1: dict, p2: dict) -> str:
    return ("CONTINUE" if all(p.get("pass") for p in (p0, p1, p2))
            else "NEGATIVE-at-probe")


# ---------------------------------------------------------------------------
# Grid (frozen: 2 cells)
# ---------------------------------------------------------------------------

N_PLACEBO = 500


def run_grid(days, klines, universe, symbols, active_map, mats,
             n_placebo: int = N_PLACEBO, log: bool = True) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(klines, days, symbols).loc[dev]
    M = membership_mask(days, symbols, universe).loc[dev]

    controls = {}
    C1 = control_signal(klines, days, symbols, "vol").loc[dev]
    controls["vol"] = sharpe_365(run_config(C1, R, M & C1.notna(),
                                            LEG_FRAC["decile"]))
    supply = mats["supply"].reindex(columns=list(symbols))
    C2 = mcap_control_signal(klines, supply, days).loc[dev]
    controls["mcap"] = sharpe_365(run_config(C2, R, M & C2.notna(),
                                             LEG_FRAC["decile"]))

    amend = {}
    for slug, sym in sorted(active_map.items()):
        amend[sym] = amendment_exposure(load_events(EMISSIONS_DIR, slug),
                                        pd.Timestamp(DEV[0], tz="UTC"),
                                        pd.Timestamp(DEV[1], tz="UTC"))
    total_mass = sum(a["dev_unlock_mass"] for a in amend.values())
    amended_mass = sum(a["amended_mass_abs"] for a in amend.values())

    ledger_before = unique_config_hashes()
    rng = np.random.default_rng(20260808)
    results = []
    for lookahead, breadth in GRID:
        S = mats["burden"][lookahead].reindex(columns=list(symbols)).loc[dev]
        valid = M & S.notna()
        leg = LEG_FRAC[breadth]
        port = run_config(S, R, valid, leg)
        net_sr = sharpe_365(port)

        srs_a = [sharpe_365(run_config(circular_shift_columns(S, rng), R, valid, leg))
                 for _ in range(n_placebo)]
        srs_b = [sharpe_365(run_config(rank_shuffle_columns(S, rng), R, valid, leg))
                 for _ in range(n_placebo)]
        p_a = rank_placebo_pvalue(net_sr, srs_a)
        p_b = rank_placebo_pvalue(net_sr, srs_b)
        p_worse = max(p_a, p_b)

        dsr_own = dsr_or_nan(port, n_trials=len(GRID))
        dsr_ledger = dsr_or_nan(port, n_trials=ledger_before + len(GRID))
        d_c1 = net_sr - controls["vol"]
        d_c2 = net_sr - controls["mcap"]
        gate = gate_config(net_sr, p_worse, dsr_own, d_c1, d_c2)

        cfg = {"lookahead_days": lookahead, "breadth": breadth,
               "leg_frac": leg, "lag_days": 0, "cost_bps": 10.0,
               "rebalance": "weekly_monday",
               "universe": "unlock_xs_universe.json",
               "n_symbols": int(len(symbols))}
        metrics = {"net_sr": net_sr, "maxdd": float(maxdd(port)),
                   "n_bars": int(len(port)),
                   "placebo_p_shiftfam": p_a, "placebo_p_randfam": p_b,
                   "placebo_p_worse": p_worse,
                   "dsr_own_n": dsr_own, "dsr_own_n_trials": len(GRID),
                   "dsr_ledger_n": dsr_ledger,
                   "dsr_ledger_n_trials": ledger_before + len(GRID),
                   "sr_control_vol": controls["vol"],
                   "sr_control_mcap": controls["mcap"],
                   "delta_sr_vs_c1": d_c1, "delta_sr_vs_c2": d_c2,
                   **{f"gate_{k}": v for k, v in gate["checks"].items()},
                   "gate_pass": gate["pass"]}
        if log:
            log_trial("unlock_xs_t1", cfg, DEV, metrics)
        results.append({"config": cfg, "metrics": metrics})
        print(f"lookahead={lookahead}/{breadth}: SR {net_sr:+.3f} p {p_worse:.4f} "
              f"DSR {dsr_own:.3f} dC1 {d_c1:+.3f} dC2 {d_c2:+.3f} "
              f"{'PASS' if gate['pass'] else 'FAIL'}")

    passing = [r for r in results if r["metrics"]["gate_pass"]]
    out = {"experiment": "unlock_xs_t1", "controls": controls,
           "gate": GRID_GATE,
           "dev_window_used": list(DEV),
           "c1_lag_note": ("C1 vol control inherits value_xs's lag_days=2 "
                           "(CoinMetrics t-2 convention) while the burden "
                           "signal and C2 run at lag 0 — the unlock schedule "
                           "is ex-ante knowable, so it has no publication "
                           "lag; 30d realized-vol ranks are ~invariant over "
                           "2 days, so the asymmetry is disclosed, not "
                           "material"),
           "ledger_unique_hashes_before": ledger_before,
           "amendment_exposure": {
               "dev_unlock_mass_total": total_mass,
               "amended_mass_abs_total": amended_mass,
               "amended_share": (amended_mass / total_mass) if total_mass else 0.0,
               "note": "reported_not_gated; first-linear-rate counterfactual "
                       "proxy, see unlock_xs.amendment_exposure"},
           "results": results, "n_pass": len(passing),
           "verdict": "GO-at-dev" if passing else "NEGATIVE"}
    (OUT_DIR / "grid.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"VERDICT: {out['verdict']} ({len(passing)}/{len(GRID)})")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    days, klines, universe, symbols, active_map, mats = _load_all()
    p0 = probe_p0_restatement(active_map)
    p1 = probe_p1_breadth(universe, days, symbols, mats)
    p2 = probe_p2_event_study(mats, klines, days, symbols)
    verdict = verdict_from_probes(p0, p1, p2)
    out = {"experiment": "unlock_xs_t1", "probes": [p0, p1, p2],
           "verdict": verdict}
    (OUT_DIR / "probes.json").write_text(json.dumps(out, indent=1, default=str))
    for p in (p0, p1, p2):
        keys = {k: v for k, v in p.items()
                if k not in ("per_name", "events", "no_reference_symbols")}
        print(f"{p['probe']}: {'PASS' if p['pass'] else 'FAIL'}  {keys}")
    print(f"VERDICT: {verdict}")
    if verdict != "CONTINUE":
        sys.exit(2)
    # Registered breadth contingency (gates.json universe.breadth_stop): if
    # the first two dev years fall below the floor, the dev window truncates
    # forward — already logged in probes.json before the grid runs.
    global DEV
    if p1.get("dev_truncation_triggered"):
        DEV = ("2023-01-01", DEV[1])
        print(f"DEV WINDOW TRUNCATED per registration: {DEV}")
    run_grid(days, klines, universe, symbols, active_map, mats)


if __name__ == "__main__":
    main()
