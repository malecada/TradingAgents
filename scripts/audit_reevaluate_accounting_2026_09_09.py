"""Immutable, development-only replay of the 24 registered accounting cells.

No legacy runner main, model fit, data fetch, or holdout read is used. Run only
after the source and registration are committed: --family NAME --execute.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from tradingagents.strategies.v3.backtest.dsr import (
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect import carry_xs, liq_fade, portfolio, trend, universe

FAMILIES = ('momentum', 'carry', 'liq_fade')
DEV = ('2021-01-01', '2025-03-31')
END_EXCLUSIVE = '2025-04-01'
N_PLACEBO = 500
BENCHMARK_DATES = ('2021-05-19', '2022-06-13', '2022-11-09', '2024-08-05', '2025-02-03')
MAJORS = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT', 'TRXUSDT')


@dataclass
class Prepared:
    replay: Callable
    expected_clock: pd.DatetimeIndex
    placebo: Callable
    benchmark: pd.Series | None = None
    metadata: dict = field(default_factory=dict)
    benchmark_required: bool = False


class PreparationBlocked(ValueError):
    def __init__(self, reason, metadata=None):
        super().__init__(reason)
        self.metadata = metadata or {}


def utc_clock(start, end, frequency='D'):
    def stamp(value):
        value = pd.Timestamp(value)
        return value.tz_localize('UTC') if value.tz is None else value.tz_convert('UTC')
    return pd.date_range(stamp(start), stamp(end), freq=frequency)


def weekly_book(members, rebalances, returns, cost_bps=10.):
    """Use the audited fixed-contract library twin, never the old script fast path."""
    days = returns.index
    return portfolio.fast_weekly_portfolio(
        members, rebalances, days, {d: i for i, d in enumerate(days)},
        returns.to_numpy(), {s: i for i, s in enumerate(returns.columns)}, cost_bps,
    )


def carry_book(weights, returns, funding, cost_bps=10., rf_daily=carry_xs.RF_DAILY):
    return carry_xs.run_ls_portfolio(weights, returns, funding, cost_bps, rf_daily)


def hourly_book(weights, returns, cost_bps=10., rf_annual=.045, *, lifecycle_events=None):
    if lifecycle_events:
        from tradingagents.xsect.lifecycle import guard_target_schedule
        guard_target_schedule(weights, lifecycle_events)
    return liq_fade.run_hourly_portfolio(weights, returns, cost_bps, rf_annual)


def dsr(values, n):
    """Original per-series house estimator; n is frozen, not data selected."""
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        return None
    sd = float(values.std(ddof=1))
    variance = variance_of_sr(values)
    if sd <= 0 or not np.isfinite(variance) or variance <= 0:
        return None
    return float(deflated_sharpe_ratio(values.mean()/sd,
        expected_max_sharpe(n, variance), np.sqrt(variance)))


def summarize(series, expected_clock, original_n, current_n, hourly_family=False):
    if not series.index.equals(expected_clock) or not np.isfinite(series.to_numpy()).all():
        raise ValueError('incomplete return clock or unavailable portfolio observation')
    sr_fn = liq_fade.sharpe_daily if hourly_family else portfolio.sr
    return {'net_sr': float(sr_fn(series)), 'maxdd': portfolio.maxdd(series),
            'total_return': float((1.+series).prod()-1.), 'mean_daily_return': float(series.mean()),
            'n_days': len(series), 'first': str(series.index.min()), 'last': str(series.index.max()),
            'original_dsr_n': original_n, 'current_dsr_n': current_n,
            'dsr_original_denominator': dsr(series.to_numpy(), original_n),
            'dsr_current_denominator': dsr(series.to_numpy(), current_n),
            'dsr_policy': 'original_per_series_skew_kurtosis_estimator; trial counts are policy counts, not measured independence'}


def evaluate_cell(config, family_gate, current_n, prepared):
    original_n = family_gate['original_dsr_n']
    floor = family_gate['primary_thresholds']
    result = {'status': 'complete', 'original_gate_pass': None,
              'current_dsr_policy_pass': None, 'forensics': {}}
    streams = {}
    variants = [('primary', float(family_gate['cost_bps']), 'simple'),
                ('zero_fee', 0., 'simple'),
                ('double_fee', float(family_gate['stress_cost_bps']), 'simple'),
                ('invalid_log_pnl', float(family_gate['cost_bps']), 'log')]
    for name, cost, convention in variants:
        try:
            net = prepared.replay(config, cost, convention)
            metrics = summarize(net, prepared.expected_clock, original_n, current_n,
                                hourly_family='thr' in config)
            streams[name] = net
            if name == 'primary':
                result['corrected'] = metrics
            else:
                result['forensics'][name] = {'status': 'computed', **metrics,
                    'eligible': False, 'cost_bps': cost, 'convention': convention}
        except Exception as exc:
            failure = {'status': 'blocked', 'reason': f'{type(exc).__name__}: {exc}'}
            if name == 'primary':
                result.update(failure)
            else:
                result['forensics'][name] = failure
    if 'corrected' not in result:
        # Advance a shared placebo RNG even when this cell cannot be evaluated.
        try:
            prepared.placebo(config, False)
        except Exception as exc:
            result['placebo_rng_advance_error'] = f'{type(exc).__name__}: {exc}'
        result['remaining_gates'] = {'status': 'not_run_primary_data_unavailable'}
        return result, streams

    m = result['corrected']
    sr_ok = m['net_sr'] >= floor['net_sr_min']
    original_dsr = m['dsr_original_denominator']
    original_dsr_ok = original_dsr is not None and original_dsr >= floor['dsr_min']
    result['primary_checks'] = {'net_sr': sr_ok,
        'dsr_original_denominator': original_dsr_ok if original_dsr is not None else None}
    run_remaining = sr_ok and original_dsr_ok
    if not run_remaining:
        result['original_gate_pass'] = False if not sr_ok or original_dsr is not None else None
        result['current_dsr_policy_pass'] = False if not sr_ok or m['dsr_current_denominator'] is not None else None
        result['remaining_gates'] = {'status': 'not_run_primary_gate_failed' if result['original_gate_pass'] is False
                                      else 'not_run_primary_inference_unavailable'}
        try:
            prepared.placebo(config, False)
        except Exception as exc:
            result['placebo_rng_advance_error'] = f'{type(exc).__name__}: {exc}'
        return result, streams

    try:
        if prepared.benchmark_required and prepared.benchmark is None:
            raise ValueError('required benchmark unavailable; paired gates cannot be evaluated')
        remaining = prepared.placebo(config, True)
        if remaining.get('status') != 'computed' or not np.isfinite(remaining['placebo_p']):
            raise ValueError('incomplete placebo family')
        checks = {'placebo_p': remaining['placebo_p'] <= floor['placebo_p_max']}
        if prepared.benchmark is not None:
            if not prepared.benchmark.index.equals(prepared.expected_clock):
                raise ValueError('benchmark clock differs')
            params = family_gate['bootstrap']
            paired = portfolio.paired_bootstrap(streams['primary'], prepared.benchmark,
                block=params['mean_block'], n=params['draws'], seed=params['seed'])
            remaining['paired_bootstrap'] = paired
            checks['delta_sr'] = paired['delta_sr'] > floor['delta_sr_vs_benchmark_min']
            checks['p_pos'] = paired['p_pos'] >= floor['p_pos_min']
        remaining['checks'] = checks
        result['remaining_gates'] = remaining
        result['original_gate_pass'] = all(checks.values())
        result['current_dsr_policy_pass'] = bool(result['original_gate_pass'] and
            m['dsr_current_denominator'] is not None and m['dsr_current_denominator'] >= floor['dsr_min'])
    except Exception as exc:
        result['status'] = 'incomplete_remaining_gates'
        result['remaining_gates'] = {'status': 'blocked', 'reason': f'{type(exc).__name__}: {exc}'}
    return result, streams


def _source(ctx):
    return Path(ctx.gate['source_roots'][0])


def _json(ctx, path):
    return json.loads(ctx.track(path).read_text())


def original_results(ctx, family):
    directory = {'momentum': 'xs_mom', 'carry': 'carry_xs', 'liq_fade': 'liq_fade'}[family]
    data = _json(ctx, _source(ctx)/'rebuild'/directory/'dev_results.json')
    found = {}
    for cell in ctx.family_gate['cells']:
        matches = [r for r in data['results'] if all(r['config'].get(k) == v for k, v in cell.items() if k != 'id')]
        if len(matches) != 1:
            raise ValueError(f'original cell provenance ambiguous or absent: {cell["id"]}')
        row = matches[0]
        n = row['metrics'].get('n_trials_at_eval', data.get('n_trials_at_eval'))
        if n != ctx.family_gate['original_dsr_n']:
            raise ValueError(f'original DSR denominator differs for {cell["id"]}: {n}')
        found[cell['id']] = {'metrics': row['metrics'], 'gate_pass': row.get('gate_pass'),
                              'interpretation': 'preserved historical measurement; prior accounting invalidated'}
    return found


def load_daily(ctx):
    root = _source(ctx)/'xsect'
    manifest = _json(ctx, root/'klines_manifest.json')
    if not manifest:
        raise ValueError('empty original daily inventory')
    klines = {}
    for name in sorted(manifest):
        frame = ctx.read_market(root/'klines'/f'{name}.parquet', start=None, end_exclusive=END_EXCLUSIVE)
        if not frame.empty:
            if not {'close', 'quote_volume'} <= set(frame.columns):
                raise ValueError(f'missing price/volume columns: {name}')
            klines[name] = frame
    if not klines:
        raise ValueError('no development daily inputs')
    required = utc_clock(*DEV)
    btc = klines.get('BTCUSDT')
    if btc is None or not np.isfinite(btc.close.reindex(required)).all() or (btc.close.reindex(required) <= 0).any():
        raise ValueError('incomplete BTC development daily anchor clock')
    return klines


def _daily_returns(klines, names):
    days = utc_clock(min(klines[s].index.min() for s in names), DEV[1])
    close = pd.DataFrame({s: klines[s].close.reindex(days) for s in names}, index=days)
    close = close.where(close > 0)
    return np.log(close).diff()


def prepare_momentum(ctx):
    klines = load_daily(ctx)
    reb = universe.weekly_rebalance_dates(*DEV)
    eligible = {d: universe.eligibility(klines, d, top_n=100) for d in reb}
    bad = {str(d): len(v) for d, v in eligible.items() if d.year == 2021 and len(v) < 20}
    if bad:
        raise PreparationBlocked('original eligibility <20 on 2021 Monday', {'bad_rebalances': bad})
    lr = _daily_returns(klines, sorted(set().union(*map(set, eligible.values()))))
    simple = np.expm1(lr)
    clock = utc_clock(reb[0]+pd.Timedelta(days=1), DEV[1])
    bench = None
    try:
        candidate = weekly_book(eligible, reb, simple, ctx.family_gate['cost_bps'])
        benchmark_metadata = summarize(candidate, clock, ctx.family_gate['original_dsr_n'], ctx.gate['current_dsr']['n_trials'])
        # Original benchmark range guard is retained as a comparator qualification.
        if not 1450 <= len(candidate) <= 1550 or not -1.5 < portfolio.sr(candidate) < 2.:
            raise ValueError('original benchmark harness range check failed')
        bench = candidate
        benchmark_metadata['status'] = 'computed'
        ctx.write_frame('benchmark.parquet', bench.rename('net').to_frame())
    except Exception as exc:
        bench = None
        benchmark_metadata = {'status': 'unavailable', 'reason': f'{type(exc).__name__}: {exc}'}
    scores = {(c['L'], c['skip']): None for c in ctx.family_gate['cells']}
    for key in scores:
        scores[key] = {d: portfolio.momentum_scores(klines, eligible[d], d, *key) for d in reb}
    def members(config):
        return {d: [s for s, _ in sorted(v.items(), key=lambda item: -item[1])[:config['K']]]
                for d, v in scores[config['L'], config['skip']].items()}
    def replay(config, cost, convention):
        return weekly_book(members(config), reb, simple if convention == 'simple' else lr, cost)
    def placebo(config, run):
        if not run:
            return {'status': 'not_run_primary_gate_failed'}
        real_sr = portfolio.sr(replay(config, ctx.family_gate['cost_bps'], 'simple'))
        srs = []
        for p in range(N_PLACEBO):
            rng = np.random.default_rng(p)
            shuffled = {}
            for d, score in scores[config['L'], config['skip']].items():
                names = list(score)
                rng.shuffle(names)
                shuffled[d] = names[:config['K']]
            srs.append(portfolio.sr(weekly_book(shuffled, reb, simple, ctx.family_gate['cost_bps'])))
        return {'status': 'computed', 'n_draws': N_PLACEBO,
                'placebo_p': portfolio.rank_placebo_pvalue(real_sr, srs), 'placebo_srs': srs}
    return Prepared(replay, clock, placebo, bench,
        {'n_source_symbols': len(klines), 'n_rebalances': len(reb),
         'benchmark': benchmark_metadata,
         'holding_contract': 'weekly fixed contracts; first accrual January5; no terminal liquidation invented'},
         benchmark_required=True)


def prepare_carry(ctx):
    klines = load_daily(ctx)
    refresh = trend.monthly_refresh_dates(*DEV)
    members = {d: universe.eligibility(klines, d, top_n=50) for d in refresh}
    names = sorted(set().union(*map(set, members.values())))
    if not names:
        raise ValueError('empty carry universe')
    lr = _daily_returns(klines, names)
    funding = {s: ctx.read_market(_source(ctx)/'xsect/funding'/f'{s}.parquet',
                start=None, end_exclusive=END_EXCLUSIVE) for s in names}
    fund = carry_xs.build_funding_matrix(funding, lr.index, names)
    weights = {}
    for c in ctx.family_gate['cells']:
        weights[c['id']] = carry_xs.carry_weights(lr.index, carry_xs.carry_signal(fund, c['L']), fund, members, c['leg_frac'])
    rf = (1.+ctx.family_gate['rf_annual'])**(1./365)-1
    def book(w, cost, convention='simple'):
        return carry_book(w, np.expm1(lr) if convention == 'simple' else lr, fund, cost, rf).loc[lambda x: x.index > refresh[0]]
    def replay(config, cost, convention):
        return book(weights[config['id']], cost, convention)
    def placebo(config, run):
        if not run:
            return {'status': 'not_run_primary_gate_failed'}
        real_sr = portfolio.sr(replay(config, ctx.family_gate['cost_bps'], 'simple'))
        results = {}
        for name, shift in [('independent', trend.circular_shift_weights), ('shared', trend.shared_shift_weights)]:
            srs = [portfolio.sr(book(shift(weights[config['id']], np.random.default_rng(p)), ctx.family_gate['cost_bps']))
                   for p in range(N_PLACEBO)]
            results[name] = {'p': portfolio.rank_placebo_pvalue(real_sr, srs), 'srs': srs}
        return {'status': 'computed', 'n_draws_per_family': N_PLACEBO,
                'placebo_p': max(v['p'] for v in results.values()), 'families': results}
    clock = utc_clock(refresh[0]+pd.Timedelta(days=1), DEV[1])
    return Prepared(replay, clock, placebo, metadata={
        'n_source_symbols': len(klines), 'n_carry_symbols': len(names), 'n_refreshes': len(refresh),
        'funding': 'observed daily sum, supplied missing funding never filled', 'rf_daily': rf,
        'placebo_clock': 'available pre-April2025 history including causal warmup; no later prices or weights'})


def membership_mask(universe_by_month, columns, index):
    mask = pd.DataFrame(False, index=index, columns=columns)
    months = sorted((utc_clock(k, k)[0], v) for k, v in universe_by_month.items())
    for i, (start, names) in enumerate(months):
        end = months[i+1][0] if i+1 < len(months) else index[-1]+pd.Timedelta(hours=1)
        mask.loc[(index >= start) & (index < end), [s for s in names if s in columns]] = True
    return mask


def forward_probe(returns, triggers, horizon, *, lifecycle_events=None):
    original = returns.rolling(horizon, min_periods=horizon).sum().shift(-horizon)
    compound = np.expm1(np.log1p(returns).rolling(horizon, min_periods=horizon).sum().shift(-horizon))
    selected = triggers.to_numpy()
    positions = np.arange(len(returns))[:, None]
    censored = selected & (positions+horizon >= len(returns))
    missing = selected & ~censored & ~np.isfinite(compound.to_numpy())
    lifecycle = np.zeros_like(selected, dtype=bool)
    lifecycle_fields = {}
    if lifecycle_events:
        from tradingagents.xsect.lifecycle import unavailable_forward_windows
        lifecycle = selected & ~censored & unavailable_forward_windows(
            returns.index, returns.columns, horizon, lifecycle_events).to_numpy()
        lifecycle_fields = {'n_lifecycle_unavailable_window': int(lifecycle.sum()),
                            'n_missing_return_and_lifecycle': int((missing & lifecycle).sum()),
                            'lifecycle_window': 'entry t+1; fixed-quantity horizon; exit availability t+H+1; terminal touch unavailable'}
        missing &= ~lifecycle  # disjoint reason counts; overlap is reported above
    scoreable = selected & ~censored & ~missing & ~lifecycle
    unavailable = missing.any() or lifecycle.any()
    return {'status': 'unavailable' if unavailable else 'computed',
            'n_events': int(selected.sum()), 'n_scoreable': int(scoreable.sum()),
            'n_endpoint_censored': int(censored.sum()), 'n_missing_internal_window': int(missing.sum()),
            'mean_original_sum': float(original.to_numpy()[scoreable].mean()) if scoreable.any() else None,
            'mean_compounded_return': float(compound.to_numpy()[scoreable].mean()) if scoreable.any() else None,
            'gate_value': (float(compound.to_numpy()[scoreable].mean())
                           if scoreable.any() and not (lifecycle_events and unavailable) else None),
            'gate_measure': 'compounded simple forward return; original sum retained as historical diagnostic',
            **lifecycle_fields}


def p1_probe(close, qvol, benchmark_dates=BENCHMARK_DATES, required=4):
    """A missing event-day bar cannot establish absence of a cascade."""
    close, qvol = close.loc[DEV[0]:, list(MAJORS)], qvol.loc[DEV[0]:, list(MAJORS)]
    r = np.log(close.where(close > 0)).diff()
    volume = np.log1p(qvol.where(qvol >= 0))
    history = (r.notna().rolling(2160, min_periods=1).sum() >= 1440) & (
        volume.notna().rolling(2160, min_periods=1).sum() >= 1440)
    known = np.isfinite(r) & np.isfinite(volume) & history
    targets = pd.DatetimeIndex([hour for day in benchmark_dates
        for hour in pd.date_range(pd.Timestamp(day, tz='UTC'), periods=24, freq='h')])
    missing = ~known.reindex(targets, fill_value=False)
    triggers = liq_fade.cascade_triggers(close, qvol, 2.5)
    observed = triggers & known
    daily = observed.groupby(observed.index.normalize()).any()
    flags = {}
    known_hits, known_misses, unknown = [], [], []
    for day in benchmark_dates:
        timestamp = pd.Timestamp(day, tz='UTC')
        flags[day] = daily.loc[timestamp].index[daily.loc[timestamp]].tolist() if timestamp in daily.index else []
        hours = pd.date_range(timestamp, periods=24, freq='h')
        if flags[day]:
            known_hits.append(day)
        elif known.reindex(hours, fill_value=False).to_numpy().all():
            known_misses.append(day)
        else:
            unknown.append(day)
    passes = True if len(known_hits) >= required else (False if len(known_hits)+len(unknown) < required else None)
    return {'pass': passes, 'matched': flags, 'required': required,
            'n_known_hit_days': len(known_hits), 'known_hit_days': known_hits,
            'known_miss_days': known_misses, 'unknown_days': unknown,
            'n_unavailable_benchmark_hours': int(missing.to_numpy().sum()),
            'n_required_symbol_hours': len(targets)*len(MAJORS)}


def p2_gate(cells):
    known = {name: r for name, r in cells.items()
             if r['status'] == 'computed' and r.get('gate_value') is not None and np.isfinite(r['gate_value'])}
    passes = any(r['gate_value'] > .0025 for r in known.values())
    result = True if passes else (False if len(known) == len(cells) else None)
    return {'pass': result, 'cells': cells, 'threshold': .0025,
            'n_scoreable_cells': len(known), 'n_registered_cells': len(cells)}


def draw_liq_placebo(triggers, mask, rng, family, materialize=True):
    """Draw exactly the original RNG calls, optionally without building a book."""
    out = np.zeros(triggers.shape, dtype=bool) if materialize else None
    n = len(triggers)
    if family == 'shift':
        if n-24 <= 24:
            raise ValueError('trigger clock too short for original 24-hour offset')
        for j in range(len(triggers.columns)):
            shift = int(rng.integers(24, n-24+1))
            if materialize:
                out[:, j] = np.roll(triggers.iloc[:, j].to_numpy(), shift)
    elif family == 'random':
        counts = triggers.sum(axis=0).to_numpy()
        for j, count in enumerate(counts):
            if count:
                eligible = np.flatnonzero(mask.iloc[:, j].to_numpy())
                selected = rng.choice(eligible, size=int(count), replace=False)
                if materialize:
                    out[selected, j] = True
    else:
        raise ValueError(f'unknown placebo family {family}')
    return pd.DataFrame(out, index=triggers.index, columns=triggers.columns) if materialize else None


def prepare_liq_fade(ctx):
    lifecycle_events = ctx.gate.get('lifecycle_events', [])
    source = _source(ctx)/'xsect'
    symbols = [s.strip() for s in ctx.track(source/'liq_fade_symbols.txt').read_text().splitlines() if s.strip()]
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError('empty or duplicate original liq-fade symbols')
    monthly = _json(ctx, source/'liq_fade_universe.json')
    hourly_clock = utc_clock(ctx.family_gate['warmup_start'], ctx.family_gate['hourly_end'], 'h')
    frames = {s: ctx.read_market(source/'klines_1h'/f'{s}.parquet',
              start=ctx.family_gate['warmup_start'], end_exclusive=END_EXCLUSIVE) for s in sorted(set(symbols)|set(MAJORS))}
    if any(frame.empty for frame in frames.values()):
        raise ValueError('required liq-fade hourly symbol has no development observations')
    close = pd.DataFrame({s: f.close.reindex(hourly_clock) for s, f in frames.items()}, index=hourly_clock).where(lambda x: x > 0)
    qvol = pd.DataFrame({s: f.quote_volume.reindex(hourly_clock) for s, f in frames.items()}, index=hourly_clock)
    dev_clock = utc_clock(DEV[0], ctx.family_gate['hourly_end'], 'h')
    if not np.isfinite(close.BTCUSDT.reindex(dev_clock)).all():
        raise PreparationBlocked('incomplete BTC hourly anchor clock')
    daily = ctx.read_market(source/'klines/BTCUSDT.parquet', start=DEV[0], end_exclusive=END_EXCLUSIVE)
    a = close.BTCUSDT.loc[DEV[0]:].resample('D').last().pct_change(fill_method=None)
    daily_clock = utc_clock(*DEV)
    b = daily.close.reindex(daily_clock).pct_change(fill_method=None)
    paired = pd.concat({'hourly': a, 'daily': b}, axis=1).iloc[1:]
    p0 = {'pass': None, 'n_days': len(paired)}
    if np.isfinite(paired.to_numpy()).all() and len(paired) >= 2:
        corr = float(paired.hourly.corr(paired.daily))
        p0.update(corr=corr, **{'pass': bool(corr > .99)})
    # Original P1 uses the eight majors without the membership mask.
    p1 = p1_probe(close.loc[dev_clock], qvol.loc[dev_clock])
    cols = sorted(symbols)
    close, qvol = close[cols], qvol[cols]
    lr = np.log(close).diff()
    ret = np.expm1(lr).loc[dev_clock]
    mask = membership_mask(monthly, cols, hourly_clock)
    triggers = {thr: (liq_fade.cascade_triggers(close, qvol, thr) & mask).loc[dev_clock]
                for thr in sorted({c['thr'] for c in ctx.family_gate['cells']})}
    p2_cells = {c['id']: forward_probe(ret, triggers[c['thr']], c['H'], lifecycle_events=lifecycle_events)
                for c in ctx.family_gate['cells']}
    p2 = p2_gate(p2_cells)
    metadata = {'probes': {'P0': p0, 'P1': p1, 'P2': p2}, 'n_original_symbols': len(symbols),
                'funding': 'excluded as originally registered; not executable all-in net',
                'placebo_seed_policy': 'shared default_rng(48), original grid order, skipped books advance identical draws'}
    if lifecycle_events:
        metadata['lifecycle'] = {'events': lifecycle_events, 'synthetic_settlement': False,
            'scope': 'declared contract terminations only; no flag certifies complete lifecycle history',
            'guard': 'P2 hypothetical windows and every primary/cost/convention/placebo target schedule'}
    if any(p['pass'] is not True for p in (p0, p1, p2)):
        raise PreparationBlocked('original corrected probe requirements not all satisfied', metadata)
    rng = np.random.default_rng(48)
    weights = {}
    active = {}
    for c in ctx.family_gate['cells']:
        trig = triggers[c['thr']]
        names = trig.columns[trig.to_numpy().any(axis=0)].tolist()
        active[c['id']] = (trig[names], mask.loc[dev_clock, names])
        weights[c['id']] = liq_fade.event_weights_hourly(trig[names], c['H'], w_per=.1, cap=1.)
    def replay(config, cost, convention):
        w = weights[config['id']]
        returns = ret[w.columns] if convention == 'simple' else lr.loc[dev_clock, w.columns]
        return hourly_book(w, returns, cost, ctx.family_gate['rf_annual'], lifecycle_events=lifecycle_events)
    def placebo(config, run):
        trig, member = active[config['id']]
        real_sr = liq_fade.sharpe_daily(replay(config, ctx.family_gate['cost_bps'], 'simple')) if run else None
        result = {}
        failure = None
        for family in ('shift', 'random'):
            srs = []
            for _ in range(N_PLACEBO):
                draw = draw_liq_placebo(trig, member, rng, family, materialize=run and failure is None)
                if run and failure is None:
                    try:
                        w = liq_fade.event_weights_hourly(draw, config['H'], .1, 1.)
                        srs.append(liq_fade.sharpe_daily(hourly_book(w, ret[w.columns],
                            ctx.family_gate['cost_bps'], ctx.family_gate['rf_annual'], lifecycle_events=lifecycle_events)))
                    except Exception as exc:
                        # Remaining RNG draws still advance; no dropping failed placebos.
                        failure = exc
            if run and failure is None:
                result[family] = {'p': portfolio.rank_placebo_pvalue(real_sr, srs), 'srs': srs}
        if failure is not None:
            raise failure
        if not run:
            return {'status': 'not_run_primary_gate_failed', 'rng_advanced': True}
        return {'status': 'computed', 'families': result, 'n_draws_per_family': N_PLACEBO,
                'placebo_p': max(v['p'] for v in result.values())}
    return Prepared(replay, daily_clock, placebo, metadata=metadata)


PREPARERS = {'momentum': prepare_momentum, 'carry': prepare_carry, 'liq_fade': prepare_liq_fade}


def run_family(ctx, family):
    declared = ctx.family_gate['cells']
    cells = []
    originals = {}
    prepared = None
    payload = {'family': family, 'status': 'completed', 'no_selection': True, 'holdout_read': False,
               'models_refit': False, 'interpretation': 'historical gate correction; no strategy validation or promotion',
               'n_registered_cells': len(declared), 'original_dsr_n': ctx.family_gate['original_dsr_n'],
               'current_dsr_n': ctx.gate['current_dsr']['n_trials']}
    try:
        originals = original_results(ctx, family)
        prepared = PREPARERS[family](ctx)
    except Exception as exc:
        payload.update(status='blocked', reason=f'{type(exc).__name__}: {exc}')
        if isinstance(exc, PreparationBlocked):
            payload['preparation'] = exc.metadata
        for cell in declared:
            cells.append({'id': cell['id'], 'config': {k: v for k, v in cell.items() if k != 'id'},
                          'metrics': {'status': 'blocked', 'reason': payload['reason'],
                                      'original': originals.get(cell['id']), 'original_gate_pass': None,
                                      'remaining_gates': {'status': 'not_run_data_or_probe_blocked'},
                                      'forensics': {'status': 'not_run_data_or_probe_blocked'}}})
    if prepared is not None:
        payload['preparation'] = prepared.metadata
        for cell in declared:
            print(f'{family} {cell["id"]}: accounting and declared forensics', flush=True)
            metrics, streams = evaluate_cell(cell, ctx.family_gate, ctx.gate['current_dsr']['n_trials'], prepared)
            metrics['original'] = originals.get(cell['id'])
            if originals.get(cell['id']) and metrics.get('corrected'):
                old = originals[cell['id']]['metrics']
                metrics['differences_from_original'] = {
                    k: metrics['corrected'][k]-old[k] for k in ('net_sr', 'maxdd') if k in old}
            if streams:
                ctx.write_frame(f'{cell["id"]}.parquet', pd.DataFrame(streams))
            cells.append({'id': cell['id'], 'config': {k: v for k, v in cell.items() if k != 'id'}, 'metrics': metrics})
            print(f'{family} {cell["id"]}: {metrics["status"]}; original gate={metrics["original_gate_pass"]}', flush=True)
        if any(c['metrics']['status'] != 'complete' for c in cells):
            payload['status'] = 'completed_with_unavailable_cells'
    payload['n_complete'] = sum(c['metrics']['status'] == 'complete' for c in cells)
    payload['n_original_gate_pass'] = sum(c['metrics']['original_gate_pass'] is True for c in cells)
    return ctx.finish(payload, cells)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=FAMILIES, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({'family': args.family, 'execute': False, 'status': 'no inputs consumed'}))
        return
    from scripts.audit_reeval_common import RunContext
    run_family(RunContext(args.family), args.family)


if __name__ == '__main__':
    main()
