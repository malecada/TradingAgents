"""One immutable, registered18-cell development-only factor correction.

No loader, network fallback, parameter search or historical output mutation.
The invalid-log shadow is a frozen-exposure diagnostic, never executable PnL.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from scripts.baseline_strategy_v2 import run_coin_backtest
from tradingagents.predlab import registry
from tradingagents.strategies.v2_sizing import (
    build_positions_with_hold, compute_realized_vol, vol_regime_mask,
)

ROOT = Path(__file__).resolve().parents[1]
KEY = 'audit_factor_floor_2026_09_10'
WINDOW = ('2021-11-07', '2025-03-31')
COINS = ('bitcoin', 'ethereum')
BASE = ROOT / 'data/factor-correction/2026-09-10'
ARCHIVE = ROOT / 'docs/factor-correction/original'
COSTS = dict(fee_rate=.0004, slippage=.0005, spread=.0001,
             price_impact=.00005, funding_rate=.0003,
             stop_loss=1., max_portfolio_dd=.15, take_profit=0.)
VARIANTS = ('primary', 'zero_execution', 'double_execution', 'zero_funding', 'legacy')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    with Path(path).open('x') as handle:
        json.dump(data, handle, indent=2, allow_nan=False)
        handle.write('\n')


def reserve_output(path, provenance):
    path.mkdir(parents=True, exist_ok=False)
    write_json(path / 'started.json', provenance)


def validate_market(frame):
    frame = frame.copy()
    dates = pd.DatetimeIndex(pd.to_datetime(frame['Date'], utc=True)).tz_localize(None)
    if (not len(dates) or not dates.is_monotonic_increasing or not dates.is_unique
            or not dates.equals(dates.normalize()) or dates[-1] > pd.Timestamp(WINDOW[1])
            or not dates.equals(pd.date_range(dates[0], dates[-1], freq='D'))):
        raise ValueError('invalid, incomplete or out-of-window market clock')
    vals = frame[['Open', 'High', 'Low', 'Close']].to_numpy(dtype=float)
    if (not np.isfinite(vals).all() or (vals <= 0).any()
            or (vals[:, 1] < vals.max(axis=1)).any()
            or (vals[:, 2] > vals.min(axis=1)).any()):
        raise ValueError('invalid OHLC values or envelope')
    frame['Date'] = dates
    return frame.reset_index(drop=True)


def metrics(returns):
    r = np.asarray(returns, dtype=float)
    if not len(r) or not np.isfinite(r).all() or (r <= -1).any():
        raise ValueError('unavailable return series')
    eq = np.r_[1., np.cumprod(1. + r)]
    sd = r.std(ddof=1) if len(r) > 1 else 0.
    nz = np.flatnonzero(r)
    active = r[:nz[-1]+1] if len(nz) else np.array([])
    active_sd = active.std(ddof=1) if len(active) > 1 else 0.
    return dict(sharpe=float(np.sqrt(365)*r.mean()/sd) if sd > 0 else 0.,
                sharpe_252=float(np.sqrt(252)*r.mean()/sd) if sd > 0 else 0.,
                total_return=float(eq[-1]-1),
                max_drawdown=float((eq/np.maximum.accumulate(eq)-1).min()),
                n_bars=len(r), n_trailing_zero_bars=int(len(r)-len(active)),
                active_sharpe_diagnostic=float(np.sqrt(365)*active.mean()/active_sd) if active_sd > 0 else 0.)


def index_returns(sleeves):
    a = np.asarray(sleeves, dtype=float)
    if a.ndim != 2 or a.shape[0] != 2 or not np.isfinite(a).all():
        raise ValueError('both complete sleeve clocks are required')
    return a.mean(axis=0)


def log_shadow(trace):
    r = trace['mark_return'].to_numpy(dtype=float)
    exposure = trace['exposure'].to_numpy(dtype=float)
    if (r <= -1).any() or not np.isfinite(r).all():
        raise ValueError('invalid log diagnostic arithmetic')
    net = trace['post_nav'].to_numpy()/trace['pre_nav'].to_numpy()-1
    shadow = net + exposure*(np.log1p(r)-r)
    if not np.isfinite(shadow).all() or (shadow <= -1).any():
        raise ValueError('invalid log diagnostic NAV')
    return shadow


def extract_functions(path, names):
    """Compile only pinned pure function definitions, without historical imports."""
    tree = ast.parse(Path(path).read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes} != set(names):
        raise ValueError('required archived functions absent')
    env = {'np': np, 'pd': pd}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return env


def build_targets(spec, data, functions):
    working = data
    if spec.get('xs'):
        start = max(df['Date'].iloc[0] for df in data.values())
        working = {c: df[df['Date'] >= start].reset_index(drop=True) for c, df in data.items()}
        if not working[COINS[0]]['Date'].equals(working[COINS[1]]['Date']):
            raise ValueError('XS common prior clock mismatch')
        sigs = dict(zip(COINS, functions['xs_mom_signals'](
            *(working[c]['Close'].to_numpy() for c in COINS), k=30)))
    else:
        sigs = {c: spec['builder'](df) for c, df in working.items()}
    out = {}
    for c, df in working.items():
        mask = (df['Date'] >= WINDOW[0]) & (df['Date'] <= WINDOW[1])
        frame = df.loc[mask].reset_index(drop=True)
        expected = pd.date_range(*WINDOW, freq='D')
        if not pd.DatetimeIndex(frame['Date']).equals(expected):
            raise ValueError('development clock differs from registration')
        if (df['Date'] < WINDOW[0]).sum() < 200:
            raise ValueError('insufficient signal warmup')
        signal = np.asarray(sigs[c])[mask]
        px = frame['Close'].to_numpy(dtype=float)
        visible = np.r_[px[0], px[:-1]]
        rv = compute_realized_vol(visible, lookback=20)
        pos = build_positions_with_hold(signal, vol_regime_mask(rv, .95),
            np.where(signal != 0, 1., 0.), rv, visible, .10, .5, 3., 7, .015)
        frame['signal'], frame['target'] = signal, pos
        out[c] = frame
    return out


def cost_variant(variant):
    costs = dict(COSTS)
    if variant in ('zero_execution', 'double_execution'):
        scale = 0 if variant == 'zero_execution' else 2
        for k in ('fee_rate', 'slippage', 'spread', 'price_impact'):
            costs[k] *= scale
    if variant == 'zero_funding': costs['funding_rate'] = 0.
    return costs


def old_metric_parity(r, saved):
    eq = np.cumprod(1 + r)
    measured = {'sharpe': metrics(r)['sharpe_252'], 'total_return': float(eq[-1]-1),
                'max_drawdown': float((eq/np.maximum.accumulate(eq)-1).min()), 'n_bars': len(r)}
    delta = {k: float(measured[k]-saved[k]) for k in measured}
    return {'matched': all(abs(v) <= 1e-10 for v in delta.values()), 'deltas': delta}


def guarded_variants(run):
    results = {}
    for variant in VARIANTS:
        try: results[variant] = run(variant)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            results[variant] = {'status': 'unavailable', 'reason': f'{type(exc).__name__}: {exc}'}
    return results


def main():
    provenance = registry.preflight(KEY, WINDOW)
    gate = registry.get_experiment(KEY)
    if gate['variants'] != list(VARIANTS): raise ValueError('variant grid mismatch')
    hashes = gate['pinned_files']
    for name, digest in hashes.items():
        if sha(ROOT / name) != digest: raise ValueError(f'input hash mismatch: {name}')
    output = BASE / 'results'
    reserve_output(output, {**provenance, 'started_utc': datetime.now(timezone.utc).isoformat(),
                            'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__})
    functions = extract_functions(ARCHIVE / 'factor_baselines_f359050.py',
        ['tsmom_signal', 'ma_cross_signal', 'donchian_signal', 'xs_mom_signals', 'long_only', 'build_config_specs'])
    specs = functions['build_config_specs']()
    configs = [{k:v for k,v in spec.items() if k != 'builder'} for spec in specs]
    if configs != gate['cells']: raise ValueError('configuration grid mismatch')
    old_engine = extract_functions(ARCHIVE / 'baseline_strategy_v2_f359050.py', ['run_coin_backtest'])['run_coin_backtest']
    original = {c['configname']: c['original_metrics'] for c in json.loads((ARCHIVE/'comparison.json').read_text())['cells']}
    data, data_errors = {}, {}
    for c in COINS:
        try: data[c] = validate_market(pd.read_csv(BASE/'inputs'/f'{c}.csv'))
        except (ValueError, KeyError, TypeError, OSError) as exc: data_errors[c] = str(exc)
    cells = []
    for spec, config in zip(specs, configs):
        name = spec['name']
        cell = {'id': name, 'config': config, 'metrics': {}, 'variants': {}, 'original_metrics': original[name]}
        try:
            if data_errors: raise ValueError(str(data_errors))
            targets = build_targets(spec, data, functions)
            traces, series_by_variant = {}, {}
            for c, frame in targets.items(): frame.to_parquet(output/f'{name}-{c}-targets.parquet', index=False)
            def run_variant(variant):
                sleeves, detail = [], {}
                for c, frame in targets.items():
                    trace = []
                    engine = old_engine if variant == 'legacy' else run_coin_backtest
                    kwargs = {} if variant == 'legacy' else {'trace': trace}
                    equity, m = engine(frame['Date'].to_numpy(), frame['Close'].to_numpy(),
                        frame['target'].to_numpy(), 10000., **cost_variant(variant),
                        highs=frame['High'].to_numpy(), lows=frame['Low'].to_numpy(), price_stop_pct=.03, **kwargs)
                    rets = np.asarray(equity)[1:]/np.asarray(equity)[:-1]-1
                    sleeves.append(rets)
                    detail[c] = {'metrics': metrics(rets), 'halted': bool(m['halted'])}
                    if variant != 'legacy':
                        t = pd.DataFrame(trace)
                        t.to_parquet(output/f'{name}-{variant}-{c}-trace.parquet', index=False)
                        halt = t[t['halted_after']]
                        detail[c]['halt_date'] = str(halt.iloc[0]['date']) if len(halt) else None
                        for field in ('gross_dollars', 'funding_dollars', 'fee_dollars', 'impact_dollars', 'turnover_dollars'):
                            detail[c][field] = float(t[field].sum())
                        detail[c]['price_stops'] = int(t['price_stop_hit'].sum())
                        detail[c]['stop_fills_outside_envelope'] = int(t['stop_outside_envelope'].sum())
                        if variant == 'primary': traces[c] = t
                portfolio = index_returns(sleeves)
                saved = pd.DataFrame(dict(zip(COINS, sleeves)), index=targets[COINS[0]]['Date'].iloc[1:])
                saved['index_return'] = portfolio
                saved.to_parquet(output/f'{name}-{variant}-returns.parquet')
                series_by_variant[variant] = saved
                return {'status': 'measured', 'metrics': metrics(portfolio), 'sleeves': detail}
            cell['variants'] = guarded_variants(run_variant)
            if cell['variants']['primary'].get('status') == 'measured':
                cell['metrics'] = {**cell['variants']['primary']['metrics'], 'status': 'qualified_benchmark_measurement', 'validated': False}
            else:
                cell['metrics'] = {**cell['variants']['primary'], 'validated': False}
            cell['legacy_scalar_parity'] = {'status': 'unavailable'}
            if cell['variants']['legacy'].get('status') == 'measured':
                cell['legacy_scalar_parity'] = old_metric_parity(series_by_variant['legacy']['index_return'].to_numpy(), original[name])
                if name == 'macross_10_50_ls':
                    best = pd.read_csv(ARCHIVE/'BEST_daily_returns.csv', index_col=0, parse_dates=True)
                    replay = series_by_variant['legacy'][list(COINS)]
                    cell['legacy_best_stream_parity'] = bool(replay.index.equals(best.index) and
                        np.allclose(replay.to_numpy(), best[list(COINS)].to_numpy(), rtol=0, atol=1e-10))
            try:
                if cell['variants']['primary'].get('status') != 'measured':
                    raise ValueError('primary exposure schedule unavailable')
                shadow = index_returns([log_shadow(traces[c]) for c in COINS])
                pd.DataFrame({'invalid_log_shadow': shadow}, index=series_by_variant['primary'].index).to_parquet(output/f'{name}-log-shadow.parquet')
                cell['invalid_log_shadow'] = {'metrics': metrics(shadow), 'status': 'invalid_frozen_exposure_diagnostic'}
            except (ValueError, KeyError, TypeError) as exc:
                cell['invalid_log_shadow'] = {'status': 'unavailable', 'reason': str(exc)}
        except (ValueError, KeyError, TypeError, OSError) as exc:
            # Data/target preparation failure still preserves every registered variant.
            reason = f'{type(exc).__name__}: {exc}'
            cell['metrics'] = {'status': 'unavailable', 'reason': reason, 'validated': False}
            for variant in VARIANTS:
                cell['variants'].setdefault(variant, {'status': 'unavailable', 'reason': reason})
            cell.setdefault('invalid_log_shadow', {'status': 'unavailable', 'reason': reason})
        cells.append(cell)
        print(name, json.dumps(cell['metrics']), flush=True)
    if len(cells) != 18: raise ValueError('incomplete grid')
    for name, digest in hashes.items():
        if sha(ROOT/name) != digest: raise ValueError(f'input changed: {name}')
    if registry.preflight(KEY, WINDOW) != provenance: raise ValueError('source/gate/policy changed')
    payload = {**provenance, 'experiment': KEY, 'window': list(WINDOW), 'cells': cells,
               'holdout_evaluated': False, 'models_refit': False, 'validated_strategies': 0,
               'input_sha256': hashes, 'completed_utc': datetime.now(timezone.utc).isoformat(),
               'output_sha256': {p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    write_json(output/'result.json', payload)
    for cell in cells:
        registry.log_trial(KEY, cell['id'], 'fixed_factor_correction', cell['config'], WINDOW,
            {**cell['metrics'], 'variants': cell['variants'], 'invalid_log_shadow':cell.get('invalid_log_shadow'),
             'result_sha256':sha(output/'result.json')})
    print('Completed18 fixed configuration records; no strategy validation.', flush=True)


if __name__ == '__main__':
    main()
