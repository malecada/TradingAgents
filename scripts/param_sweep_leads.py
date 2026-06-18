"""Lead #3 — quant param sweeps on frozen V5-MIX 4-coin predictions.

Two experiments, both reuse the production cost/risk engine (run_coin_backtest)
and frozen walk-forward predictions (no LLM, no retrain):

  A. vol-target x trend-multiplier grid (baseline cell = 0.10 / 1.5).
  B. Kelly-per-regime: kelly chosen at entry bar by BTC-drawdown regime
     (bull/sideways/bear), vs uniform-kelly baseline.

Portfolio = equal-weight 4-coin (BTC,ETH,BNB,SOL), the V5-MIX core.
Reports Sharpe / total-return / maxDD per cell. Print-only; writes JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import (  # noqa: E402
    COSTS, DEFAULT_ROUTING, _load_crypto_ohlcv, _load_preds, ANN,
)
from scripts.regime_breakdown import regime_label  # noqa: E402
from tradingagents.strategies.v2_sizing import (  # noqa: E402
    apply_leverage, apply_trend_filter, compute_realized_vol,
    generate_term_structure_signals, vol_regime_mask, vol_targeted_size,
)

V5_CONFIDENCE_REF = 0.05
V5_ASYMMETRIC = True
CORE = ["bitcoin", "ethereum", "binancecoin", "solana"]
START, END = "2021-11-07", "2026-04-14"


def _build_positions_kelly_array(
    signals, vol_ok, confidence, realized_vol, prices,
    target_vol, kelly_arr, max_leverage, min_hold, early_exit_loss=0.015,
):
    """Copy of build_positions_with_hold but kelly is per-bar (array).

    Kelly at entry/flip uses kelly_arr[i] of the entry bar. Everything else
    identical to the production sizer.
    """
    positions = np.zeros(len(signals))
    current_pos = 0.0
    current_dir = 0
    bars_held = 0
    entry_price = 0.0
    for i in range(len(signals)):
        sig = int(signals[i])
        if current_dir != 0:
            bars_held += 1
        if current_dir != 0 and bars_held >= 3 and bars_held < min_hold:
            if entry_price > 0 and prices[i] > 0:
                pnl = current_dir * (prices[i] - entry_price) / entry_price
                if pnl < -early_exit_loss and (sig != current_dir):
                    current_pos = 0.0; current_dir = 0; bars_held = 0
        if current_dir == 0 and sig != 0 and vol_ok[i]:
            base = vol_targeted_size(sig, confidence[i], realized_vol[i],
                                     target_vol, float(kelly_arr[i]))
            current_pos = apply_leverage(base, confidence[i], max_leverage)
            current_dir = sig; bars_held = 0; entry_price = prices[i]
        elif (current_dir != 0 and sig != 0 and sig != current_dir
              and bars_held >= min_hold and vol_ok[i]):
            base = vol_targeted_size(sig, confidence[i], realized_vol[i],
                                     target_vol, float(kelly_arr[i]))
            current_pos = apply_leverage(base, confidence[i], max_leverage)
            current_dir = sig; bars_held = 0; entry_price = prices[i]
        positions[i] = current_pos
    return positions


def _merged(coin):
    preds = _load_preds(Path(DEFAULT_ROUTING[coin]), coin)
    preds = preds[(preds["date"] >= START) & (preds["date"] <= END)]
    ohlcv = _load_crypto_ohlcv(coin, END)
    ohlcv["Date"] = pd.to_datetime(ohlcv["Date"]).dt.tz_localize(None).dt.normalize()
    m = preds.merge(ohlcv[["Date", "Close"]], left_on="date", right_on="Date")
    m = m.dropna(subset=["Close"]).reset_index(drop=True)
    m["ref_price"] = m["Close"]
    return m


def _returns_from_positions(merged, pos):
    costs = dict(COSTS)
    equity, _ = run_coin_backtest(
        dates=merged["date"].values, prices=merged["Close"].values,
        positions=pos, initial_capital=10_000.0, **costs,
    )
    eq = np.asarray(equity, dtype=float)
    rets = eq[1:] / eq[:-1] - 1.0
    return pd.Series(rets, index=merged["date"].values[1:])


def _coin_series_vol_trend(coin, target_vol, trend_mult, kelly=0.5):
    m = _merged(coin)
    sig, conf = generate_term_structure_signals(
        m, [7, 14], V5_CONFIDENCE_REF, asymmetric=V5_ASYMMETRIC)
    px = m["Close"].astype(float).values
    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    from tradingagents.strategies.v2_sizing import build_positions_with_hold
    pos = build_positions_with_hold(
        signals=sig, vol_ok=mask, confidence=conf, realized_vol=rv, prices=px,
        target_vol=target_vol, kelly_fraction=kelly, max_leverage=3.0,
        min_hold=7, early_exit_loss=0.015)
    pos = apply_trend_filter(pos, px, sma_period=30, multiplier=trend_mult)
    return _returns_from_positions(m, pos)


def _coin_series_kelly_regime(coin, kelly_map, btc_prices_dates):
    """kelly_map: {bull,sideways,bear}->float. Regime from BTC drawdown."""
    m = _merged(coin)
    sig, conf = generate_term_structure_signals(
        m, [7, 14], V5_CONFIDENCE_REF, asymmetric=V5_ASYMMETRIC)
    px = m["Close"].astype(float).values
    rv = compute_realized_vol(px, lookback=20)
    mask = vol_regime_mask(rv, percentile_cap=0.95)
    # map BTC regime onto this coin's dates
    btc_reg = btc_prices_dates  # Series indexed by date -> label
    dts = pd.to_datetime(m["date"]).values
    kelly_arr = np.full(len(m), kelly_map["sideways"], dtype=float)
    reg_aligned = pd.Series(btc_reg).reindex(pd.to_datetime(dts)).ffill()
    for i, lab in enumerate(reg_aligned.values):
        kelly_arr[i] = kelly_map.get(lab if isinstance(lab, str) else "sideways",
                                     kelly_map["sideways"])
    pos = _build_positions_kelly_array(
        sig, mask, conf, rv, px, 0.10, kelly_arr, 3.0, 7)
    pos = apply_trend_filter(pos, px, sma_period=30, multiplier=1.5)
    return _returns_from_positions(m, pos)


def _portfolio(series_list):
    df = pd.concat(series_list, axis=1).dropna(how="all")
    port = df.mean(axis=1)  # equal weight
    return port.dropna()


def _metrics(r):
    eq = (1 + r).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    sd = r.std()
    return dict(sharpe=float(r.mean() / sd * ANN) if sd > 0 else 0.0,
                total_return=float(eq.iloc[-1] - 1.0), max_dd=dd,
                ann_vol=float(sd * ANN), n=int(len(r)))


def main():
    out = {"exp_A_vol_trend": {}, "exp_B_kelly_regime": {}}

    # ---- BTC regime series (global, §11.7) ----
    btc_m = _merged("bitcoin")
    btc_lab = regime_label(btc_m["Close"].astype(float).values,
                           window=365, bull_dd=0.10, bear_dd=0.30)
    btc_reg = pd.Series(btc_lab, index=pd.to_datetime(btc_m["date"]).values)
    counts = pd.Series(btc_lab).value_counts().to_dict()
    out["regime_counts"] = counts
    print("regime bar counts:", counts)

    # ============ EXP A: vol-target x trend-mult ============
    print("\n=== EXP A: vol-target x trend-multiplier (EW 4-coin) ===")
    vols = [0.07, 0.10, 0.13, 0.16]
    trends = [1.0, 1.3, 1.5, 1.7, 2.0]
    print(f"{'tv\\tm':>8}", *[f"{t:>7}" for t in trends])
    for tv in vols:
        row = []
        for tm in trends:
            series = [_coin_series_vol_trend(c, tv, tm) for c in CORE]
            port = _portfolio(series)
            mt = _metrics(port)
            out["exp_A_vol_trend"][f"tv{tv}_tm{tm}"] = mt
            row.append(mt["sharpe"])
        print(f"{tv:>8}", *[f"{s:>7.3f}" for s in row])
    base = out["exp_A_vol_trend"]["tv0.1_tm1.5"]
    print(f"\nbaseline (0.10/1.5): SR {base['sharpe']:.3f}  "
          f"ret {base['total_return']*100:+.1f}%  DD {base['max_dd']*100:.1f}%")

    # ============ EXP B: Kelly-per-regime ============
    print("\n=== EXP B: Kelly-per-regime (EW 4-coin) ===")
    kelly_variants = {
        "uniform_0.50 (baseline)": {"bull": .50, "sideways": .50, "bear": .50},
        "bear_down_0.25":          {"bull": .50, "sideways": .50, "bear": .25},
        "bear_up_0.75":            {"bull": .50, "sideways": .50, "bear": .75},
        "bull_up_0.75":            {"bull": .75, "sideways": .50, "bear": .50},
        "bull_up_side_up":         {"bull": .75, "sideways": .65, "bear": .35},
        "risk_off_bear":           {"bull": .60, "sideways": .55, "bear": .20},
    }
    for name, km in kelly_variants.items():
        series = [_coin_series_kelly_regime(c, km, btc_reg) for c in CORE]
        port = _portfolio(series)
        mt = _metrics(port)
        out["exp_B_kelly_regime"][name] = {**mt, "kelly_map": km}
        print(f"  {name:<26} SR {mt['sharpe']:.3f}  "
              f"ret {mt['total_return']*100:+8.1f}%  DD {mt['max_dd']*100:5.1f}%")

    outpath = REPO / "data" / "param_sweep_leads.json"
    outpath.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {outpath}")


if __name__ == "__main__":
    main()
