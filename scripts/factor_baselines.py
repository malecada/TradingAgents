#!/usr/bin/env python
"""Model-free factor floor — 18 pre-registered configs (Phase 2, step 1).

The honest rebuild's Phase 1 established a causal harness; this module builds
the model-free baselines that any ML sleeve must later beat (gate: F6/H2,
gates.json "ml_survival.vs = best factor-floor config"). Every signal is a
classical, parameter-free (no fit) trend/momentum rule.

CRITICAL PROPERTY — causality. Every signal value at index t is computable from
data up to index t-1 only. The prior system was invalidated by same-bar
look-ahead (audit 2026-07-07); here we err toward extra lag:
  * tsmom      : sign(close[t-1] / close[t-1-k] - 1)
  * ma_cross   : sign(SMA_fast - SMA_slow), both MAs end at index t-1
  * donchian   : channel break / mid-channel exit decided on bars <= t-1
  * xs_mom     : 30d relative strength of BTC vs ETH computed on data <= t-1
Warm-up bars (insufficient history) emit 0. Confidence = 1.0 where signal != 0.

The 18-config pre-registered enumeration (no additions without a new
gates.json entry) — 8 + 6 + 2 + 1 + 1 = 18:

  TSMOM long-short   k in {7, 14, 30, 90}                      -> 4
  TSMOM long-only    k in {7, 14, 30, 90}   (max(sign, 0))     -> 4
  MA-cross long-short (10,50) (20,100) (50,200)                -> 3
  MA-cross long-only  (10,50) (20,100) (50,200)                -> 3
  Donchian long-short n in {20, 55}                            -> 2
  XS-momentum BTC-vs-ETH 30d dollar-neutral pair               -> 1
  TSMOM long-short   k = 180  (the documented 18th)            -> 1
                                                          total = 18

Shared sizing path (identical for every config, per coin bitcoin+ethereum):
  signal (int8 {-1,0,+1}) -> confidence 1.0 where != 0
  -> causal lag (px_sizing[1:] = px[:-1]) fed to vol / vol-mask / positions
  -> build_positions_with_hold(target_vol=0.10, kelly_fraction=0.5,
       max_leverage=3.0, min_hold=7, early_exit_loss=0.015, vol_lookback=20,
       vol cap 0.95)   [NO trend filter — these ARE the trend strategies]
  -> run_coin_backtest(core-coin causal costs, price_stop_pct=0.03,
       real Close for P&L, real High/Low for the intrabar stop)
Equal-weight the two coins' daily returns -> portfolio SR / total return / maxDD.

Window: 2021-11-07 .. 2025-03-31 (dev; strictly before the locked holdout).

Usage:
    uv run python scripts/factor_baselines.py --start 2021-11-07 --end 2025-03-31

HALT-LATCH TRANSPARENCY (adjudicated 2026-07-09, reviewer finding, Critical).
`run_coin_backtest`'s max_portfolio_dd=0.15 circuit breaker is a PERMANENT
latch: once a coin's drawdown-from-peak breaches 15%, `halted=True` is never
reset, and every subsequent bar for that coin returns a flat 0.0. In the
former BEST config (macross_10_50_ls), ETH halts on 2022-07-18 and BTC halts
on 2023-03-03; the trailing zero tail is 61% of the window, and it drags rank
13-15 (macross_20_100_lo / macross_50_200_lo / tsmom_k90_lo) to byte-identical
full-series metrics because the dead tail washes out any residual difference
between them. The controller's decision: the halt STAYS — it is the live
system's real circuit breaker and it is applied identically to every
rebuild-arm config, so full-series Sharpe remains a fair, apples-to-apples
gate metric across configs. What changes here is TRANSPARENCY only: each
config's recorded metrics now also carry `sr_active` (the portfolio Sharpe
computed only over bars up to the last nonzero portfolio return, i.e. with
the trailing post-halt zero tail excluded — diagnostic only, never used for
selection), `halted_bitcoin` / `halted_ethereum` (bool + first date at which
that coin's returns go permanently to zero, or null if never halted), and
`n_trailing_zero_bars` (portfolio-level trailing zero-bar count). The
full-series Sharpe (column/key `sr`) remains THE primary metric and BEST
selection is unchanged (max full-series `sr`).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402
from scripts.baseline_v5_mix import costs_for_coin  # noqa: E402
from tradingagents.dataflows.coingecko_binance import _load_crypto_ohlcv  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.v2_sizing import (  # noqa: E402
    build_positions_with_hold,
    compute_realized_vol,
    vol_regime_mask,
)

ANN = np.sqrt(252)
COINS = ("bitcoin", "ethereum")
DEFAULT_START = "2021-11-07"
DEFAULT_END = "2025-03-31"
OUT_DIR = PROJECT_ROOT / "data" / "rebuild" / "factor_floor"

# Sizing constants (task brief — the shared causal path).
TARGET_VOL = 0.10
KELLY_FRACTION = 0.5
MAX_LEVERAGE = 3.0
MIN_HOLD = 7
EARLY_EXIT_LOSS = 0.015
VOL_LOOKBACK = 20
VOL_CAP = 0.95
PRICE_STOP_PCT = 0.03
INITIAL_CAPITAL = 10_000.0


# ── Signal builders — int8 {-1, 0, +1}, strictly from index <= t-1 ─────────
def tsmom_signal(closes: np.ndarray, k: int) -> np.ndarray:
    """Time-series momentum: sign(close[t-1] / close[t-1-k] - 1).

    The most recent price the signal at index t may see is close[t-1]; the
    k-day return therefore compares close[t-1] to close[t-1-k]. Bars with
    t < k + 1 (no valid t-1-k) emit 0.
    """
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    sig = np.zeros(n, dtype=np.int8)
    for t in range(k + 1, n):
        past, base = closes[t - 1], closes[t - 1 - k]
        if base > 0 and not np.isnan(past) and not np.isnan(base):
            sig[t] = np.sign(past / base - 1.0)
    return sig


def ma_cross_signal(closes: np.ndarray, fast: int, slow: int) -> np.ndarray:
    """MA crossover: sign(SMA_fast - SMA_slow), both windows ending at t-1.

    SMA_w at reference index j = mean(closes[j-w+1 : j+1]) needs j >= w-1.
    For signal[t] we use j = t-1, so the first non-zero bar is t = slow.
    Bars with t < slow emit 0 (warm-up neutral).
    """
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    sig = np.zeros(n, dtype=np.int8)
    # csum[i] = sum(closes[:i]) so a window mean is a difference of prefixes.
    csum = np.concatenate([[0.0], np.cumsum(closes)])
    for t in range(slow, n):
        j = t - 1  # last visible index
        fast_ma = (csum[j + 1] - csum[j + 1 - fast]) / fast
        slow_ma = (csum[j + 1] - csum[j + 1 - slow]) / slow
        sig[t] = np.sign(fast_ma - slow_ma)
    return sig


def donchian_signal(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, n: int
) -> np.ndarray:
    """Donchian breakout: enter on n-day high/low break, exit at mid-channel.

    Stateful. The signal at index t is the position state after observing the
    most recent completed bar t-1: the breakout close is close[t-1] and the
    n-day channel is built from the n bars strictly before it,
    highs/lows[t-1-n : t-1]. Bars with t < n + 1 emit 0.
    """
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)
    length = len(closes)
    sig = np.zeros(length, dtype=np.int8)
    state = 0
    for t in range(length):
        if t < n + 1:
            sig[t] = 0
            continue
        upper = np.max(highs[t - 1 - n : t - 1])   # n bars ending at t-2
        lower = np.min(lows[t - 1 - n : t - 1])
        mid = 0.5 * (upper + lower)
        c = closes[t - 1]                          # most recent visible close
        if c > upper:
            state = 1
        elif c < lower:
            state = -1
        elif state == 1 and c < mid:
            state = 0
        elif state == -1 and c > mid:
            state = 0
        sig[t] = state
    return sig


def xs_mom_signals(
    btc_closes: np.ndarray, eth_closes: np.ndarray, k: int = 30
) -> tuple[np.ndarray, np.ndarray]:
    """Cross-sectional momentum: long the stronger of BTC/ETH by k-day return,
    short the weaker (dollar-neutral pair). Both k-day returns computed on
    close[t-1] / close[t-1-k] - 1. Warm-up (t < k+1) emits (0, 0).

    Returns (btc_sig, eth_sig). The two arrays must be aligned on the same
    calendar; callers pass inner-joined closes.
    """
    btc = np.asarray(btc_closes, dtype=float)
    eth = np.asarray(eth_closes, dtype=float)
    length = min(len(btc), len(eth))
    btc_sig = np.zeros(length, dtype=np.int8)
    eth_sig = np.zeros(length, dtype=np.int8)
    for t in range(k + 1, length):
        rb = btc[t - 1] / btc[t - 1 - k] - 1.0 if btc[t - 1 - k] > 0 else np.nan
        re = eth[t - 1] / eth[t - 1 - k] - 1.0 if eth[t - 1 - k] > 0 else np.nan
        if np.isnan(rb) or np.isnan(re) or rb == re:
            continue
        if rb > re:
            btc_sig[t], eth_sig[t] = 1, -1
        else:
            btc_sig[t], eth_sig[t] = -1, 1
    return btc_sig, eth_sig


def long_only(sig: np.ndarray) -> np.ndarray:
    """max(sign, 0): drop shorts, keep the long leg only."""
    return np.maximum(sig, 0).astype(np.int8)


# ── Shared causal sizing path ──────────────────────────────────────────────
def _size_and_backtest(
    coin: str, dates: np.ndarray, closes: np.ndarray, highs: np.ndarray,
    lows: np.ndarray, signal: np.ndarray,
) -> tuple[pd.Series, bool]:
    """Signal (windowed) + real OHLC -> (daily net return series, halted flag).

    Causal pattern: px_sizing lags one bar (px_sizing[1:] = px[:-1]); vol,
    vol-mask and position hold-prices see close(D-1). The engine gets the real
    Close for P&L and real High/Low for the intrabar 3% price stop.

    ``halted`` mirrors ``run_coin_backtest``'s permanent max_portfolio_dd
    circuit breaker for this coin (see module docstring — HALT-LATCH
    TRANSPARENCY). It is surfaced so callers can report the halt date; it
    never affects the sizing/backtest math itself.
    """
    px = np.asarray(closes, dtype=float)
    px_sizing = np.empty_like(px)
    px_sizing[1:] = px[:-1]
    px_sizing[0] = px[0]

    rv = compute_realized_vol(px_sizing, lookback=VOL_LOOKBACK)
    mask = vol_regime_mask(rv, percentile_cap=VOL_CAP)
    conf = np.where(signal != 0, 1.0, 0.0)

    pos = build_positions_with_hold(
        signals=signal, vol_ok=mask, confidence=conf, realized_vol=rv,
        prices=px_sizing, target_vol=TARGET_VOL, kelly_fraction=KELLY_FRACTION,
        max_leverage=MAX_LEVERAGE, min_hold=MIN_HOLD,
        early_exit_loss=EARLY_EXIT_LOSS,
    )  # NO trend filter — the signal itself is the trend rule.

    # Core-coin causal costs; the 3% price stop replaces the equity-axis proxy.
    costs = costs_for_coin("bitcoin", convention="causal")
    costs["stop_loss"] = 1.0
    equity, m = run_coin_backtest(
        dates=dates, prices=px, positions=pos, initial_capital=INITIAL_CAPITAL,
        **costs, highs=np.asarray(highs, dtype=float),
        lows=np.asarray(lows, dtype=float), price_stop_pct=PRICE_STOP_PCT,
    )
    eq = np.asarray(equity, dtype=float)
    rets = eq[1:] / eq[:-1] - 1.0
    series = pd.Series(rets, index=pd.to_datetime(dates[1:]), name=coin)
    return series, bool(m["halted"])


def _coin_halt_date(series: pd.Series, halted: bool) -> str | None:
    """First date after which ``series`` is permanently zero, or None.

    Proxy (task-specified, simplest robust form): the index one bar after the
    LAST nonzero return — the halt latch zeros every subsequent bar, so this
    is exactly the date equity stops changing. Only computed when the engine
    itself reports ``halted=True`` for this coin.
    """
    if not halted:
        return None
    vals = series.to_numpy()
    nz = np.nonzero(vals)[0]
    idx = (nz[-1] + 1) if len(nz) else 0
    idx = min(idx, len(series.index) - 1)
    return series.index[idx].strftime("%Y-%m-%d")


def _trailing_zero_info(port: pd.Series) -> tuple[float, int]:
    """(sr_active, n_trailing_zero_bars) — SR truncated at the last nonzero
    portfolio return, with the trailing post-halt zero tail excluded.

    Diagnostic only (see module docstring); never used for BEST selection.
    Same annualization (sqrt(252), ddof=1) as the primary full-series SR.
    """
    vals = port.to_numpy()
    nz = np.nonzero(vals)[0]
    if len(nz) == 0:
        return 0.0, len(vals)
    last_nz = int(nz[-1])
    trimmed = vals[: last_nz + 1]
    n_trailing = len(vals) - (last_nz + 1)
    sd = trimmed.std(ddof=1) if len(trimmed) > 1 else 0.0
    sr = float(trimmed.mean() / sd * ANN) if sd > 0 else 0.0
    return sr, n_trailing


def _portfolio_metrics(df: pd.DataFrame) -> dict:
    """Equal-weight the coin columns; return SR/total_return/maxDD/n_bars."""
    port = df.mean(axis=1)
    eq = (1 + port).cumprod()
    dd = float((eq / eq.cummax() - 1.0).min())
    sd = port.std(ddof=1)
    sr = float(port.mean() / sd * ANN) if sd > 0 else 0.0
    return {
        "sharpe": sr,
        "total_return": float(eq.iloc[-1] - 1.0),
        "max_drawdown": dd,
        "n_bars": int(len(port)),
    }


# ── Data loading (full history, then windowed with signals) ────────────────
def _load_windowed(coin: str, start: str, end: str) -> pd.DataFrame:
    """Full-history OHLCV -> normalized, sorted, sliced to <= end.

    Signals are built on the FULL series (so a k=180 lookback at the window
    start still sees real prior prices), then the frame is windowed to
    [start, end] for the sizing/backtest pass (vol warm-up inside the window,
    matching the established baseline_v5_mix pattern).
    """
    df = _load_crypto_ohlcv(coin, end)
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.normalize()
    df = df[df["Date"] <= pd.to_datetime(end)]
    df = df.dropna(subset=["Close"]).sort_values("Date").reset_index(drop=True)
    return df


def _window_mask(dates: pd.Series, start: str, end: str) -> np.ndarray:
    return ((dates >= pd.to_datetime(start)) & (dates <= pd.to_datetime(end))).values


# ── Config enumeration (18, pinned) ────────────────────────────────────────
def build_config_specs() -> list[dict]:
    """Return the 18 pre-registered config specs.

    Each per-coin config carries a ``builder(df) -> int8 array`` over the FULL
    history. The single XS-momentum config is flagged ``xs=True`` and handled
    by the cross-sectional path instead.
    """
    specs: list[dict] = []

    # TSMOM long-short + long-only, k in {7,14,30,90}; plus k=180 long-short.
    for k in (7, 14, 30, 90):
        specs.append({
            "name": f"tsmom_k{k}_ls", "family": "tsmom", "k": k, "side": "ls",
            "builder": (lambda df, k=k: tsmom_signal(df["Close"].values, k)),
        })
    for k in (7, 14, 30, 90):
        specs.append({
            "name": f"tsmom_k{k}_lo", "family": "tsmom", "k": k, "side": "lo",
            "builder": (lambda df, k=k: long_only(tsmom_signal(df["Close"].values, k))),
        })
    specs.append({  # the documented 18th config
        "name": "tsmom_k180_ls", "family": "tsmom", "k": 180, "side": "ls",
        "builder": (lambda df: tsmom_signal(df["Close"].values, 180)),
    })

    # MA cross long-short + long-only.
    for fast, slow in ((10, 50), (20, 100), (50, 200)):
        specs.append({
            "name": f"macross_{fast}_{slow}_ls", "family": "ma_cross",
            "fast": fast, "slow": slow, "side": "ls",
            "builder": (lambda df, f=fast, s=slow: ma_cross_signal(df["Close"].values, f, s)),
        })
    for fast, slow in ((10, 50), (20, 100), (50, 200)):
        specs.append({
            "name": f"macross_{fast}_{slow}_lo", "family": "ma_cross",
            "fast": fast, "slow": slow, "side": "lo",
            "builder": (lambda df, f=fast, s=slow: long_only(ma_cross_signal(df["Close"].values, f, s))),
        })

    # Donchian long-short.
    for nn in (20, 55):
        specs.append({
            "name": f"donchian_n{nn}_ls", "family": "donchian", "n": nn, "side": "ls",
            "builder": (lambda df, nn=nn: donchian_signal(
                df["High"].values, df["Low"].values, df["Close"].values, nn)),
        })

    # XS momentum BTC-vs-ETH 30d (dollar-neutral pair) — special path.
    specs.append({
        "name": "xsmom_btc_eth_30d", "family": "xs_mom", "k": 30, "side": "ls",
        "xs": True,
    })

    assert len(specs) == 18, f"expected 18 configs, got {len(specs)}"
    return specs


# ── Runners ─────────────────────────────────────────────────────────────────
def run_per_coin_config(spec: dict, data: dict[str, pd.DataFrame],
                        start: str, end: str) -> tuple[pd.DataFrame, dict]:
    """Build one config's BTC+ETH daily-return frame (same builder per coin).

    Returns (returns_df, halts) where halts maps coin -> {"halted": bool,
    "date": str | None} (see module docstring, HALT-LATCH TRANSPARENCY).
    """
    cols = {}
    halts = {}
    for coin in COINS:
        df = data[coin]
        sig_full = np.asarray(spec["builder"](df), dtype=np.int8)
        m = _window_mask(df["Date"], start, end)
        series, halted = _size_and_backtest(
            coin, df["Date"].values[m], df["Close"].values[m],
            df["High"].values[m], df["Low"].values[m], sig_full[m],
        )
        cols[coin] = series
        halts[coin] = {"halted": halted, "date": _coin_halt_date(series, halted)}
    return pd.DataFrame(cols).dropna().sort_index(), halts


def run_xs_config(spec: dict, data: dict[str, pd.DataFrame],
                  start: str, end: str) -> tuple[pd.DataFrame, dict]:
    """Cross-sectional BTC/ETH pair on the shared (inner-joined) calendar.

    Returns (returns_df, halts) — see run_per_coin_config.
    """
    btc, eth = data["bitcoin"], data["ethereum"]
    merged = btc[["Date", "Close", "High", "Low"]].merge(
        eth[["Date", "Close", "High", "Low"]], on="Date",
        suffixes=("_btc", "_eth")).sort_values("Date").reset_index(drop=True)
    btc_sig_full, eth_sig_full = xs_mom_signals(
        merged["Close_btc"].values, merged["Close_eth"].values, k=spec["k"])
    m = _window_mask(merged["Date"], start, end)
    dates = merged["Date"].values[m]
    btc_series, btc_halted = _size_and_backtest(
        "bitcoin", dates, merged["Close_btc"].values[m],
        merged["High_btc"].values[m], merged["Low_btc"].values[m],
        btc_sig_full[m])
    eth_series, eth_halted = _size_and_backtest(
        "ethereum", dates, merged["Close_eth"].values[m],
        merged["High_eth"].values[m], merged["Low_eth"].values[m],
        eth_sig_full[m])
    cols = {"bitcoin": btc_series, "ethereum": eth_series}
    halts = {
        "bitcoin": {"halted": btc_halted, "date": _coin_halt_date(btc_series, btc_halted)},
        "ethereum": {"halted": eth_halted, "date": _coin_halt_date(eth_series, eth_halted)},
    }
    return pd.DataFrame(cols).dropna().sort_index(), halts


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default=DEFAULT_START)
    p.add_argument("--end", default=DEFAULT_END)
    p.add_argument("--output-dir", default=str(OUT_DIR))
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 78}")
    print(f"  Factor floor — 18 pre-registered model-free configs")
    print(f"  window: {args.start} -> {args.end}   coins: {', '.join(COINS)}")
    print(f"{'=' * 78}\n")

    data = {c: _load_windowed(c, args.start, args.end) for c in COINS}
    specs = build_config_specs()

    rows = []  # (name, metrics, df)
    for spec in specs:
        if spec.get("xs"):
            df, halts = run_xs_config(spec, data, args.start, args.end)
        else:
            df, halts = run_per_coin_config(spec, data, args.start, args.end)
        m = _portfolio_metrics(df)
        port = df.mean(axis=1)
        sr_active, n_trailing = _trailing_zero_info(port)
        m["sr_active"] = sr_active
        m["n_trailing_zero_bars"] = n_trailing
        m["halted_bitcoin"] = halts["bitcoin"]
        m["halted_ethereum"] = halts["ethereum"]
        cfg = {k: v for k, v in spec.items() if k not in ("builder",)}
        log_trial(
            experiment="factor_floor", config=cfg,
            window=(args.start, args.end), metrics=m,
        )
        rows.append((spec["name"], m, df))
        print(f"  {spec['name']:22s}  SR={m['sharpe']:+.2f} (active {sr_active:+.2f})  "
              f"ret={m['total_return']:+8.1%}  maxDD={m['max_drawdown']:6.1%}  "
              f"({m['n_bars']} bars, {n_trailing} trailing-zero)")

    rows.sort(key=lambda r: r[1]["sharpe"], reverse=True)

    def _halt_str(m: dict) -> str:
        parts = []
        for label, key in (("ETH", "halted_ethereum"), ("BTC", "halted_bitcoin")):
            h = m[key]
            if h["halted"]:
                parts.append(f"{label} {h['date']}")
        return "; ".join(parts) if parts else "—"

    # Floor table.
    lines = [
        "# Factor floor — 18 pre-registered model-free configs",
        "",
        f"Window: {args.start} .. {args.end} (dev). Coins: bitcoin + ethereum, "
        "equal weight.",
        "Shared causal sizing path (target_vol=0.10, kelly=0.5, max_lev=3.0, "
        "min_hold=7, early_exit=0.015, vol_lookback=20, vol_cap=0.95, "
        "price_stop=3%). Sorted by portfolio Sharpe (desc).",
        "",
        "**Halt-latch transparency** (adjudicated Critical finding, "
        "2026-07-09): `run_coin_backtest`'s max_portfolio_dd=0.15 circuit "
        "breaker is a PERMANENT per-coin latch — once tripped it never "
        "resets, and every later bar for that coin is a flat 0.0. The halt "
        "is kept as-is (it is the live-system circuit breaker, applied "
        "identically to every config, so full-series SR stays a fair gate "
        "metric), but is now surfaced for transparency: `sr_active` is the "
        "portfolio Sharpe computed only up to the last nonzero portfolio "
        "return (trailing post-halt zero tail excluded) — diagnostic only, "
        "never used for BEST selection, which remains max full-series `sr`. "
        "`halts` lists the first date each coin's returns went permanently "
        "to zero. `n_trailing_zero_bars` is the portfolio-level trailing "
        "zero-bar count.",
        "",
        "| rank | config | sr | sr_active | total_return | maxDD | halts | "
        "n_trailing_zero_bars | n_bars |",
        "|-----:|--------|-----:|-----:|-------------:|------:|-------|"
        "---------------------:|-------:|",
    ]
    for rank, (name, m, _df) in enumerate(rows, start=1):
        lines.append(
            f"| {rank} | {name} | {m['sharpe']:+.3f} | {m['sr_active']:+.3f} | "
            f"{m['total_return']:+.1%} | {m['max_drawdown']:.1%} | "
            f"{_halt_str(m)} | {m['n_trailing_zero_bars']} | {m['n_bars']} |")
    lines.append("")
    best_name = rows[0][0]
    best_m = rows[0][1]
    lines.append(
        f"**Best config: `{best_name}`** — portfolio SR {best_m['sharpe']:+.3f} "
        f"(active-period SR {best_m['sr_active']:+.3f}), "
        f"total return {best_m['total_return']:+.1%}, "
        f"maxDD {best_m['max_drawdown']:.1%}, halts: {_halt_str(best_m)}. "
        "Selection remains max full-series SR (`sr`); `sr_active` is "
        "diagnostic only — see Halt-latch transparency note above.")
    lines.append("")
    (out_dir / "floor_table.md").write_text("\n".join(lines))

    # BEST daily returns.
    best_df = rows[0][2].copy()
    best_df["portfolio"] = best_df.mean(axis=1)
    best_out = out_dir / "BEST"
    if best_out.exists():
        shutil.rmtree(best_out)
    best_out.mkdir(parents=True, exist_ok=True)
    best_df.index.name = "date"
    best_df.reset_index()[["date", "bitcoin", "ethereum", "portfolio"]].to_csv(
        best_out / "daily_returns.csv", index=False)

    # Append-only ledger note documenting the halt-transparency decision
    # (the existing 18 per-config rows above are never rewritten).
    log_trial(
        experiment="factor_floor",
        config={"kind": "halt_transparency_note"},
        window=(args.start, args.end),
        metrics={
            "best_sr_full": best_m["sharpe"],
            "best_sr_active": best_m["sr_active"],
            "decision": "identical-engine dual-reporting",
        },
    )

    print(f"\n{'=' * 78}")
    print(f"  BEST: {best_name}  SR={best_m['sharpe']:+.3f}  "
          f"ret={best_m['total_return']:+.1%}  maxDD={best_m['max_drawdown']:.1%}")
    print(f"  floor table -> {out_dir / 'floor_table.md'}")
    print(f"  best series -> {best_out / 'daily_returns.csv'}")
    print(f"{'=' * 78}\n")


if __name__ == "__main__":
    main()
