#!/usr/bin/env python
"""Intraday (1h) triple-barrier fill engine for the SL/TP sweep.

Overlays SL / TP / trailing barriers on the daily V2 equity loop, checked
intrabar by walking each day's 1h (high, low) bars in chronological order.
Barriers fire on equity-since-entry (matching baseline_strategy_v2's daily
stop semantics; leverage is already baked into the position size). When no
barrier touches within a day, the day reduces to the exact close-to-close
computation of run_coin_backtest (see tests/strategies/test_intraday_fills.py
::test_equivalence_when_no_intraday_excursion).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def group_intraday_by_day(
    intraday_df: pd.DataFrame, daily_dates: np.ndarray,
) -> dict[int, np.ndarray]:
    """Map daily index i → ndarray of (high, low) 1h bars on that calendar day.

    daily_dates are UTC-naive midnight-normalized. intraday_df.open_time is
    UTC-naive. Days with no intraday bars map to an empty (0, 2) array.
    """
    df = intraday_df.copy()
    df["day"] = pd.to_datetime(df["open_time"]).dt.normalize()
    grouped = {d: g[["high", "low"]].to_numpy(dtype=float)
               for d, g in df.groupby("day", sort=False)}
    out: dict[int, np.ndarray] = {}
    for i, d in enumerate(daily_dates):
        key = pd.Timestamp(d).normalize()
        out[i] = grouped.get(key, np.empty((0, 2), dtype=float))
    return out


def _barrier_exit_equity(
    bars: np.ndarray, e0: float, p_prev: float, p_curr: float, pos: float,
    entry_equity: float, peak_eq: float,
    stop_loss: float, take_profit: float, trailing_stop: float,
) -> tuple[float | None, float]:
    """Walk a day's (high, low) bars; return (exit_equity or None, updated_peak).

    exit_equity is None when no barrier fires INTRABAR (before the close); the
    caller then falls back to the exact daily close-to-close path (which carries
    its own daily-style close stop). Priority within a bar: fixed SL > TP >
    trailing (most conservative wins ties).

    A bar only produces an intrabar fill when its relevant extreme is strictly
    beyond the day's close (``p_curr``) in the triggering direction. A flat bar
    (high == low == close) thus never fires intrabar — there is no pre-close
    moment at which the barrier could have been touched — so a no-excursion day
    reduces exactly to ``run_coin_backtest``'s close-to-close arithmetic. This is
    what makes the equivalence test load-bearing rather than merely close.
    """
    if pos == 0.0 or p_prev <= 0.0 or bars.shape[0] == 0:
        return None, peak_eq

    def eq_at(price: float) -> float:
        return e0 * (1.0 + pos * (price - p_prev) / p_prev)

    for hi, lo in bars:
        adverse = lo if pos > 0 else hi
        favorable = hi if pos > 0 else lo
        eq_adv = eq_at(adverse)
        eq_fav = eq_at(favorable)
        # Genuine intrabar excursion = extreme strictly more adverse / more
        # favorable than the day's close. Equality (flat bar) is deferred to the
        # daily close path so equivalence holds byte-for-byte.
        adverse_excursion = (adverse < p_curr) if pos > 0 else (adverse > p_curr)
        favorable_excursion = (favorable > p_curr) if pos > 0 else (favorable < p_curr)

        if adverse_excursion and entry_equity > 0 and \
                (entry_equity - eq_adv) / entry_equity >= stop_loss:
            return entry_equity * (1.0 - stop_loss), peak_eq
        if favorable_excursion and take_profit > 0 and entry_equity > 0 and \
                (eq_fav - entry_equity) / entry_equity >= take_profit:
            return entry_equity * (1.0 + take_profit), peak_eq
        if favorable_excursion:
            peak_eq = max(peak_eq, eq_fav)
        if adverse_excursion and trailing_stop > 0 and peak_eq > 0 and \
                (peak_eq - eq_adv) / peak_eq >= trailing_stop:
            return peak_eq * (1.0 - trailing_stop), peak_eq

    return None, peak_eq


def _barrier_exit_price(
    bars: np.ndarray, e0: float, p_prev: float, p_curr: float, pos: float,
    entry_price: float, peak_price: float,
    stop_loss: float, take_profit: float, trailing_stop: float,
) -> tuple[float | None, float]:
    """PRICE-based triple barrier (mirrors the live STOP_MARKET semantics).

    Long: SL at entry_price*(1-stop_loss), TP at entry_price*(1+take_profit),
    trailing at peak_price*(1-trailing_stop). Short: mirror (SL above, TP below,
    trailing off the running min). Fires intrabar only when the relevant 1h
    extreme is strictly beyond the day's close (flat bars defer to the
    close-to-close path). Returns (exit_equity_or_None, updated_peak_price).
    The exit equity books the move from p_prev to the barrier PRICE:
    e0 * (1 + pos*(barrier_price - p_prev)/p_prev).
    """
    if pos == 0.0 or p_prev <= 0.0 or entry_price <= 0.0 or bars.shape[0] == 0:
        return None, peak_price

    def exit_eq(barrier_price: float) -> float:
        return e0 * (1.0 + pos * (barrier_price - p_prev) / p_prev)

    if pos > 0:
        sl_price = entry_price * (1.0 - stop_loss)
        tp_price = entry_price * (1.0 + take_profit)
        for hi, lo in bars:
            adv_exc = lo < p_curr        # genuine downside excursion below close
            fav_exc = hi > p_curr
            if adv_exc and lo <= sl_price:
                return exit_eq(sl_price), peak_price
            if fav_exc and take_profit > 0 and hi >= tp_price:
                return exit_eq(tp_price), peak_price
            if fav_exc:
                peak_price = max(peak_price, hi)
            if adv_exc and trailing_stop > 0:
                trail_price = peak_price * (1.0 - trailing_stop)
                if lo <= trail_price:
                    return exit_eq(trail_price), peak_price
    else:  # short
        sl_price = entry_price * (1.0 + stop_loss)
        tp_price = entry_price * (1.0 - take_profit)
        for hi, lo in bars:
            adv_exc = hi > p_curr        # upside excursion = adverse for a short
            fav_exc = lo < p_curr
            if adv_exc and hi >= sl_price:
                return exit_eq(sl_price), peak_price
            if fav_exc and take_profit > 0 and lo <= tp_price:
                return exit_eq(tp_price), peak_price
            if fav_exc:
                peak_price = min(peak_price, lo)
            if adv_exc and trailing_stop > 0:
                trail_price = peak_price * (1.0 + trailing_stop)
                if hi >= trail_price:
                    return exit_eq(trail_price), peak_price
    return None, peak_price


def run_coin_backtest_intrabar(
    dates: np.ndarray,
    prices: np.ndarray,
    positions: np.ndarray,
    intraday: dict[int, np.ndarray],
    initial_capital: float,
    fee_rate: float,
    slippage: float,
    spread: float,
    price_impact: float,
    funding_rate: float,
    stop_loss: float,
    max_portfolio_dd: float,
    take_profit: float = 0.0,
    trailing_stop: float = 0.0,
    stop_mode: str = "equity",
    funding_series: np.ndarray | None = None,
) -> tuple[list, dict]:
    """Intraday-fill twin of baseline_strategy_v2.run_coin_backtest.

    Identical cost model, funding, portfolio circuit breaker, metrics. The only
    difference: SL/TP/trailing are evaluated intrabar (per-day 1h bars in
    ``intraday[i]``) instead of on the day's close.
    """
    equity = [initial_capital]
    daily_returns: list[float] = []
    prev_pos = 0.0
    entry_equity = initial_capital
    entry_price = prices[0] if len(prices) > 0 else 0.0
    peak_equity = initial_capital
    peak_eq_since_entry = initial_capital
    peak_price_since_entry = prices[0] if len(prices) > 0 else 0.0
    halted = False

    for i in range(1, len(dates)):
        p_prev = prices[i - 1]
        p_curr = prices[i]

        if np.isnan(p_prev) or np.isnan(p_curr) or p_prev == 0:
            daily_returns.append(0.0); equity.append(equity[-1]); continue
        if halted:
            daily_returns.append(0.0); equity.append(equity[-1]); prev_pos = 0.0; continue

        target_pos = positions[i]
        trade_notional = abs(target_pos - prev_pos)

        if target_pos != prev_pos and target_pos != 0:
            entry_equity = equity[-1]
            peak_eq_since_entry = equity[-1]
            entry_price = p_prev
            peak_price_since_entry = p_prev
        if target_pos == 0 and prev_pos != 0:
            entry_equity = equity[-1]

        e0 = equity[-1]
        bars = intraday.get(i, np.empty((0, 2), dtype=float))
        if stop_mode == "price":
            exit_eq, peak_price_since_entry = _barrier_exit_price(
                bars, e0=e0, p_prev=p_prev, p_curr=p_curr, pos=target_pos,
                entry_price=entry_price, peak_price=peak_price_since_entry,
                stop_loss=stop_loss, take_profit=take_profit, trailing_stop=trailing_stop)
        else:
            exit_eq, peak_eq_since_entry = _barrier_exit_equity(
                bars, e0=e0, p_prev=p_prev, p_curr=p_curr, pos=target_pos,
                entry_equity=entry_equity, peak_eq=peak_eq_since_entry,
                stop_loss=stop_loss, take_profit=take_profit, trailing_stop=trailing_stop)

        fee_cost = (2 * fee_rate + slippage + 2 * spread) * trade_notional
        impact_cost = price_impact * trade_notional * trade_notional
        if funding_series is None:
            holding_cost = funding_rate * abs(target_pos)
        else:
            holding_cost = funding_series[i] * target_pos

        if exit_eq is not None:
            # Genuine intrabar barrier touch (a high/low strictly beyond the
            # close crossed the barrier before the close): exit at the clamped
            # barrier equity, flatten for the rest of day i (re-entry, if the
            # signal persists, happens on day i+1). Cost model is IDENTICAL to
            # the daily engine — no extra exit fee — so the only difference from
            # run_coin_backtest is fill TIMING (the day's return is capped at the
            # barrier instead of booked to the close). The round-trip fee for the
            # exit+re-entry is charged on day i+1's position change, exactly as in
            # the daily engine.
            gross_ret = exit_eq / e0 - 1.0
            net_ret = gross_ret - (fee_cost + impact_cost + holding_cost)
            new_equity = e0 * (1 + net_ret)
            filled_pos = 0.0
        else:
            # No intrabar touch → identical to run_coin_backtest: realize the
            # full close-to-close return, then apply the daily-style post-cost
            # close stop (which flattens FORWARD without altering this day's
            # return). This branch must be byte-identical to the daily engine.
            price_return = (p_curr - p_prev) / p_prev
            gross_ret = target_pos * price_return
            net_ret = gross_ret - (fee_cost + impact_cost + holding_cost)
            new_equity = e0 * (1 + net_ret)
            filled_pos = target_pos
            if stop_mode == "price":
                if target_pos > 0:
                    if p_curr <= entry_price * (1 - stop_loss):
                        filled_pos = 0.0
                    elif take_profit > 0 and p_curr >= entry_price * (1 + take_profit):
                        filled_pos = 0.0
                elif target_pos < 0:
                    if p_curr >= entry_price * (1 + stop_loss):
                        filled_pos = 0.0
                    elif take_profit > 0 and p_curr <= entry_price * (1 - take_profit):
                        filled_pos = 0.0
                peak_price_since_entry = (max(peak_price_since_entry, p_curr) if target_pos > 0
                                          else min(peak_price_since_entry, p_curr) if target_pos < 0
                                          else peak_price_since_entry)
            else:
                # existing equity-mode daily stop/TP check (unchanged)
                if target_pos != 0 and entry_equity > 0:
                    trade_dd = (entry_equity - new_equity) / entry_equity
                    if trade_dd >= stop_loss:
                        filled_pos = 0.0
                    trade_up = (new_equity - entry_equity) / entry_equity
                    if take_profit > 0 and trade_up >= take_profit:
                        filled_pos = 0.0
                peak_eq_since_entry = max(peak_eq_since_entry, new_equity)

        daily_returns.append(net_ret)
        equity.append(new_equity)
        prev_pos = filled_pos

        peak_equity = max(peak_equity, new_equity)
        dd_from_peak = (peak_equity - new_equity) / peak_equity if peak_equity > 0 else 0
        if dd_from_peak >= max_portfolio_dd:
            halted = True

    returns = np.array(daily_returns)
    total_return = (equity[-1] - initial_capital) / initial_capital
    n_days = len(returns)
    ann_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
    daily_rf = (1 + 0.045) ** (1 / 252) - 1
    traded_mask = np.abs(np.array([positions[i] for i in range(1, len(dates))])) > 1e-9
    traded_returns = returns[traded_mask]
    if len(traded_returns) > 1:
        excess = traded_returns - daily_rf
        std_ex = np.std(excess, ddof=1)
        sharpe = float(np.mean(excess) / std_ex * np.sqrt(252)) if std_ex > 0 else 0
    else:
        sharpe = 0
    eq = np.array(equity)
    running_max = np.maximum.accumulate(eq)
    dd = np.where(running_max > 0, (running_max - eq) / running_max, 0)
    max_dd = float(np.max(dd))
    n_trades = int(np.sum(np.abs(np.diff(positions)) > 1e-9))
    wins = int(np.sum(traded_returns > 0))
    win_rate = wins / len(traded_returns) if len(traded_returns) > 0 else 0
    gross_profit = float(np.sum(traded_returns[traded_returns > 0]))
    gross_loss = float(np.abs(np.sum(traded_returns[traded_returns < 0])))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0)
    metrics = {
        "total_return": total_return, "annualized_return": ann_return,
        "sharpe_ratio": sharpe, "max_drawdown": max_dd, "win_rate": win_rate,
        "n_trades": n_trades, "profit_factor": pf, "halted": halted,
    }
    return equity, metrics
