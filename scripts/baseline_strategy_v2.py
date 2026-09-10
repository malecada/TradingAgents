#!/usr/bin/env python
"""Baseline Strategy V2: Multi-Horizon Term Structure Consensus.

Reads LGB multi-horizon predictions and backtests per-coin with:
- Term structure consensus (h=7 + h=14 must agree on direction)
- Minimum 7-day hold period
- Vol-targeted Kelly sizing with conditional leverage
- Per-trade stop-loss + portfolio circuit breaker

Usage:
    python scripts/baseline_strategy_v2.py --pred-dir data/multi_5coins_v2
    python scripts/baseline_strategy_v2.py --pred-dir data/multi_2coins_v2 --coins bitcoin ethereum
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.strategies.v2_sizing import (
    generate_term_structure_signals,
    compute_realized_vol,
    vol_regime_mask,
    vol_targeted_size,
    apply_leverage,
    apply_trend_filter,
    build_positions_with_hold,
)


# ── Data Loading ─────────────────────────────────────────────────────


def load_horizon_predictions(pred_dir: Path, horizons: list[int]) -> pd.DataFrame:
    """Load and merge prediction CSVs for multiple horizons.

    Returns DataFrame with columns: date, coin_id, ref_price, actual_h7,
    pred_h7, actual_h14, pred_h14, etc.
    """
    dfs = []
    for h in horizons:
        path = pred_dir / f"preds_lgb_h{h}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing prediction file: {path}")
        df = pd.read_csv(path, parse_dates=["date"])
        df = df.rename(columns={
            "prediction": f"pred_h{h}",
            "actual": f"actual_h{h}",
        })
        dfs.append(df)

    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(
            df.drop(columns=["ref_price"]),
            on=["date", "coin_id"],
            how="inner",
        )
    return merged.sort_values(["coin_id", "date"]).reset_index(drop=True)


# ── Signal Generation, Sizing, Trend Filter ──────────────────────────
# Imported from tradingagents.strategies.v2_sizing — see the import block
# near the top of this module. The functions previously defined inline
# here now live in that module so the live trading cycle can reuse them.


def run_coin_backtest(
    dates: np.ndarray,
    prices: np.ndarray,
    positions: np.ndarray,
    initial_capital: float,
    fee_rate: float,
    slippage: float,
    spread: float,
    price_impact: float,
    funding_rate: float,
    stop_loss: float,
    max_portfolio_dd: float,
    take_profit: float = 0.0,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    price_stop_pct: float = 0.0,
    *,
    trace: list[dict] | None = None,
    target_policy=None,
) -> tuple[list, dict]:
    """Executable contracts with signed funding and explicit risk-stop exits.

    Positions are same-row pretrade NAV targets. Fee, slippage and spread
    inputs are one-way rates; impact remains the declared quadratic turnover
    model. Historical results from the former doubled-fee model are unchanged.

    ``trace`` optionally receives one record per return bar (no initial NAV
    anchor). It observes the existing book without changing targets or risk
    decisions. Dollar charges include both the opening trade and any stop
    exit, each using that leg's NAV. Funding remains the declared daily
    opening-exposure assumption, including on price-stop days. The effective
    mark return includes an assumed stop fill; it is not the raw close return.

    An optional target policy resolves each saved raw target before the bar
    and receives notification after an executed price-stop exit. It changes
    neither accounting nor the price-stop anchor on same-sign resizing.
    The default None path and its original trace schema remain unchanged.
    """
    from tradingagents.accounting import accounting_step
    from tradingagents.backtesting.engine import compute_metrics
    equity = [initial_capital]
    daily_returns, actual_positions = [], []
    notionals = pd.Series(dtype=float)
    previous_target = 0.
    entry_equity = peak_equity = initial_capital
    halted = False
    use_price_stop = price_stop_pct > 0 and highs is not None and lows is not None
    entry_price = 0.
    trades = 0
    fee = fee_rate + slippage + spread
    for i in range(1,len(dates)):
        nav = equity[-1]
        p_prev, p_curr = prices[i-1], prices[i]
        policy_fields = None
        if target_policy is None:
            target_pos = 0. if halted else positions[i]
        else:
            target_pos, policy_fields = target_policy.decide(i, positions[i], halted, date=dates[i])
            if (isinstance(target_pos, (bool, np.bool_))
                    or not isinstance(target_pos, (int, float, np.integer, np.floating))
                    or not np.isfinite(target_pos)):
                raise ValueError(f'invalid policy target at {dates[i]}')
            if halted and target_pos != 0.:
                raise ValueError(f'policy target attempts to release permanent halt at {dates[i]}')
            if not isinstance(policy_fields, dict):
                raise ValueError('policy trace metadata must be a dictionary')
        target = pd.Series({'asset':target_pos}) if np.isfinite(target_pos) else None
        exposure = float(target_pos) if target is not None else notionals.get('asset',0.)/nav
        if target is not None and target_pos != previous_target:
            entry_equity = nav
        if exposure != 0 and (previous_target == 0 or np.sign(exposure) != np.sign(previous_target)):
            entry_price = p_prev
        valid_price = np.isfinite(p_prev) and np.isfinite(p_curr) and p_prev > 0 and p_curr > 0
        mark = p_curr
        price_stop_hit = False
        if use_price_stop and exposure != 0 and valid_price and entry_price > 0:
            stop_level = entry_price*(1-price_stop_pct if exposure > 0 else 1+price_stop_pct)
            price_stop_hit = bool(lows[i] <= stop_level if exposure > 0 else highs[i] >= stop_level)
            if price_stop_hit:
                mark = stop_level
        ret = mark/p_prev-1 if valid_price else np.nan
        trade_fraction = abs(exposure-notionals.get('asset',0.)/nav) if target is not None else 0.
        row = accounting_step(nav,notionals,pd.Series({'asset':ret}),target_weights=target,
            funding=pd.Series({'asset':funding_rate}),fee_rate=fee,date=dates[i],
            capital_charge=price_impact*trade_fraction**2)
        if trace is not None:
            audit_row = {
                'date': pd.Timestamp(dates[i]).isoformat(),
                'nav_before': float(nav), 'pre_nav': float(nav),
                'target_position': float(target_pos) if target is not None else None,
                'exposure': float(row['weights'].get('asset', 0.)),
                'mark_return': float(ret) if np.isfinite(ret) else None,
                'mark_price': float(mark) if np.isfinite(mark) else None,
                'entry_price': float(entry_price) if np.isfinite(entry_price) and entry_price > 0 else None,
                'gross_dollars': float(row['gross'] * nav),
                'funding_dollars': float(row['carry'] * nav),
                'entry_fee_dollars': float(row['cost'] * nav),
                'entry_impact_dollars': float(nav * (price_impact * trade_fraction**2)),
                'entry_turnover_dollars': float(row['turnover'] * nav),
                'exit_fee_dollars': 0., 'exit_impact_dollars': 0.,
                'exit_turnover_dollars': 0., 'exit_notional': 0.,
                'exit_executed': False, 'halted_before': bool(halted),
                'price_stop_hit': bool(price_stop_hit),
                'stop_outside_envelope': bool(price_stop_hit and not lows[i] <= mark <= highs[i]),
            }
        new_equity, notionals = row['nav'],row['notionals']
        actual_positions.append(float(row['weights'].get('asset',0.)))
        trades += int(row['turnover'] > 1e-9)
        trade_dd = (entry_equity-new_equity)/entry_equity
        trade_up = (new_equity-entry_equity)/entry_equity
        peak_equity = max(peak_equity,new_equity)
        portfolio_stop = (peak_equity-new_equity)/peak_equity >= max_portfolio_dd
        close_now = price_stop_hit or portfolio_stop or (exposure != 0 and
                    (trade_dd >= stop_loss or (take_profit > 0 and trade_up >= take_profit)))
        if close_now and len(notionals):
            exit_fraction = float(notionals.abs().sum())/new_equity
            closed = accounting_step(new_equity,notionals,pd.Series({'asset':0.}),
                target_weights=pd.Series(dtype=float),fee_rate=fee,date=dates[i],
                capital_charge=price_impact*exit_fraction**2)
            if trace is not None:
                audit_row.update(
                    exit_fee_dollars=float(closed['cost'] * new_equity),
                    exit_impact_dollars=float(new_equity * (price_impact * exit_fraction**2)),
                    exit_turnover_dollars=float(closed['turnover'] * new_equity),
                    exit_notional=float(notionals.get('asset', 0.)),
                    exit_executed=True,
                )
            new_equity, notionals = closed['nav'],closed['notionals']
            if target_policy is not None and price_stop_hit:
                policy_fields.update(target_policy.on_price_stop(i, exposure))
            trades += int(closed['turnover'] > 1e-9)
            previous_target, entry_price = 0.,0.
        else:
            previous_target = exposure
        peak_equity = max(peak_equity,new_equity)
        halted = halted or (peak_equity-new_equity)/peak_equity >= max_portfolio_dd
        daily_returns.append((new_equity-nav)/nav)
        equity.append(new_equity)
        if trace is not None:
            audit_row.update(
                nav_after=float(new_equity), post_nav=float(new_equity),
                net_return=float(daily_returns[-1]),
                fee_dollars=audit_row['entry_fee_dollars'] + audit_row['exit_fee_dollars'],
                impact_dollars=audit_row['entry_impact_dollars'] + audit_row['exit_impact_dollars'],
                turnover_dollars=audit_row['entry_turnover_dollars'] + audit_row['exit_turnover_dollars'],
                closing_notional=float(notionals.get('asset', 0.)),
                portfolio_stop_hit=bool(portfolio_stop), halted_after=bool(halted),
            )
            if policy_fields is not None:
                if set(policy_fields).intersection(audit_row):
                    raise ValueError('policy metadata cannot overwrite original accounting trace fields')
                audit_row.update(policy_fields)
            trace.append(audit_row)
    metrics = compute_metrics(daily_returns,actual_positions,initial_capital,equity,
                              risk_free_rate=.045,periods_per_year=365.)
    metrics.update(n_trades=trades,halted=halted)
    return equity,metrics


# ── CLI ──────────────────────────────────────────────────────────────


def parse_args():
    p = argparse.ArgumentParser(
        description="Baseline Strategy V2: Multi-Horizon Term Structure Consensus.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--pred-dir", required=True, help="Directory with preds_lgb_h*.csv files.")
    p.add_argument("--coins", nargs="+", default=None,
                    help="Subset of coins to trade (default: all in CSVs).")
    p.add_argument("--horizons", nargs="+", type=int, default=[7, 14],
                    help="Horizons for consensus.")
    p.add_argument("--initial-capital", type=float, default=10_000.0)
    p.add_argument("--min-hold", type=int, default=7,
                    help="Minimum days to hold a position before allowing exit.")
    p.add_argument("--target-vol", type=float, default=0.10)
    p.add_argument("--vol-lookback", type=int, default=20)
    p.add_argument("--kelly-fraction", type=float, default=0.5)
    p.add_argument("--max-leverage", type=float, default=3.0)
    p.add_argument("--stop-loss", type=float, default=0.03)
    p.add_argument("--max-portfolio-dd", type=float, default=0.15)
    p.add_argument("--vol-cap-pct", type=float, default=0.95)
    p.add_argument("--confidence-ref-return", type=float, default=0.02)
    p.add_argument("--fee-rate", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.001)
    p.add_argument("--spread", type=float, default=0.0005)
    p.add_argument("--price-impact", type=float, default=0.001)
    p.add_argument("--funding-rate", type=float, default=0.0001)
    p.add_argument("--symmetric", action="store_true",
                    help="Use symmetric consensus (both horizons must agree for longs too).")
    p.add_argument("--early-exit-loss", type=float, default=0.015,
                    help="Loss threshold for early exit from losing positions.")
    p.add_argument("--trend-sma", type=int, default=30,
                    help="SMA period for trend filter (0 to disable).")
    p.add_argument("--trend-multiplier", type=float, default=1.5,
                    help="Position scaling when aligned/against trend.")
    p.add_argument("--arima-filter", action="store_true",
                    help="Require ARIMA h=1 agreement as additional consensus filter.")
    p.add_argument("--output-plot", default=None)
    return p.parse_args()


# ── Main ─────────────────────────────────────────────────────────────


def main():
    args = parse_args()
    pred_dir = Path(args.pred_dir)

    print(f"\n{'=' * 70}")
    print(f"  Baseline Strategy V2: Term Structure Consensus")
    print(f"{'=' * 70}")

    # Load predictions
    merged = load_horizon_predictions(pred_dir, args.horizons)

    # Optionally load ARIMA h=1 for additional consensus filter
    arima_df = None
    if args.arima_filter:
        arima_path = pred_dir / "preds_arima_h1.csv"
        if not arima_path.exists():
            print(f"  WARNING: --arima-filter set but {arima_path} not found, ignoring")
            args.arima_filter = False
        else:
            arima_df = pd.read_csv(arima_path, parse_dates=["date"])
            arima_df = arima_df.rename(columns={"prediction": "arima_pred", "actual": "arima_actual"})
            if "ref_price" in arima_df.columns:
                arima_df = arima_df.drop(columns=["ref_price"])
            merged = merged.merge(arima_df, on=["date", "coin_id"], how="left")

    coins = args.coins or sorted(merged["coin_id"].unique())
    print(f"  Pred dir    : {pred_dir}")
    print(f"  Horizons    : {args.horizons}")
    print(f"  ARIMA filter: {'yes' if args.arima_filter else 'no'}")
    print(f"  Asymmetric  : {'no (symmetric)' if args.symmetric else 'yes'}")
    print(f"  Trend SMA   : {args.trend_sma}d (multiplier {args.trend_multiplier}x)" if args.trend_sma > 0 else "  Trend SMA   : disabled")
    print(f"  Early exit  : {args.early_exit_loss:.1%} loss threshold")
    print(f"  Coins       : {', '.join(coins)}")
    print(f"  Min hold    : {args.min_hold} days")
    print(f"  Max leverage: {args.max_leverage}x")
    print(f"  Date range  : {merged['date'].min():%Y-%m-%d} to {merged['date'].max():%Y-%m-%d}")

    cost_kwargs = dict(
        fee_rate=args.fee_rate, slippage=args.slippage, spread=args.spread,
        price_impact=args.price_impact, funding_rate=args.funding_rate,
        stop_loss=args.stop_loss, max_portfolio_dd=args.max_portfolio_dd,
    )

    all_results = {}
    all_equity = {}
    all_bh = {}

    for coin in coins:
        df_coin = merged[merged["coin_id"] == coin].sort_values("date").reset_index(drop=True)
        if len(df_coin) < 30:
            print(f"\n  {coin}: skipped (only {len(df_coin)} rows)")
            continue

        # Signals
        signals, confidence = generate_term_structure_signals(
            df_coin, args.horizons, args.confidence_ref_return,
            asymmetric=not args.symmetric,
        )

        # ARIMA veto: zero out signals where ARIMA h=1 disagrees
        if args.arima_filter and "arima_pred" in df_coin.columns:
            ref = df_coin["ref_price"].values
            arima_pred = df_coin["arima_pred"].values
            for i in range(len(signals)):
                if signals[i] != 0 and not np.isnan(arima_pred[i]) and ref[i] > 0:
                    arima_dir = 1 if arima_pred[i] > ref[i] else -1
                    if arima_dir != int(signals[i]):
                        signals[i] = 0
                        confidence[i] = 0

        # Volatility
        prices = df_coin["ref_price"].values
        dates = df_coin["date"].values
        realized_vol = compute_realized_vol(prices, args.vol_lookback)
        vol_ok = vol_regime_mask(realized_vol, args.vol_cap_pct)

        # Positions
        positions = build_positions_with_hold(
            signals, vol_ok, confidence, realized_vol, prices,
            args.target_vol, args.kelly_fraction, args.max_leverage,
            args.min_hold, args.early_exit_loss,
        )

        # Trend filter
        if args.trend_sma > 0:
            positions = apply_trend_filter(
                positions, prices, args.trend_sma, args.trend_multiplier,
            )

        # Use ref_price for the backtest (price at prediction time)
        equity, metrics = run_coin_backtest(
            dates, prices, positions,
            initial_capital=args.initial_capital,
            **cost_kwargs,
        )

        # Buy & Hold
        bh_ret = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0

        all_results[coin] = metrics
        all_equity[coin] = equity
        all_bh[coin] = bh_ret

        n_signals = int(np.sum(signals != 0))
        n_agree = int(np.sum(signals != 0))
        print(f"\n  {coin}: signals={n_signals}  trades={metrics['n_trades']}  "
              f"return={metrics['total_return']:+.2%}  B&H={bh_ret:+.2%}")

    # ── Per-Coin Results Table ───────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  Per-Coin Results")
    print(f"{'=' * 70}")

    header = (f"{'Coin':<12s} {'Return':>10s} {'Ann.Ret':>10s} {'Sharpe':>8s} "
              f"{'MaxDD':>8s} {'WinRate':>8s} {'#Trades':>8s} {'vs B&H':>10s}")
    print(f"  {'-' * len(header)}")
    print(f"  {header}")
    print(f"  {'-' * len(header)}")

    for coin in coins:
        if coin not in all_results:
            continue
        m = all_results[coin]
        bh = all_bh[coin]
        vs_bh = m["total_return"] - bh
        pf_str = f"{m['profit_factor']:.2f}" if m["profit_factor"] != float("inf") else "inf"
        print(f"  {coin:<12s} {m['total_return']:>+10.2%} {m['annualized_return']:>+10.2%} "
              f"{m['sharpe_ratio']:>8.2f} {m['max_drawdown']:>8.2%} "
              f"{m['win_rate']:>8.1%} {m['n_trades']:>8d} {vs_bh:>+10.2%}")

    print(f"  {'-' * len(header)}")

    # Buy & Hold row
    for coin in coins:
        if coin in all_bh:
            print(f"  {coin + ' B&H':<12s} {all_bh[coin]:>+10.2%}")

    # ── Equal-Weight Portfolio ───────────────────────────────────────
    if len(all_equity) > 1:
        min_len = min(len(eq) for eq in all_equity.values())
        port_equity = np.zeros(min_len)
        for eq in all_equity.values():
            port_equity += np.array(eq[:min_len])
        port_equity /= len(all_equity)

        port_return = (port_equity[-1] - args.initial_capital) / args.initial_capital
        port_daily = np.diff(port_equity) / port_equity[:-1]
        port_daily = port_daily[~np.isnan(port_daily)]
        daily_rf = (1 + 0.045) ** (1 / 252) - 1
        if len(port_daily) > 1:
            excess = port_daily - daily_rf
            std_ex = np.std(excess, ddof=1)
            port_sharpe = float(np.mean(excess) / std_ex * np.sqrt(252)) if std_ex > 0 else 0
        else:
            port_sharpe = 0
        running_max = np.maximum.accumulate(port_equity)
        port_dd = np.where(running_max > 0, (running_max - port_equity) / running_max, 0)
        port_max_dd = float(np.max(port_dd))

        print(f"\n{'=' * 70}")
        print(f"  Equal-Weight Portfolio ({len(all_equity)} coins)")
        print(f"{'=' * 70}")
        print(f"  Return     : {port_return:+.2%}")
        print(f"  Sharpe     : {port_sharpe:.2f}")
        print(f"  Max DD     : {port_max_dd:.2%}")

    # ── Cost Assumptions ─────────────────────────────────────────────
    print(f"\n  Cost: fee={args.fee_rate:.2%}/side  slip={args.slippage:.2%}  "
          f"spread={args.spread:.2%}  impact={args.price_impact:.4f}  "
          f"funding={args.funding_rate:.2%}/day")

    # ── Plot ─────────────────────────────────────────────────────────
    plot_path = args.output_plot or str(pred_dir / "baseline_v2_equity.png")

    fig, ax = plt.subplots(figsize=(16, 8))

    for coin in coins:
        if coin not in all_equity:
            continue
        eq = all_equity[coin]
        # Get dates for this coin
        df_coin = merged[merged["coin_id"] == coin].sort_values("date")
        dates_pd = pd.to_datetime(df_coin["date"].values)
        # equity has len(dates)+1 entries (index 0 = initial capital before first bar)
        # eq[1:] aligns with dates[0:] only when len(eq)-1 == len(dates_pd)
        # In practice eq may be shorter if halted; trim both to the same length
        n_plot = min(len(eq) - 1, len(dates_pd))
        ax.plot(dates_pd[:n_plot], eq[1:n_plot + 1], linewidth=1.2,
                label=f"{coin} ({all_results[coin]['total_return']:+.1%})")

    if len(all_equity) > 1:
        # Portfolio line
        ref_coin = coins[0] if coins[0] in all_equity else list(all_equity.keys())[0]
        df_ref = merged[merged["coin_id"] == ref_coin].sort_values("date")
        port_dates = pd.to_datetime(df_ref["date"].values)
        n_port = min(min_len - 1, len(port_dates))
        ax.plot(port_dates[:n_port], port_equity[1:n_port + 1], linewidth=2, color="black",
                linestyle="-", label=f"Portfolio ({port_return:+.1%})")

    ax.axhline(y=args.initial_capital, color="gray", linestyle="--",
               linewidth=0.8, alpha=0.5)

    ax.set_title("Baseline V2: Term Structure Consensus (per coin)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (USD)")
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"\n  Equity plot -> {plot_path}")


if __name__ == "__main__":
    main()
