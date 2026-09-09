"""Registered PRX persistence correction; synthetic-testable and P0 only.

Actual-data execution is permitted only after the new gate and this source
are committed. The shared RunContext enforces that boundary and owns output
integrity/ledger writes. No legacy main function or pair-trading engine runs.
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from collections.abc import Callable
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from statsmodels.tsa.stattools import adfuller, coint

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.predlab_xfam_lib import ar1_half_life
from tradingagents.predlab.meanstats import stationary_bootstrap_means

MONTHS = pd.date_range('2021-01-01', '2025-02-01', freq='MS', tz='UTC')
START = '2020-10-03'
END_EXCLUSIVE = '2025-03-01'
CELL_ID = 'top50_90d_persistence'
CONFIG = {
    'months': ['2021-01-01', '2025-02-01'], 'n_months': 50,
    'top_n': 50, 'formation_days': 90, 'minimum_paired': 60,
    'formation_test': 'augmented_engle_granger', 'trend': 'c',
    'maxlag': 5, 'autolag': None, 'formation_p_max': .05,
    'half_life_bounds': [2., 20.], 'selected_cap': 20,
    'random_seed': 42, 'random_scoreable_target': 20, 'random_attempt_cap': 200,
    'persistence_minimum': 25, 'persistence_p_max': .10,
    'historical_ratio_min': 1.5, 'historical_wilcoxon_p_max': .05,
    'dependence': {'mean_block': 3, 'draws': 2000, 'seed': 4242,
                   'interval': [.025, .975]},
    'promotion': 'none',
}


def _paired(a: pd.Series, b: pd.Series) -> pd.DataFrame:
    frame = pd.concat({'a': a, 'b': b}, axis=1)
    return frame.loc[np.isfinite(frame.to_numpy(dtype=float)).all(axis=1)]


def fit_pair(a: pd.Series, b: pd.Series) -> dict:
    """Fit formation beta and the estimated-residual cointegration null."""
    paired = _paired(a, b)
    result = {'n_paired': len(paired), 'beta': None, 'p': None,
              'half_life': None, 'status': 'unavailable', 'reason': None}
    if len(paired) < 60:
        return {**result, 'reason': 'fewer_than_60_formation_observations'}
    if paired['b'].std() == 0:
        return {**result, 'reason': 'constant_regressor'}
    try:
        beta = float(np.polyfit(paired.b, paired.a, 1)[0])
        # Preserve the original constant-insensitive spread/AR1 definition;
        # coint itself includes the fitted intercept in its residual test.
        residual = paired.a - beta * paired.b
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            p = float(coint(paired.a, paired.b, trend='c', maxlag=5, autolag=None)[1])
        hl = ar1_half_life(residual)
        if not np.isfinite(beta) or not np.isfinite(p):
            return {**result, 'reason': 'nonfinite_cointegration_fit'}
        return {**result, 'beta': beta, 'p': p,
                'half_life': float(hl) if np.isfinite(hl) else None,
                'status': 'complete'}
    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
        return {**result, 'reason': f'formation_fit_failed:{type(exc).__name__}'}


def formation_pairs(close: pd.DataFrame, qv: pd.DataFrame, month: pd.Timestamp) -> dict:
    lo, hi = month - pd.Timedelta(days=90), month - pd.Timedelta(days=1)
    volume = qv.loc[(qv.index >= lo) & (qv.index <= hi)]
    med = volume.median().replace([np.inf, -np.inf], np.nan).dropna()
    top = med.nlargest(50).index.tolist()
    window = close.reindex(columns=top).loc[(close.index >= lo) & (close.index <= hi)]
    logc = np.log(window.where(window > 0))
    selected, unavailable = [], []
    tested = 0
    for a, b in combinations(top, 2):
        fit = fit_pair(logc[a], logc[b])
        if fit['status'] != 'complete':
            unavailable.append({'a': a, 'b': b, **fit})
            continue
        tested += 1
        if fit['p'] < .05 and fit['half_life'] is not None and 2 <= fit['half_life'] <= 20:
            selected.append({'a': a, 'b': b, **fit})
    selected.sort(key=lambda r: (r['p'], r['a'], r['b'], r['beta']))
    return {'formation_start': str(lo.date()), 'formation_end': str(hi.date()),
            'n_formation_days': len(window), 'universe': top,
            'n_pairs_possible': len(top) * (len(top) - 1) // 2,
            'n_formation_tested': tested, 'formation_unavailable': unavailable,
            'n_admitted_before_cap': len(selected), 'selected': selected[:20]}


def score_spread(a: pd.Series, b: pd.Series, beta: float) -> dict:
    paired = _paired(a, b)
    spread = (paired.a - beta * paired.b).to_numpy()
    result = {'n_observed': len(spread), 'p': None, 'stationary': None,
              'reason': None}
    if len(spread) < 25:
        return {**result, 'reason': 'fewer_than_25_observations'}
    if np.std(spread) == 0:
        return {**result, 'reason': 'constant_spread'}
    try:
        p = float(adfuller(spread, maxlag=5, autolag=None)[1])
        if not np.isfinite(p):
            return {**result, 'reason': 'nonfinite_adf'}
        return {**result, 'p': p, 'stationary': bool(p < .10)}
    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
        return {**result, 'reason': f'adf_failed:{type(exc).__name__}'}


def _missing_dates(frame: pd.DataFrame, clock: pd.DatetimeIndex) -> list[str]:
    return [str(d.date()) for d in clock.difference(frame.index)]


def score_month(close: pd.DataFrame, qv: pd.DataFrame, month: pd.Timestamp,
                rng: np.random.Generator) -> dict:
    formation = formation_pairs(close, qv, month)
    end = month + pd.offsets.MonthBegin(1)
    fclock = pd.date_range(month - pd.Timedelta(days=90), month - pd.Timedelta(days=1), tz='UTC')
    tclock = pd.date_range(month, end - pd.Timedelta(days=1), tz='UTC')
    missing = {'close_formation': _missing_dates(close, fclock),
               'qv_formation': _missing_dates(qv, fclock),
               'close_persistence': _missing_dates(close, tclock)}
    top = formation['universe']
    c = close.reindex(columns=top)
    logs = np.log(c.where(c > 0))
    lw = logs.loc[(logs.index >= fclock[0]) & (logs.index <= fclock[-1])]
    tw = logs.loc[(logs.index >= month) & (logs.index < end)]
    selected = []
    for pair in formation['selected']:
        selected.append({**pair, 'persistence': score_spread(tw[pair['a']], tw[pair['b']], pair['beta'])})
    # Legacy comparator draws ordered pairs, allowing repeats/reversals, and
    # retries failed formation/OOS observations until 20 scores or 200 tries.
    random, scores = [], []
    while len(top) >= 2 and len(scores) < 20 and len(random) < 200:
        a, b = rng.choice(top, size=2, replace=False)
        paired = _paired(lw[a], lw[b])
        record = {'a': str(a), 'b': str(b), 'n_formation_observed': len(paired)}
        if len(paired) < 60 or paired.b.std() == 0:
            random.append({**record, 'beta': None, 'persistence': None,
                           'reason': 'unavailable_random_formation'})
            continue
        try:
            beta = float(np.polyfit(paired.b, paired.a, 1)[0])
            score = score_spread(tw[a], tw[b], beta)
        except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
            random.append({**record, 'beta': None, 'persistence': None,
                           'reason': f'random_fit_failed:{type(exc).__name__}'})
            continue
        random.append({**record, 'beta': beta, 'persistence': score, 'reason': score['reason']})
        if score['stationary'] is not None:
            scores.append(score['stationary'])
    sel_scores = [r['persistence']['stationary'] for r in selected
                  if r['persistence']['stationary'] is not None]
    ordered = [(r['a'], r['b']) for r in random]
    unique_ordered = set(ordered)
    unique_unordered = {tuple(sorted(pair)) for pair in ordered}
    reasons = []
    if not selected:
        reasons.append('no_selected_pairs')
    if len(sel_scores) != len(selected):
        reasons.append('unscoreable_selected_pairs')
    if len(scores) != 20:
        reasons.append('fewer_than_20_scoreable_random_pairs')
    if any(missing.values()):
        reasons.append('missing_calendar_panel_dates')
    if any(r['reason'].startswith('formation_fit_failed') or r['reason'] == 'nonfinite_cointegration_fit'
           for r in formation['formation_unavailable']):
        reasons.append('failed_formation_tests')
    selected_rate = float(np.mean(sel_scores)) if sel_scores else None
    random_rate = float(np.mean(scores)) if scores else None
    return {'month': str(month.date()), 'status': 'incomplete' if reasons else 'complete',
            'missing_reasons': reasons, 'missing_panel_dates': missing,
            **formation, 'selected': selected, 'n_selected': len(selected),
            'n_selected_scoreable': len(sel_scores),
            'n_selected_unavailable': len(selected) - len(sel_scores),
            'random': random, 'n_random_attempts': len(random),
            'n_random_scoreable': len(scores), 'n_random_unavailable': len(random) - len(scores),
            'random_ordered_duplicates': len(ordered) - len(unique_ordered),
            'random_unordered_duplicates': len(ordered) - len(unique_unordered),
            'random_reversed_pairs': sum((a, b) in unique_ordered and (b, a) in unique_ordered
                                         for a, b in unique_unordered),
            'selected_rate': selected_rate, 'random_rate': random_rate,
            'paired_difference': selected_rate - random_rate
            if selected_rate is not None and random_rate is not None else None}


def summarize_months(rows: list[dict]) -> dict:
    expected = [str(d.date()) for d in MONTHS]
    if [r['month'] for r in rows] != expected:
        raise ValueError('Exactly the registered 50 monthly records in order are required')
    paired = [r for r in rows if r['selected_rate'] is not None and r['random_rate'] is not None
              and np.isfinite([r['selected_rate'], r['random_rate']]).all()]
    sel = np.array([r['selected_rate'] for r in paired])
    rnd = np.array([r['random_rate'] for r in paired])
    diff = sel - rnd
    p = ratio = None
    if len(diff):
        if np.all(diff == 0):
            p = 1.
        else:
            p = float(wilcoxon(sel, rnd, alternative='greater').pvalue)
        ratio = float(sel.mean() / max(float(rnd.mean()), 1e-9))
    historical_pass = bool(ratio is not None and p is not None and ratio >= 1.5 and p < .05)
    complete = len(paired) == 50 and all(r['status'] == 'complete' for r in rows)
    diag = {'status': 'unavailable_incomplete_calendar', **CONFIG['dependence'],
            'mean_difference': None, 'interval_95': None, 'fraction_positive': None,
            'interpretation': 'Dependence sensitivity only; fraction positive is not a posterior probability or promotion gate.'}
    if complete:
        draws = stationary_bootstrap_means(diff, n_boot=2000, mean_block=3, seed=4242)
        diag.update(status='complete', mean_difference=float(diff.mean()),
                    interval_95=np.quantile(draws, [.025, .975]).tolist(),
                    fraction_positive=float(np.mean(draws > 0)))
    return {'n_months_planned': 50, 'n_months_paired': len(paired),
            'n_months_complete': sum(r['status'] == 'complete' for r in rows),
            'mean_selected_rate': float(sel.mean()) if len(sel) else None,
            'mean_random_rate': float(rnd.mean()) if len(rnd) else None,
            'historical_conditional_gate': {'n_months': len(paired), 'ratio': ratio,
                                            'wilcoxon_p': p, 'passes': historical_pass,
                                            'zero_random_baseline': bool(len(rnd) and rnd.mean() == 0),
                                            'ratio_denominator': max(float(rnd.mean()), 1e-9) if len(rnd) else None,
                                            'interpretation': 'Original conditional comparator only; no strategy validation.'},
            'complete_panel_verdict': ('historical_comparator_pass' if historical_pass else 'historical_comparator_fail')
            if complete else 'unavailable', 'dependence_diagnostic': diag,
            'candidate_selected': False, 'strategy_validation': False}


def _validate_panel(frame: pd.DataFrame) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError('Market panels require UTC datetime indices')
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing or not frame.columns.is_unique:
        raise ValueError('Market panels require sorted unique times and symbols')
    if str(frame.index.tz) != 'UTC' or not (frame.index == frame.index.normalize()).all():
        raise ValueError('Market panels require daily UTC observations')


def evaluate_p0(close: pd.DataFrame, qv: pd.DataFrame,
                progress: Callable[[int, int], None] | None = None) -> dict:
    for frame in (close, qv):
        _validate_panel(frame)
    lo, hi = pd.Timestamp(START, tz='UTC'), pd.Timestamp(END_EXCLUSIVE, tz='UTC')
    close = close.loc[(close.index >= lo) & (close.index < hi)]
    qv = qv.loc[(qv.index >= lo) & (qv.index < hi)]
    rng = np.random.default_rng(42)
    rows = []
    for i, month in enumerate(MONTHS, start=1):
        rows.append(score_month(close, qv, month, rng))
        if progress is not None and i % 5 == 0:
            progress(i, len(MONTHS))
    return {'family': 'prx', 'cell': CELL_ID, 'config': CONFIG,
            'months': rows, 'summary': summarize_months(rows),
            'p1_executed': False, 'holdout_read': False, 'forecast_models_refit': False,
            'formation_regressions_recomputed': True,
            'candidate_selected': False, 'strategy_validation': False}


def validate_gate(gate: dict) -> None:
    required = {'months': ['2021-01-01', '2025-02-01'], 'n_months': 50,
                'random_seed': 42, 'cells': [{'id': CELL_ID}],
                'formation': 'original top50 prior90d median quote volume; at least60 paired rows; coint trend=c maxlag5 autolag=None; p<.05 and original AR1 half-life2..20; cap20 lowest p',
                'persistence': 'next-month fixed-beta spread ADF maxlag5 autolag=None p<.10',
                'original_gate_thresholds': 'mean selected rate >=1.5x mean random rate AND paired greater Wilcoxon p<.05',
                'random_pairs': 'original random ordered pairs and retry algorithm, max200 tries to obtain20 scoreable; duplicates/reversals disclosed'}
    if any(gate.get(k) != v for k, v in required.items()):
        raise ValueError('PRX parameters differ from the registered specification')
    dependence = gate.get('dependence_diagnostic', {})
    required_dep = {'statistic': 'paired monthly mean(selected_rate-random_rate)',
                    'bootstrap': 'stationary', 'mean_block': 3, 'draws': 2000,
                    'seed': 4242, 'interval': [.025, .975]}
    if dependence != required_dep:
        raise ValueError('PRX dependence diagnostic differs from the registered specification')


def load_inputs(ctx, data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Hash original files, then materialize only the registered input clock."""
    data_root = Path(data_root)
    original_path = ctx.track(data_root / 'predlab/xfam/prx_result.json')
    original = json.loads(original_path.read_text())
    p0 = original['P0']
    if p0['n_months'] != 50 or [r['month'] for r in p0['per_month']] != [str(d.date()) for d in MONTHS]:
        raise ValueError('Saved PRX result does not contain the original 50-month clock')
    close = ctx.read_market(data_root / 'predlab/t7_panels/close.parquet',
                            start=START, end_exclusive=END_EXCLUSIVE)
    qv = ctx.read_market(data_root / 'predlab/t7_panels/qv.parquet',
                         start=START, end_exclusive=END_EXCLUSIVE)
    previous = {'source_git_commit': original.get('git_commit'),
                'source_timestamp': original.get('ts_utc'),
                'metrics': {k: v for k, v in p0.items() if k != 'per_month'},
                'monthly': [{k: r[k] for k in ('month', 'n_selected', 'sel_rate', 'rnd_rate') if k in r}
                            for r in p0['per_month']],
                'interpretation': 'Preserved original ordinary-ADF screen; historical source provenance remains qualified.'}
    return close, qv, previous


def _blocked_payload(reason: str) -> dict:
    rows = [{'month': str(d.date()), 'status': 'blocked',
             'missing_reasons': [reason], 'n_selected': None,
             'n_selected_scoreable': None, 'n_random_scoreable': None,
             'selected_rate': None, 'random_rate': None, 'paired_difference': None}
            for d in MONTHS]
    return {'family': 'prx', 'cell': CELL_ID, 'config': CONFIG,
            'status': 'blocked', 'reason': reason, 'months': rows,
            'summary': summarize_months(rows), 'p1_executed': False,
            'holdout_read': False, 'forecast_models_refit': False,
            'formation_regressions_recomputed': False,
            'candidate_selected': False, 'strategy_validation': False}


def run(ctx, data_root: Path | None = None) -> Path:
    """Consume registered cached panels and publish exactly one P0 cell."""
    if (ctx.output_dir / 'result.json').exists():
        raise FileExistsError(ctx.output_dir / 'result.json')
    validate_gate(ctx.family_gate)
    registered_root = Path(ctx.gate['source_roots'][1]).resolve()
    if data_root is not None and Path(data_root).resolve() != registered_root:
        raise ValueError('PRX data root must equal the registered predlab source root')
    try:
        close, qv, previous = load_inputs(ctx, registered_root)
        payload = evaluate_p0(close, qv, progress=lambda done, total: print(
            f'PRX formation months completed: {done}/{total}', flush=True))
        payload['original'] = previous
        payload['status'] = ('diagnostic_complete' if payload['summary']['n_months_complete'] == 50
                             else 'incomplete')
    except (FileNotFoundError, ValueError, KeyError) as exc:
        payload = _blocked_payload(f'required_input_unavailable:{type(exc).__name__}:{exc}')
    keys = ('month', 'status', 'n_selected', 'n_selected_scoreable', 'n_selected_unavailable',
            'n_random_attempts', 'n_random_scoreable', 'n_random_unavailable',
            'selected_rate', 'random_rate', 'paired_difference')
    archive = pd.DataFrame([{k: r.get(k) for k in keys} for r in payload['months']])
    archive['missing_reasons'] = [json.dumps(r['missing_reasons']) for r in payload['months']]
    ctx.write_frame('monthly.parquet', archive)
    metrics = {'status': payload['status'], **payload['summary'], 'p1_executed': False}
    return ctx.finish(payload, [{'id': CELL_ID, 'config': CONFIG, 'metrics': metrics}])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true',
                        help='Execute the committed registered P0 correction once')
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({'family': 'prx', 'execute': False, 'status': 'no inputs consumed'}))
        return 0
    # Lazy import keeps pure synthetic functions independent of run-state I/O.
    from scripts.audit_reeval_common import RunContext
    ctx = RunContext('prx')
    output = run(ctx)
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
