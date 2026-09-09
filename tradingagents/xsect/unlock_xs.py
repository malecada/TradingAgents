"""PIT token-unlock burden signal (unlock_xs_t1).

Reconstructs each token's unlock schedule by replaying DefiLlama
``metadata.events`` in timestamp order, applying only events with
``timestamp <= t`` for the supply side, so ``circulating_supply(t)`` is the
curve as encoded by the snapshotted schedule at t. The forward burden

    unlock_burden(t, N) = tokens_unlocking(t, t+N] / circulating_supply(t)

uses the scheduled (public, ex-ante-knowable) events in ``(t, t+N]``.
High burden = short leg. Registered in gates.json under ``unlock_xs_t1``.

Empirical calibration decisions (2026-08-08, made against supply data only,
before any return was computed; see probes.json):

- **Linear rate unit is tokens per WEEK.** ``noOfTokens[1]`` of a linear
  event divided by 7 gives tokens/day. Validated against the summed
  ``documentedData`` unlock curve on aptos: ratio 1.017-1.021 across three
  probe dates; the tokens-per-``rateDurationDays`` reading undercounts by
  ~20% and the tokens-per-day reading overcounts 2.5x.
- **Supply includes ALL categories** (also ``noncirculating``). All-category
  cumulative unlocked tracks CoinGecko circulating supply (aptos 1.005,
  apecoin 1.000, dydx 0.858 on 2026-08-08); excluding ``noncirculating``
  undershoots badly (apecoin 0.380). P0 quantifies the residual per name
  over time.

Single-snapshot hazard: DefiLlama serves the CURRENT schedule and amends it
silently, so a replay cannot see pre-amendment history. P0 (silent
restatement vs an independent supply series) is the registered discriminator
and STOPs the experiment if divergence grows toward the present.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SECONDS_PER_DAY = 86_400
WEEK_DAYS = 7.0
# Perp bases that are stablecoins or pegged wrappers: no unlock economics.
STABLE_EXCLUDE = {"USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "USDPUSDT",
                  "DAIUSDT", "USDEUSDT", "USD1USDT", "USTCUSDT"}


# ---------------------------------------------------------------------------
# Mapping: emissions slug -> perp symbol
# ---------------------------------------------------------------------------

def _gecko_id(doc: dict, slug: str) -> str | None:
    gid = doc.get("gecko_id")
    if gid:
        return gid
    tok = (doc.get("metadata") or {}).get("token") or ""
    if tok.startswith("coingecko:"):
        return tok.split(":", 1)[1]
    return slug  # last resort: many slugs equal the coingecko id


def map_slugs_to_perps(emissions_dir: Path, gecko_list_file: Path,
                       perp_symbols: set) -> dict[str, str]:
    """slug -> perp symbol for every emissions file whose token trades a perp.

    Ticker comes from the snapshotted CoinGecko coins list; perp candidates
    include Binance's 1000x/1000000x memecoin prefixes. Stablecoins are
    excluded (no unlock economics on a peg).
    """
    id2sym = {c["id"]: c["symbol"].upper()
              for c in json.loads(Path(gecko_list_file).read_text())}
    out: dict[str, str] = {}
    for f in sorted(Path(emissions_dir).glob("*.json")):
        doc = json.loads(f.read_text())
        ticker = id2sym.get(_gecko_id(doc, f.stem))
        if not ticker:
            continue
        for cand in (f"{ticker}USDT", f"1000{ticker}USDT",
                     f"1000000{ticker}USDT"):
            if cand in perp_symbols and cand not in STABLE_EXCLUDE:
                out[f.stem] = cand
                break
    dupes = {s for s in out.values() if list(out.values()).count(s) > 1}
    assert not dupes, (
        f"slug->perp map not injective for {sorted(dupes)}: two schedules "
        "would silently overwrite one symbol's supply/burden columns"
    )
    return out


# ---------------------------------------------------------------------------
# Schedule replay
# ---------------------------------------------------------------------------

def load_events(emissions_dir: Path, slug: str) -> list[dict]:
    doc = json.loads((Path(emissions_dir) / f"{slug}.json").read_text())
    return (doc.get("metadata") or {}).get("events") or []


def _tok_sum(e: dict) -> float:
    """Sum of an event's noOfTokens, tolerating None entries (seen in the
    wild in the 2026-08-08 snapshot)."""
    return float(sum(t for t in (e.get("noOfTokens") or []) if t is not None))


def _ts_of(e: dict) -> float:
    """Event timestamp as float — a few files carry numeric strings
    (curve-finance, silo-finance in the 2026-08-08 snapshot)."""
    return float(e["timestamp"])


def daily_unlock_series(events: list[dict], start: pd.Timestamp,
                        end: pd.Timestamp) -> pd.Series:
    """Tokens newly unlocked per UTC calendar day over [start, end].

    Cliffs land whole on their event day. Linear events set a per-category
    tokens-per-week rate active from their timestamp until the category's
    next linear event (capped at the schedule's last event timestamp).
    """
    days = pd.date_range(start.normalize(), end.normalize(), freq="D", tz="UTC")
    vals = np.zeros(len(days))
    if not events:
        return pd.Series(vals, index=days)
    day0 = days[0].value // 10 ** 9
    max_ts = max(_ts_of(e) for e in events)

    def _idx(ts: float) -> int:
        return int((ts - day0) // SECONDS_PER_DAY)

    lin: dict[str, list[dict]] = {}
    for e in events:
        if e.get("unlockType") == "cliff":
            i = _idx(_ts_of(e))
            if 0 <= i < len(days):
                vals[i] += _tok_sum(e)
        elif e.get("unlockType") == "linear":
            lin.setdefault(e.get("category") or "?", []).append(e)

    for evs in lin.values():
        evs.sort(key=_ts_of)
        for j, e in enumerate(evs):
            t0 = _ts_of(e)
            t1 = _ts_of(evs[j + 1]) if j + 1 < len(evs) else max_ts
            if t1 <= t0:
                continue
            toks = [t for t in (e.get("noOfTokens") or []) if t is not None]
            rate_day = (float(toks[-1]) if toks else 0.0) / WEEK_DAYS
            if rate_day == 0.0:
                continue
            lo, hi = _idx(t0), _idx(t1)   # [lo, hi) day-index span
            lo_c, hi_c = max(lo, 0), min(hi, len(days))
            if hi_c > lo_c:
                vals[lo_c:hi_c] += rate_day
    return pd.Series(vals, index=days)


def cliff_events(events: list[dict]) -> pd.DataFrame:
    """All cliff unlocks as (date, amount) rows — P2's event list."""
    rows = [(pd.Timestamp(_ts_of(e), unit="s", tz="UTC").normalize(),
             _tok_sum(e))
            for e in events if e.get("unlockType") == "cliff"]
    if not rows:
        return pd.DataFrame(columns=["date", "amount"])
    return (pd.DataFrame(rows, columns=["date", "amount"])
            .groupby("date", as_index=False)["amount"].sum())


def schedule_start(events: list[dict]) -> pd.Timestamp | None:
    if not events:
        return None
    return pd.Timestamp(min(_ts_of(e) for e in events),
                        unit="s", tz="UTC").normalize()


# ---------------------------------------------------------------------------
# Matrices for the backtest
# ---------------------------------------------------------------------------

def build_matrices(emissions_dir: Path, slug_to_sym: dict[str, str],
                   days: pd.DatetimeIndex,
                   lookaheads: tuple[int, ...] = (14, 30)) -> dict:
    """Supply, per-lookahead burden, and cliff tables keyed by perp symbol.

    Unlock accrual replays from each schedule's own first event (cliffs
    before ``days[0]`` must count into supply) through ``days[-1]`` plus the
    longest lookahead (the forward window near the end of ``days`` is part
    of the schedule known at t, not future market data).
    """
    horizon = max(lookaheads)
    supply_cols, burden_cols, cliffs = {}, {la: {} for la in lookaheads}, {}
    for slug, sym in sorted(slug_to_sym.items()):
        events = load_events(emissions_dir, slug)
        t0 = schedule_start(events)
        if t0 is None:
            continue
        ext_end = days[-1] + pd.Timedelta(days=horizon)
        daily = daily_unlock_series(events, min(t0, days[0]), ext_end)
        supply = daily.cumsum()
        # tokens_unlocking(t, t+N] = fwd-looking sum over the next N days
        for la in lookaheads:
            fwd = (daily.iloc[::-1].rolling(la, min_periods=1).sum()
                   .iloc[::-1].shift(-1))
            b = (fwd / supply.where(supply > 0)).reindex(days)
            b[days < t0] = np.nan          # token not yet launched at t
            burden_cols[la][sym] = b
        supply_cols[sym] = supply.reindex(days)
        cliffs[sym] = cliff_events(events)
    return {"supply": pd.DataFrame(supply_cols, index=days).sort_index(axis=1),
            "burden": {la: pd.DataFrame(cols, index=days).sort_index(axis=1)
                       for la, cols in burden_cols.items()},
            "cliffs": cliffs}


def supply_frame(emissions_dir: Path, slug_to_sym: dict[str, str],
                 days: pd.DatetimeIndex) -> pd.DataFrame:
    """Reconstructed supply on an arbitrary day index (P0 uses a full-span
    index reaching the reference stores' present frontier; schedule replay is
    not market data, so this never touches holdout returns)."""
    cols = {}
    for slug, sym in sorted(slug_to_sym.items()):
        events = load_events(emissions_dir, slug)
        t0 = schedule_start(events)
        if t0 is None:
            continue
        daily = daily_unlock_series(events, min(t0, days[0]), days[-1])
        cols[sym] = daily.cumsum().reindex(days)
    return pd.DataFrame(cols, index=days).sort_index(axis=1)


def mcap_control_signal(klines: dict, supply: pd.DataFrame,
                        days: pd.DatetimeIndex) -> pd.DataFrame:
    """C2: per-row z-score of log(close x reconstructed supply).

    High signal = large cap = short leg (the size-factor orientation,
    consistent with the house convention that high control signal shorts).
    Supply comes from the same reconstruction as the burden signal, per the
    registration (NOT CoinMetrics — the universes barely overlap).
    """
    cols = {}
    for sym in supply.columns:
        df = klines.get(sym)
        if df is None:
            cols[sym] = pd.Series(np.nan, index=days)
            continue
        close = df["close"].reindex(days)
        cols[sym] = close * supply[sym]
    mcap = pd.DataFrame(cols, index=days)
    lg = np.log(mcap.where(mcap > 0))
    mu = lg.mean(axis=1)
    sd = lg.std(axis=1, ddof=1)
    return lg.sub(mu, axis=0).div(sd.where(sd > 0), axis=0)


# ---------------------------------------------------------------------------
# Amendment exposure (reported_not_gated)
# ---------------------------------------------------------------------------

def amendment_exposure(events: list[dict], dev_start: pd.Timestamp,
                       dev_end: pd.Timestamp) -> dict:
    """Best-effort proxy for schedule-amendment share of dev-window unlocks.

    A single snapshot cannot distinguish TGE-original from amended entries;
    the proxy treats each category's FIRST linear event as the original rate
    and counts dev-window accrual from later rate changes (delta vs the
    original rate) as amended mass. Cliffs are assumed original. Reported,
    not gated, per the registration.
    """
    actual = daily_unlock_series(events, dev_start, dev_end)
    original = [e for e in events if e.get("unlockType") == "cliff"]
    seen: set = set()
    for e in sorted((e for e in events if e.get("unlockType") == "linear"),
                    key=_ts_of):
        if e.get("category") not in seen:
            seen.add(e.get("category"))
            original.append(e)
    counterfactual = daily_unlock_series(original, dev_start, dev_end)
    total = float(actual.sum())
    amended = float((actual - counterfactual).abs().sum())
    return {"dev_unlock_mass": total,
            "amended_mass_abs": amended,
            "amended_share": amended / total if total > 0 else 0.0,
            "n_linear_rate_changes": sum(
                1 for e in events if e.get("unlockType") == "linear") - len(seen)}
