"""liq_fade_r1 forensics: verify the NEGATIVE-at-probe verdict rather than
restate it.

liq_fade_r1 froze the liq_fade_i1 (THESIS section 49) config exactly and
moved ONE axis -- the universe, from monthly-PIT top-50 to monthly-PIT ranks
51-150 (304 symbols, disjoint from i1 by (symbol, month)). Task 7 (the gated
primary run) was correctly SKIPPED per the plan's pre-registered decision
point: P3 (the vol-drift control) closed and P2 (the gross event-study floor)
failed on its own terms, so no `results.json` exists for this experiment and
`assert_probes_passed` would refuse a primary run anyway. Consequently there
is no gated Sharpe, no placebo distribution, and no ledger row to decompose --
most of the eleven-section battery specified for a PASS or gate-failure
outcome is moot here. This script implements the subset that outcome calls
for, all recomputed from the frozen 1h panel rather than read back from a
results file (there being no such file), plus one entirely new analysis (the
liquidity gradient) that the original spec commissioned as a descriptive
partition, not a gated config.

Sections implemented:
  power               -- events/year, events/symbol, SE of the mean event
                          return (F4 analog): is this a real negative or an
                          underpowered one.
  p3_control          -- primary vs vol-drift-control event counts and net
                          SRs, independently re-derived from the frozen
                          panel (F9 analog) -- the check i1's own forensics
                          left open, now closed on an independent universe.
  liquidity_gradient  -- band symbols split into "near-top50" (188 symbols
                          that were i1's top-50 in some OTHER PIT month) vs
                          "never-top50" (116 symbols never in the i1
                          universe at any point) -- new, not part of the
                          original F1-F11 list; the most informative
                          descriptive breakdown available for this outcome.
  per_symbol          -- fraction of band symbols with positive mean event
                          return; best/worst names (F10 analog); also
                          absorbs F2's concentration question (is the
                          negative driven by a handful of names, or broad).
  horizon             -- mean gross forward return at H in {1, 6, 24, 48}
                          on the SAME (thr=3.5) trigger set (new: the
                          original grid varied H as part of a gated sweep;
                          here it is a diagnostic over one frozen trigger
                          set, never gated).
  contrast            -- liq_fade_i1 vs liq_fade_r1 headline numbers,
                          side by side (F11 analog), read directly from
                          each experiment's own probes/ledger files.

Explicitly SKIPPED sections, named per the plan's anti-silent-omission rule:
  F1 inversion         -- inversion checks whether a PASSING signal's sign
                          is genuine (long beats short). The primary here
                          never reached a gate: it failed P2 (gross event
                          return below the +25bp floor) before G1-G3 were
                          ever evaluated. There is no positive result whose
                          sign needs verifying, and inverting a signal that
                          already loses gross only produces a mirror-image
                          number, not a falsification test.
  F3 yearly stability  -- yearly SR requires a realized, cost-and-rf-applied
                          daily net-return series from a primary run; Task 7
                          was skipped, so no such series exists. The `power`
                          section's events-per-year table covers the
                          adjacent question (is the sample thin in any
                          sub-period) using only the raw trigger data that
                          does exist.
  F5 DSR decomposition -- DSR discounts a GATE-EVALUATED Sharpe for search
                          multiplicity. No gate was evaluated (Task 7
                          skipped, no results.json, no ledger row), so there
                          is no Sharpe to deflate and no n_trials was spent.
  F6 cost curve        -- cost sensitivity is informative when a strategy is
                          marginal net of costs. This one is negative
                          GROSS, before any cost assumption enters (mean
                          event return -0.418% at zero cost) -- moving cost
                          bps up or down cannot rescue or further sink a
                          verdict already decided before costs are applied.
  F7 P2 reconciliation -- reconciles the P2 event-study mean against a
                          realized, compounded portfolio return series.
                          No such series exists (Task 7 skipped).
  F8 placebo audit     -- re-derives a registered placebo p-value. No
                          placebo was run: gates.json's P3 pass_rule routes
                          a probe failure straight to write-up without ever
                          touching the placebo machinery, so there is
                          nothing to independently verify.

Reads data/rebuild/liq_fade_r1/probes.json (the only rebuild artifact this
experiment produced) plus the frozen 1h panel via scripts/liq_fade_repl.py's
loaders, and data/rebuild/liq_fade/{probes,dev_results}.json plus
trial_ledger.jsonl for the i1 side of the contrast table. Writes
forensics.json (machine-readable) and forensics.md (prose) to
data/rebuild/liq_fade_r1/. tradingagents/xsect/liq_fade.py is imported
unchanged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import liq_fade_repl as lfr  # noqa: E402
from tradingagents.xsect.liq_fade import (  # noqa: E402
    cascade_triggers, event_weights_hourly, run_hourly_portfolio, sharpe_daily,
)

R1_DIR = PROJECT_ROOT / "data" / "rebuild" / "liq_fade_r1"
I1_DIR = PROJECT_ROOT / "data" / "rebuild" / "liq_fade"
LEDGER_PATH = PROJECT_ROOT / "data" / "rebuild" / "trial_ledger.jsonl"
OUT_JSON = R1_DIR / "forensics.json"
OUT_MD = R1_DIR / "forensics.md"

HORIZONS = (1, 6, 24, 48)   # matches i1's reported mean_fade_ret_{1,6,24}h + primary H=48


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(v) for v in obj]
    return obj


def _load_i1_thr35_h48():
    """Pull the i1 thr=3.5/H=48 headline numbers directly from its own
    committed artifacts (probes.json for the P2 event-study mean, the trial
    ledger for the gated net SR) rather than hardcoding them, so the
    contrast table cannot silently drift from the source-of-record files."""
    i1_probes = json.loads((I1_DIR / "probes.json").read_text())
    p2_cell = next(c for c in i1_probes["p2"]["grid"] if c["thr"] == 3.5 and c["H"] == 48)
    ledger_row = None
    with open(LEDGER_PATH) as f:
        for line in f:
            row = json.loads(line)
            if (row.get("experiment") == "liq_fade_i1"
                    and row["config"].get("thr") == 3.5 and row["config"].get("H") == 48):
                ledger_row = row
    if ledger_row is None:
        raise RuntimeError("no liq_fade_i1 thr=3.5/H=48 row found in trial_ledger.jsonl")
    return {
        "universe": "top-50 PIT monthly (799-symbol survivorship-safe store)",
        "cost_bps": ledger_row["config"]["cost_bps"],
        "n_events": p2_cell["n_events"],
        "n_events_with_full_forward_window": p2_cell["n_events_with_full_forward_window"],
        "gross_return_per_event": p2_cell["mean_fwd_ret"],
        "net_sr": ledger_row["metrics"]["net_sr"],
        "n_symbols_active": ledger_row["metrics"]["n_symbols_active"],
        "gate_outcome": "2/3 -- DSR 0.479 < 0.9 (0.881 at own n_trials=6); NEGATIVE, DSR-bound",
    }


def main() -> None:
    probes = json.loads((R1_DIR / "probes.json").read_text())
    p2, p3 = probes["p2"], probes["p3"]
    assert p3["verdict"] == "NEGATIVE" and probes["stop"], (
        "this script assumes the registered liq_fade_r1 probe failure; "
        "probes.json no longer matches the outcome this write-up describes")

    symbols = lfr.load_symbols_r1()
    universe = json.loads(lfr.UNIVERSE_FILE.read_text())
    close, qvol = lfr.load_hourly_panel(symbols)
    R = close.pct_change(fill_method=None)
    mask = lfr.membership_mask_hourly(universe, close.columns.tolist(), close.index)
    print(f"[panel] {len(close.columns)} symbols, {len(close)} bars")

    dev_lo = pd.Timestamp(lfr.DEV[0], tz="UTC")
    dev_hi = pd.Timestamp(lfr.DEV[1], tz="UTC") + pd.Timedelta(hours=23)

    # Reproduce probe_p2's exact row selection: masked triggers over the
    # FULL loaded index (which already ends at DEV[1]), gated to dev_lo only
    # on the lower bound -- boundary-truncated forward windows near DEV[1]
    # are what separates n_events (1892) from n_events_with_full_forward_window.
    row_sel_lo = np.asarray(close.index >= dev_lo)
    trig_all = cascade_triggers(close, qvol, thr=lfr.THR) & mask
    trig_dev = pd.DataFrame(trig_all.to_numpy() & row_sel_lo[:, None],
                            index=trig_all.index, columns=trig_all.columns)
    n_events_masked = int(trig_dev.to_numpy().sum())
    assert n_events_masked == p2["n_events"], (
        f"recomputed masked trigger count {n_events_masked} != probes.json "
        f"p2.n_events {p2['n_events']} -- panel or universe file drifted")

    # ── event-level table with symbol identity, at the primary H=48 ─────────
    fwd48 = R.rolling(lfr.H, min_periods=lfr.H).sum().shift(-lfr.H)
    T = trig_dev.to_numpy()
    F48 = fwd48.to_numpy()
    rows, cols = np.where(T)
    vals48 = F48[rows, cols]
    valid = ~np.isnan(vals48)
    rows_v, cols_v, vals48 = rows[valid], cols[valid], vals48[valid]
    ev_syms = np.array(trig_dev.columns)[cols_v]
    ev_dates = trig_dev.index[rows_v]
    events = pd.DataFrame({"date": ev_dates, "symbol": ev_syms, "fwd_ret": vals48})
    n_events_full_window = len(events)
    assert n_events_full_window == p2["n_events_with_full_forward_window"], (
        f"recomputed full-window event count {n_events_full_window} != probes.json "
        f"p2.n_events_with_full_forward_window {p2['n_events_with_full_forward_window']}")
    print(f"[verify] masked triggers={n_events_masked} full-window events="
          f"{n_events_full_window} (both match probes.json)")

    mean_ret = float(events["fwd_ret"].mean())
    assert abs(mean_ret - p2["mean_fwd_ret"]) < 1e-9, (
        f"recomputed mean fwd ret {mean_ret} != probes.json {p2['mean_fwd_ret']}")

    # ══════════════════════════════════════════════════════════════════════
    # POWER (F4 analog)
    # ══════════════════════════════════════════════════════════════════════
    years_spanned = (pd.Timestamp(lfr.DEV[1]) - pd.Timestamp(lfr.DEV[0])).days / 365.25
    events_per_year = n_events_masked / years_spanned
    n_band_symbols = len(close.columns)
    events_per_symbol = n_events_masked / n_band_symbols
    sd_ret = float(events["fwd_ret"].std(ddof=1))
    se_ret = sd_ret / np.sqrt(n_events_full_window)
    t_stat = mean_ret / se_ret
    ev_by_year = trig_dev.to_numpy().sum(axis=1)
    ev_year_series = pd.Series(ev_by_year, index=trig_dev.index)
    events_per_year_table = {str(yr): int(sl.sum())
                             for yr, sl in ev_year_series.groupby(ev_year_series.index.year)}
    power = {
        "n_events_masked": n_events_masked,
        "n_events_full_window": n_events_full_window,
        "n_band_symbols": n_band_symbols,
        "years_spanned": years_spanned,
        "events_per_year": events_per_year,
        "events_per_symbol": events_per_symbol,
        "events_per_year_table": events_per_year_table,
        "mean_fwd_ret": mean_ret,
        "sd_fwd_ret": sd_ret,
        "se_mean_fwd_ret": se_ret,
        "t_stat": t_stat,
        "distinguishable_from_zero_at_5pct": bool(abs(t_stat) > 1.96),
    }
    print(f"[power] {n_events_masked} events / {n_band_symbols} symbols over "
          f"{years_spanned:.2f}y = {events_per_year:.0f}/yr, "
          f"{events_per_symbol:.2f}/symbol; mean={mean_ret:+.4%} se={se_ret:.4%} "
          f"t={t_stat:.2f}")

    # ══════════════════════════════════════════════════════════════════════
    # P3 CONTROL DETAIL (F9 analog) -- independently re-derived
    # ══════════════════════════════════════════════════════════════════════
    row_sel_p3 = (close.index >= dev_lo) & (close.index <= dev_hi)

    def _sr(trig_full_local):
        trig_m = (trig_full_local & mask).loc[row_sel_p3]
        R_p3 = R.loc[row_sel_p3]
        active = trig_m.columns[trig_m.to_numpy().any(axis=0)].tolist()
        if not active:
            return 0.0, 0
        W = event_weights_hourly(trig_m[active], lfr.H, w_per=lfr.W_PER, cap=lfr.CAP)
        net = run_hourly_portfolio(W, R_p3[active], cost_bps=lfr.COST_BPS,
                                   rf_annual=lfr.RF_ANNUAL)
        return sharpe_daily(net), int(trig_m[active].to_numpy().sum())

    primary_sr, n_primary = _sr(cascade_triggers(close, qvol, thr=lfr.THR))
    control_sr, n_control = _sr(lfr.vol_only_triggers(qvol, lfr.THR))
    separation = primary_sr - control_sr
    assert abs(primary_sr - p3["primary_net_sr"]) < 1e-9, "primary SR recompute drifted from probes.json"
    assert abs(control_sr - p3["control_net_sr"]) < 1e-9, "control SR recompute drifted from probes.json"
    assert n_primary == p3["n_primary_events"] and n_control == p3["n_control_events"], \
        "P3 event counts recompute drifted from probes.json"
    p3_control = {
        "primary_net_sr": primary_sr, "control_net_sr": control_sr,
        "separation": separation, "n_primary_events": n_primary,
        "n_control_events": n_control,
        "control_max_net_sr": p3["control_max_net_sr"], "min_separation": p3["min_separation"],
        "verdict": p3["verdict"], "reason": p3["reason"],
        "reproduced_from_probes_json": True,
    }
    print(f"[p3_control] primary={primary_sr:+.4f} ({n_primary} ev) "
          f"control={control_sr:+.4f} ({n_control} ev) sep={separation:+.4f} "
          f"-- reproduces probes.json exactly")

    # ══════════════════════════════════════════════════════════════════════
    # LIQUIDITY GRADIENT (new)
    # ══════════════════════════════════════════════════════════════════════
    i1_universe = json.loads(lfr.I1_UNIVERSE_FILE.read_text())
    i1_union = {s for v in i1_universe.values() for s in v}
    band_symbols = set(close.columns)
    near_top50 = sorted(band_symbols & i1_union)
    never_top50 = sorted(band_symbols - i1_union)
    assert len(near_top50) + len(never_top50) == n_band_symbols

    def _partition_stats(names):
        """Mean/SE/t plus a single-symbol concentration check: the top
        contributor to the partition's total pp-sum and what the mean looks
        like with it excluded. A partition mean can be dominated by one
        catastrophic (or one outsized) symbol rather than reflecting a
        pattern shared across the partition -- this guards against reading
        such a case as a broad liquidity-gradient effect."""
        sub = events[events["symbol"].isin(names)]
        n = len(sub)
        if n == 0:
            return {"n_symbols_in_partition": len(names), "n_events": 0,
                    "mean_fwd_ret": None, "sd_fwd_ret": None, "se_mean_fwd_ret": None,
                    "t_stat": None}
        mean = float(sub["fwd_ret"].mean())
        sd = float(sub["fwd_ret"].std(ddof=1)) if n > 1 else None
        se = sd / np.sqrt(n) if sd is not None else None
        t = mean / se if se else None
        by_sym_sum = sub.groupby("symbol")["fwd_ret"].sum().sort_values()
        total_sum = float(by_sym_sum.sum())
        # top contributor by absolute pp-sum, in the direction of the partition mean
        top_sym = by_sym_sum.index[0] if mean < 0 else by_sym_sum.index[-1]
        top_sum = float(by_sym_sum.loc[top_sym])
        top_share = (top_sum / total_sum) if total_sum != 0 else None
        top_n_events = int((sub["symbol"] == top_sym).sum())
        excl = sub[sub["symbol"] != top_sym]
        excl_mean = float(excl["fwd_ret"].mean()) if len(excl) else None
        excl_sd = float(excl["fwd_ret"].std(ddof=1)) if len(excl) > 1 else None
        excl_se = excl_sd / np.sqrt(len(excl)) if excl_sd is not None else None
        excl_t = excl_mean / excl_se if excl_se else None
        return {
            "n_symbols_in_partition": len(names), "n_events": n,
            "mean_fwd_ret": mean, "sd_fwd_ret": sd, "se_mean_fwd_ret": se, "t_stat": t,
            "top_contributor_symbol": top_sym, "top_contributor_sum_pp": top_sum,
            "top_contributor_share_of_total_sum": top_share,
            "top_contributor_n_events": top_n_events,
            "n_events_excl_top_contributor": int(len(excl)),
            "mean_fwd_ret_excl_top_contributor": excl_mean,
            "t_stat_excl_top_contributor": excl_t,
        }

    near_stats = _partition_stats(near_top50)
    never_stats = _partition_stats(never_top50)
    liquidity_gradient = {"near_top50": near_stats, "never_top50": never_stats,
                         "near_top50_symbols_n": len(near_top50),
                         "never_top50_symbols_n": len(never_top50)}
    print(f"[liquidity_gradient] near-top50 ({len(near_top50)} syms): "
          f"{near_stats['n_events']} ev, mean={near_stats['mean_fwd_ret']:+.4%} "
          f"t={near_stats['t_stat']:.2f}, top contributor "
          f"{near_stats['top_contributor_symbol']} "
          f"({near_stats['top_contributor_share_of_total_sum']:.0%} of total sum) | "
          f"never-top50 ({len(never_top50)} syms): {never_stats['n_events']} ev, "
          f"mean={never_stats['mean_fwd_ret']:+.4%} t={never_stats['t_stat']:.2f}, "
          f"top contributor {never_stats['top_contributor_symbol']} "
          f"({never_stats['top_contributor_share_of_total_sum']:.0%} of total sum)")

    # ══════════════════════════════════════════════════════════════════════
    # PER-SYMBOL DISTRIBUTION (F10 analog, absorbs F2 concentration question)
    # ══════════════════════════════════════════════════════════════════════
    by_symbol = events.groupby("symbol")["fwd_ret"].agg(["mean", "count"]).sort_values("mean")
    n_symbols_with_events = len(by_symbol)
    n_positive = int((by_symbol["mean"] > 0).sum())
    frac_positive = n_positive / n_symbols_with_events
    worst = by_symbol.head(5)
    best = by_symbol.tail(5).iloc[::-1]
    per_symbol = {
        "n_symbols_with_events": n_symbols_with_events,
        "n_band_symbols_total": n_band_symbols,
        "n_positive_mean": n_positive,
        "frac_positive_mean": frac_positive,
        "worst5": [{"symbol": s, "mean_fwd_ret": float(r["mean"]), "n_events": int(r["count"])}
                   for s, r in worst.iterrows()],
        "best5": [{"symbol": s, "mean_fwd_ret": float(r["mean"]), "n_events": int(r["count"])}
                  for s, r in best.iterrows()],
    }
    print(f"[per_symbol] {n_positive}/{n_symbols_with_events} symbols with events have "
          f"positive mean fwd ret ({frac_positive:.1%}); worst={per_symbol['worst5'][0]}; "
          f"best={per_symbol['best5'][0]}")

    # ══════════════════════════════════════════════════════════════════════
    # HORIZON CHECK (new)
    # ══════════════════════════════════════════════════════════════════════
    horizon = {}
    for h in HORIZONS:
        vals_h = lfr.event_forward_sum(R, trig_dev, h)
        n_h = len(vals_h)
        mean_h = float(vals_h.mean()) if n_h else None
        se_h = float(vals_h.std(ddof=1) / np.sqrt(n_h)) if n_h > 1 else None
        horizon[str(h)] = {
            "n_events_with_full_window": int(n_h),
            "mean_gross_fwd_ret": mean_h,
            "se_gross_fwd_ret": se_h,
            "t_stat": (mean_h / se_h) if se_h else None,
        }
    all_negative = all(v["mean_gross_fwd_ret"] is not None and v["mean_gross_fwd_ret"] < 0
                       for v in horizon.values())
    horizon["all_horizons_negative"] = all_negative
    print(f"[horizon] " + " ".join(
        f"H={h}:{horizon[str(h)]['mean_gross_fwd_ret']:+.4%}(t={horizon[str(h)]['t_stat']:.2f})"
        for h in HORIZONS))

    # ══════════════════════════════════════════════════════════════════════
    # CONTRAST i1 vs r1 (F11 analog)
    # ══════════════════════════════════════════════════════════════════════
    i1 = _load_i1_thr35_h48()
    r1_contrast = {
        "universe": f"monthly PIT ranks 51-150 band ({n_band_symbols} symbols)",
        "cost_bps": lfr.COST_BPS,
        "n_events": p2["n_events"],
        "n_events_with_full_forward_window": p2["n_events_with_full_forward_window"],
        "gross_return_per_event": p2["mean_fwd_ret"],
        "net_sr": p3["primary_net_sr"],
        "n_symbols_active": per_symbol["n_symbols_with_events"],
        "gate_outcome": p3["reason"],
    }
    contrast = {"liq_fade_i1_thr3.5_H48": i1, "liq_fade_r1_thr3.5_H48": r1_contrast}
    print(f"[contrast] i1: {i1['n_events']} ev, gross/event={i1['gross_return_per_event']:+.4%}, "
          f"net_sr={i1['net_sr']:+.3f} @ {i1['cost_bps']}bps | "
          f"r1: {r1_contrast['n_events']} ev, gross/event="
          f"{r1_contrast['gross_return_per_event']:+.4%}, net_sr={r1_contrast['net_sr']:+.3f} "
          f"@ {r1_contrast['cost_bps']}bps")

    skipped = {
        "F1_inversion": "no gated result to invert -- P2 already failed gross, before any gate",
        "F3_yearly_stability": "no realized net-return series exists (Task 7 skipped); "
                               "power section's events-per-year table covers the adjacent "
                               "question from raw trigger data alone",
        "F5_dsr_decomposition": "no gate was evaluated (Task 7 skipped, no results.json, "
                                "no ledger row) -- nothing to deflate",
        "F6_cost_curve": "signal loses gross before any cost bps is applied -- cost "
                         "sensitivity cannot rescue or further sink that verdict",
        "F7_p2_reconciliation": "no realized, compounded portfolio series exists to "
                                "reconcile against the P2 event-study mean",
        "F8_placebo_audit": "no placebo was run -- P3 failure routes straight to write-up "
                            "per gates.json's pass_rule, so there is no p-value to re-derive",
    }

    payload = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "experiment": "liq_fade_r1", "outcome": "NEGATIVE-at-probe (P2/P3), gates never evaluated",
        "power": power, "p3_control": p3_control, "liquidity_gradient": liquidity_gradient,
        "per_symbol": per_symbol, "horizon": horizon, "contrast": contrast,
        "sections_skipped": skipped,
    }
    R1_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(_sanitize(payload), f, indent=1, allow_nan=False, default=str)
    print(f"\nwrote {OUT_JSON}")

    write_markdown(payload, near_top50, never_top50)
    print(f"wrote {OUT_MD}")


def write_markdown(p: dict, near_top50: list[str], never_top50: list[str]) -> None:
    pw, p3c, lg = p["power"], p["p3_control"], p["liquidity_gradient"]
    ps, hz, ct = p["per_symbol"], p["horizon"], p["contrast"]
    i1, r1 = ct["liq_fade_i1_thr3.5_H48"], ct["liq_fade_r1_thr3.5_H48"]
    near, never = lg["near_top50"], lg["never_top50"]

    lines = []
    a = lines.append
    a("# liq_fade_r1 forensics — NEGATIVE-at-probe verified\n")
    a("Replication of `liq_fade_i1` (THESIS section 49) on the monthly-PIT "
      "51-150 rank band (304 symbols), frozen config `thr=3.5, H=48, w_per=0.1, "
      "cap=1.0`, cost raised to 20bps for the thinner band. The pre-registered "
      "P3 control ran first and closed: primary net SR does not clear the 1.0 "
      "floor, so the verdict is plain NEGATIVE, not NEGATIVE-confounded. Task 7 "
      "(the gated primary run) was correctly skipped per the plan's decision "
      "point — no `results.json` was produced, no gate was evaluated, and no "
      "trial-ledger row exists for this experiment. The holdout window "
      "(2025-04-01 onward) was never touched.\n")

    a("## Power\n")
    a(f"{pw['n_events_masked']} masked triggers across {pw['n_band_symbols']} band "
      f"symbols over {pw['years_spanned']:.2f} years of dev window "
      f"({pw['events_per_year']:.0f} events/year, {pw['events_per_symbol']:.2f} "
      f"events/symbol) — comparable order of magnitude to `liq_fade_i1`'s 710 "
      f"events over 88 symbols (8.07 events/symbol there). {pw['n_events_full_window']} "
      f"events have a full H=48 forward window and enter the mean below.\n")
    a(f"Mean gross forward return per event: **{pw['mean_fwd_ret']:+.4%}**, "
      f"sd {pw['sd_fwd_ret']:.4%}, standard error of the mean "
      f"{pw['se_mean_fwd_ret']:.4%} → t = {pw['t_stat']:.2f}. This does **not** "
      f"clear the conventional |t| > 1.96 threshold for distinguishing the mean "
      f"from zero: individual event returns are extremely dispersed relative to "
      f"the mean (sd ≈ 43× the mean magnitude), and 1884 events is not enough to "
      f"average that dispersion down to significance. The events are also not "
      f"strictly independent draws — market-wide crash days trigger many band "
      f"symbols simultaneously — so the true standard error (clustered by day) "
      f"is if anything larger than the naive one reported here, meaning the "
      f"non-significance is a conservative finding, not an artifact that a "
      f"better test would resolve in the negative's favor.\n")
    a(f"The honest characterization is therefore **a well-powered null**, not a "
      f"well-powered, confidently-signed negative: the sample size is large "
      f"(more events, more symbols, than `liq_fade_i1`), but the per-event "
      f"effect size is small relative to per-event noise, and a naive test "
      f"cannot rule out that the population mean is exactly zero. This does not "
      f"change the P2 outcome — P2 is a pre-registered **absolute floor** "
      f"(mean gross return must exceed +25bp), not a significance test, and "
      f"−0.418% fails that floor decisively in point-estimate terms regardless "
      f"of whether it is significantly different from zero on the downside. "
      f"But it matters for how the result should be read: the band shows no "
      f"detectable *positive* timing edge, which is itself sufficient to fail "
      f"the pre-registered gate — there is no need to additionally claim the "
      f"band actively punishes crash-fading, and the data does not clearly "
      f"support that stronger claim.\n")
    yr_tbl = ", ".join(f"{y}: {n}" for y, n in sorted(pw["events_per_year_table"].items()))
    a(f"Events by calendar year: {yr_tbl}.\n")

    a("## P3 control detail (the check `liq_fade_i1`'s own forensics left open)\n")
    a(f"`liq_fade_i1`'s forensics (THESIS 49.5, item 9) flagged an open item: "
      f"a generic long-bias-on-high-volatility-days drift could produce the "
      f"same inversion signature as genuine crash-timing, and the "
      f"discriminating control was never run on that universe. `liq_fade_r1` "
      f"pre-registered and ran it, and this section independently re-derives "
      f"it from the frozen panel (not read back from `probes.json`) as a "
      f"verification pass.\n")
    a(f"- Primary (crash condition, `z_ret ≤ −3.5 AND z_vol ≥ 3.5`): "
      f"**{p3c['n_primary_events']} events**, net SR **{p3c['primary_net_sr']:+.4f}**\n")
    a(f"- Control (vol-only, `z_vol ≥ 3.5`, crash condition removed): "
      f"**{p3c['n_control_events']} events**, net SR **{p3c['control_net_sr']:+.4f}**\n")
    a(f"- Separation (primary − control): **{p3c['separation']:+.4f}**\n")
    a(f"Recomputation matches `probes.json` exactly (primary, control, and "
      f"both event counts reproduced to floating-point precision). What this "
      f"establishes and what it does not: the crash condition beats vol-only "
      f"exposure by +0.485 SR, so the crash timing is not simply relabeled "
      f"high-volatility drift — **but both numbers are negative**, and the "
      f"primary (−0.048) sits below the 1.0 floor the confounded label "
      f"requires. Per the pre-registered scope rule, this makes the result "
      f"plain NEGATIVE rather than NEGATIVE-confounded: the separation is "
      f"informative about the mechanism (crash timing ≠ vol drift) but is not "
      f"itself evidence of a profitable effect, since it separates two losing "
      f"strategies rather than lifting a winning one clear of a confound.\n")

    a("## Liquidity gradient (new analysis)\n")
    a(f"304 band symbols split by whether they were ever a `liq_fade_i1` "
      f"top-50 member in some OTHER PIT month: **{lg['near_top50_symbols_n']} "
      f"\"near-top50\"** symbols (rotate in and out of the top-50 across the "
      f"5-year PIT history) vs **{lg['never_top50_symbols_n']} \"never-top50\"** "
      f"symbols (never top-50 at any point).\n")
    a(f"- Near-top50: {near['n_events']} events, mean fwd ret "
      f"**{near['mean_fwd_ret']:+.4%}** (se {near['se_mean_fwd_ret']:.4%}, "
      f"t={near['t_stat']:.2f}). Top single-symbol contributor: "
      f"**{near['top_contributor_symbol']}**, {near['top_contributor_share_of_total_sum']:.0%} "
      f"of the partition's total pp-sum; excluding it, mean = "
      f"{near['mean_fwd_ret_excl_top_contributor']:+.4%} "
      f"(t={near['t_stat_excl_top_contributor']:.2f}) over "
      f"{near['n_events_excl_top_contributor']} events.\n")
    a(f"- Never-top50: {never['n_events']} events, mean fwd ret "
      f"**{never['mean_fwd_ret']:+.4%}** (se {never['se_mean_fwd_ret']:.4%}, "
      f"t={never['t_stat']:.2f}). Top single-symbol contributor: "
      f"**{never['top_contributor_symbol']}**, {never['top_contributor_share_of_total_sum']:.0%} "
      f"of the partition's total pp-sum; excluding it, mean = "
      f"{never['mean_fwd_ret_excl_top_contributor']:+.4%} "
      f"(t={never['t_stat_excl_top_contributor']:.2f}) over "
      f"{never['n_events_excl_top_contributor']} events.\n")
    a(f"The headline never-top50 number (**{never['mean_fwd_ret']:+.2%}**) is "
      f"substantially a single-symbol artifact: **{never['top_contributor_symbol']}** "
      f"— the FTX exchange token, which collapsed to near-zero in November 2022 "
      f"and never recovered — alone accounts for "
      f"{never['top_contributor_share_of_total_sum']:.0%} of the partition's "
      f"total loss from just {never['top_contributor_n_events']} events. \"Fading\" a "
      f"cascade in a token headed to a permanent delisting is a fundamentally "
      f"different bet than fading a liquidity-driven overreaction, and this "
      f"single collapse should not be read as representative of the "
      f"never-top50 population. Excluding it, the partition's mean shrinks "
      f"roughly fourfold (to {never['mean_fwd_ret_excl_top_contributor']:+.2%}) "
      f"but remains negative and nominally significant at conventional levels "
      f"(t={never['t_stat_excl_top_contributor']:.2f}).\n")
    a(f"The near-top50 partition, by contrast, shows a small **positive** point "
      f"estimate ({near['mean_fwd_ret']:+.2%}), though it does not clear "
      f"conventional significance (t={near['t_stat']:.2f}) and is itself "
      f"moderately concentrated (one symbol, "
      f"{near['top_contributor_symbol']}, contributes "
      f"{near['top_contributor_share_of_total_sum']:.0%} of the total; excluding "
      f"it the mean is smaller but still positive, "
      f"{near['mean_fwd_ret_excl_top_contributor']:+.2%}).\n")
    a(f"**Honest reading**: there is a directional split consistent with a "
      f"liquidity gradient — proximity to the top-50 tilts positive, distance "
      f"from it tilts negative — but neither side is a statistically robust, "
      f"broad-based finding once single-symbol concentration is accounted for. "
      f"This sharpens the section-49 story modestly (the effect does not "
      f"invert sign as cleanly as \"both partitions negative\" would suggest, "
      f"and there is a real, order-of-magnitude decay from i1's own +2.77% "
      f"down toward the near-top50 group's small positive tilt) without "
      f"licensing a claim that the underlying effect is real and merely "
      f"attenuated by liquidity — the pooled, whole-band result (Power, above) "
      f"remains a statistically indistinguishable-from-zero null that fails "
      f"the pre-registered gate on its own terms.\n")

    a("## Per-symbol distribution\n")
    a(f"{ps['n_symbols_with_events']} of {ps['n_band_symbols_total']} band "
      f"symbols registered at least one event. **{ps['n_positive_mean']}/"
      f"{ps['n_symbols_with_events']} ({ps['frac_positive_mean']:.1%})** have a "
      f"positive mean forward event return — essentially a coin flip, not a "
      f"lopsided majority in either direction. That is itself informative and "
      f"consistent with the Power section's finding above: the aggregate "
      f"negative mean does **not** come from most symbols individually leaning "
      f"negative (which would show as a small minority positive, well under "
      f"50%). It comes from the *magnitude* of losses among the losing names "
      f"exceeding the magnitude of gains among the winning ones — a fat left "
      f"tail sitting on top of an otherwise roughly symmetric distribution, "
      f"which is exactly what the worst/best tables below show.\n")
    a("Worst 5 by mean forward return:\n")
    for r in ps["worst5"]:
        a(f"- {r['symbol']}: {r['mean_fwd_ret']:+.4%} ({r['n_events']} events)")
    a("")
    a("Best 5 by mean forward return:\n")
    for r in ps["best5"]:
        a(f"- {r['symbol']}: {r['mean_fwd_ret']:+.4%} ({r['n_events']} events)")
    a("")
    a(f"The worst name is FTTUSDT at −46.7% mean forward return (27 events) — "
      f"the FTX token collapse discussed in the liquidity-gradient section "
      f"above — an order of magnitude larger in magnitude than any other name "
      f"in either tail. This is the single-symbol tail-risk mechanism that "
      f"drags the pooled mean negative despite an even sign split: a small "
      f"number of names undergoing a genuine, permanent collapse (not a "
      f"liquidity-driven overreaction that mean-reverts) generate losses large "
      f"enough to outweigh many smaller, roughly-offsetting gains and losses "
      f"elsewhere in the band.\n")

    a("## Horizon check\n")
    for h in HORIZONS:
        v = hz[str(h)]
        a(f"- H={h}h: mean gross forward return **{v['mean_gross_fwd_ret']:+.4%}** "
          f"(t={v['t_stat']:.2f}, {v['n_events_with_full_window']} events with a "
          f"full forward window)")
    a("")
    a(f"All four horizons are negative "
      f"({'confirmed' if hz['all_horizons_negative'] else 'NOT confirmed — see above'}), "
      f"though none individually clears conventional significance (all |t| < 2). "
      f"The failure is not an artifact of the H=48 choice specifically — "
      f"shortening the hold to 1h, 6h, or 24h does not turn the crash-fade "
      f"gross return positive at any horizon tested; there is no shorter "
      f"exit that would have rescued the primary config.\n")

    a("## Contrast: liq_fade_i1 vs liq_fade_r1 (thr=3.5, H=48)\n")
    a("| | liq_fade_i1 (§49) | liq_fade_r1 |")
    a("|---|---|---|")
    a(f"| Universe | {i1['universe']} | {r1['universe']} |")
    a(f"| Cost (bps/side) | {i1['cost_bps']:.0f} | {r1['cost_bps']:.0f} |")
    a(f"| Events (masked, full window) | {i1['n_events']} ({i1['n_events_with_full_forward_window']}) "
      f"| {r1['n_events']} ({r1['n_events_with_full_forward_window']}) |")
    a(f"| Symbols active | {i1['n_symbols_active']} | {r1['n_symbols_active']} |")
    a(f"| Gross return / event | {i1['gross_return_per_event']:+.3%} | {r1['gross_return_per_event']:+.3%} |")
    a(f"| Net SR (primary config) | {i1['net_sr']:+.3f} | {r1['net_sr']:+.3f} |")
    a(f"| Gate outcome | {i1['gate_outcome']} | {r1['gate_outcome']} |")
    a("")

    a("## Sections skipped (named per the anti-silent-omission rule)\n")
    a("The plan's Task 8 template lists eleven forensic sections (F1-F11) "
      "written for a PASS or a DSR-bound gate-failure outcome. Six sections "
      "above cover what this NEGATIVE-at-probe outcome calls for (power, P3 "
      "control detail, liquidity gradient, per-symbol distribution, horizon "
      "check, i1-vs-r1 contrast). The remaining six are skipped, not silently "
      "omitted:\n")
    for k, v in p["sections_skipped"].items():
        a(f"- **{k}**: {v}")
    a("")

    a("## Verdict\n")
    a("`liq_fade_r1` closes as plain **NEGATIVE**, decided at probes P2/P3 "
      "before any gate (G1-G3) was ever evaluated. The universe move (top-50 "
      "→ ranks 51-150, same frozen signal and holding rule) does not merely "
      "shrink the section-49 effect — the point estimate flips sign "
      "(+2.77%/event on the original universe vs "
      f"{pw['mean_fwd_ret']:+.3%}/event on the band). That said, the "
      "pooled per-event negative is not itself statistically distinguishable "
      "from zero at conventional levels (Power section, t≈−1.0) — the honest "
      "characterization is a **well-powered null**, not a confidently-signed "
      "harm, and it fails the pre-registered P2 floor (which requires the mean "
      "to clear +25bp, a bar a null result also fails) rather than because the "
      "band actively punishes crash-fading. The per-symbol distribution shows "
      "a roughly even sign split (50.2% positive) with the pooled negative "
      "driven by a small number of fat-tailed losers (worst: FTTUSDT −46.7%, "
      "the FTX collapse), not a broad-based majority-negative pattern. The "
      "liquidity-gradient partition shows a directional split consistent with "
      "a gradient — near-top50 symbols tilt positive (+0.49%, not "
      "significant), never-top50 symbols tilt negative (−7.84%, but 78% of "
      "that is one symbol's permanent collapse; ex-that-symbol the negative "
      "shrinks to −1.98%) — real but partial and not robust enough on its own "
      "to overturn the pooled null. Every horizon tested (1h/6h/24h/48h) has "
      "a negative point estimate, none individually significant, so H=48 was "
      "not an unlucky choice of hold. No trial-ledger row exists for this "
      "experiment and the declared n_trials=1 amendment was registered but "
      "never exercised, since the gates were never reached. The holdout "
      "(2025-04-01 onward) remains sealed and unspent.\n")

    OUT_MD.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
