"""Independent saved-artifact arithmetic checks; no bootstrap or strategy rerun."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

import verify_preservation as preservation

ROOT = preservation.ROOT
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'data/diagnostics/2026-09-10'
REGISTRATION = '38d9a67e6ff042cb1fd870877b3e0222f40fdc08'
SOURCE = 'cd8d9e3f064bb40273ba493e597e371e6f199b66'
CHECKS = Counter()


def check(group, condition, detail):
    if not condition:
        raise AssertionError(f'{group}: {detail}')
    CHECKS[group] += 1


def near(group, actual, expected, detail, atol=1e-12, rtol=1e-10):
    check(group, np.allclose(actual, expected, atol=atol, rtol=rtol, equal_nan=True), detail)


def digest(path):
    return preservation.inspect_file(path)['sha256']


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def clock(frame, column=None):
    return pd.DatetimeIndex(pd.to_datetime(frame[column] if column else frame.index, utc=True))


def bounded_baseline(path, start, end):
    dataset = ds.dataset(path, format='parquet')
    t = dataset.schema.field('ts').type
    check('input_bounds', pa.types.is_timestamp(t) and t.tz == 'UTC', str(path))
    # Bound before materializing any original values. No date after the frozen
    # March 31 00:00 UTC endpoint is loaded from an original baseline.
    filt = ((ds.field('ts') >= pa.scalar(start.to_pydatetime(), type=t)) &
            (ds.field('ts') <= pa.scalar(end.to_pydatetime(), type=t)))
    frame = dataset.to_table(columns=['ts', 'y_true', 'pred'], filter=filt).to_pandas()
    return frame.set_index('ts') if 'ts' in frame else frame


def manifest(family, gate):
    directory = BASE/family
    result = json.loads((directory/'result.json').read_text())
    check('provenance', result['git_commit'] == SOURCE, family+' execution commit')
    check('provenance', result['gate_sha256'] == canonical(gate), family+' exact gate')
    policy = preservation.baseline_bytes('docs/audit/corrections.jsonl', SOURCE)
    check('provenance', result['correction_policy_sha256'] == hashlib.sha256(policy).hexdigest(), family+' execution policy')
    check('input_hashes', result['input_sha256'] == gate['pinned_files'], family+' exact input pins')
    check('output_hashes', set(result['output_sha256']) | {'result.json'} ==
          {p.name for p in directory.iterdir() if p.is_file()}, family+' artifact inventory')
    for name, expected in result['output_sha256'].items():
        check('output_hashes', Path(name).name == name and digest(directory/name) == expected, family+'/'+name)
    for name, expected in gate['pinned_files'].items():
        path = Path(name) if Path(name).is_absolute() else ROOT/name
        check('input_hashes', digest(path) == expected, name)
    return result


def forecast(result, gate):
    prior = json.loads((ROOT/gate['source_result']).read_text())
    prior = {c['cell']: c for c in prior['enet']}
    cells = result['cells']
    check('forecast_denominator', [c['cell'] for c in cells] == [c['cell'] for c in gate['cells']], '16 exact identities/order')
    check('forecast_denominator', len(cells) == result['expected_cells'] == result['available_cells'] == 16, 'all16 available')
    ledger = [json.loads(x) for x in (BASE/'forecast/forensic-ledger.jsonl').read_text().splitlines()]
    check('forecast_denominator', len(ledger) == 16, 'forensic rows')
    pvalues, summaries = [], []
    for spec, cell, line in zip(gate['cells'], cells, ledger):
        name = spec['cell']; stem = name.replace('|', '_')
        check('forensic_identity', line['cell'] == name and line['metrics'] == cell and line['source_commit'] == SOURCE, name)
        pair = pd.read_parquet(BASE/'forecast'/f'{stem}-paired.parquet')
        draws = pd.read_parquet(BASE/'forecast'/f'{stem}-bootstrap.parquet')
        expected = pd.date_range(spec['clock_start'], spec['clock_end'], freq='h' if spec['horizon'] == '1h' else 'D')
        check('forecast_clock', pair.index.equals(expected) and len(pair) == spec['expected_clock_rows'], name)
        source = pd.read_parquet(ROOT/spec['corrected_path'])
        base = bounded_baseline(Path(spec['baseline_path']), expected[0], expected[-1])
        check('forecast_clock', source.index.equals(base.index) and source.index.is_unique, name+' source pair')
        present = pair.origin_present.to_numpy(bool)
        check('forecast_masks', np.array_equal(present, expected.isin(source.index)), name+' present mask')
        mask = pair.scoreable.to_numpy(bool)
        for column in ('scoreable', 'fallback_used', 'raw_valid'):
            wanted = source[column].reindex(expected).eq(True).to_numpy()
            check('forecast_masks', np.array_equal(pair[column].to_numpy(), wanted), name+' '+column)
        for output_column, frame, input_column in [('y_true', source, 'y_true'), ('effective_pred', source, 'pred'),
                                                   ('baseline_pred', base, 'pred')]:
            near('forecast_source_values', pair[output_column], frame[input_column].reindex(expected), name+' '+output_column, atol=0, rtol=0)
        near('forecast_source_values', source.y_true, base.y_true, name+' baseline targets', atol=0, rtol=0)
        counts = cell['counts']
        expected_counts = dict(n_saved=len(source), n_scoreable=int(mask.sum()), n_fallback=int((pair.fallback_used & pair.scoreable).sum()),
            n_reconstructed_unavailable=int(source.reconstructed_unavailable.sum()), expected_clock_rows=len(pair),
            missing_origin_count=int((~present).sum()), unavailable_clock_rows=int((~mask).sum()))
        check('forecast_counts', all(counts[k] == v for k, v in expected_counts.items()), name)
        for key in ('n_saved', 'n_scoreable', 'n_fallback', 'n_reconstructed_unavailable'):
            check('forecast_counts', counts[key] == prior[name][key], name+' prior '+key)
        near('forecast_counts', counts['raw_valid_coverage'], pair.loc[mask, 'raw_valid'].mean(), name+' raw coverage')
        y, b, c = (pair[x].to_numpy(float) for x in ('y_true', 'baseline_pred', 'effective_pred'))
        with np.errstate(all='ignore'):
            if spec['target'] == 'T1_ret': lb, lc = (y-b)**2, (y-c)**2
            elif spec['target'] == 'T2_dir': lb, lc = (b-(y > 0))**2, (c-(y > 0))**2
            elif spec['target'] == 'T3_rv': lb, lc = y/b-np.log(y/b)-1, y/c-np.log(y/c)-1
            else: lb, lc = abs(y-b), abs(y-c)
        lb, lc = np.where(mask, lb, np.nan), np.where(mask, lc, np.nan)
        near('forecast_losses', pair.loss_baseline, lb, name+' baseline')
        near('forecast_losses', pair.loss_candidate, lc, name+' candidate')
        near('forecast_losses', pair.loss_difference, lb-lc, name+' paired difference')
        check('forecast_losses', pair.loc[pair.fallback_used & pair.scoreable, 'loss_difference'].eq(0).all(), name+' fallback zero')
        check('forecast_masks', pair.loc[~mask, ['loss_baseline', 'loss_candidate', 'loss_difference']].isna().all().all(), name+' unavailable losses')
        bm, cm, dm = np.mean(lb[mask]), np.mean(lc[mask]), np.mean((lb-lc)[mask])
        report = cell['bootstrap']
        for key, value in [('mean_baseline_loss', bm), ('mean_candidate_loss', cm), ('mean_difference', dm), ('relative_improvement', dm/bm)]:
            near('forecast_means', report[key], value, name+' '+key)
        if spec['target'] == 'T4_vol':
            near('forecast_means', cm/bm, prior[name]['corrected_loss_mean']/prior[name]['baseline_loss_mean'], name+' original MASE ratio', rtol=1e-9)
        else:
            near('forecast_means', bm, prior[name]['baseline_loss_mean'], name+' prior baseline', rtol=1e-9)
            near('forecast_means', cm, prior[name]['corrected_loss_mean'], name+' prior model', rtol=1e-9)
        check('saved_bootstrap', len(draws) == 2000 and report['draws'] == 2000, name+' all draws')
        check('saved_bootstrap', draws.difference_valid.all() and draws.relative_valid.all(), name+' finite draws')
        check('saved_bootstrap', draws.sampled_scoreable_count.between(1, len(pair)).all(), name+' draw denominators')
        check('saved_bootstrap', report['valid_difference_draws'] == report['valid_relative_draws'] == 2000, name+' report counts')
        near('saved_bootstrap', draws.mean_difference, draws.mean_baseline_loss-draws.mean_candidate_loss, name+' saved differences')
        near('saved_bootstrap', draws.relative_improvement, draws.mean_difference/draws.mean_baseline_loss, name+' saved relative')
        near('saved_bootstrap', report['difference_ci'], draws.mean_difference.quantile([.025, .975]), name+' difference CI')
        near('saved_bootstrap', report['relative_improvement_ci'], draws.relative_improvement.quantile([.025, .975]), name+' relative CI')
        p = (1+int((draws.mean_difference-dm >= dm).sum()))/2001
        near('saved_bootstrap', report['diagnostic_p'], p, name+' centered p', atol=0, rtol=0)
        check('forecast_eligibility', cell['inference_eligible'] == (spec['target'] == 'T4_vol') and cell['formal_model_class_p'] is None and cell['strategy_promotion'] is False, name)
        if cell['inference_eligible']:
            near('forecast_eligibility', cell['eligible_primary_p'], p, name+' primary p', atol=0, rtol=0)
            pvalues.append(p)
        else:
            check('forecast_eligibility', cell['eligible_primary_p'] is None and cell['holm_adjusted_p'] is None, name+' excluded nesting')
            pvalues.append(1.)
        for period in cell['stability_periods']:
            selected = mask & (pair.index >= pd.Timestamp(period['start'], tz='UTC')) & (pair.index < pd.Timestamp(period['end'], tz='UTC')+pd.Timedelta(days=1))
            value = np.mean((lb-lc)[selected])
            check('forecast_stability', period['n_scoreable'] == int(selected.sum()) and period['positive'] == bool(value > 0), name)
            near('forecast_stability', period['mean_difference'], value, name)
        stable = all(x['n_scoreable'] >= 30 for x in cell['stability_periods']) and sum(x['positive'] for x in cell['stability_periods']) >= 2
        check('forecast_stability', cell['historical_stability_descriptor'] == stable, name+' descriptor')
        if spec['target'] == 'T2_dir':
            check('forecast_eligibility', cell['effect']['auc_ci'] is None and cell['effect']['original_conjunctive_floor_met'] is None, name+' AUC restriction')
        summaries.append(dict(cell=name, clock_rows=len(pair), scoreable_rows=int(mask.sum()),
            missing_origin_rows=int((~present).sum()), fallback_rows=counts['n_fallback'], bootstrap_draws=len(draws),
            inference_eligible=cell['inference_eligible'], conditional_family_reject=cell['conditional_family_reject']))
    order = np.argsort(pvalues, kind='stable')
    adjusted = np.empty(16)
    adjusted[order] = np.minimum(1, np.maximum.accumulate((16-np.arange(16))*np.asarray(pvalues)[order]))
    for i, cell in enumerate(cells):
        near('forecast_holm', cell['holm_input_p'], pvalues[i], cell['cell'], atol=0, rtol=0)
        near('forecast_holm', cell['holm_adjusted_slot_p'], adjusted[i], cell['cell'], atol=0, rtol=0)
        check('forecast_holm', cell['conditional_family_reject'] == bool(cell['inference_eligible'] and adjusted[i] <= .05), cell['cell'])
    return summaries


def distribution(values, active):
    values, active = np.asarray(values, float), np.asarray(active, bool)
    finite = np.isfinite(values); observed = values[active & finite]
    result = dict(total_rows=len(values), finite_rows=int(finite.sum()), unavailable_rows=int((~finite).sum()),
        active_rows=int(active.sum()), active_finite_rows=len(observed), active_unavailable_rows=int((active & ~finite).sum()),
        median=None, p90=None, p99=None, maximum=None)
    if len(observed):
        result.update(zip(('median', 'p90', 'p99'), map(float, np.quantile(observed, [.5, .9, .99]))))
        result['maximum'] = float(observed.max())
    return result


def compare_distribution(actual, expected, label):
    for key, value in expected.items():
        if value is None: check('risk_distributions', actual[key] is None, label+' '+key)
        else: near('risk_distributions', actual[key], value, label+' '+key)


def risk(result, gate):
    prior = json.loads((ROOT/gate['source_result']).read_text())
    prior = {c['id']: c for c in prior['cells']}
    ledger = [json.loads(x) for x in (BASE/'risk/forensic-ledger.jsonl').read_text().splitlines()]
    cells = result['cells']
    check('risk_denominator', len(cells) == len(ledger) == 36 and result['counts'] == dict(expected_sleeves=36, complete_sleeves=36, unavailable_sleeves=0), 'all36')
    check('risk_denominator', [c['id'] for c in cells] == [c['id'] for c in gate['cells']], 'registered identities/order')
    summaries = []
    for spec, cell, line in zip(gate['cells'], cells, ledger):
        name = spec['id']; summary = cell['summary']; stem = name.replace('|', '__')
        check('forensic_identity', line['cell'] == name and line['summary'] == summary and line['git_commit'] == SOURCE, name)
        daily = pd.read_parquet(BASE/'risk'/f'{stem}-daily.parquet')
        events = pd.read_parquet(BASE/'risk'/f'{stem}-events.parquet')
        original = pd.read_parquet(ROOT/spec['trace_path'])
        targets = pd.read_parquet(ROOT/spec['target_path'], columns=['Date', 'target'])
        dates = clock(daily, 'date')
        check('risk_clocks', dates.equals(pd.date_range('2021-11-08', '2025-03-31', tz='UTC')) and len(daily) == 1240, name)
        check('risk_clocks', clock(targets, 'Date').equals(pd.date_range('2021-11-07', '2025-03-31', tz='UTC')) and len(targets) == 1241, name+' target')
        check('risk_clocks', dates.equals(clock(original, 'date')), name+' original dates')
        for col in original:
            if col == 'date': continue
            if pd.api.types.is_numeric_dtype(original[col]): near('risk_source_values', daily[col], original[col], name+' '+col, atol=0, rtol=0)
            else: check('risk_source_values', daily[col].equals(original[col]), name+' '+col)
        near('risk_source_values', daily.latent_target, targets.target.iloc[1:], name+' saved targets', atol=0, rtol=0)
        old = prior[spec['configuration']['name']]['variants']['primary']['sleeves'][spec['coin']]
        for col in ('gross_dollars', 'funding_dollars', 'fee_dollars', 'impact_dollars'):
            near('risk_totals', summary['components'][col], original[col].sum(), name+' '+col, atol=1e-9)
            near('risk_totals', old[col], original[col].sum(), name+' prior '+col, atol=1e-9)
        near('risk_totals', summary['turnover_dollars'], original.turnover_dollars.sum(), name+' turnover', atol=1e-9)
        near('risk_totals', summary['components']['net_dollars'], original.nav_after.iloc[-1]-10000, name+' NAV attribution', atol=1e-9)
        halted = original.halted_before.to_numpy(bool)
        check('risk_halts', summary['halted_cash_rows'] == int(halted.sum()), name+' cash mask')
        first = dates[original.halted_after.to_numpy(bool)][0] if original.halted_after.any() else None
        check('risk_halts', old['halted'] == (first is not None), name+' prior latch')
        if first is not None:
            check('risk_halts', first == pd.Timestamp(old['halt_date'], tz='UTC') == pd.Timestamp(summary['first_halt']['date'], tz='UTC'), name+' exact halt date')
        nav, after, weight = (daily[x].to_numpy(float) for x in ('nav_before', 'nav_after', 'applied_weight'))
        held = np.r_[0., daily.closing_notional.to_numpy(float)[:-1]]
        old_weight = np.r_[0., weight[:-1]]; reference = np.where(held != 0, old_weight, 0.)
        a, b = nav*(weight-reference), nav*reference-held
        near('risk_turnover', daily.target_change_dollars, a, name+' target component', atol=1e-9)
        near('risk_turnover', daily.maintenance_dollars, b, name+' maintenance component', atol=1e-9)
        near('risk_turnover', daily.entry_turnover_dollars, abs(a+b), name+' actual trade', atol=1e-9)
        near('risk_turnover', daily.component_netting_dollars, abs(a)+abs(b)-abs(a+b), name+' netting', atol=1e-9)
        near('risk_weights', daily.incoming_weight, held/nav, name+' incoming')
        near('risk_weights', daily.closing_weight, daily.closing_notional/after, name+' closing')
        near('risk_weights', weight, np.where(halted, 0, daily.latent_target), name+' applied/halt')
        net = daily.gross_dollars+daily.funding_dollars-daily.fee_dollars-daily.impact_dollars
        near('risk_stages', after-nav, net, name+' dollar identity', atol=1e-9)
        pre = nav+daily.gross_dollars+daily.funding_dollars-daily.entry_fee_dollars-daily.entry_impact_dollars
        near('risk_stages', daily.pre_exit_nav, pre, name+' pre-exit stage', atol=1e-9)
        staged = np.column_stack((pre, after)).ravel()
        peaks = np.maximum.accumulate(np.r_[10000., staged])[1:].reshape((-1,2))
        near('risk_stages', daily.running_peak_nav, peaks[:,1], name+' running peak', atol=1e-9)
        near('risk_stages', daily.pre_exit_drawdown, (peaks[:,0]-pre)/peaks[:,0], name+' pre DD')
        near('risk_stages', daily.post_exit_drawdown, (peaks[:,1]-after)/peaks[:,1], name+' post DD')
        if first is not None:
            at = int(np.flatnonzero(dates == first)[0]); halt = summary['first_halt']
            near('risk_halts', halt['peak_nav'], peaks[at,1], name+' halt peak', atol=1e-9)
            near('risk_halts', halt['peak_to_halt_components']['net_dollars'], after[at]-peaks[at,1], name+' peak-to-halt', atol=1e-9)
            expected_stage = 'pre_exit' if daily.pre_exit_drawdown.iloc[at] >= .15 else 'post_exit'
            check('risk_halts', halt['crossing_stage'] == expected_stage, name+' crossing stage')
        sigma = daily.sigma_252.to_numpy(float); ref = daily.reference_entry_risk.to_numpy(float)
        for label in ('latent', 'incoming', 'applied', 'closing'):
            w = daily.latent_target.to_numpy(float) if label == 'latent' else daily[label+'_weight'].to_numpy(float)
            value = abs(w)*sigma; active = w != 0
            with np.errstate(all='ignore'): ratio = value/np.where(ref > 0, ref, np.nan)
            near('risk_proxies', daily[label+'_risk_proxy'], value, name+' '+label)
            near('risk_proxies', daily[label+'_reference_risk_ratio'], ratio, name+' '+label+' ratio')
            compare_distribution(summary['risk_distributions'][label], distribution(value, active), name+' '+label)
            compare_distribution(summary['risk_distributions'][label+'_reference_ratio'], distribution(ratio, active), name+' '+label+' ratio')
            known = np.isfinite(value) & np.isfinite(ref); budget_known = np.isfinite(value)
            wanted = dict(active_rows=int(active.sum()), reference_available_active_rows=int((active & known).sum()),
                reference_unavailable_active_rows=int((active & ~known).sum()), nominal_budget_available_active_rows=int((active & budget_known).sum()),
                nominal_budget_unavailable_active_rows=int((active & ~budget_known).sum()),
                above_reference_risk=int((active & known & (value > ref+1e-12)).sum()),
                above_nominal_entry_budget=int((active & budget_known & (value > .15+1e-12)).sum()))
            check('risk_threshold_denominators', summary['counts'][label+'_risk_thresholds'] == wanted, name+' '+label)
            check('risk_threshold_denominators', summary['counts'][label+'_above_leverage_cap'] == int((abs(w)>3+1e-12).sum()), name+' '+label+' leverage')
        indices = np.flatnonzero(daily.price_stop_hit.to_numpy(bool))
        check('risk_events', clock(events, 'date').equals(dates[indices]) and len(events) == summary['price_stops'] == old['price_stops'], name+' all price stops')
        fees, impact, successors = 0., 0., Counter()
        for (_, event), index in zip(events.iterrows(), indices):
            kind = 'end_of_window_censored'
            if index+1 < len(daily):
                nxt = daily.iloc[index+1]
                kind = ('permanently_halted' if nxt.halted_before else 'flat' if nxt.applied_weight == 0 else
                        'same_sign_reentry' if np.sign(nxt.applied_weight) == np.sign(daily.applied_weight.iloc[index]) else 'opposite_sign_entry')
                check('risk_events', pd.Timestamp(event.next_date) == pd.Timestamp(nxt.date), name+' successor date')
                check('risk_events', event.raw_target_changed == (nxt.latent_target != daily.latent_target.iloc[index]), name+' target change')
                if kind in ('same_sign_reentry', 'opposite_sign_entry'):
                    fees += nxt.entry_fee_dollars; impact += nxt.entry_impact_dollars
                    near('risk_events', event.next_entry_fee_dollars, nxt.entry_fee_dollars, name+' next fee', atol=1e-9)
                    near('risk_events', event.next_entry_impact_dollars, nxt.entry_impact_dollars, name+' next impact', atol=1e-9)
                    check('risk_events', event.reused_sizing_reference == (nxt.sizing_date == daily.sizing_date.iloc[index]), name+' sizing reuse')
            check('risk_events', event.successor == kind, name+' successor class')
            successors[kind] += 1
        check('risk_events', dict(successors) == summary['stop_successors'], name+' successor denominator')
        near('risk_events', summary['unique_stop_successor_entry_fees'], fees, name+' unique fees', atol=1e-9)
        near('risk_events', summary['unique_stop_successor_entry_impact'], impact, name+' unique impact', atol=1e-9)
        summaries.append(dict(cell=name, target_rows=len(targets), trace_rows=len(daily), halted_cash_rows=int(halted.sum()),
            halt_date=first.isoformat() if first is not None else None, price_stops=len(events), all_four_exposure_summaries_verified=True))
    return summaries


def verify():
    prior = preservation.verify(REGISTRATION)
    gates = json.loads((ROOT/preservation.GATES).read_text())
    fgate, rgate = (gates[k] for k in preservation.KEYS)
    fresult, rresult = manifest('forecast', fgate), manifest('risk', rgate)
    for name in ('tradingagents/predlab/saved_forecast_inference.py', 'scripts/audit_saved_forecast_inference_2026_09_10.py',
                 'tradingagents/strategies/factor_risk_diagnostics.py', 'scripts/audit_factor_risk_2026_09_10.py'):
        check('source_hashes', digest(ROOT/name) == hashlib.sha256(preservation.baseline_bytes(name, SOURCE)).hexdigest(), name)
    for name, expected in rresult['source_sha256'].items():
        path = Path(name); relative = path.relative_to(ROOT)
        check('source_hashes', digest(path) == expected == hashlib.sha256(preservation.baseline_bytes(str(relative), SOURCE)).hexdigest(), name)
    fs, rs = forecast(fresult, fgate), risk(rresult, rgate)
    check('financial_ledger', digest(ROOT/preservation.LEDGER) == preservation.LEDGER_SHA, 'unchanged after review')
    return dict(status='PASS', execution_source=SOURCE, registration_commit=REGISTRATION,
        result_sha256={family:digest(BASE/family/'result.json') for family in ('forecast','risk')},
        output_files_verified=dict(forecast=len(fresult['output_sha256']),risk=len(rresult['output_sha256'])),
        input_references_verified=35+78, unique_input_pins=112,
        checks=dict(CHECKS), forecast_cells=fs, risk_sleeves=rs,
        forecast_clock_rows=sum(x['clock_rows'] for x in fs), forecast_scoreable_rows=sum(x['scoreable_rows'] for x in fs),
        saved_bootstrap_draw_rows=sum(x['bootstrap_draws'] for x in fs), risk_trace_rows=sum(x['trace_rows'] for x in rs),
        risk_target_rows=sum(x['target_rows'] for x in rs), risk_price_stop_events=sum(x['price_stops'] for x in rs),
        prior_preservation=dict(tracked_files=prior['baseline_tracked_files'],byte_identical_files=prior['baseline_byte_identical_files'],
            prior_gate_objects_unchanged=prior['prior_gate_objects_unchanged'],external_original_inputs_verified=prior['external_original_inputs_verified'],
            financial_ledger=prior['financial_ledger']),
        documentary_correction=dict(old_prose_max_halted_cash_rows=1157,correct_max_halted_before_rows=1158,
            cell='tsmom_k180_ls|ethereum',halt_date='2022-01-28',first_already_halted_cash_date='2022-01-29',
            last_date='2025-03-31',source_trace_halted_after_rows=1159,
            explanation='The original immutable trace has1158 already-halted cash rows. Prior prose1157 is off by one; the original result halt date and new diagnostic agree. Old artifacts remain unchanged.'),
        runner_calls=0, bootstrap_resampling_calls=0, strategy_replays=0, network_requests=0,
        qualification='Saved numerical identities, hashes and denominators only. No new method, resampling, strategy replay, source-cache repair or validation claim. Original values were bounded before baseline materialization. Git retention is verified separately.')


if __name__ == '__main__':
    report = verify()
    report.update(verified_utc=datetime.now(timezone.utc).isoformat(), checker_sha256=digest(Path(__file__)))
    preservation.write_new(OUT/'result-review.json', report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('forecast_cells','risk_sleeves')}, indent=2))
