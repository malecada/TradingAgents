#!/usr/bin/env python
"""llm_p5_hybrid — causal ETH hybrid A/B per gates.json["llm_p5_hybrid"].

Arm A: canonical V2 leg on corrected preds (purged + rolling730 + onchain-pit),
causal convention, causal costs, 3% intrabar price-stop replay — the audited
`baseline_v5_mix.run_coin` path, re-implemented here only to expose the
position vector for arm B.

Arm B: pos_A[slot i] × (1 + effective_weight × (multiplier − 1)) where the
modulation factors come from the signals CSV row dated D−1 for position slot D
(modulator decision at close d applies to the bar accrued on d+1 — the same
00:05-UTC live-cycle alignment as the quant leg's ref_price = close(D−1)).
Missing CSV row / failed extraction → factor 1.0 (production fallback),
counted as a registered diagnostic.

Gate: paired stationary block bootstrap (block 21, n 2000) on the daily diff,
PASS iff p_pos >= 0.90. One-shot.

Usage:
    python scripts/llm_p5_ab.py \\
        --signals-csv data/llm_p5/signals/ethereum_2026-01-16_2026-05-21.csv \\
        --pred-dir data/audit_fix/rolling730/multi_2coins_pit_wf_p5 \\
        --start 2026-01-16 --end 2026-05-21 --output-dir data/rebuild/llm_p5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    _load_preds, _metrics, _v2_positions, costs_for_coin,
)
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402
from tradingagents.rebuild.compare import paired_bootstrap  # noqa: E402

COIN = "ethereum"
PRICE_STOP_PCT = 0.03
P_POS_MIN = 0.90


def build_arm_frames(pred_dir: Path, start: str, end: str):
    """Replicates baseline_v5_mix.run_coin data prep (causal) and returns
    (merged, pos_a) so arm B can reuse the identical engine inputs."""
    preds = _load_preds(pred_dir, COIN)
    preds = preds[(preds["date"] >= start) & (preds["date"] <= end)]
    if preds.empty:
        raise ValueError(f"no predictions in [{start}, {end}] under {pred_dir}")
    ohlcv = _load_crypto_ohlcv(COIN, end)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    merged = preds.merge(ohlcv[["Date", "Close", "High", "Low"]],
                         left_on="date", right_on="Date")
    merged = merged.dropna(subset=["Close"]).reset_index(drop=True)
    # causal: keep CSV ref_price (= close(D-1)); never overwrite with same-day close
    pos_a = _v2_positions(merged, convention="causal")
    return merged, pos_a


def run_engine(merged: pd.DataFrame, pos: np.ndarray) -> pd.Series:
    costs = costs_for_coin(COIN, convention="causal")
    costs["stop_loss"] = 1.0  # price-axis stop replaces the equity-axis proxy
    equity, _m = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=pos, initial_capital=10_000.0, **costs,
        highs=merged["High"].values, lows=merged["Low"].values,
        price_stop_pct=PRICE_STOP_PCT,
    )
    eq = np.asarray(equity, dtype=float)
    rets = eq[1:] / eq[:-1] - 1.0
    return pd.Series(rets, index=pd.to_datetime(merged["date"].values[1:]))


def modulation_factors(merged: pd.DataFrame, signals_csv: Path) -> tuple[np.ndarray, dict]:
    sig = pd.read_csv(signals_csv, parse_dates=["date"])
    sig["date"] = sig["date"].dt.tz_localize(None).dt.normalize()
    sig = sig.drop_duplicates(subset="date", keep="last").set_index("date")
    mult = pd.to_numeric(sig["llm_multiplier"], errors="coerce")
    eff = pd.to_numeric(sig["effective_weight"], errors="coerce")
    n_extract_fail = int(mult.isna().sum())
    f_csv = 1.0 + eff.fillna(0.0) * (mult.fillna(1.0) - 1.0)

    # slot alignment: position slot dated D is decided at close(D-1) -> factor
    # from the CSV row dated D-1.
    slot_dates = pd.to_datetime(merged["date"].values)
    lookup_dates = slot_dates - pd.Timedelta(days=1)
    f_slot = f_csv.reindex(lookup_dates)
    n_missing = int(f_slot.isna().sum())
    f_slot = f_slot.fillna(1.0).to_numpy()

    diag = {
        "n_csv_rows": int(len(sig)),
        "n_extract_fail": n_extract_fail,
        "n_slots": int(len(slot_dates)),
        "n_slot_factor_missing": n_missing,
        "pct_slots_modulated": float((np.abs(f_slot - 1.0) > 1e-9).mean()),
        "multiplier_mean": float(mult.mean()),
        "multiplier_std": float(mult.std()),
        "multiplier_pct_ne_1": float((mult.dropna() != 1.0).mean()) if mult.notna().any() else float("nan"),
        "effective_weight_mean": float(eff.mean()),
        "effective_weight_std": float(eff.std()),
        "factor_min": float(np.min(f_slot)), "factor_max": float(np.max(f_slot)),
    }
    return f_slot, diag


def parity_probe(merged: pd.DataFrame, signals_csv: Path) -> dict:
    """CSV quant_direction (decision date d) vs pred-CSV h7/h14 consensus for
    position slot d+1 — honest-denominator mismatch count."""
    from scripts.baseline_v5_mix import V5_ASYMMETRIC, V5_CONFIDENCE_REF
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals
    sig_arr, _conf = generate_term_structure_signals(
        merged, [7, 14], V5_CONFIDENCE_REF, asymmetric=V5_ASYMMETRIC,
    )
    sigs = pd.Series(sig_arr, index=pd.to_datetime(merged["date"].values))
    csv = pd.read_csv(signals_csv, parse_dates=["date"])
    csv["date"] = csv["date"].dt.tz_localize(None).dt.normalize()
    csv = csv.drop_duplicates(subset="date", keep="last").set_index("date")
    dmap = {"long": 1, "short": -1, "flat": 0}
    n_cmp = n_match = 0
    for d, row in csv.iterrows():
        slot = d + pd.Timedelta(days=1)
        if slot in sigs.index and row.get("quant_direction") in dmap:
            n_cmp += 1
            n_match += int(np.sign(sigs[slot]) == dmap[row["quant_direction"]])
    return {"n_compared": n_cmp, "n_match": n_match,
            "match_rate": float(n_match / n_cmp) if n_cmp else float("nan")}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--signals-csv", required=True)
    p.add_argument("--pred-dir", required=True)
    p.add_argument("--start", default="2026-01-16")
    p.add_argument("--end", default="2026-05-21")
    p.add_argument("--output-dir", default="data/rebuild/llm_p5")
    args = p.parse_args()

    merged, pos_a = build_arm_frames(Path(args.pred_dir), args.start, args.end)
    f_slot, diag = modulation_factors(merged, Path(args.signals_csv))
    pos_b = pos_a * f_slot

    r_a = run_engine(merged, pos_a)
    r_b = run_engine(merged, pos_b)

    boot = paired_bootstrap(r_a, r_b, block=21, n=2000)
    m_a, m_b = _metrics(r_a), _metrics(r_b)
    parity = parity_probe(merged, Path(args.signals_csv))

    gate_pass = bool(boot["p_pos"] >= P_POS_MIN)
    out = {
        "experiment": "llm_p5_hybrid",
        "window": [args.start, args.end],
        "n_bars": int(len(merged)),
        "gate": {"p_pos_min": P_POS_MIN, "p_pos": boot["p_pos"],
                 "pass": gate_pass},
        "bootstrap": boot,
        "arm_a_quant": m_a,
        "arm_b_hybrid": m_b,
        "delta_maxdd": float(m_b["max_drawdown"] - m_a["max_drawdown"]),
        "modulation_diagnostics": diag,
        "parity_probe": parity,
    }
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "ab_results.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    pd.DataFrame({"quant": r_a, "hybrid": r_b}).to_csv(outdir / "daily_returns_ab.csv")

    print(json.dumps({k: out[k] for k in
                      ("gate", "arm_a_quant", "arm_b_hybrid", "delta_maxdd")},
                     indent=1, default=str))
    print(f"parity: {parity}")
    print(f"diag: {diag}")
    print(f"\nVERDICT: {'PASS' if gate_pass else 'FAIL'} "
          f"(p_pos={boot['p_pos']:.3f} vs {P_POS_MIN})")


if __name__ == "__main__":
    main()
