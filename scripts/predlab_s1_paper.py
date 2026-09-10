"""Version-2 S1 paper measurement, using shared decision and net accounting.

The two new journals journal_v2.jsonl and journal_champion_v2.jsonl do not
mix historical gross-only rows with corrected measurements. Signals use the
explicit next trade day and its prior calendar month's liquidity universe.
Base/overlay account states retain marked notionals; settlement charges actual
turnover once, signed observed funding and simple-return PnL. Gross close/mark
returns remain separately labelled diagnostics. Missing held prices or funding
make net measurement incomplete; local event stores are read without mutation.
No orders are submitted. This is measurement, not strategy validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import pp, opt
from tradingagents.accounting import ACCOUNTING_VERSION, accounting_step  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
JDIR = DATA_ROOT / "predlab" / "s1_paper"
JOURNAL_VERSION = 2
JOURNAL = JDIR / "journal_v2.jsonl"
CH_JOURNAL = JDIR / "journal_champion_v2.jsonl"
FAPI = "https://fapi.binance.com"
LOOKBACK_D = 70  # prior-month median qv + ewma-20 burn-in (tail wt < 0.2%) + slack
VT_TARGET, VT_CAP = 0.10, 2.0
CH_VT_TARGET, CH_BREADTH_FLOOR = 0.15, 100  # Phase-O champion overlay


def _fetch_klines(symbol: str, days: int) -> "pd.DataFrame | None":
    import urllib.request

    url = (f"{FAPI}/fapi/v1/klines?symbol={symbol}&interval=1d&limit={days}")
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            rows = json.load(r)
    except Exception:
        return None
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=[
        "open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "tb_base", "tb_quote", "ignore"])
    df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df[["high", "low", "close", "quote_volume"]].astype(float)


def _perp_symbols() -> "list[str]":
    import urllib.request

    with urllib.request.urlopen(f"{FAPI}/fapi/v1/exchangeInfo", timeout=20) as r:
        info = json.load(r)
    return sorted(s["symbol"] for s in info["symbols"]
                  if s["contractType"] == "PERPETUAL"
                  and s["quoteAsset"] == "USDT" and s["status"] == "TRADING")


def fetch_marks() -> dict[str, float] | None:
    """Midquotes observed now; missing/stale exchange event time is unavailable."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{FAPI}/fapi/v1/ticker/bookTicker", timeout=20) as r:
            rows = json.load(r)
    except Exception:
        return None
    now = datetime.now(timezone.utc).timestamp()
    marks = {}
    for row in rows:
        try:
            age = now - float(row['time']) / 1000
            bid, ask = float(row['bidPrice']), float(row['askPrice'])
            if 0 <= age <= 90 and 0 < bid <= ask and math.isfinite(ask):
                marks[row['symbol']] = (bid + ask) / 2
        except (ValueError, KeyError, TypeError):
            continue
    return marks or None


def load_panels_online(*, funding_snapshot=None, measurement_time=None) -> "dict[str, pd.DataFrame]":
    syms = _perp_symbols()
    highs, lows, closes, qvs = {}, {}, {}, {}
    for i, sym in enumerate(syms):
        df = _fetch_klines(sym, LOOKBACK_D)
        if df is None or len(df) < 40:
            continue
        # drop today's incomplete bar
        df = df[df.index < pd.Timestamp.now(tz=timezone.utc).floor("D")]
        highs[sym], lows[sym] = df["high"], df["low"]
        closes[sym], qvs[sym] = df["close"], df["quote_volume"]
        if i % 25 == 0:
            time.sleep(0.5)  # stay far under fapi weight limits
    park = {s: (np.log(highs[s] / lows[s]) ** 2) / (4 * np.log(2)) for s in highs}
    return _attach_funding({"close": pd.DataFrame(closes), "qv": pd.DataFrame(qvs),
                            "park": pd.DataFrame(park)}, funding_snapshot=funding_snapshot, measurement_time=measurement_time)


def load_panels_offline(*, funding_snapshot=None, measurement_time=None) -> "dict[str, pd.DataFrame]":
    closes, qvs, parks = {}, {}, {}
    for p in sorted((DATA_ROOT / "xsect" / "klines").glob("*.parquet")):
        df = pd.read_parquet(p).tail(LOOKBACK_D)
        closes[p.stem] = df["close"]
        qvs[p.stem] = df["quote_volume"]
        parks[p.stem] = (np.log(df["high"] / df["low"]) ** 2) / (4 * np.log(2))
    return _attach_funding({"close": pd.DataFrame(closes), "qv": pd.DataFrame(qvs),
                            "park": pd.DataFrame(parks)}, funding_snapshot=funding_snapshot, measurement_time=measurement_time)


def load_observed_funding(symbols, index, store_dir=None):
    """Read local event prints; never fill a missing settlement with zero.

    The store has no exchange schedule vintages. Coverage therefore uses a
    disclosed cadence inference, not a claim that missing events are impossible.
    A day requires a complete regular grid plus the next midnight print.
    """
    store_dir = Path(store_dir) if store_dir is not None else DATA_ROOT / 'xsect' / 'funding'
    daily = pd.DataFrame(np.nan, index=index, columns=symbols)
    coverage = {'method': 'observed_cadence_inference',
                'qualification': 'No historical exchange schedule vintage; inferred from prior 7d prints',
                'symbols': {}}
    for sym in symbols:
        path = store_dir / f'{sym}.parquet'
        info = {'covered_days': 0, 'requested_days': len(index), 'reason': 'missing store'}
        coverage['symbols'][sym] = info
        if not path.exists():
            continue
        try:
            rates = pd.read_parquet(path)['fundingRate'].astype(float).sort_index()
            if rates.index.tz is None or not rates.index.is_unique:
                info['reason'] = 'ambiguous or duplicate event timestamps'
                continue
            rates.index = rates.index.tz_convert('UTC')
            info['reason'] = 'missing event, boundary, or supported prior cadence'
            for day in index:
                prior = rates.loc[(rates.index >= day-pd.Timedelta(days=7)) & (rates.index < day)]
                if len(prior) < 3:
                    continue
                delta = prior.index.to_series().diff().dropna().min()
                hours = delta.total_seconds()/3600
                if hours not in (1, 2, 4, 8):
                    continue
                expected = pd.date_range(day, day+pd.Timedelta(days=1), freq=delta)
                observed = rates.loc[(rates.index >= day) & (rates.index <= expected[-1])]
                if not observed.index.equals(expected) or not np.isfinite(observed).all():
                    continue
                daily.loc[day, sym] = float(observed.iloc[:-1].sum())
            info['covered_days'] = int(daily[sym].notna().sum())
            if info['covered_days'] == len(index):
                info['reason'] = None
        except (ValueError, KeyError, OSError) as exc:
            info['reason'] = f'unreadable funding: {exc}'
    return daily, coverage


def _attach_funding(panels, *, funding_snapshot=None, measurement_time=None):
    if funding_snapshot is None:
        daily, coverage = load_observed_funding(panels['close'].columns, panels['close'].index)
    else:
        from tradingagents.predlab.funding_snapshot import load_funding_snapshot
        daily, coverage = load_funding_snapshot(funding_snapshot, panels['close'].columns,
                                                panels['close'].index, measurement_time=measurement_time)
    panels['funding'], panels['funding_coverage'] = daily, coverage
    return panels


def todays_book(panels: dict, signal: str = 'park_5', trade_day=None
                ) -> tuple[pd.Timestamp, pd.Series, int]:
    """Decision uses prior completed rows; universe belongs to the trade month."""
    last = panels['park'].index.max()
    trade_day = pd.Timestamp(trade_day) if trade_day is not None else last + pd.Timedelta(days=1)
    trade_day = trade_day.tz_localize('UTC') if trade_day.tzinfo is None else trade_day.tz_convert('UTC')
    trade_day = trade_day.floor('D')
    asof = trade_day - pd.Timedelta(days=1)
    if last < asof:
        raise ValueError('stale panels: last completed signal day unavailable')
    index = pd.date_range(panels['park'].index.min(), trade_day, tz='UTC')
    known = {k: panels[k].loc[panels[k].index < trade_day].reindex(index)
             for k in ('qv', 'park', 'close')}
    eligible = opt.monthly_universe(known['qv']).loc[trade_day]
    sig = opt.build_signal(known['park'], known['close'], signal).loc[trade_day].where(eligible)
    # Pandas EWMA carries a previous value across a missing last candle; it
    # is not an observable fresh signal/entry mark for that instrument.
    fresh = known['park'].loc[asof].notna() & known['close'].loc[asof].notna()
    sig = sig.where(fresh)
    w = pp.quintile_weights(sig, 'eq')
    return asof, w[w != 0], int(sig.notna().sum())


def realized_prev_return(panels: dict, prev_row: dict, asof: pd.Timestamp) -> float | None:
    """Unscaled gross close diagnostic; incomplete held prices remain null."""
    if not prev_row:
        return None
    close = panels['close']
    w = pd.Series(prev_row['weights'], dtype=float)
    w = w[w != 0]
    prev_day = pd.Timestamp(prev_row['asof'], tz='UTC')
    if prev_day not in close.index or asof not in close.index or prev_day >= asof:
        return None
    p0 = close.loc[prev_day].reindex(w.index)
    p1 = close.loc[asof].reindex(w.index)
    if not (np.isfinite(p0) & np.isfinite(p1) & (p0 > 0) & (p1 > 0)).all():
        return None
    return float((w * (p1 / p0 - 1)).sum())


def realized_prev_mark_return(prev_row: dict, marks: dict[str, float]) -> float | None:
    """Unscaled gross observed-price diagnostic, requiring every held mark."""
    prev_marks = prev_row.get('mark_px')
    if not prev_marks:
        return None
    total = 0.
    for sym, w in prev_row['weights'].items():
        if w == 0:
            continue
        p0, p1 = prev_marks.get(sym), marks.get(sym)
        if (p0 is None or p1 is None or not math.isfinite(p0) or
                not math.isfinite(p1) or p0 <= 0 or p1 <= 0):
            return None
        total += w * (p1 / p0 - 1)
    return float(total)


def _gap_free_rets(journal_rows: list[dict]) -> list[float]:
    """Latest contiguous measured NET daily sequence; legacy gross is excluded."""
    out = []
    prev_day = None
    for row in journal_rows:
        day = date.fromisoformat(row['asof'])
        ret = row.get('realized_base_net_ret')
        if (row.get('journal_version') != JOURNAL_VERSION or ret is None or
                not math.isfinite(ret) or prev_day is None or (day-prev_day).days != 1):
            out = []
        else:
            out.append(ret)
        prev_day = day
    return out


def vt_scale(journal_rows: list[dict], target: float = VT_TARGET) -> float | None:
    rets = _gap_free_rets(journal_rows)
    if len(rets) < 20:
        return None
    vol = float(np.std(rets[-20:], ddof=1)) * np.sqrt(pp.ANN_DAYS)
    return float(min(target / max(vol, 1e-9), VT_CAP))


def _settle(panels, prev, asof, account, targets):
    """Settle the prior intended daily book using the engine's exact step."""
    state = prev.get(account + '_state')
    if state is None:
        return None, None, 'previous account measurement incomplete'
    prev_day = pd.Timestamp(prev['asof'], tz='UTC')
    if asof - prev_day != pd.Timedelta(days=1):
        return None, None, 'journal gap: daily settlement unavailable'
    weights = pd.Series(targets, dtype=float)
    held = weights[weights != 0].index
    close = panels['close']
    if prev_day not in close.index or asof not in close.index:
        return None, None, 'held closing prices unavailable'
    p0, p1 = close.loc[prev_day].reindex(held), close.loc[asof].reindex(held)
    if not (np.isfinite(p0) & np.isfinite(p1) & (p0 > 0) & (p1 > 0)).all():
        return None, None, 'held closing prices incomplete'
    funding = panels.get('funding')
    if len(held) and (funding is None or asof not in funding.index):
        return None, None, 'observed daily funding unavailable'
    f = funding.loc[asof].reindex(held) if len(held) else pd.Series(dtype=float)
    if not np.isfinite(f).all():
        return None, None, 'observed daily funding incomplete'
    try:
        result = accounting_step(state['nav'], pd.Series(state['notionals'], dtype=float),
            p1/p0-1, target_weights=weights, funding=f, fee_rate=pp.TAKER_BP/1e4,
            date=prev['trade_day'])
    except ValueError as exc:
        return None, None, str(exc)
    current = {'nav': result['nav'], 'notionals': result['notionals'].to_dict()}
    measured = {k: result[k] for k in ('gross','carry','cost','net','turnover')}
    measured['postfee_weights'] = result['postfee_weights'].to_dict()
    return current, measured, None


def journal_one(journal: Path, panels: dict, signal: str, scale_key: str,
                vt_target: float, breadth_floor: int | None = None,
                marks: dict[str, float] | None = None, trade_day=None, *,
                prepare_only=False, require_complete=False, measurement_time=None) -> str | dict:
    rows = ([json.loads(line) for line in journal.read_text().splitlines()]
            if journal.exists() else [])
    if any(r.get('journal_version') != JOURNAL_VERSION for r in rows):
        raise ValueError('legacy journal version cannot mix with corrected v2 measurement')
    try:
        asof, w, breadth = todays_book(panels, signal, trade_day=trade_day)
    except ValueError as exc:
        return f'WAIT: {exc}'
    if require_complete:
        try:
            _admission_history(rows, asof)
        except ValueError as exc:
            return f'WAIT: {exc}'
    if w.empty:
        return 'WAIT: insufficient current signals; no new target instruction'
    if any(r['asof'] == str(asof.date()) for r in rows):
        return f'{journal.name}: already has {asof.date()} — idempotent skip'
    prev = rows[-1] if rows else None
    base_state, base, reason = {'nav': 1., 'notionals': {}}, None, 'initial measurement'
    overlay_state, overlay, overlay_reason = {'nav': 1., 'notionals': {}}, None, 'scale warmup'
    if prev:
        base_state, base, reason = _settle(panels, prev, asof, 'base', prev['weights'])
        if prev.get('executed_scale') is not None:
            targets = {s: v * prev['executed_scale'] for s, v in prev['weights'].items()}
            overlay_state, overlay, overlay_reason = _settle(panels, prev, asof, 'overlay', targets)
        else:
            overlay_state = prev.get('overlay_state')
    candidate = {'journal_version': JOURNAL_VERSION, 'asof': str(asof.date()),
                 'realized_base_net_ret': base['net'] if base else None}
    scale = vt_scale(rows + [candidate], vt_target)
    if breadth_floor is not None and scale is not None and breadth < breadth_floor:
        scale = 0.
    valid_marks = {s: marks[s] for s in w.index if marks and s in marks
                   and (not require_complete or (isinstance(marks[s], (int, float)) and not isinstance(marks[s], bool)))
                   and math.isfinite(marks[s]) and marks[s] > 0}
    missing_marks = set(w.index) - valid_marks.keys()
    if require_complete and prev:
        prior_held = {s for s, weight in prev['weights'].items() if weight != 0}
        missing_marks |= {s for s in prior_held if not marks or s not in marks or
                         not isinstance(marks[s], (int, float)) or isinstance(marks[s], bool) or
                         not math.isfinite(marks[s]) or marks[s] <= 0}
    gross = realized_prev_return(panels, prev, asof) if prev else None
    mark_ret = realized_prev_mark_return(prev, marks) if prev and marks else None
    # Row t stores the account before trading the newly decided next-day book.
    # Its realized fields settle row t-1, including that interval's entry fee.
    row = dict(candidate, trade_day=str((asof + pd.Timedelta(days=1)).date()),
        accounting_version=ACCOUNTING_VERSION, written_utc=(pd.Timestamp(measurement_time).isoformat()
            if measurement_time is not None else datetime.now(timezone.utc).isoformat()),
        n_universe=int(panels['park'].shape[1]), breadth=breadth,
        membership_hash=hashlib.sha256(','.join(sorted(w.index)).encode()).hexdigest()[:12],
        weights={k: float(v) for k,v in w.items()},
        realized_book_ret=gross, realized_mark_ret=mark_ret,
        diagnostic_return_definition='unscaled gross; excluded from volatility sizing',
        realized_net_ret=overlay['net'] if overlay else None,
        base_state=base_state, overlay_state=overlay_state,
        base_measurement=base, overlay_measurement=overlay,
        measurement_scale=prev.get('executed_scale') if prev else None,
        executed_scale=scale, scale_definition='target weights times scale at pretrade NAV',
        funding_coverage=_compact_snapshot_coverage(panels.get('funding_coverage', {'method': 'caller_supplied_daily_panel'}), asof),
        fee_rate=pp.TAKER_BP/1e4, funding_definition='observed daily signed rate; positive paid by longs',
        measurement_status='complete' if base is not None and overlay is not None and not missing_marks else 'incomplete',
        measurement_reason='; '.join(r for r in [reason, overlay_reason,
                                'current quotes incomplete' if missing_marks else None] if r),
        mark_px=valid_marks or None,
        mark_ts=datetime.now(timezone.utc).isoformat() if valid_marks else None,
        mark_coverage='complete' if not missing_marks else 'incomplete',
        est_turnover=None, est_cost=None)
    row[scale_key] = scale
    if require_complete:
        if missing_marks:
            return 'WAIT: current quotes incomplete'
        if prev and (base is None or (prev.get('executed_scale') is not None and overlay is None)):
            return f"WAIT: {row['measurement_reason']}"
    if prepare_only:
        return row
    return _append_prepared(journal, row, scale_key)


def _compact_snapshot_coverage(coverage, day):
    """Persist one measurement day's details plus immutable full-input provenance."""
    if coverage.get('method') != 'snapshot_observed_cadence_inference':
        return coverage
    key = day.isoformat()
    result = dict(coverage, settlement_day=str(day.date()), symbols={})
    for symbol, info in coverage['symbols'].items():
        detail = info['days'].get(key, {'status': 'unavailable', 'reason': info.get('reason') or 'day not covered'})
        result['symbols'][symbol] = dict(info, requested_days=1,
            covered_days=int(detail['status'] == 'admitted_inferred'),
            reason=detail['reason'], days={key: dict(detail)})
    return result


def _append_prepared(journal, row, scale_key):
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open('a') as fh:
        fh.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
        fh.flush()
        os.fsync(fh.fileno())
    return f"{journal.name} {row['asof']}: {len(row['weights'])} legs, {row['measurement_status']}, {scale_key} {row[scale_key]}"


def _admission_history(rows, asof):
    """An opted-in run cannot advance an ambiguous or already broken account."""
    def numeric(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

    def state_ok(value):
        return (isinstance(value, dict) and numeric(value.get('nav')) and value['nav'] > 0
                and isinstance(value.get('notionals'), dict)
                and all(isinstance(k, str) and numeric(v) for k, v in value['notionals'].items()))

    def finite_tree(value):
        if isinstance(value, dict):
            return all(finite_tree(v) for v in value.values())
        if isinstance(value, list):
            return all(finite_tree(v) for v in value)
        return not isinstance(value, float) or math.isfinite(value)

    previous = None
    for row in rows:
        if (not finite_tree(row) or row.get('measurement_status') not in ('complete', 'incomplete')
                or 'executed_scale' not in row
                or (row['executed_scale'] is not None and
                    (not numeric(row['executed_scale']) or row['executed_scale'] < 0))
                or row.get('journal_version') != JOURNAL_VERSION or row.get('accounting_version') != ACCOUNTING_VERSION
                or not isinstance(row.get('weights'), dict)
                or not all(numeric(v) for v in row['weights'].values())):
            raise ValueError('unsupported or malformed existing v2 journal')
        day = pd.Timestamp(row['asof'], tz='UTC')
        if day != day.floor('D') or str(day.date()) != row['asof'] or day > asof:
            raise ValueError('invalid or future existing journal date')
        if previous is not None and day - previous[0] != pd.Timedelta(days=1):
            raise ValueError('existing journal dates are duplicate or gapped')
        if row.get('mark_coverage') != 'complete':
            raise ValueError('existing journal has incomplete quote observations')
        for account, ret_key in [('base', 'realized_base_net_ret'), ('overlay', 'realized_net_ret')]:
            state = row.get(account + '_state')
            if not state_ok(state):
                raise ValueError(f'existing {account} state is broken or invalid')
            if ret_key not in row or account + '_measurement' not in row:
                raise ValueError(f'existing {account} measurement fields unavailable')
            ret, measure = row.get(ret_key), row.get(account + '_measurement')
            if previous is None:
                if ret is not None or measure is not None or any(state['notionals'].values()):
                    raise ValueError('existing journal lacks an observed flat initial state')
            elif account == 'overlay' and previous[1].get('executed_scale') is None:
                if (ret is not None or measure is not None or any(state['notionals'].values()) or
                        not math.isclose(state['nav'], previous[1]['overlay_state']['nav'], rel_tol=1e-9, abs_tol=1e-12)):
                    raise ValueError('existing overlay warmup is not observed flat')
            elif (not numeric(ret) or ret <= -1 or not isinstance(measure, dict)
                  or not all(numeric(measure.get(k)) for k in ('net', 'gross', 'carry', 'cost', 'turnover'))
                  or not math.isclose(ret, measure['net'], rel_tol=1e-9, abs_tol=1e-12)
                  or not math.isclose(ret, measure['gross']+measure['carry']-measure['cost'], rel_tol=1e-9, abs_tol=1e-12)
                  or not math.isclose(ret, state['nav']/previous[1][account+'_state']['nav']-1, rel_tol=1e-9, abs_tol=1e-12)):
                raise ValueError(f'existing {account} net measurement is incomplete or inconsistent')
        previous = (day, row)
    if previous is not None and asof - previous[0] not in (pd.Timedelta(0), pd.Timedelta(days=1)):
        raise ValueError('journal gap: daily settlement unavailable')


def journal_pair(panels, *, marks, funding_snapshot, trade_day=None, measurement_time=None, journals=None):
    """Prepare both unchanged paper algorithms before either financial append.

    This is logical admission of a pair, not a two-file filesystem transaction.
    Failures are returned as WAIT; already-written rows are never rewritten.
    """
    if funding_snapshot is None:
        return ['WAIT: explicit funding snapshot required']
    journals = (JOURNAL, CH_JOURNAL) if journals is None else tuple(journals)
    if len(journals) != 2 or journals[0] == journals[1]:
        raise ValueError('two distinct paper journals required')
    measurement_time = pd.Timestamp.now(tz='UTC') if measurement_time is None else pd.Timestamp(measurement_time)
    configurations = [('park_5', 'vt10_scale', VT_TARGET, None),
                      ('ewma_20', 'vt15_b100_scale', CH_VT_TARGET, CH_BREADTH_FLOOR)]
    try:
        loaded = _attach_funding(dict(panels), funding_snapshot=funding_snapshot, measurement_time=measurement_time)
        prepared = []
        for journal, (signal, key, target, breadth) in zip(journals, configurations):
            row = journal_one(Path(journal), loaded, signal, key, target, breadth, marks=marks,
                              trade_day=trade_day, prepare_only=True, require_complete=True,
                              measurement_time=measurement_time)
            if isinstance(row, str) and row.startswith('WAIT:'):
                return [row]
            prepared.append(row)
        # Serialization is part of admission, before opening either journal.
        for row in prepared:
            if isinstance(row, dict):
                json.dumps(row, sort_keys=True, allow_nan=False)
    except (ValueError, KeyError, TypeError, OSError, AttributeError) as exc:
        return [f'WAIT: {exc}']
    return [_append_prepared(Path(journal), row, configuration[1]) if isinstance(row, dict) else row
            for journal, row, configuration in zip(journals, prepared, configurations)]


def _already_done(date_str: str) -> bool:
    """Cheap pre-fetch guard: True if BOTH journals already hold `date_str`.
    Lets an hourly cron (laptop may be off at any fixed hour) exit before
    the ~500-request kline fetch on all but the first wake-up of the day."""
    for j in (JOURNAL, CH_JOURNAL):
        if not j.exists() or not any(
                json.loads(l)["asof"] == date_str
                for l in j.read_text().splitlines()):
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--funding-snapshot", default=os.environ.get("S1_FUNDING_SNAPSHOT"),
                    help="Immutable operational funding snapshot; no legacy fallback when configured")
    args = ap.parse_args()
    JDIR.mkdir(parents=True, exist_ok=True)
    expected = str((datetime.now(timezone.utc) - timedelta(days=1)).date())
    if not args.offline and _already_done(expected):
        print(f"both journals have {expected} — pre-fetch skip")
        return
    try:
        loader = load_panels_offline if args.offline else load_panels_online
        panels = loader(funding_snapshot=args.funding_snapshot) if args.funding_snapshot is not None else loader()
    except ValueError as exc:
        if args.funding_snapshot is None:
            raise
        print(f'WAIT: {exc}')
        return
    # prices as of write time — both journals share one snapshot
    marks = None if args.offline else fetch_marks()
    if args.funding_snapshot is not None:
        for message in journal_pair(panels, marks=marks, funding_snapshot=args.funding_snapshot,
                                    trade_day=pd.Timestamp.now(tz='UTC').floor('D')):
            print(message)
        return
    # original Phase-P book — config frozen for the pp2 vt10 confirmation
    print(journal_one(JOURNAL, panels, "park_5", "vt10_scale", VT_TARGET,
                      marks=marks, trade_day=pd.Timestamp.now(tz="UTC").floor("D")))
    # Phase-O final champion book — parallel forward journal
    print(journal_one(CH_JOURNAL, panels, "ewma_20", "vt15_b100_scale",
                      CH_VT_TARGET, CH_BREADTH_FLOOR, marks=marks,
                      trade_day=pd.Timestamp.now(tz="UTC").floor("D")))


if __name__ == "__main__":
    main()
