"""Synthetic saved-forecast inference; no research inputs or network."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tradingagents.predlab import saved_forecast_inference as inference
from scripts import audit_saved_forecast_inference_2026_09_10 as command


BOOT = {'method': 'full_clock_masked_ratio_stationary_bootstrap', 'mean_block_days': 21,
        'draws': 2000, 'seed': 20260910, 'ci_quantiles': [.025, .975],
        'pvalue': 'one_sided_null_centered_plus_one', 'seed_reset_per_cell': True}
STABILITY = {'periods': [['2021-01-01', '2022-12-31'], ['2023-01-01', '2024-12-31'],
                         ['2025-01-01', '2025-03-31']],
             'min_scoreable_per_period': 30, 'positive_periods_min': 2}
MULT = {'method': 'Holm', 'family_size': 16, 'unavailable_or_ineligible_p': 1., 'alpha': .05}
FLOORS = {'T1_oos_r2': {'1h': .002, '24h': .005}, 'T2_edge_pp': 2.,
          'T2_auc_ci_excludes': .5, 'T3_dqlike': .02, 'T4_dmase': .05}
POLICY = {'bootstrap': BOOT, 'stability': STABILITY,
          'reconciliation': {'rtol': 1e-9, 'atol': 1e-12}, 'multiplicity': MULT}


def fixture(target='T4_vol', n=120, missing=False):
    clock = pd.date_range('2024-01-01', periods=n, freq='h', tz='UTC')
    y = np.ones(n)
    pred = y + np.linspace(.1, .5, n)
    baseline_pred = y + np.linspace(.9, 1.2, n)
    corrected = pd.DataFrame({'y_true': y, 'raw_pred': pred, 'pred': pred,
        'fallback_used': False, 'fallback_reason': '', 'raw_valid': True,
        'target_valid': True, 'baseline_valid': True, 'scoreable': True,
        'saved_pred': pred, 'reconstructed_unavailable': False}, index=clock)
    baseline = pd.DataFrame({'y_true': y, 'pred': baseline_pred}, index=clock)
    spec = {'cell': f'BTCUSDT|1h|{target}', 'symbol': 'BTCUSDT', 'horizon': '1h',
        'target': target, 'strong_baseline': 'seasonal_naive_m24',
        'clock_start': clock[0].isoformat(), 'clock_end': clock[-1].isoformat(),
        'expected_clock_rows': n, 'known_unavailable_origin': None,
        'inference_eligible': target == 'T4_vol'}
    if missing:
        spec['known_unavailable_origin'] = clock[50].isoformat()
        corrected = corrected.drop(clock[50]); baseline = baseline.drop(clock[50])
    return corrected, baseline, spec


def reference(corrected, baseline, target='T4_vol'):
    m = corrected.scoreable.to_numpy()
    b, c = inference.loss_pair(corrected.y_true.to_numpy(), baseline.pred.to_numpy(),
                                corrected.pred.to_numpy(), target)
    return {'cell': f'BTCUSDT|1h|{target}', 'status': 'diagnostic_complete',
        'loss': {'T1_ret': 'se', 'T2_dir': 'brier', 'T3_rv': 'qlike', 'T4_vol': 'mase'}[target],
        'n_saved': len(corrected), 'n_scoreable': int(m.sum()),
        'n_fallback': int(corrected.loc[m, 'fallback_used'].sum()),
        'n_reconstructed_unavailable': int(corrected.reconstructed_unavailable.sum()),
        'raw_valid_coverage': float(corrected.loc[m, 'raw_valid'].mean()),
        'baseline_loss_mean': float(b[m].mean()), 'corrected_loss_mean': float(c[m].mean())}


def prepared(corrected, baseline, spec, prior=None):
    return inference.prepare_pair(corrected, baseline, spec,
        prior or reference(corrected, baseline, spec['target']), POLICY['reconciliation'])


def test_missing_middle_hour_preserves_physical_clock_and_unknown_values():
    c, b, spec = fixture(missing=True)
    pair, counts = prepared(c, b, spec)
    assert len(pair) == 120 and counts['n_scoreable'] == 119
    missing = pd.Timestamp(spec['known_unavailable_origin'])
    assert not pair.loc[missing, 'scoreable']
    assert pd.isna(pair.loc[missing, 'loss_baseline'])
    assert counts['missing_origin_count'] == 1


def test_fallback_keeps_origin_and_has_zero_difference():
    c, b, spec = fixture()
    c.loc[c.index[10], ['raw_pred']] = np.nan
    c.loc[c.index[10], ['pred']] = b.pred.iloc[10]
    c.loc[c.index[10], ['fallback_used', 'reconstructed_unavailable']] = True
    c.loc[c.index[10], ['raw_valid']] = False
    c.loc[c.index[10], 'fallback_reason'] = 'missing_or_nonfinite'
    pair, counts = prepared(c, b, spec)
    assert counts['n_fallback'] == 1 and counts['n_scoreable'] == len(c)
    assert pair.loss_difference.iloc[10] == 0.


@pytest.mark.parametrize('fault', ['target', 'duplicate', 'clock', 'fallback', 'mask', 'bool_value'])
def test_alignment_or_saved_policy_changes_are_rejected(fault):
    c, b, spec = fixture()
    prior = reference(c, b)
    if fault == 'target': b.iloc[0, 0] = 9.
    elif fault == 'duplicate': c = pd.concat([c, c.iloc[[0]]])
    elif fault == 'clock': c = c.drop(c.index[3]); b = b.drop(b.index[3])
    elif fault == 'fallback': c.iloc[0, c.columns.get_loc('fallback_used')] = True
    elif fault == 'mask': c.iloc[0, c.columns.get_loc('scoreable')] = False
    else: c['pred'] = True
    with pytest.raises(ValueError): prepared(c, b, spec, prior)


def test_variance_known_invalid_target_stays_unscoreable():
    c, b, spec = fixture('T3_rv')
    d = c.index[50]; spec['known_unavailable_origin'] = d.isoformat()
    c.loc[d, 'y_true'] = b.loc[d, 'y_true'] = 0.
    c.loc[d, ['scoreable', 'target_valid', 'baseline_valid']] = False
    pair, counts = prepared(c, b, spec)
    assert not pair.loc[d, 'scoreable'] and counts['n_scoreable'] == 119
    assert counts['missing_origin_count'] == 0


def test_old_nonvolume_mean_and_volume_ratio_must_reconcile():
    c, b, spec = fixture()
    prior = reference(c, b); prior['corrected_loss_mean'] *= 2
    with pytest.raises(ValueError, match='reconcil'): prepared(c, b, spec, prior)
    spec['target'] = 'T1_ret'; spec['cell'] = 'BTCUSDT|1h|T1_ret'
    spec['inference_eligible'] = False
    prior = reference(c, b, 'T1_ret'); prior['baseline_loss_mean'] += 1
    with pytest.raises(ValueError, match='reconcil'): prepared(c, b, spec, prior)


def test_bootstrap_is_paired_deterministic_and_preserves_constant_loss_relation():
    base = np.arange(1., 101.); model = base*.5; mask = np.ones(100, dtype=bool)
    mask[50] = False; base[50] = model[50] = np.nan
    first, draws = inference.bootstrap_pair(base, model, mask, mean_block=21, policy=BOOT)
    second, same = inference.bootstrap_pair(base, model, mask, mean_block=21, policy=BOOT)
    pd.testing.assert_frame_equal(draws, same)
    assert first == second
    assert np.allclose(draws.mean_candidate_loss, .5*draws.mean_baseline_loss)
    assert np.allclose(draws.relative_improvement, .5)
    assert first['valid_difference_draws'] == 2000
    assert (draws.sampled_scoreable_count <= 100).all()


def test_bootstrap_sign_and_positive_scale_invariance():
    base = np.linspace(1., 3., 100); model = np.linspace(.8, 1., 100); mask = np.ones(100, bool)
    a, _ = inference.bootstrap_pair(base, model, mask, mean_block=21, policy=BOOT)
    scaled, _ = inference.bootstrap_pair(7*base, 7*model, mask, mean_block=21, policy=BOOT)
    reverse, _ = inference.bootstrap_pair(model, base, mask, mean_block=21, policy=BOOT)
    assert a['mean_difference'] == pytest.approx(-reverse['mean_difference'])
    assert a['relative_improvement'] == pytest.approx(scaled['relative_improvement'])
    assert a['diagnostic_p'] == scaled['diagnostic_p']
    assert a['diagnostic_p'] < .05 and reverse['diagnostic_p'] > .95


def test_bootstrap_zero_denominator_draws_are_not_silently_removed():
    base = np.full(100, np.nan); model = base.copy(); mask = np.zeros(100, bool)
    base[0], model[0], mask[0] = 2., 1., True
    result, draws = inference.bootstrap_pair(base, model, mask, mean_block=21, policy=BOOT)
    assert result['valid_difference_draws'] < BOOT['draws']
    assert result['difference_ci'] is None and result['diagnostic_p'] is None
    assert len(draws) == BOOT['draws']


def test_identical_and_constant_difference_are_degenerate():
    x = np.arange(1., 101.); mask = np.ones(100, bool)
    for other in (x, x+1):
        result, _ = inference.bootstrap_pair(x, other, mask, mean_block=21, policy=BOOT)
        assert result['degenerate'] and result['diagnostic_p'] is None


def test_ineligible_cell_keeps_conditional_diagnostic_but_no_primary_p():
    c, b, spec = fixture('T1_ret')
    record, pair, draws = inference.analyze_cell(c, b, spec, reference(c, b, 'T1_ret'), POLICY, FLOORS)
    assert record['bootstrap']['diagnostic_p'] is not None
    assert record['eligible_primary_p'] is None
    assert record['inference_eligible'] is False and record['strategy_promotion'] is False


def test_direction_point_auc_ties_and_floor_never_claimed_without_interval():
    labels = np.array([0, 1, 0, 1], bool)
    assert inference.point_auc(labels, np.array([.5, .5, .5, .5])) == .5
    assert inference.point_auc(labels, np.array([.1, .9, .2, .8])) == 1.
    assert inference.point_auc(np.ones(4, bool), np.ones(4)) is None


def test_holm_uses_all_sixteen_slots_and_preserves_ineligible_null():
    records = [{'cell': str(i), 'inference_eligible': i < 2,
                'eligible_primary_p': .002 if i == 0 else .004 if i == 1 else None} for i in range(16)]
    inference.apply_holm(records, MULT)
    assert records[0]['holm_adjusted_p'] == pytest.approx(.032)
    assert records[1]['holm_adjusted_p'] == pytest.approx(.060)
    assert records[2]['holm_input_p'] == 1. and records[2]['holm_adjusted_p'] is None
    with pytest.raises(ValueError, match='16'): inference.apply_holm(records[:15], MULT)


def test_default_and_help_do_not_preflight_or_create_outputs(monkeypatch):
    monkeypatch.setattr(command.registry, 'preflight', lambda *a: pytest.fail('preflight consumed'))
    assert command.main([]) == 0
    with pytest.raises(SystemExit) as error: command.main(['--help'])
    assert error.value.code == 0


def test_date_filter_precedes_dataframe_materialization(tmp_path):
    p = tmp_path/'baseline.parquet'
    frame = pd.DataFrame({'ts': pd.to_datetime(['2025-03-31', '2025-04-01'], utc=True),
                          'y_true': [1., 999.], 'pred': [2., 999.]})
    frame.to_parquet(p, index=False)
    result = command.read_frame(p, pd.Timestamp('2025-03-31', tz='UTC'), pd.Timestamp('2025-03-31', tz='UTC'))
    assert len(result) == 1 and result.y_true.iloc[0] == 1.


def test_pinned_input_changed_and_output_overwrite_refused(tmp_path):
    p = tmp_path/'source'; p.write_bytes(b'original')
    pinned = {str(p): command.sha(p)}
    command.verify_hashes(pinned, tmp_path)
    p.write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'): command.verify_hashes(pinned, tmp_path)
    out = tmp_path/'result.json'; out.write_bytes(b'old')
    with pytest.raises(FileExistsError): command.write_json(out, {'new': 1})
    assert out.read_bytes() == b'old'


def test_direction_floor_descriptor_preserves_missing_auc_interval():
    c, b, spec = fixture('T2_dir')
    y = np.tile([-1., 1.], len(c)//2)
    pred = np.where(y > 0, .9, .1)
    c['y_true'] = b['y_true'] = y
    for col in ('raw_pred', 'pred', 'saved_pred'): c[col] = pred
    b['pred'] = .5
    record, _, _ = inference.analyze_cell(c, b, spec, reference(c, b, 'T2_dir'), POLICY, FLOORS)
    assert record['effect']['point_auc'] == 1.
    assert record['effect']['accuracy_edge_floor_met']
    assert record['effect']['original_conjunctive_floor_met'] is None
    assert record['eligible_primary_p'] is None


def test_registered_policy_and_cell_denominators_are_enforced():
    # Registration metadata only; no empirical source file is opened by this test.
    gate = json.loads((command.ROOT/'data/predlab/gates.json').read_text())[command.KEY]
    command.validate_gate(gate, command.ROOT)
    for field, value in [('draws', 100), ('mean_block_days', 7), ('seed', 1)]:
        changed = deepcopy(gate); changed['bootstrap'][field] = value
        with pytest.raises(ValueError, match='policy'): command.validate_gate(changed, command.ROOT)
    changed = deepcopy(gate); changed['cells'] = changed['cells'][:-1]
    with pytest.raises(ValueError, match='sixteen'): command.validate_gate(changed, command.ROOT)


def runner_fixture(tmp_path, monkeypatch, invalid_first=False):
    root = tmp_path/'checkout'; root.mkdir()
    ledger = root/command.LEDGER; ledger.parent.mkdir(parents=True)
    ledger_bytes = b'{}\n'*748; ledger.write_bytes(ledger_bytes)
    gate = deepcopy(POLICY)
    gate.update(output_dir=command.OUTPUT, cells=[], expected_cell_count=16, forensic_ledger_rows=16,
        baseline_commit='a'*40, source_result='prior.json', original_gates='original-gates.json',
        charter='charter.md', pinned_files={})
    prior = {'experiment': 'audit_correction_2026_09_09', 'enet': [],
             'input_sha256': {}, 'output_sha256': {}}
    original = {'predlab_p1_classical': {'effect_floors': FLOORS}, 'predlab_p2_ml': {'cells': []}}
    for i in range(16):
        c, b, spec = fixture()
        spec['cell'] = f'fixture-{i}'
        ref = reference(c, b); ref['cell'] = spec['cell']
        if invalid_first and i == 0: c = pd.concat([c, c.iloc[[0]]])
        cp, bp = root/f'corrected-{i}.parquet', root/f'baseline-{i}.parquet'
        c.index.name = b.index.name = 'ts'
        c.to_parquet(cp); b.to_parquet(bp)
        spec.update(corrected_path=cp.name, baseline_path=str(bp))
        gate['cells'].append(spec)
        gate['pinned_files'].update({cp.name: command.sha(cp), str(bp): command.sha(bp)})
        prior['enet'].append(ref)
        prior['output_sha256'][cp.name] = command.sha(cp)
        prior['input_sha256'][str(bp)] = command.sha(bp)
        original['predlab_p2_ml']['cells'].append({'cell': spec['cell']})
    command.write_json(root/'prior.json', prior)
    command.write_json(root/'original-gates.json', original)
    (root/'charter.md').write_text('Synthetic charter; no research data.\n')
    for name in ('prior.json', 'original-gates.json', 'charter.md'):
        gate['pinned_files'][name] = command.sha(root/name)
    monkeypatch.setattr(command, 'ROOT', root)
    # Tiny test clocks bypass only production identity validation, tested above.
    monkeypatch.setattr(command, 'validate_gate', lambda gate, root: None)
    monkeypatch.setattr(command.registry, 'get_experiment', lambda key: gate)
    monkeypatch.setattr(command.registry, 'preflight', lambda *a: {'git_commit': 'b'*40, 'gate_sha256': 'c'*64})
    monkeypatch.setattr(command.subprocess, 'check_output', lambda *a, **kw: ledger_bytes)
    return root, gate, ledger_bytes


def test_runner_preserves_unavailable_slot_and_financial_ledger(tmp_path, monkeypatch):
    root, gate, original_ledger = runner_fixture(tmp_path, monkeypatch, invalid_first=True)
    result = command.execute()
    assert len(result['cells']) == 16 and result['available_cells'] == 15
    assert result['cells'][0]['status'] == 'unavailable'
    assert result['cells'][0]['holm_input_p'] == 1.
    assert (root/command.LEDGER).read_bytes() == original_ledger
    output = root/gate['output_dir']
    assert len((output/'forensic-ledger.jsonl').read_text().splitlines()) == 16
    assert result['prior_receipt_agreement'] and result['financial_ledger']['new_rows'] == 0
    for name, expected in result['output_sha256'].items(): assert command.sha(output/name) == expected
    with pytest.raises(FileExistsError): command.execute()


@pytest.mark.parametrize('mutation', ['input', 'preflight'])
def test_runner_postflight_mutation_preserves_failure_and_does_not_publish(tmp_path, monkeypatch, mutation):
    root, gate, original_ledger = runner_fixture(tmp_path, monkeypatch)
    if mutation == 'input':
        original = command.inference.analyze_cell
        fired = False
        def analyze(*args):
            nonlocal fired
            result = original(*args)
            if not fired:
                fired = True
                with Path(gate['cells'][0]['baseline_path']).open('ab') as out: out.write(b'mutated')
            return result
        monkeypatch.setattr(command.inference, 'analyze_cell', analyze)
    else:
        calls = 0
        def preflight(*args):
            nonlocal calls
            calls += 1
            return {'git_commit': 'b'*40, 'gate_sha256': 'before' if calls == 1 else 'after'}
        monkeypatch.setattr(command.registry, 'preflight', preflight)
    with pytest.raises(ValueError): command.execute()
    output = root/gate['output_dir']
    assert (output/'start.json').exists() and (output/'failure.json').exists()
    assert not (output/'result.json').exists() and not (output/'forensic-ledger.jsonl').exists()
    assert (root/command.LEDGER).read_bytes() == original_ledger


def test_prior_receipt_conflict_preserves_attempt_and_all_failure_identities(tmp_path, monkeypatch):
    root, gate, _ = runner_fixture(tmp_path, monkeypatch)
    p = root/gate['source_result']
    previous = json.loads(p.read_text())
    previous['input_sha256'][gate['cells'][0]['baseline_path']] = '0'*64
    p.write_text(json.dumps(previous))
    gate['pinned_files'][gate['source_result']] = command.sha(p)
    with pytest.raises(ValueError, match='prior receipt'): command.execute()
    output = root/gate['output_dir']
    assert (output/'start.json').exists() and (output/'failure.json').exists()
    assert not (output/'admission.json').exists() and not (output/'result.json').exists()
    rows = [json.loads(line) for line in (output/'failure-forensic-ledger.jsonl').read_text().splitlines()]
    assert len(rows) == 16 and all(row['status'] == 'unavailable' for row in rows)


@pytest.mark.parametrize('fault', ['missing', 'changed', 'ledger'])
def test_global_input_admission_failure_preserves_attempt_without_parsing(tmp_path, monkeypatch, fault):
    root, gate, ledger = runner_fixture(tmp_path, monkeypatch)
    source = Path(gate['cells'][0]['baseline_path'])
    if fault == 'missing': source.unlink()
    elif fault == 'changed': source.write_bytes(b'wrong bytes')
    else: (root/command.LEDGER).write_bytes(b'changed ledger')
    monkeypatch.setattr(command, 'read_frame', lambda *a: pytest.fail('mismatched inputs parsed'))
    with pytest.raises((OSError, ValueError)): command.execute()
    output = root/gate['output_dir']
    assert json.loads((output/'start.json').read_text())['admission_status'] == 'pending'
    assert (output/'failure.json').exists() and not (output/'admission.json').exists()
    assert not (output/'result.json').exists() and not (output/'forensic-ledger.jsonl').exists()
    rows = [json.loads(line) for line in (output/'failure-forensic-ledger.jsonl').read_text().splitlines()]
    assert [r['cell'] for r in rows] == [c['cell'] for c in gate['cells']]
    assert all(r['status'] == 'unavailable' and r['accepted_metrics'] is False for r in rows)
