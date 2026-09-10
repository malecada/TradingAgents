"""Fixed saved-forecast diagnostics; no fitting, I/O, trading or selection."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from tradingagents.predlab import losses

FLAGS = ('fallback_used', 'raw_valid', 'target_valid', 'baseline_valid', 'scoreable',
         'reconstructed_unavailable')
NUMBERS = ('y_true', 'raw_pred', 'pred', 'saved_pred')


def loss_pair(y, baseline, candidate, target):
    y, baseline, candidate = (np.asarray(a, dtype=float) for a in (y, baseline, candidate))
    with np.errstate(all='ignore'):
        if target == 'T1_ret':
            return losses.se(y, baseline), losses.se(y, candidate)
        if target == 'T2_dir':
            return losses.brier(baseline, y > 0), losses.brier(candidate, y > 0)
        if target == 'T3_rv':
            return losses.qlike(baseline, y), losses.qlike(candidate, y)
        if target == 'T4_vol':
            # Common positive training MASE scale cancels from this inference.
            return losses.ae(y, baseline), losses.ae(y, candidate)
    raise ValueError('unknown registered target')


def _index(frame, label):
    idx = frame.index
    if not isinstance(idx, pd.DatetimeIndex) or str(idx.tz) != 'UTC':
        raise ValueError(f'{label}: expected UTC index')
    if not idx.is_unique or not idx.is_monotonic_increasing or idx.hasnans:
        raise ValueError(f'{label}: duplicate, unsorted or missing timestamps')


def prepare_pair(corrected, baseline, spec, prior, tolerance):
    """Check saved policy algebra, preserving its decisions and physical clock."""
    _index(corrected, 'corrected'); _index(baseline, 'baseline')
    required = set(FLAGS + NUMBERS + ('fallback_reason',))
    if not required.issubset(corrected) or not {'y_true', 'pred'}.issubset(baseline):
        raise ValueError('missing saved forecast columns')
    for col in FLAGS:
        if not pd.api.types.is_bool_dtype(corrected[col]) or corrected[col].isna().any():
            raise ValueError(f'inconsistent boolean mask: {col}')
    for frame, columns in ((corrected, NUMBERS), (baseline, ('y_true', 'pred'))):
        if any(pd.api.types.is_bool_dtype(frame[c]) or not pd.api.types.is_numeric_dtype(frame[c]) for c in columns):
            raise ValueError('forecast values must be numeric, not boolean')
    freq = 'h' if spec['horizon'] == '1h' else 'D'
    clock = pd.date_range(spec['clock_start'], spec['clock_end'], freq=freq)
    if str(clock.tz) != 'UTC' or len(clock) != spec['expected_clock_rows']:
        raise ValueError('registered full clock mismatch')
    known = pd.Timestamp(spec['known_unavailable_origin']) if spec['known_unavailable_origin'] else None
    omitted = [known] if known is not None and spec['target'] == 'T4_vol' else []
    expected_saved = clock.drop(omitted)
    if not corrected.index.equals(expected_saved) or not baseline.index.equals(expected_saved):
        raise ValueError('saved clock differs from registered full clock/known omission')
    y = corrected.y_true.to_numpy(dtype=float)
    base = baseline.pred.to_numpy(dtype=float)
    candidate, raw, saved = (corrected[c].to_numpy(dtype=float) for c in ('pred', 'raw_pred', 'saved_pred'))
    if not np.array_equal(y, baseline.y_true.to_numpy(dtype=float), equal_nan=True):
        raise ValueError('baseline target disagreement')
    lb, lc = loss_pair(y, base, candidate, spec['target'])
    _, lr = loss_pair(y, base, raw, spec['target'])
    target_valid = np.isfinite(y)
    if spec['target'] == 'T3_rv': target_valid &= y > 0
    base_valid = np.isfinite(base) & np.isfinite(lb)
    if spec['target'] == 'T2_dir': base_valid &= (base >= 0) & (base <= 1)
    scoreable = corrected.scoreable.to_numpy()
    for name, expected in (('target_valid', target_valid), ('baseline_valid', base_valid),
                           ('scoreable', target_valid & base_valid)):
        if not np.array_equal(corrected[name].to_numpy(), expected):
            raise ValueError(f'inconsistent saved {name} mask')
    bad_times = corrected.index[~scoreable]
    expected_bad = pd.DatetimeIndex([known]) if known is not None and spec['target'] == 'T3_rv' else clock[:0]
    if not bad_times.equals(expected_bad):
        raise ValueError('unregistered unscoreable origin')
    raw_valid = corrected.raw_valid.to_numpy()
    reasons = corrected.fallback_reason
    if reasons.isna().any() or not reasons.map(lambda x: isinstance(x, str)).all():
        raise ValueError('invalid fallback reason')
    if not np.array_equal(raw_valid, reasons.eq('').to_numpy()):
        raise ValueError('raw-valid/fallback-reason disagreement')
    if np.any(raw_valid & ~np.isfinite(raw)) or np.any(raw_valid & scoreable & ~np.isfinite(lr)):
        raise ValueError('invalid raw prediction marked valid')
    if spec['target'] == 'T2_dir' and np.any(raw_valid & ((raw < 0) | (raw > 1))):
        raise ValueError('invalid raw probability')
    if spec['target'] == 'T3_rv' and np.any(raw_valid & (raw <= 0)):
        raise ValueError('invalid raw variance')
    reconstructed = corrected.reconstructed_unavailable.to_numpy()
    if not np.array_equal(raw, np.where(reconstructed, np.nan, saved), equal_nan=True):
        raise ValueError('saved raw prediction or availability reconstruction changed')
    fallback = corrected.fallback_used.to_numpy()
    if not np.array_equal(fallback, ~raw_valid & base_valid):
        raise ValueError('fallback mask inconsistent')
    if not np.array_equal(candidate, np.where(fallback, base, raw), equal_nan=True):
        raise ValueError('saved effective prediction changed')
    if not scoreable.any() or not np.isfinite(lb[scoreable]).all() or not np.isfinite(lc[scoreable]).all():
        raise ValueError('unavailable required paired loss')
    counts = {'n_saved': len(corrected), 'n_scoreable': int(scoreable.sum()),
        'n_fallback': int((fallback & scoreable).sum()),
        'n_reconstructed_unavailable': int(reconstructed.sum()),
        'raw_valid_coverage': float(raw_valid[scoreable].mean())}
    if prior['status'] != 'diagnostic_complete' or prior['cell'] != spec['cell']:
        raise ValueError('prior correction cell/status mismatch')
    for key, value in counts.items():
        if not np.isclose(value, prior[key], **tolerance):
            raise ValueError(f'prior count reconciliation failed: {key}')
    bm, cm = float(lb[scoreable].mean()), float(lc[scoreable].mean())
    if spec['target'] == 'T4_vol':
        match = bm > 0 and prior['baseline_loss_mean'] > 0 and np.isclose(
            cm/bm, prior['corrected_loss_mean']/prior['baseline_loss_mean'], **tolerance)
    else:
        match = np.isclose(bm, prior['baseline_loss_mean'], **tolerance) and np.isclose(
            cm, prior['corrected_loss_mean'], **tolerance)
    if not match: raise ValueError('prior loss reconciliation failed')
    pair = pd.DataFrame({'y_true': y, 'baseline_pred': base, 'effective_pred': candidate,
        'scoreable': scoreable, 'fallback_used': fallback, 'raw_valid': raw_valid,
        'origin_present': True, 'loss_baseline': np.where(scoreable, lb, np.nan),
        'loss_candidate': np.where(scoreable, lc, np.nan)}, index=corrected.index).reindex(clock)
    for col in ('scoreable', 'fallback_used', 'raw_valid', 'origin_present'):
        pair[col] = pair[col].eq(True)
    pair['loss_difference'] = pair.loss_baseline - pair.loss_candidate
    pair.index.name = 'ts'
    counts.update(expected_clock_rows=len(clock), missing_origin_count=len(omitted),
                  unavailable_clock_rows=int((~pair.scoreable).sum()),
                  reconciliation='matched_prior_correction')
    return pair, counts


def stationary_sums(values, mean_block, draws, seed):
    """Circular geometric blocks, vectorized over draws using segment sums.

    A uniform starting index and independent geometric block lengths produce
    the stationary bootstrap. Restarts choose any physical clock row, including
    unavailable rows. Storage is O(clock * fields + draws * fields), not B*T.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or not len(values) or not np.isfinite(values).all():
        raise ValueError('bootstrap values must be a finite nonempty matrix')
    if mean_block < 1 or draws < 1 or int(draws) != draws:
        raise ValueError('invalid bootstrap dimensions')
    n = len(values)
    prefix = np.vstack([np.zeros(values.shape[1]), np.cumsum(np.vstack([values, values]), axis=0)])
    rng = np.random.default_rng(seed)
    total = np.zeros((draws, values.shape[1]))
    remaining = np.full(draws, n, dtype=np.int64)
    while np.any(remaining):
        active = np.flatnonzero(remaining)
        starts = rng.integers(0, n, size=len(active))
        lengths = np.minimum(rng.geometric(1./mean_block, size=len(active)), remaining[active])
        total[active] += prefix[starts+lengths] - prefix[starts]
        remaining[active] -= lengths
    return total


def bootstrap_pair(base, candidate, mask, *, mean_block, policy):
    base, candidate = np.asarray(base, float), np.asarray(candidate, float)
    mask = np.asarray(mask)
    if mask.dtype != bool or base.shape != candidate.shape or base.shape != mask.shape or base.ndim != 1:
        raise ValueError('bootstrap pair shape/mask mismatch')
    if not mask.any() or not np.isfinite(base[mask]).all() or not np.isfinite(candidate[mask]).all():
        raise ValueError('no complete observed pair')
    if np.any(base[mask] < 0) or np.any(candidate[mask] < 0):
        raise ValueError('registered losses must be nonnegative')
    bmean, cmean = float(base[mask].mean()), float(candidate[mask].mean())
    diff = base[mask]-candidate[mask]
    observed = float(diff.mean())
    degenerate = bool(np.ptp(diff) == 0)
    values = np.column_stack([mask, np.where(mask, base, 0.), np.where(mask, candidate, 0.)])
    sums = stationary_sums(values, mean_block, policy['draws'], policy['seed'])
    count = np.rint(sums[:, 0]).astype(np.int64)
    with np.errstate(all='ignore'):
        bm, cm = sums[:, 1]/count, sums[:, 2]/count
        dm = bm-cm
        relative = dm/bm
    valid_diff = (count > 0) & np.isfinite(dm)
    valid_relative = valid_diff & (bm > 0) & np.isfinite(relative)
    all_diff, all_relative = bool(valid_diff.all()), bool(valid_relative.all())
    quantiles = policy['ci_quantiles']
    result = {'mean_baseline_loss': bmean, 'mean_candidate_loss': cmean,
        'mean_difference': observed, 'relative_improvement': observed/bmean if bmean > 0 else None,
        'mean_block_origins': mean_block, 'draws': policy['draws'], 'seed': policy['seed'],
        'valid_difference_draws': int(valid_diff.sum()), 'valid_relative_draws': int(valid_relative.sum()),
        'difference_ci': np.quantile(dm, quantiles).tolist() if all_diff else None,
        'relative_improvement_ci': np.quantile(relative, quantiles).tolist() if all_relative else None,
        'diagnostic_p': float((1+np.count_nonzero(dm-observed >= observed))/(policy['draws']+1))
            if all_diff and not degenerate else None,
        'degenerate': degenerate,
        'status': 'conditional_diagnostic_complete' if all_diff and all_relative else 'incomplete_bootstrap_draws'}
    draws = pd.DataFrame({'sampled_scoreable_count': count, 'mean_baseline_loss': bm,
        'mean_candidate_loss': cm, 'mean_difference': dm, 'relative_improvement': relative,
        'difference_valid': valid_diff, 'relative_valid': valid_relative})
    return result, draws


def point_auc(labels, predictions):
    labels, predictions = np.asarray(labels, bool), np.asarray(predictions, float)
    n1, n0 = int(labels.sum()), int((~labels).sum())
    if not n1 or not n0: return None
    ranks = rankdata(predictions, method='average')
    return float((ranks[labels].sum()-n1*(n1+1)/2)/(n1*n0))


def analyze_cell(corrected, baseline, spec, prior, policy, floors):
    pair, counts = prepare_pair(corrected, baseline, spec, prior, policy['reconciliation'])
    mean_block = policy['bootstrap']['mean_block_days'] * (24 if spec['horizon'] == '1h' else 1)
    bootstrap, draws = bootstrap_pair(pair.loss_baseline.to_numpy(), pair.loss_candidate.to_numpy(),
        pair.scoreable.to_numpy(), mean_block=mean_block, policy=policy['bootstrap'])
    stable = []
    for start, end in policy['stability']['periods']:
        mask = pair.scoreable & (pair.index >= pd.Timestamp(start, tz='UTC')) & (
            pair.index < pd.Timestamp(end, tz='UTC')+pd.Timedelta(days=1))
        n = int(mask.sum()); value = float(pair.loc[mask, 'loss_difference'].mean()) if n else None
        stable.append({'start': start, 'end': end, 'n_scoreable': n,
                       'mean_difference': value, 'positive': value > 0 if value is not None else None})
    descriptor = all(p['n_scoreable'] >= policy['stability']['min_scoreable_per_period'] for p in stable)
    descriptor &= sum(p['positive'] is True for p in stable) >= policy['stability']['positive_periods_min']
    relative = bootstrap['relative_improvement']
    target = spec['target']
    if target == 'T2_dir':
        obs = pair.loc[pair.scoreable]
        labels = obs.y_true.to_numpy() > 0
        accuracy = float(np.mean((obs.effective_pred.to_numpy() > .5) == labels))
        base_accuracy = float(np.mean((obs.baseline_pred.to_numpy() > .5) == labels))
        effects = {'accuracy': accuracy, 'baseline_accuracy': base_accuracy,
            'accuracy_edge_pp': 100*(accuracy-base_accuracy), 'accuracy_edge_floor_pp': floors['T2_edge_pp'],
            'accuracy_edge_floor_met': 100*(accuracy-base_accuracy) >= floors['T2_edge_pp'],
            'point_auc': point_auc(labels, obs.effective_pred.to_numpy()),
            'auc_ci': None, 'auc_ci_exclusion_threshold': floors['T2_auc_ci_excludes'],
            'original_conjunctive_floor_met': None, 'qualification': 'AUC interval not supplied'}
    else:
        threshold = floors['T1_oos_r2'][spec['horizon']] if target == 'T1_ret' else floors[
            'T3_dqlike' if target == 'T3_rv' else 'T4_dmase']
        effects = {'metric': 'oos_r2' if target == 'T1_ret' else 'relative_loss_improvement',
            'value': relative, 'original_floor': threshold,
            'original_floor_met': relative >= threshold if relative is not None else None}
    eligible = bool(spec['inference_eligible'])
    record = {'cell': spec['cell'], 'status': 'diagnostic_complete', 'counts': counts,
        'target': target, 'strong_baseline': spec['strong_baseline'], 'bootstrap': bootstrap,
        'loss_units': 'absolute_log_volume_error' if target == 'T4_vol' else prior['loss'],
        'prior_loss_reference': {k: prior[k] for k in ('loss', 'corrected_loss_mean', 'baseline_loss_mean')},
        'stability_periods': stable, 'historical_stability_descriptor': bool(descriptor), 'effect': effects,
        'inference_eligible': eligible,
        'eligible_primary_p': bootstrap['diagnostic_p'] if eligible else None,
        'formal_model_class_p': None, 'strategy_promotion': False,
        'qualification': 'Retrospective fixed-forecast conditional diagnostic; no fresh validation or model-class test.',
        'nesting_qualification': None if eligible else 'Unresolved nesting/penalized-estimation test applicability',
        'original_nonbaseline_contenders': 2 if target == 'T1_ret' else 3}
    return record, pair, draws


def apply_holm(records, policy):
    m = policy['family_size']
    if m != 16 or len(records) != 16 or len({r['cell'] for r in records}) != 16:
        raise ValueError('Holm requires exactly 16 distinct registered slots')
    pvalues = []
    for row in records:
        p = row.get('eligible_primary_p') if row.get('inference_eligible') else None
        if p is not None and (not np.isfinite(p) or not 0 <= p <= 1):
            raise ValueError('invalid primary p-value')
        pvalues.append(policy['unavailable_or_ineligible_p'] if p is None else p)
    order = np.argsort(pvalues, kind='stable')
    adjusted = np.empty(m)
    adjusted[order] = np.minimum(1., np.maximum.accumulate((m-np.arange(m))*np.asarray(pvalues)[order]))
    for i, row in enumerate(records):
        usable = bool(row.get('inference_eligible') and row.get('eligible_primary_p') is not None)
        row.update(holm_input_p=float(pvalues[i]), holm_adjusted_slot_p=float(adjusted[i]),
                   holm_adjusted_p=float(adjusted[i]) if usable else None,
                   conditional_family_reject=bool(usable and adjusted[i] <= policy['alpha']))
