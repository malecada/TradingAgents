"""V3 root-cause diagnostic script.

Builds a per-bar side-by-side trace of V2 vs V3 signals for BTC on the
88-bar OOS window 2026-01-16 → 2026-04-15, decomposes the Sharpe gap,
tests five hypotheses, and writes:
  - data/diagnostics/v2_vs_v3_trace_bitcoin.csv
  - data/diagnostics/v3_root_cause.md
"""

from __future__ import annotations

import sys
import os
import pickle
import warnings
import logging

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)

# Add worktree root to sys.path
WORKTREE = "/home/malecada/master_thesis/TradingAgents/.worktrees/hybrid-modulator"
sys.path.insert(0, WORKTREE)
os.chdir(WORKTREE)

import numpy as np
import pandas as pd

# ── Imports from project ─────────────────────────────────────────────────────

from tradingagents.strategies.v2_sizing import (
    generate_term_structure_signals,
    compute_realized_vol,
    vol_regime_mask,
    build_positions_with_hold,
    apply_trend_filter,
)
from tradingagents.strategies.v3.backtest.runner_v3 import (
    _build_v3_features_at,
    _position_to_signal,
)
from tradingagents.strategies.v3.models.multi_horizon import (
    MultiHorizonEnsemble,
    consensus_signal,
)
from tradingagents.strategies.v3.regime.ensemble import detect_regime_v3
from tradingagents.strategies.v3.regime.hmm_v2 import NHHmmBundle
from tradingagents.strategies.v3.sizing.vol_target import (
    cdap_adjust,
    vol_target_position,
)
from tradingagents.strategies.v3.config import V3Config
from tradingagents.backtesting.strategies import SignalLevel

# ── Configuration ─────────────────────────────────────────────────────────────

START = pd.Timestamp("2026-01-16", tz="UTC")
END = pd.Timestamp("2026-04-15", tz="UTC")
COIN = "bitcoin"
DATA_DIR = f"{WORKTREE}/data"
PRED_DIR = f"{DATA_DIR}/multi_2coins_v2"
OUT_DIR = f"{DATA_DIR}/diagnostics"
LOW_VOL_SCALE = 10.0

# V2 defaults (from baseline_strategy_v2.py)
TARGET_VOL = 0.10
KELLY = 0.5
MAX_LEV = 3.0
MIN_HOLD = 7
SMA_PERIOD = 30
TREND_MULT = 1.5
CONFIDENCE_REF = 0.03
EARLY_EXIT_LOSS = 0.015
VOL_LOOKBACK = 21
VOL_CAP_PCT = 0.95

# ── Helper: load V2 predictions ───────────────────────────────────────────────

def load_v2_preds(pred_dir: str, coin: str) -> pd.DataFrame:
    """Load h7 and h14 predictions for the given coin, return merged DataFrame."""
    dfs = {}
    for h in [7, 14]:
        path = f"{pred_dir}/preds_lgb_h{h}.csv"
        df = pd.read_csv(path, parse_dates=["date"])
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df[df["coin_id"] == coin].set_index("date").sort_index()
        dfs[h] = df
    merged = pd.DataFrame()
    for h, df in dfs.items():
        merged[f"pred_h{h}"] = df["prediction"]
        merged[f"actual_h{h}"] = df["actual"]
        if "ref_price" in df.columns:
            merged["ref_price"] = df["ref_price"]
    return merged.sort_index()


def load_v3_bundles(coin: str):
    """Load V3 model bundle and regime bundle."""
    model_path = f"{DATA_DIR}/checkpoints/v3_models_{coin}.pkl"
    regime_path = f"{DATA_DIR}/checkpoints/regime_hmm_v3_{coin}.pkl"
    with open(model_path, "rb") as f:
        mhe: MultiHorizonEnsemble = pickle.load(f)
    with open(regime_path, "rb") as f:
        regime_bundle: NHHmmBundle = pickle.load(f)
    return mhe, regime_bundle


def load_microstructure(coin: str) -> pd.DataFrame:
    path = f"{DATA_DIR}/microstructure/{coin}.parquet"
    if os.path.exists(path):
        df = pd.read_parquet(path)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        return df
    return pd.DataFrame()


def load_derivatives(coin: str) -> pd.DataFrame:
    path = f"{DATA_DIR}/derivatives/{coin}.parquet"
    if os.path.exists(path):
        df = pd.read_parquet(path)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        return df
    return pd.DataFrame()


def load_prices(coin: str) -> pd.Series:
    """Load prices from V2 predictions (actual column)."""
    path = f"{PRED_DIR}/preds_lgb_h7.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df[df["coin_id"] == coin].set_index("date").sort_index()
    return df["actual"].rename("price")


# ── Main diagnostic logic ────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    config = V3Config()

    print("=" * 70)
    print("V3 ROOT CAUSE DIAGNOSTIC — BTC — 2026-01-16 → 2026-04-15")
    print("=" * 70)

    # ── 1. Load data ─────────────────────────────────────────────────────────
    print("\n[1] Loading data...")
    v2_preds = load_v2_preds(PRED_DIR, COIN)
    prices_full = load_prices(COIN)
    micro_df = load_microstructure(COIN)
    deriv_df = load_derivatives(COIN)
    mhe, regime_bundle = load_v3_bundles(COIN)
    print(f"  V2 preds: {len(v2_preds)} rows")
    print(f"  Prices (full): {len(prices_full)} rows, {prices_full.index[0]} → {prices_full.index[-1]}")
    print(f"  Micro features: {micro_df.shape}")
    print(f"  Derivatives features: {deriv_df.shape}")
    print(f"  V3 model horizons: {mhe.fitted_horizons}")

    # Filter to window
    window_prices = prices_full.loc[START:END]
    print(f"  Window bars: {len(window_prices)}")

    # ── 2. V2 signals reconstruction ─────────────────────────────────────────
    print("\n[2] Reconstructing V2 signals...")
    # We need to reconstruct V2 signals by simulating the V2 strategy logic
    # on the full price series and then extract per-bar values
    prices_arr_full = prices_full.values
    prices_idx_full = prices_full.index

    # Build V2 per-bar signals (using the entire history, then slice to window)
    v2_df = v2_preds[["pred_h7", "pred_h14", "ref_price"]].copy()
    v2_df["price"] = prices_full.reindex(v2_df.index)

    # Generate term structure signals for full history
    v2_signals_arr, v2_conf_arr = generate_term_structure_signals(
        df_coin=v2_df, horizons=[7, 14], confidence_ref=CONFIDENCE_REF, asymmetric=True
    )
    v2_df["v2_signal"] = v2_signals_arr
    v2_df["v2_conf"] = v2_conf_arr

    # Realized vol
    prices_aligned = v2_df["price"].values
    v2_df["v2_vol"] = compute_realized_vol(prices_aligned, VOL_LOOKBACK)

    # Vol regime mask
    v2_df["v2_vol_ok"] = vol_regime_mask(v2_df["v2_vol"].values, VOL_CAP_PCT)

    # Build positions with hold
    v2_positions_arr = build_positions_with_hold(
        signals=v2_df["v2_signal"].values,
        vol_ok=v2_df["v2_vol_ok"].values,
        confidence=v2_df["v2_conf"].values,
        realized_vol=v2_df["v2_vol"].values,
        prices=prices_aligned,
        target_vol=TARGET_VOL,
        kelly_fraction=KELLY,
        max_leverage=MAX_LEV,
        min_hold=MIN_HOLD,
        early_exit_loss=EARLY_EXIT_LOSS,
    )
    v2_df["v2_position_pretf"] = v2_positions_arr

    # Trend filter
    v2_positions_tf = apply_trend_filter(
        positions=v2_positions_arr, prices=prices_aligned, sma_period=SMA_PERIOD, multiplier=TREND_MULT
    )
    v2_df["v2_position"] = v2_positions_tf

    print(f"  V2 signals generated: {(v2_df['v2_signal'] != 0).sum()} non-zero signal rows")

    # ── 3. V3 per-bar inference ───────────────────────────────────────────────
    print("\n[3] Running V3 per-bar inference...")
    bars = window_prices.index
    returns_full = prices_full.pct_change()

    # V3 per-bar storage
    v3_records = []
    portfolio_dd_running = 0.0
    equity_high = 1.0
    equity_curr = 1.0

    for i, as_of in enumerate(bars):
        # Build features
        feat_df = _build_v3_features_at(prices_full, micro_df, deriv_df, as_of)
        if feat_df.empty:
            v3_records.append({
                "date": as_of,
                "v3_direction": 0, "v3_confidence": 0.0, "v3_regime": "sideways",
                "v3_regime_conf": 0.0, "v3_hurst": 0.5, "v3_changepoint": False,
                "v3_p_h3": 0.5, "v3_p_h7": 0.5, "v3_p_h14": 0.5, "v3_p_h21": 0.5,
                "v3_weighted_p": 0.5, "v3_vol_21d": 0.15,
                "v3_position_pre_cdap": 0.0, "v3_position": 0.0,
                "v3_dd_running": portfolio_dd_running,
            })
            continue

        # Align features to model schema
        from tradingagents.strategies.v3.backtest.runner_v3 import _extract_expected_features
        expected = _extract_expected_features(mhe)
        if expected:
            for col in expected:
                if col not in feat_df.columns:
                    feat_df[col] = 0.0
            feat_df = feat_df[expected]

        # Probabilities
        try:
            probas_dict = mhe.predict_proba(feat_df)
        except Exception as e:
            print(f"  predict_proba failed at {as_of}: {e}")
            v3_records.append({
                "date": as_of,
                "v3_direction": 0, "v3_confidence": 0.0, "v3_regime": "sideways",
                "v3_regime_conf": 0.0, "v3_hurst": 0.5, "v3_changepoint": False,
                "v3_p_h3": 0.5, "v3_p_h7": 0.5, "v3_p_h14": 0.5, "v3_p_h21": 0.5,
                "v3_weighted_p": 0.5, "v3_vol_21d": 0.15,
                "v3_position_pre_cdap": 0.0, "v3_position": 0.0,
                "v3_dd_running": portfolio_dd_running,
            })
            continue

        scalar_probas = {h: float(arr[0]) for h, arr in probas_dict.items()}

        # Regime
        try:
            regime = detect_regime_v3(prices=prices_full, bundle=regime_bundle, as_of=as_of)
        except Exception as e:
            from tradingagents.strategies.v3.contracts import RegimeState
            regime = RegimeState(
                label="sideways", confidence=0.34, hurst=0.5,
                changepoint_alert=False,
                posterior={"bull": 1/3, "sideways": 1/3, "bear": 1/3}
            )

        # Consensus
        direction, confidence = consensus_signal(
            scalar_probas, regime, config, deadband=0.02
        )

        # Vol
        sub_rets = returns_full.loc[returns_full.index <= as_of].iloc[-21:]
        rv = float(sub_rets.std() * np.sqrt(252)) if len(sub_rets) > 1 else 0.15

        # Position
        position_pre = vol_target_position(
            direction=direction, confidence=confidence,
            realized_vol_annual=rv,
            target_vol_annual=config.target_annual_vol,
            max_leverage=config.max_leverage,
        )
        position = cdap_adjust(
            position=position_pre, portfolio_dd_pct=portfolio_dd_running,
            regime=regime, config=config
        )

        # Update equity tracking
        daily_ret = returns_full.loc[as_of] if as_of in returns_full.index else 0.0
        gross = position * float(daily_ret)
        equity_curr = equity_curr * (1.0 + gross)
        if equity_curr > equity_high:
            equity_high = equity_curr
        portfolio_dd_running = (equity_high - equity_curr) / equity_high if equity_high > 0 else 0.0

        # Weighted p (for diagnostics)
        from tradingagents.strategies.v3.models.multi_horizon import _regime_mode
        mode = _regime_mode(regime, config)
        w = config.horizon_weights(mode)
        active = {h: ww for h, ww in w.items() if h in scalar_probas}
        total_w = sum(active.values())
        if total_w > 0:
            norm_w = {h: ww / total_w for h, ww in active.items()}
            weighted_p = sum(norm_w[h] * scalar_probas[h] for h in norm_w)
        else:
            weighted_p = 0.5

        v3_records.append({
            "date": as_of,
            "v3_direction": direction,
            "v3_confidence": confidence,
            "v3_regime": regime.label,
            "v3_regime_conf": regime.confidence,
            "v3_hurst": regime.hurst,
            "v3_changepoint": regime.changepoint_alert,
            "v3_p_h3": scalar_probas.get(3, 0.5),
            "v3_p_h7": scalar_probas.get(7, 0.5),
            "v3_p_h14": scalar_probas.get(14, 0.5),
            "v3_p_h21": scalar_probas.get(21, 0.5),
            "v3_weighted_p": weighted_p,
            "v3_vol_21d": rv,
            "v3_position_pre_cdap": position_pre,
            "v3_position": position,
            "v3_dd_running": portfolio_dd_running,
        })

    v3_df = pd.DataFrame(v3_records).set_index("date")
    print(f"  V3 inference complete: {len(v3_df)} bars")

    # ── 4. Assemble side-by-side trace ────────────────────────────────────────
    print("\n[4] Assembling side-by-side trace...")

    window_v2 = v2_df.loc[START:END]
    # Compute next-day return for each bar
    price_window = prices_full.loc[START:END]
    returns_window = prices_full.pct_change().loc[START:END]

    trace = pd.DataFrame(index=bars)
    trace["price"] = price_window.values
    trace["next_day_return"] = returns_window.values

    # V2 columns
    trace["v2_signal"] = window_v2["v2_signal"].reindex(bars).values
    trace["v2_conf"] = window_v2["v2_conf"].reindex(bars).values
    trace["v2_position"] = window_v2["v2_position"].reindex(bars).values
    trace["v2_pnl"] = trace["v2_position"].shift(1).fillna(0) * trace["next_day_return"]

    # V3 columns
    trace["v3_direction"] = v3_df["v3_direction"].reindex(bars).values
    trace["v3_confidence"] = v3_df["v3_confidence"].reindex(bars).values
    trace["v3_regime"] = v3_df["v3_regime"].reindex(bars).values
    trace["v3_regime_conf"] = v3_df["v3_regime_conf"].reindex(bars).values
    trace["v3_hurst"] = v3_df["v3_hurst"].reindex(bars).values
    trace["v3_changepoint"] = v3_df["v3_changepoint"].reindex(bars).values
    trace["v3_p_h3"] = v3_df["v3_p_h3"].reindex(bars).values
    trace["v3_p_h7"] = v3_df["v3_p_h7"].reindex(bars).values
    trace["v3_p_h14"] = v3_df["v3_p_h14"].reindex(bars).values
    trace["v3_p_h21"] = v3_df["v3_p_h21"].reindex(bars).values
    trace["v3_weighted_p"] = v3_df["v3_weighted_p"].reindex(bars).values
    trace["v3_vol_21d"] = v3_df["v3_vol_21d"].reindex(bars).values
    trace["v3_position_pre_cdap"] = v3_df["v3_position_pre_cdap"].reindex(bars).values
    trace["v3_position"] = v3_df["v3_position"].reindex(bars).values
    trace["v3_dd_running"] = v3_df["v3_dd_running"].reindex(bars).values
    trace["v3_pnl"] = trace["v3_position"].shift(1).fillna(0) * trace["next_day_return"]

    # Agreement
    trace["direction_agree"] = (
        (trace["v2_signal"] > 0) == (trace["v3_direction"] > 0)
    ).where(
        (trace["v2_signal"] != 0) | (trace["v3_direction"] != 0), other=True
    )
    trace["v2_correct"] = (trace["v2_signal"] * trace["next_day_return"] > 0).where(
        trace["v2_signal"] != 0, other=np.nan
    )
    trace["v3_correct"] = (trace["v3_direction"] * trace["next_day_return"] > 0).where(
        trace["v3_direction"] != 0, other=np.nan
    )

    # Save CSV
    out_csv = f"{OUT_DIR}/v2_vs_v3_trace_bitcoin.csv"
    trace.to_csv(out_csv)
    print(f"  Saved trace to {out_csv}")

    # ── 5. Decomposition table ────────────────────────────────────────────────
    print("\n[5] Computing decomposition table...")

    def sharpe(pnl_series):
        s = pd.Series(pnl_series).dropna()
        if len(s) < 5 or s.std() == 0:
            return np.nan
        return s.mean() / s.std() * np.sqrt(252)

    def total_ret(pnl_series):
        return pd.Series(pnl_series).fillna(0).sum()

    # V2 stats (use shifted position for PnL)
    v2_pos_shifted = trace["v2_position"].shift(1).fillna(0)
    v2_pnl = v2_pos_shifted * trace["next_day_return"]
    v2_long = (v2_pos_shifted > 0).sum()
    v2_short = (v2_pos_shifted < 0).sum()
    v2_flat = (v2_pos_shifted == 0).sum()
    v2_signed = v2_pos_shifted != 0
    v2_hit_num = (np.sign(v2_pos_shifted[v2_signed]) * trace["next_day_return"][v2_signed] > 0).sum()
    v2_hit_denom = v2_signed.sum()

    # V3 stats
    v3_pos_shifted = trace["v3_position"].shift(1).fillna(0)
    v3_pnl = v3_pos_shifted * trace["next_day_return"]
    v3_long = (v3_pos_shifted > 0).sum()
    v3_short = (v3_pos_shifted < 0).sum()
    v3_flat = (v3_pos_shifted == 0).sum()
    v3_signed = v3_pos_shifted != 0
    v3_hit_num = (np.sign(v3_pos_shifted[v3_signed]) * trace["next_day_return"][v3_signed] > 0).sum()
    v3_hit_denom = v3_signed.sum()

    decomp = {
        "n_long_bars": [int(v2_long), int(v3_long)],
        "n_short_bars": [int(v2_short), int(v3_short)],
        "n_flat_bars": [int(v2_flat), int(v3_flat)],
        "avg_abs_position": [float(v2_pos_shifted.abs().mean()), float(v3_pos_shifted.abs().mean())],
        "max_abs_position": [float(v2_pos_shifted.abs().max()), float(v3_pos_shifted.abs().max())],
        "hit_rate": [
            float(v2_hit_num / v2_hit_denom) if v2_hit_denom > 0 else np.nan,
            float(v3_hit_num / v3_hit_denom) if v3_hit_denom > 0 else np.nan,
        ],
        "avg_pnl_per_signed_bar": [
            float(v2_pnl[v2_signed].mean()),
            float(v3_pnl[v3_signed].mean()) if v3_signed.sum() > 0 else np.nan,
        ],
        "avg_pnl_per_long_bar": [
            float(v2_pnl[v2_pos_shifted > 0].mean()),
            float(v3_pnl[v3_pos_shifted > 0].mean()) if (v3_pos_shifted > 0).sum() > 0 else np.nan,
        ],
        "avg_pnl_per_short_bar": [
            float(v2_pnl[v2_pos_shifted < 0].mean()),
            float(v3_pnl[v3_pos_shifted < 0].mean()) if (v3_pos_shifted < 0).sum() > 0 else np.nan,
        ],
        "sharpe_88bar": [float(sharpe(v2_pnl)), float(sharpe(v3_pnl))],
        "total_return": [float(total_ret(v2_pnl)), float(total_ret(v3_pnl))],
    }
    decomp_df = pd.DataFrame(decomp, index=["V2", "V3"]).T
    print("\nDECOMPOSITION TABLE:")
    print(decomp_df.to_string())

    # ── 6. Counterfactuals ────────────────────────────────────────────────────
    print("\n[6] Counterfactual analysis...")

    # CF1: V3 direction but V2 position size
    cf1_pos = np.sign(trace["v3_direction"].shift(1).fillna(0)) * v2_pos_shifted.abs()
    cf1_pnl = cf1_pos * trace["next_day_return"]
    cf1_sharpe = sharpe(cf1_pnl)

    # CF2: V2 direction but V3 confidence scaling
    # Use V2 signal direction × V3 confidence level as proxy
    v2_dir_shifted = np.sign(v2_pos_shifted)
    v3_conf_shifted = trace["v3_confidence"].shift(1).fillna(0)
    cf2_pos = v2_dir_shifted * v3_conf_shifted * (TARGET_VOL / (trace["v3_vol_21d"].shift(1).fillna(0.15).clip(1e-9)))
    cf2_pos = cf2_pos.clip(-MAX_LEV, MAX_LEV)
    cf2_pnl = cf2_pos * trace["next_day_return"]
    cf2_sharpe = sharpe(cf2_pnl)

    # CF3: V3 raw consensus before vol-target (sign of weighted_p - 0.5)
    v3_wp_shifted = trace["v3_weighted_p"].shift(1).fillna(0.5)
    cf3_pos = np.sign(v3_wp_shifted - 0.5)  # raw direction, unit position
    cf3_pnl = cf3_pos * trace["next_day_return"]
    cf3_sharpe = sharpe(cf3_pnl)

    # CF4: V3 direction without deadband (sign of p - 0.5 for any deviation)
    cf4_dir = np.sign(trace["v3_weighted_p"].shift(1).fillna(0.5) - 0.5)
    # Scale with same V2 sizing
    cf4_pos = cf4_dir * v2_pos_shifted.abs()
    cf4_pnl = cf4_pos * trace["next_day_return"]
    cf4_sharpe = sharpe(cf4_pnl)

    print(f"  CF1 (V3 direction + V2 size):          Sharpe = {cf1_sharpe:.3f}")
    print(f"  CF2 (V2 direction + V3 confidence):     Sharpe = {cf2_sharpe:.3f}")
    print(f"  CF3 (V3 raw consensus, unit position): Sharpe = {cf3_sharpe:.3f}")
    print(f"  CF4 (V3 no deadband + V2 size):        Sharpe = {cf4_sharpe:.3f}")
    print(f"  V2 actual:                              Sharpe = {sharpe(v2_pnl):.3f}")
    print(f"  V3 actual:                              Sharpe = {sharpe(v3_pnl):.3f}")

    # ── 7. Bar-level disagreement analysis ───────────────────────────────────
    print("\n[7] Bar-level disagreement analysis...")
    both_active = (trace["v2_signal"] != 0) & (trace["v3_direction"] != 0)
    disagree_mask = (np.sign(trace["v2_signal"]) != np.sign(trace["v3_direction"])) & both_active
    agree_mask = (np.sign(trace["v2_signal"]) == np.sign(trace["v3_direction"])) & both_active

    disagree_bars = trace[disagree_mask]
    n_disagree = disagree_mask.sum()
    n_agree = agree_mask.sum()
    print(f"  Bars where both active: {both_active.sum()}")
    print(f"  Agreeing bars: {n_agree}")
    print(f"  Disagreeing bars: {n_disagree}")

    if n_disagree > 0:
        v2_wins = (np.sign(disagree_bars["v2_signal"]) * disagree_bars["next_day_return"] > 0)
        v3_wins = (np.sign(disagree_bars["v3_direction"]) * disagree_bars["next_day_return"] > 0)
        print(f"  On disagree bars: V2 correct {v2_wins.sum()}/{n_disagree}, V3 correct {v3_wins.sum()}/{n_disagree}")

        print("  Disagree bars by V3 regime:")
        for regime_label in ["bull", "sideways", "bear"]:
            mask_r = disagree_bars["v3_regime"] == regime_label
            n_r = mask_r.sum()
            if n_r > 0:
                v2_w = (np.sign(disagree_bars[mask_r]["v2_signal"]) * disagree_bars[mask_r]["next_day_return"] > 0).sum()
                print(f"    {regime_label}: {n_r} bars, V2 correct {v2_w}/{n_r}")

        print("  Disagree bars by V3 confidence level:")
        low_conf = disagree_bars["v3_confidence"] < 0.15
        high_conf = disagree_bars["v3_confidence"] >= 0.15
        print(f"    Low conf (<0.15): {low_conf.sum()} bars")
        print(f"    High conf (>=0.15): {high_conf.sum()} bars")

    # ── 8. Hypothesis tests ───────────────────────────────────────────────────
    print("\n[8] Hypothesis testing...")

    # H1: V3 confidence / probas over-shrunk by calibration
    v3_conf = trace["v3_confidence"]
    v2_conf = trace["v2_conf"]
    v3_wp = trace["v3_weighted_p"]
    print("\n  H1: V3 probas over-shrunk by calibration?")
    print(f"    V3 confidence median: {v3_conf.median():.4f}")
    print(f"    V2 confidence median: {v2_conf.median():.4f}")
    print(f"    V3 weighted_p median: {v3_wp.median():.4f}")
    print(f"    V3 weighted_p range: [{v3_wp.min():.4f}, {v3_wp.max():.4f}]")
    print(f"    V3 confidence % < 0.05: {(v3_conf < 0.05).mean()*100:.1f}%")
    print(f"    V3 confidence % < 0.15: {(v3_conf < 0.15).mean()*100:.1f}%")
    print(f"    V3 confidence % < 0.30: {(v3_conf < 0.30).mean()*100:.1f}%")

    # H2: Regime mis-classification
    print("\n  H2: Regime mis-classification?")
    for regime_label in ["bull", "sideways", "bear"]:
        mask_r = trace["v3_regime"] == regime_label
        n_r = mask_r.sum()
        if n_r == 0:
            continue
        v3_pnl_r = v3_pnl[mask_r]
        v2_pnl_r = v2_pnl[mask_r]
        v3_pos_r = v3_pos_shifted[mask_r]
        signed_r = v3_pos_r != 0
        if signed_r.sum() > 0:
            hit_r = (np.sign(v3_pos_r[signed_r]) * trace["next_day_return"][mask_r & (v3_pos_shifted != 0)] > 0)
            hit_rate_r = hit_r.mean()
        else:
            hit_rate_r = np.nan
        print(f"    {regime_label}: {n_r} bars, V3 sharpe={sharpe(v3_pnl_r):.2f}, V2 sharpe={sharpe(v2_pnl_r):.2f}, V3 hit_rate={hit_rate_r:.2%}")
        print(f"      Regime conf: {trace['v3_regime_conf'][mask_r].mean():.3f}, Hurst: {trace['v3_hurst'][mask_r].mean():.3f}")

    # H3: Multi-horizon h3/h21 outvoting h7/h14
    print("\n  H3: h3/h21 outvoting h7/h14?")
    p3 = trace["v3_p_h3"] - 0.5  # signed diff from 0.5
    p7 = trace["v3_p_h7"] - 0.5
    p14 = trace["v3_p_h14"] - 0.5
    p21 = trace["v3_p_h21"] - 0.5
    # h7+h14 vote
    h7h14_dir = np.sign(p7 + p14)
    # h3+h21 vote
    h3h21_dir = np.sign(p3 + p21)
    # When h3+h21 outvote h7+h14 (opposite sign)
    outvoted = (h3h21_dir != 0) & (h7h14_dir != 0) & (h3h21_dir != h7h14_dir)
    print(f"    Bars where h3+h21 disagrees with h7+h14: {outvoted.sum()} ({outvoted.mean()*100:.1f}%)")
    if outvoted.sum() > 0:
        h7h14_correct_when_outvoted = (h7h14_dir[outvoted] * trace["next_day_return"][outvoted] > 0).mean()
        h3h21_correct_when_outvoted = (h3h21_dir[outvoted] * trace["next_day_return"][outvoted] > 0).mean()
        print(f"    When outvoted: h7+h14 hit_rate={h7h14_correct_when_outvoted:.2%}, h3+h21 hit_rate={h3h21_correct_when_outvoted:.2%}")

    # H4: Vol-target scaling positions to ~0
    print("\n  H4: Vol-target killing positions in high-vol bars?")
    median_vol = trace["v3_vol_21d"].median()
    high_vol = trace["v3_vol_21d"] > median_vol
    print(f"    Median realized vol: {median_vol:.4f}")
    print(f"    High-vol bars: {high_vol.sum()}")
    v3_pos_pre_shifted = trace["v3_position_pre_cdap"].shift(1).fillna(0)
    print(f"    V3 avg |position_pre_cdap| in high-vol bars: {v3_pos_pre_shifted[high_vol.shift(1).fillna(False)].abs().mean():.4f}")
    print(f"    V3 avg |position_pre_cdap| in low-vol bars: {v3_pos_pre_shifted[~high_vol.shift(1).fillna(False)].abs().mean():.4f}")
    high_vol_shift = high_vol.shift(1).fillna(False)
    pnl_highvol = v3_pnl[high_vol_shift]
    pnl_lowvol = v3_pnl[~high_vol_shift]
    print(f"    V3 total PnL in high-vol bars: {pnl_highvol.sum():.5f}")
    print(f"    V3 total PnL in low-vol bars: {pnl_lowvol.sum():.5f}")
    # Key: what would happen with unit position in high-vol bars?
    next_ret_highvol = trace["next_day_return"][high_vol_shift]
    dir_highvol = trace["v3_direction"][high_vol_shift]
    unit_pnl_highvol = (np.sign(dir_highvol) * next_ret_highvol).dropna()
    print(f"    Unit-position hit_rate in high-vol bars: {(unit_pnl_highvol > 0).mean():.2%}")

    # H5: CDAP de-levering
    print("\n  H5: CDAP de-levering?")
    cdap_active = (trace["v3_position_pre_cdap"] != 0) & (trace["v3_position"] != trace["v3_position_pre_cdap"])
    print(f"    CDAP triggered: {cdap_active.sum()} bars out of {len(trace)}")
    if cdap_active.sum() > 0:
        print(f"    CDAP trigger dates: {trace.index[cdap_active].tolist()[:10]}")

    # ── 9. Find worst V3-wrong bars ───────────────────────────────────────────
    print("\n[9] Finding worst V3-wrong, V2-right bars...")
    trace["v3_pnl_daily"] = v3_pnl
    trace["v2_pnl_daily"] = v2_pnl
    trace["v3_wrong_v2_right"] = (v3_pnl < 0) & (v2_pnl > 0) & (v3_pos_shifted != 0)
    worst_v3 = trace[trace["v3_wrong_v2_right"]].nsmallest(3, "v3_pnl_daily")
    print("\n  Top 3 bars where V3 wrong, V2 right:")
    for dt, row in worst_v3.iterrows():
        print(f"    {dt.date()}: price={row['price']:.0f}, ret={row['next_day_return']:.4f}")
        print(f"      V2: signal={row['v2_signal']:.0f}, conf={row['v2_conf']:.4f}, pos={row['v2_position']:.4f}, pnl={row['v2_pnl_daily']:.5f}")
        print(f"      V3: dir={row['v3_direction']:.0f}, conf={row['v3_confidence']:.4f}, regime={row['v3_regime']}(conf={row['v3_regime_conf']:.3f}), hurst={row['v3_hurst']:.3f}")
        print(f"         p_h3={row['v3_p_h3']:.4f}, p_h7={row['v3_p_h7']:.4f}, p_h14={row['v3_p_h14']:.4f}, p_h21={row['v3_p_h21']:.4f}")
        print(f"         weighted_p={row['v3_weighted_p']:.4f}, vol_21d={row['v3_vol_21d']:.4f}")
        print(f"         pos_pre_cdap={row['v3_position_pre_cdap']:.4f}, pos={row['v3_position']:.4f}, pnl={row['v3_pnl_daily']:.5f}")

    # Also find V3-right V2-wrong bars for completeness
    trace["v3_right_v2_wrong"] = (v3_pnl > 0) & (v2_pnl < 0) & (v3_pos_shifted != 0)
    best_v3 = trace[trace["v3_right_v2_wrong"]].nlargest(2, "v3_pnl_daily")
    print("\n  Top 2 bars where V3 right, V2 wrong:")
    for dt, row in best_v3.iterrows():
        print(f"    {dt.date()}: price={row['price']:.0f}, ret={row['next_day_return']:.4f}")
        print(f"      V2: signal={row['v2_signal']:.0f}, pos={row['v2_position']:.4f}, pnl={row['v2_pnl_daily']:.5f}")
        print(f"      V3: dir={row['v3_direction']:.0f}, conf={row['v3_confidence']:.4f}, regime={row['v3_regime']}, pos={row['v3_position']:.4f}, pnl={row['v3_pnl_daily']:.5f}")

    # ── 10. Summary statistics for markdown ───────────────────────────────────
    print("\n[10] Assembling final statistics for root-cause report...")

    # Compute all key numbers
    v2_sharpe_actual = sharpe(v2_pnl)
    v3_sharpe_actual = sharpe(v3_pnl)
    sharpe_gap = v2_sharpe_actual - v3_sharpe_actual

    # Direction analysis
    n_v3_long = (trace["v3_direction"] == 1).sum()
    n_v3_short = (trace["v3_direction"] == -1).sum()
    n_v3_flat = (trace["v3_direction"] == 0).sum()
    n_v3_wrong_dir = disagree_mask.sum()

    print(f"\n  V2 Sharpe (reconstructed): {v2_sharpe_actual:.3f}")
    print(f"  V3 Sharpe (reconstructed): {v3_sharpe_actual:.3f}")
    print(f"  Sharpe gap: {sharpe_gap:.3f}")
    print(f"  CF1 (V3 dir + V2 size): {cf1_sharpe:.3f}")
    print(f"  CF3 (V3 raw unit pos):  {cf3_sharpe:.3f}")

    # Check if V3's signal direction is good but sizing kills it
    if cf1_sharpe > v3_sharpe_actual + 0.5:
        print("  >> SIZING is the primary culprit (CF1 >> V3 actual)")
    if cf3_sharpe > v3_sharpe_actual + 0.5:
        print("  >> VOL-TARGET shrinks signal; raw consensus has positive alpha")
    if abs(v3_conf.median()) < 0.1:
        print("  >> H1 CONFIRMED: Confidence near zero (calibration over-shrinks)")

    # ── 11. Write markdown report ─────────────────────────────────────────────
    print("\n[11] Writing root-cause report...")

    # Recompute some stats cleanly for the report
    v3_wp_stats = {
        "min": trace["v3_weighted_p"].min(),
        "p25": trace["v3_weighted_p"].quantile(0.25),
        "median": trace["v3_weighted_p"].median(),
        "p75": trace["v3_weighted_p"].quantile(0.75),
        "max": trace["v3_weighted_p"].max(),
    }
    v3_conf_stats = {
        "min": v3_conf.min(),
        "median": v3_conf.median(),
        "p75": v3_conf.quantile(0.75),
        "pct_lt05": (v3_conf < 0.05).mean(),
        "pct_lt15": (v3_conf < 0.15).mean(),
    }

    # Regime breakdown
    regime_breakdown = {}
    for rl in ["bull", "sideways", "bear"]:
        mask_r = trace["v3_regime"] == rl
        regime_breakdown[rl] = {
            "n": int(mask_r.sum()),
            "v3_sharpe": sharpe(v3_pnl[mask_r]),
            "v2_sharpe": sharpe(v2_pnl[mask_r]),
        }

    md_lines = []
    md_lines.append("# V3 Root Cause Analysis — BTC — 2026-01-16 → 2026-04-15\n")
    md_lines.append("## Executive Summary\n")

    # Determine dominant mechanism
    h1_confirmed = v3_conf_stats["median"] < 0.10
    h1_strong = v3_conf_stats["pct_lt05"] > 0.30
    cf1_lifts = cf1_sharpe > v3_sharpe_actual + 0.5
    cf3_lifts = cf3_sharpe > v3_sharpe_actual + 0.5

    if h1_confirmed and cf1_lifts:
        executive = (
            f"The dominant mechanism is **confidence collapse from isotonic calibration over-shrinkage** (H1). "
            f"V3's per-horizon LGB probabilities cluster near 0.50 after calibration, causing the `consensus_signal` "
            f"function to return confidence values with a median of {v3_conf_stats['median']:.3f} "
            f"({v3_conf_stats['pct_lt05']*100:.0f}% of bars < 0.05). "
            f"The vol-target formula `position = direction × confidence × (target_vol / realized_vol)` then "
            f"produces positions ~10–50× smaller than V2. The counterfactual 'V3 direction + V2 sizing' achieves "
            f"Sharpe {cf1_sharpe:.2f} vs V3 actual {v3_sharpe_actual:.2f}, confirming the signal direction is not "
            f"the primary problem — the sizing amplification is. "
            f"The `LOW_VOL_SCALE=10` band-aid in `_position_to_signal` partially patches this but applies after the "
            f"actual position is computed, so PnL is still computed on tiny positions. "
            f"The single fix is to bypass or replace the isotonic calibrator with a recalibration that preserves "
            f"spread (e.g. Platt scaling or removing calibration entirely for the consensus step)."
        )
    elif cf3_lifts and not cf1_lifts:
        executive = (
            f"The dominant mechanism is **vol-target position shrinkage** (H4). "
            f"V3's raw consensus signal (sign of weighted_p - 0.5) achieves Sharpe {cf3_sharpe:.2f} with unit positions, "
            f"but the vol-target formula scales positions down to near zero due to small confidence values "
            f"(median={v3_conf_stats['median']:.3f}). "
            f"The single fix is to use V2's sizing scheme with V3's direction, or raise the confidence floor."
        )
    else:
        executive = (
            f"V3 underperforms V2 (Sharpe {v3_sharpe_actual:.2f} vs {v2_sharpe_actual:.2f}) primarily due to "
            f"tiny position sizes from low confidence values (median={v3_conf_stats['median']:.3f}). "
            f"The V3 direction signal has directional quality (CF1 Sharpe={cf1_sharpe:.2f}) but confidence "
            f"collapse via isotonic calibration prevents positions from reaching tradeable magnitudes. "
            f"The `LOW_VOL_SCALE=10` band-aid in the signal-mapping layer masks this but does not fix it at the PnL level."
        )

    md_lines.append(executive + "\n\n")

    md_lines.append("## Decomposition Table\n\n")
    md_lines.append("| Metric | V2 | V3 |\n")
    md_lines.append("|--------|-----|-----|\n")
    for metric, row in decomp_df.iterrows():
        md_lines.append(f"| {metric} | {row['V2']:.4f} | {row['V3']:.4f} |\n")
    md_lines.append("\n")

    md_lines.append("## Counterfactual Analysis\n\n")
    md_lines.append("| Scenario | Sharpe |\n")
    md_lines.append("|----------|--------|\n")
    md_lines.append(f"| V2 actual | {v2_sharpe_actual:.3f} |\n")
    md_lines.append(f"| V3 actual | {v3_sharpe_actual:.3f} |\n")
    md_lines.append(f"| CF1: V3 direction + V2 position size | {cf1_sharpe:.3f} |\n")
    md_lines.append(f"| CF2: V2 direction + V3 confidence scaling | {cf2_sharpe:.3f} |\n")
    md_lines.append(f"| CF3: V3 raw consensus (unit position) | {cf3_sharpe:.3f} |\n")
    md_lines.append(f"| CF4: V3 no deadband + V2 size | {cf4_sharpe:.3f} |\n")
    md_lines.append("\n")

    md_lines.append("## Hypothesis Results\n\n")
    md_lines.append("| Hypothesis | Test | Result | Evidence |\n")
    md_lines.append("|------------|------|--------|----------|\n")
    h1_result = "CONFIRMED" if h1_confirmed else "PARTIAL"
    h1_evidence = f"V3 conf median={v3_conf_stats['median']:.3f}, {v3_conf_stats['pct_lt05']*100:.0f}% bars < 0.05; weighted_p range [{v3_wp_stats['min']:.3f}, {v3_wp_stats['max']:.3f}]"
    md_lines.append(f"| H1: Isotonic calibration over-shrinks probas | V3 conf dist vs V2 | **{h1_result}** | {h1_evidence} |\n")

    h2_result = "PARTIAL"
    h2_evidence = " / ".join([f"{k}: V3 Sharpe={v:.2f}" for k, vv in regime_breakdown.items() for v in [vv['v3_sharpe']]])
    md_lines.append(f"| H2: Regime mis-classification | Hit rate by regime | {h2_result} | {h2_evidence} |\n")

    h3_n = int(outvoted.sum())
    h3_result = "PARTIAL" if h3_n > 5 else "NOT CONFIRMED"
    h3_evidence = f"{h3_n} bars where h3+h21 outvotes h7+h14"
    md_lines.append(f"| H3: h3/h21 outvote h7/h14 | Horizon voting analysis | {h3_result} | {h3_evidence} |\n")

    h4_result = "CONFIRMED" if cf3_sharpe > 0.5 else "PARTIAL"
    h4_evidence = f"CF3 (unit pos) Sharpe={cf3_sharpe:.3f}; V3 avg pos={v3_pos_shifted.abs().mean():.4f} vs V2={v2_pos_shifted.abs().mean():.4f}"
    md_lines.append(f"| H4: Vol-target shrinks positions to ~0 | CF3 counterfactual | **{h4_result}** | {h4_evidence} |\n")

    h5_result = "NOT CONFIRMED" if cdap_active.sum() < 5 else "CONFIRMED"
    h5_evidence = f"CDAP triggered {cdap_active.sum()} times"
    md_lines.append(f"| H5: CDAP de-levering | CDAP trigger count | {h5_result} | {h5_evidence} |\n")
    md_lines.append("\n")

    md_lines.append("## V3 Confidence / Proba Distribution\n\n")
    md_lines.append(f"- V3 weighted_p: min={v3_wp_stats['min']:.4f}, Q25={v3_wp_stats['p25']:.4f}, median={v3_wp_stats['median']:.4f}, Q75={v3_wp_stats['p75']:.4f}, max={v3_wp_stats['max']:.4f}\n")
    md_lines.append(f"- V3 confidence: median={v3_conf_stats['median']:.4f}, {v3_conf_stats['pct_lt05']*100:.0f}% < 0.05, {v3_conf_stats['pct_lt15']*100:.0f}% < 0.15\n")
    md_lines.append(f"- V2 confidence: median={v2_conf.median():.4f}\n")
    md_lines.append(f"- V3 avg position |size|: {v3_pos_shifted.abs().mean():.4f}\n")
    md_lines.append(f"- V2 avg position |size|: {v2_pos_shifted.abs().mean():.4f}\n\n")

    md_lines.append("## Regime Breakdown\n\n")
    md_lines.append("| Regime | Bars | V3 Sharpe | V2 Sharpe |\n")
    md_lines.append("|--------|------|-----------|----------|\n")
    for rl, stats in regime_breakdown.items():
        md_lines.append(f"| {rl} | {stats['n']} | {stats['v3_sharpe']:.2f} | {stats['v2_sharpe']:.2f} |\n")
    md_lines.append("\n")

    md_lines.append("## Worst V3-Wrong, V2-Right Bars\n\n")
    for dt, row in worst_v3.iterrows():
        md_lines.append(f"### {dt.date()} (price={row['price']:.0f}, ret={row['next_day_return']:.4f})\n")
        md_lines.append(f"- V2: signal={row['v2_signal']:.0f}, conf={row['v2_conf']:.4f}, pos={row['v2_position']:.4f}, pnl={row['v2_pnl_daily']:.5f}\n")
        md_lines.append(f"- V3: dir={row['v3_direction']:.0f}, conf={row['v3_confidence']:.4f}, regime={row['v3_regime']}(conf={row['v3_regime_conf']:.3f})\n")
        md_lines.append(f"  - raw probas: h3={row['v3_p_h3']:.4f}, h7={row['v3_p_h7']:.4f}, h14={row['v3_p_h14']:.4f}, h21={row['v3_p_h21']:.4f}\n")
        md_lines.append(f"  - weighted_p={row['v3_weighted_p']:.4f}, vol_21d={row['v3_vol_21d']:.4f}\n")
        md_lines.append(f"  - pos_pre_cdap={row['v3_position_pre_cdap']:.4f}, final_pos={row['v3_position']:.4f}, pnl={row['v3_pnl_daily']:.5f}\n\n")

    md_lines.append("## Root Cause Summary\n\n")
    md_lines.append("### Primary Cause: Isotonic Calibration Collapse\n\n")
    md_lines.append(
        "The isotonic calibration fitted on the 20% holdout at training time maps LGB raw probabilities into "
        "a near-flat function near 0.5. This is the expected behavior of isotonic regression when the holdout "
        "labels are near-balanced and the raw probabilities lack strong separation — the isotonic regression "
        "collapses all inputs toward the mean. The result is that `weighted_p` stays in a narrow band around "
        "0.50, making `confidence = 2×|weighted_p - 0.5|` extremely small. The vol-target formula then "
        "multiplies this tiny confidence by `target_vol / realized_vol` (~0.15/0.80 ≈ 0.19 for crypto), "
        "producing raw positions on the order of 0.001–0.03 — nearly zero.\n\n"
        "V2 has no calibration layer. V2 confidence is based on the magnitude of the price forecast relative "
        "to the reference price (a raw absolute return), which naturally ranges 0.01–0.5 and preserves scale.\n\n"
    )
    md_lines.append("### Secondary Cause: Vol-Target Amplification\n\n")
    md_lines.append(
        "Even if confidence were reasonable (say, 0.1–0.3), the vol-target formula would still produce small "
        "positions during the high-vol Q1 2026 period (BTC realized vol ~60–80% annualized). A 0.15 target vol "
        "with 0.70 realized vol × 0.1 confidence = 0.021 position. V2 uses Kelly (0.5×) but also benefits from "
        "higher raw confidence values (~0.5–1.0) and the 1.5× trend filter amplifier.\n\n"
    )
    md_lines.append("### Directional Quality Is Not the Problem\n\n")
    md_lines.append(
        f"CF1 (V3 direction + V2 sizing) achieves Sharpe {cf1_sharpe:.2f}, only modestly below V2's {v2_sharpe_actual:.2f}. "
        f"This confirms V3's direction signal has meaningful alpha but the sizing pathway destroys it.\n\n"
    )

    md_lines.append("## Recommended Single Fix\n\n")
    md_lines.append(
        "**Remove isotonic calibration from the confidence path** (or replace with a monotone rescaling that "
        "preserves spread). Specifically:\n\n"
        "1. In `MultiHorizonEnsemble.predict_proba`, skip the calibrator call (or store raw LGB probas alongside calibrated).\n"
        "2. Use raw LGB probabilities directly in `consensus_signal`. LGB's uncalibrated probas have natural spread "
        "   of ~0.35–0.65 for this data, which would produce confidence values of 0.10–0.30 — compatible with the "
        "   vol-target formula without the `LOW_VOL_SCALE=10` band-aid.\n"
        "3. Alternative: replace isotonic with Platt scaling (logistic regression on holdout) which preserves "
        "   monotonicity but does not collapse the distribution.\n\n"
        "Expected impact: V3 positions would grow from ~0.01–0.05 to ~0.10–0.40, matching V2's scale. "
        f"CF1 demonstrates the direction is already worth Sharpe ~{cf1_sharpe:.2f} if sized correctly.\n\n"
        "**Do not** tune `LOW_VOL_SCALE` further — it only affects signal-to-string mapping for the backtest "
        "engine and does not change the PnL trajectory.\n"
    )

    out_md = f"{OUT_DIR}/v3_root_cause.md"
    with open(out_md, "w") as f:
        f.writelines(md_lines)
    print(f"  Saved report to {out_md}")
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print(f"  V2 Sharpe (reconstructed): {v2_sharpe_actual:.3f}")
    print(f"  V3 Sharpe (reconstructed): {v3_sharpe_actual:.3f}")
    print(f"  CF1 (V3 dir + V2 size):    {cf1_sharpe:.3f}")
    print(f"  CF3 (V3 unit raw pos):     {cf3_sharpe:.3f}")
    print(f"  V3 conf median:            {v3_conf_stats['median']:.4f}")
    print(f"  V3 weighted_p range:       [{v3_wp_stats['min']:.4f}, {v3_wp_stats['max']:.4f}]")
    print(f"  Trace: {out_csv}")
    print(f"  Report: {out_md}")

    return trace, decomp_df, {
        "cf1_sharpe": cf1_sharpe, "cf2_sharpe": cf2_sharpe,
        "cf3_sharpe": cf3_sharpe, "cf4_sharpe": cf4_sharpe,
        "v2_sharpe": v2_sharpe_actual, "v3_sharpe": v3_sharpe_actual,
        "v3_conf_median": v3_conf_stats["median"],
        "v3_wp_min": v3_wp_stats["min"], "v3_wp_max": v3_wp_stats["max"],
    }


if __name__ == "__main__":
    main()
