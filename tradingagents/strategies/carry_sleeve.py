"""Perpetual funding-carry sleeve.

A delta-neutral position (short perp + long spot) harvests the funding rate.
Because the legs are delta-neutral, spot/perp price moves cancel and the daily
return is approximately the funding collected minus rebalance costs. See
docs/CARRY_SLEEVE_BACKTEST_SPEC.md.

P0 (this module): turn raw Binance 8h funding prints into a daily funding-INCOME
series. A short-perp position collects every 8h settlement, so daily income is
the SUM of the day's prints — not the mean used by the feature scraper
(onchain.py:_scrape_funding_rates).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

# One-way cost per leg = fee_rate + slippage. A position change trades BOTH legs
# (perp + spot), so a transition costs 2 * (fee_rate + slippage). Defaults match
# the V5 MIX cost model (scripts/baseline_v5_mix.py: fee 0.04%, slippage 0.05%).
DEFAULT_COSTS = {"fee_rate": 0.0004, "slippage": 0.0005}


def aggregate_daily_funding_income(raw: pd.DataFrame) -> pd.Series:
    """Sum intraday 8h funding prints into a daily funding-income series.

    Args:
        raw: DataFrame with a ``fundingRate`` column (float, per-8h) and a
            ``fundingTime`` column (epoch milliseconds, UTC) marking each
            settlement.

    Returns:
        Series indexed by ``datetime.date`` named ``funding_income``; each value
        is the SUM of that day's funding prints — the carry a short-perp leg
        collects (positive) or pays (negative) over the day.
    """
    if raw.empty:
        return pd.Series(dtype="float64", name="funding_income")

    df = raw.copy()
    df["fundingRate"] = df["fundingRate"].astype(float)
    df["date"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True).dt.date
    income = df.groupby("date")["fundingRate"].sum()
    income.name = "funding_income"
    return income


def fetch_funding_raw(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Fetch raw 8h funding prints from Binance Futures (paginated).

    Args:
        symbol: Binance perp symbol, e.g. ``"BTCUSDT"``.
        start: first day (inclusive, UTC).
        end: last day (exclusive, UTC).

    Returns:
        DataFrame with ``fundingTime`` (epoch ms) and ``fundingRate`` (float)
        columns, one row per 8h settlement. Empty if the venue returns nothing.
    """
    # Imported here to avoid a hard dataflows dependency at module import time.
    from tradingagents.dataflows.onchain import (
        _BINANCE_FUTURES_BASE_URL,
        _request_with_retry,
    )

    start_ms = int(datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(datetime.combine(end, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)

    prints: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        resp = _request_with_retry(
            f"{_BINANCE_FUTURES_BASE_URL}/fapi/v1/fundingRate",
            params={"symbol": symbol, "startTime": cursor, "limit": 1000},
            label=f"carry funding {symbol}",
        )
        data = resp.json()
        if not data:
            break
        prints.extend(data)
        nxt = data[-1]["fundingTime"] + 1
        if nxt <= cursor:  # guard against a non-advancing cursor
            break
        cursor = nxt

    if not prints:
        return pd.DataFrame(columns=["fundingTime", "fundingRate"])
    df = pd.DataFrame(prints)[["fundingTime", "fundingRate"]]
    df = df[df["fundingTime"] < end_ms].reset_index(drop=True)
    return df


def funding_daily_income(symbol: str, start: date, end: date) -> pd.Series:
    """Daily funding-income series (carry collected by a short-perp leg).

    Convenience orchestrator: fetch raw prints then sum per day.
    """
    return aggregate_daily_funding_income(fetch_funding_raw(symbol, start, end))


def blend_returns(core: pd.Series, sleeve: pd.Series, alloc: float) -> pd.Series:
    """Convex blend of the directional book and the carry sleeve.

    Models the locked "separate allocation" decision: carve ``alloc`` of the book
    for carry, leave ``1 - alloc`` in the core. Aligned on the shared dates.

    Args:
        core: daily returns of the core book (e.g. V5 MIX portfolio).
        sleeve: daily returns of the carry sleeve.
        alloc: fraction of capital allocated to the sleeve, in [0, 1].

    Returns:
        Blended daily return series named ``blended`` over the shared index.
    """
    idx = core.index.intersection(sleeve.index)
    blended = (1.0 - alloc) * core.loc[idx] + alloc * sleeve.loc[idx]
    blended.name = "blended"
    return blended


def fetch_perp_mark(symbol: str, start: date, end: date) -> pd.Series:
    """Daily perp MARK close from Binance Futures ``/fapi/v1/markPriceKlines``.

    Mark price (not last trade) is what a position is margined and liquidated on,
    so it is the correct perp leg for the delta-neutral basis calc.

    Args:
        symbol: Binance perp symbol, e.g. ``"BTCUSDT"``.
        start: first day (inclusive, UTC).
        end: last day (exclusive, UTC).

    Returns:
        Series of perp mark close indexed by ``datetime.date``, named
        ``perp_mark``. Empty if the venue returns nothing.
    """
    from tradingagents.dataflows.onchain import (
        _BINANCE_FUTURES_BASE_URL,
        _request_with_retry,
    )

    start_ms = int(datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(datetime.combine(end, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)

    rows: list[list] = []
    cursor = start_ms
    while cursor < end_ms:
        resp = _request_with_retry(
            f"{_BINANCE_FUTURES_BASE_URL}/fapi/v1/markPriceKlines",
            params={"symbol": symbol, "interval": "1d", "startTime": cursor,
                    "endTime": end_ms, "limit": 1500},
            label=f"carry perp mark {symbol}",
        )
        data = resp.json()
        if not data:
            break
        rows.extend(data)
        nxt = data[-1][0] + 1
        if nxt <= cursor:
            break
        cursor = nxt

    if not rows:
        return pd.Series(dtype="float64", name="perp_mark")
    df = pd.DataFrame(rows)
    df = df[df[0] < end_ms]
    close = pd.Series(
        df[4].astype(float).to_numpy(),
        index=pd.to_datetime(df[0], unit="ms", utc=True).dt.date.to_numpy(),
        name="perp_mark",
    )
    return close[~close.index.duplicated(keep="last")]


def compute_price_pnl(spot_close: pd.Series, perp_close: pd.Series) -> pd.Series:
    """Daily price-leg PnL of the delta-neutral position (long spot, short perp).

    A unit-notional long-spot / short-perp pair earns ``spot_ret - perp_ret`` each
    day; if the perp tracks spot exactly the hedge is perfect and this is zero. The
    residual is the basis-change risk the sleeve actually carries.

    Args:
        spot_close: daily spot close (date-indexed).
        perp_close: daily perp mark close (same index as ``spot_close``).

    Returns:
        Daily price-PnL series named ``price_pnl``; first day 0 (no prior close).
    """
    spot_ret = spot_close.astype(float).pct_change()
    perp_ret = perp_close.astype(float).pct_change()
    pnl = (spot_ret - perp_ret).fillna(0.0)
    pnl.name = "price_pnl"
    return pnl


def carry_sleeve_return(
    funding_income: pd.Series,
    sign_mode: str = "always_on",
    costs: dict | None = None,
    price_pnl: pd.Series | None = None,
    gate_k: int = 7,
    gate_hurdle: float = 0.0,
) -> pd.Series:
    """Daily return of the funding-carry sleeve on its own notional.

    The position is delta-neutral (short perp + long spot), so price moves cancel
    and the daily return is the funding collected while the sleeve is open, minus
    the round-trip cost on each open/close transition::

        return_t = pos_t * funding_income_t - |Δpos_t| * 2 * (fee_rate + slippage)

    Args:
        funding_income: daily funding-income series (date-indexed), from P0.
        sign_mode: ``"always_on"`` holds the sleeve every day. ``"gated"`` holds
            only when the trailing-``gate_k``-day mean funding (strictly before the
            day, no look-ahead) exceeds ``gate_hurdle``; idle otherwise.
        costs: dict with ``fee_rate`` and ``slippage`` (one-way, per leg).
            Defaults to :data:`DEFAULT_COSTS`.
        price_pnl: optional daily basis-leg PnL (from :func:`compute_price_pnl`),
            added while the sleeve is held. ``None`` = perfect hedge (zero), the
            original P1 behavior.
        gate_k: trailing window (days) for the funding signal (``gated`` only).
        gate_hurdle: per-day funding threshold to deploy (``gated`` only); set
            at/above the amortized round-trip cost so the sleeve idles when
            funding does not cover costs.

    Returns:
        Daily return series aligned to ``funding_income``'s index, named
        ``carry_return``.
    """
    if sign_mode not in ("always_on", "gated"):
        raise ValueError(f"unknown sign_mode={sign_mode!r}")

    c = DEFAULT_COSTS if costs is None else costs
    transition_cost = 2.0 * (c["fee_rate"] + c["slippage"])

    if funding_income.empty:
        return pd.Series(dtype="float64", name="carry_return")

    if sign_mode == "always_on":
        pos = np.ones(len(funding_income))       # open every day
    else:
        # trailing mean of funding strictly before each day (shift(1) -> no look-ahead)
        signal = funding_income.shift(1).rolling(gate_k).mean()
        pos = (signal > gate_hurdle).to_numpy(dtype=float)  # NaN -> False -> flat in warmup

    prev = np.concatenate([[0.0], pos[:-1]])     # start flat -> first open is an entry
    trades = np.abs(pos - prev)

    if price_pnl is None:
        basis = np.zeros(len(funding_income))
    else:
        basis = price_pnl.reindex(funding_income.index).fillna(0.0).to_numpy(dtype=float)

    ret = pos * (funding_income.to_numpy(dtype=float) + basis) - trades * transition_cost

    return pd.Series(ret, index=funding_income.index, name="carry_return")
