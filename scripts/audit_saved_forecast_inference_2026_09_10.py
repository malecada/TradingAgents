"""One registered, immutable saved-forecast inference diagnostic. Offline only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab import registry, saved_forecast_inference as inference

KEY = 'audit_saved_forecast_inference_2026_09_10'
WINDOW = ('2021-01-01', '2025-03-31')
LEDGER = 'data/predlab/trial_ledger.jsonl'
OUTPUT = 'data/diagnostics/2026-09-10/forecast'
BOOTSTRAP = {'method': 'full_clock_masked_ratio_stationary_bootstrap', 'mean_block_days': 21,
             'draws': 2000, 'seed': 20260910, 'ci_quantiles': [.025, .975],
             'pvalue': 'one_sided_null_centered_plus_one', 'seed_reset_per_cell': True}
MULTIPLICITY = {'method': 'Holm', 'family_size': 16, 'unavailable_or_ineligible_p': 1., 'alpha': .05}
STABILITY = {'periods': [['2021-01-01', '2022-12-31'], ['2023-01-01', '2024-12-31'],
                         ['2025-01-01', '2025-03-31']], 'min_scoreable_per_period': 30,
             'positive_periods_min': 2}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    path = Path(path)
    if path.is_symlink(): raise ValueError(f'symlink input is not admitted: {path}')
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''): digest.update(chunk)
    after = path.stat()
    stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if stamp(before) != stamp(after): raise ValueError(f'input changed during hashing: {path}')
    return digest.hexdigest()


def input_path(name, root):
    path = Path(name)
    return path if path.is_absolute() else root/path


def verify_hashes(pinned, root):
    observed = {}
    for name, expected in pinned.items():
        actual = sha(input_path(name, root))
        if actual != expected: raise ValueError(f'pinned input hash mismatch: {name}')
        observed[name] = actual
    return observed


def encode_json(payload):
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def write_json(path, payload):
    data = encode_json(payload)
    with Path(path).open('xb') as stream: stream.write(data)


def read_frame(path, start, end):
    """Apply the physical timestamp filter before Arrow-to-pandas materialization."""
    dataset = ds.dataset(path, format='parquet')
    field = dataset.schema.field('ts')
    if not pa.types.is_timestamp(field.type) or field.type.tz != 'UTC':
        raise ValueError('saved Parquet requires a UTC timestamp field')
    if str(start.tz) != 'UTC' or str(end.tz) != 'UTC' or end > pd.Timestamp('2025-03-31', tz='UTC'):
        raise ValueError('input window exceeds registered development cutoff')
    table = dataset.to_table(filter=(ds.field('ts') >= pa.scalar(start.to_pydatetime(), type=field.type)) &
        (ds.field('ts') <= pa.scalar(end.to_pydatetime(), type=field.type)))
    frame = table.to_pandas()
    if 'ts' in frame.columns: frame = frame.set_index('ts')
    return frame


def validate_gate(gate, root):
    if gate['bootstrap'] != BOOTSTRAP or gate['multiplicity'] != MULTIPLICITY or gate['stability'] != STABILITY:
        raise ValueError('unimplemented registered statistical policy')
    if gate['reconciliation'] != {'rtol': 1e-9, 'atol': 1e-12}:
        raise ValueError('unimplemented reconciliation policy')
    if (gate['expected_cell_count'], gate['forensic_ledger_rows'], gate['output_dir']) != (16, 16, OUTPUT):
        raise ValueError('registered denominator/output differs from fixed sixteen cells')
    if tuple(gate['development_window']) != WINDOW or gate['allow_holdout'] is not False:
        raise ValueError('unregistered development/holdout scope')
    if gate['models_refit'] is not False or gate['network_allowed'] is not False:
        raise ValueError('inference must not refit or use network')
    expected = []
    pin_names = {gate['charter'], gate['original_gates'], gate['source_result']}
    for symbol in ('BTCUSDT', 'ETHUSDT'):
        for horizon in ('1h', '24h'):
            for target in ('T1_ret', 'T2_dir', 'T3_rv', 'T4_vol'):
                expected.append((symbol, horizon, target))
    if len(gate['cells']) != 16: raise ValueError('expected sixteen cells')
    for cell, (symbol, horizon, target) in zip(gate['cells'], expected):
        name = f'{symbol}|{horizon}|{target}'
        start = '2021-01-01' if symbol == 'BTCUSDT' else '2021-12-01'
        count = (37201 if horizon == '1h' else 1551) if symbol == 'BTCUSDT' else (29185 if horizon == '1h' else 1217)
        baseline = {'T1_ret': 'rw_zero', 'T2_dir': 'base_rate', 'T3_rv': 'har_levels',
                    'T4_vol': 'seasonal_naive_m24' if horizon == '1h' else 'seasonal_naive_m7'}[target]
        corrected = f'data/predlab/audit_correction_2026_09_09/{name.replace("|", "_")}_enet.parquet'
        baseline_path = root.parent/'TradingAgents-predlab/data/predlab/forecasts/predlab_p2_ml'/name.replace('|', '_')/(baseline+'.parquet')
        known = '2024-10-28T20:00:00Z' if horizon == '1h' and target in ('T3_rv', 'T4_vol') else None
        values = {'cell': name, 'symbol': symbol, 'horizon': horizon, 'target': target,
                  'strong_baseline': baseline, 'eval_start': start, 'clock_start': start+'T00:00:00Z',
                  'clock_end': '2025-03-31T00:00:00Z', 'expected_clock_rows': count,
                  'known_unavailable_origin': known, 'inference_eligible': target == 'T4_vol',
                  'corrected_path': corrected, 'baseline_path': str(baseline_path)}
        if cell != values: raise ValueError(f'cell differs from the registered fixed policy: {name}')
        pin_names.update((corrected, str(baseline_path)))
    if set(gate['pinned_files']) != pin_names or len(pin_names) != 35:
        raise ValueError('pinned input scope differs from the fixed 35 files')


def prior_receipts(gate, previous, originals):
    records = previous['enet']
    if len(records) != 16 or [r['cell'] for r in records] != [r['cell'] for r in gate['cells']]:
        raise ValueError('prior correction denominator/order mismatch')
    if previous['experiment'] != 'audit_correction_2026_09_09':
        raise ValueError('unexpected correction source')
    original_cells = originals['predlab_p2_ml']['cells']
    if len(original_cells) != 16: raise ValueError('original P2 denominator differs')
    for cell, original in zip(gate['cells'], original_cells):
        if any(cell[k] != v for k, v in original.items()):
            raise ValueError('new cell differs from original P2 registration')
        if previous['output_sha256'][Path(cell['corrected_path']).name] != gate['pinned_files'][cell['corrected_path']]:
            raise ValueError('corrected vector hash differs from prior receipt')
        if previous['input_sha256'][cell['baseline_path']] != gate['pinned_files'][cell['baseline_path']]:
            raise ValueError('baseline hash differs from prior receipt')
    return {row['cell']: row for row in records}


def execute():
    provenance = registry.preflight(KEY, WINDOW)
    gate = registry.get_experiment(KEY)
    validate_gate(gate, ROOT)
    output = ROOT/gate['output_dir']
    if output.exists(): raise FileExistsError('immutable output already exists; no repeat permitted')
    output.mkdir(parents=True, exist_ok=False)
    runtime = {'python': platform.python_version(), 'numpy': np.__version__,
               'pandas': pd.__version__, 'pyarrow': pa.__version__, 'scipy': scipy.__version__}
    write_json(output/'start.json', {'started_utc': utc_now(), **provenance,
        'experiment': KEY, 'registered_gate': gate, 'expected_input_sha256': gate['pinned_files'],
        'runtime': runtime, 'admission_status': 'pending'})
    try:
        hashes = verify_hashes(gate['pinned_files'], ROOT)
        ledger_hash = sha(ROOT/LEDGER)
        baseline_ledger = subprocess.check_output(['git', 'show', f"{gate['baseline_commit']}:{LEDGER}"], cwd=ROOT)
        if hashlib.sha256(baseline_ledger).hexdigest() != ledger_hash or len(baseline_ledger.splitlines()) != 748:
            raise ValueError('original 748-row financial ledger changed')
        previous = json.loads(input_path(gate['source_result'], ROOT).read_text())
        originals = json.loads(input_path(gate['original_gates'], ROOT).read_text())
        prior = prior_receipts(gate, previous, originals)
        write_json(output/'admission.json', {'admitted_utc': utc_now(), 'admission_status': 'passed',
            'input_sha256': hashes, 'prior_receipt_agreement': True, 'financial_ledger_sha256': ledger_hash})
        records = []
        for number, cell in enumerate(gate['cells'], 1):
            print(f'Forecast diagnostic {number}/16: {cell["cell"]}', flush=True)
            try:
                start, end = pd.Timestamp(cell['clock_start']), pd.Timestamp(cell['clock_end'])
                corrected = read_frame(input_path(cell['corrected_path'], ROOT), start, end)
                baseline = read_frame(input_path(cell['baseline_path'], ROOT), start, end)
                record, pair, draws = inference.analyze_cell(corrected, baseline, cell,
                    prior[cell['cell']], gate, originals['predlab_p1_classical']['effect_floors'])
                stem = cell['cell'].replace('|', '_')
                pair.to_parquet(output/f'{stem}-paired.parquet')
                draws.to_parquet(output/f'{stem}-bootstrap.parquet', index=False)
            except (OSError, ValueError, KeyError, TypeError, pa.ArrowException) as error:
                record = {'cell': cell['cell'], 'status': 'unavailable',
                    'reason': f'{type(error).__name__}: {error}', 'expected_clock_rows': cell['expected_clock_rows'],
                    'inference_eligible': cell['inference_eligible'], 'eligible_primary_p': None,
                    'strategy_promotion': False, 'formal_model_class_p': None}
            records.append(record)
        inference.apply_holm(records, gate['multiplicity'])
        if verify_hashes(gate['pinned_files'], ROOT) != hashes: raise ValueError('inputs changed during run')
        if sha(ROOT/LEDGER) != ledger_hash: raise ValueError('financial ledger changed during run')
        if registry.preflight(KEY, WINDOW) != provenance: raise ValueError('source/gate/policy changed during run')
        forensic = [{'kind': 'nonfinancial_saved_forecast_diagnostic', 'experiment': KEY,
            'cell': r['cell'], 'source_commit': provenance['git_commit'], 'metrics': r} for r in records]
        ledger_data = ''.join(json.dumps(r, sort_keys=True, allow_nan=False)+'\n' for r in forensic).encode()
        outputs = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
        outputs['forensic-ledger.jsonl'] = hashlib.sha256(ledger_data).hexdigest()
        result = {'experiment': KEY, **provenance, 'registered_gate': gate, 'runtime': runtime,
            'completed_utc': utc_now(), 'status': 'diagnostic_complete', 'cells': records,
            'expected_cells': 16, 'available_cells': sum(r['status'] == 'diagnostic_complete' for r in records),
            'prior_receipt_agreement': True, 'input_sha256': hashes, 'inputs_unchanged_after_run': True,
            'output_sha256': outputs, 'forensic_ledger_rows': 16,
            'financial_ledger': {'sha256_before': ledger_hash, 'sha256_after': sha(ROOT/LEDGER),
                                 'rows': 748, 'new_rows': 0, 'unchanged': True},
            'holdout_read': False, 'models_refit': False, 'network_requests': 0,
            'financial_backtests': 0, 'strategy_promotion': False,
            'limitations': ['Retrospective fixed forecasts, expanding estimation and historical model selection remain qualifications.',
                'Stationary bootstrap assumes sufficiently stable weak dependence; one fixed block length cannot prove that assumption.',
                'Missing targets remain unknown; inference is conditional on the preserved scoreability mask.',
                'Holm covers exactly sixteen current slots, not the complete historical model/research search.',
                'No formal nested-model, model-class, original-gate reversal or fresh validation claim is made.']}
        encoded = encode_json(result)  # Verify both artifacts serialize before either final write.
        with (output/'forensic-ledger.jsonl').open('xb') as stream: stream.write(ledger_data)
        with (output/'result.json').open('xb') as stream: stream.write(encoded)
        print('Completed sixteen saved-forecast diagnostic records; no strategy promotion.', flush=True)
        return result
    except Exception as error:
        reason = f'{type(error).__name__}: {error}'
        failures = [{'kind': 'nonfinancial_saved_forecast_diagnostic_failure', 'experiment': KEY,
            'cell': cell['cell'], 'source_commit': provenance['git_commit'], 'status': 'unavailable',
            'accepted_metrics': False, 'expected_clock_rows': cell['expected_clock_rows'],
            'reason': reason} for cell in gate['cells']]
        data = ''.join(json.dumps(row, sort_keys=True, allow_nan=False)+'\n' for row in failures).encode()
        try:
            current_ledger = {'sha256': sha(ROOT/LEDGER)}
        except (OSError, ValueError) as ledger_error:
            current_ledger = {'sha256': None, 'error': f'{type(ledger_error).__name__}: {ledger_error}'}
        write_json(output/'failure.json', {'failed_utc': utc_now(), 'error': reason,
            'experiment': KEY, 'financial_ledger_observation': current_ledger,
            'accepted_metrics': False, 'failure_forensic_rows': len(failures),
            'failure_forensic_sha256': hashlib.sha256(data).hexdigest()})
        with (output/'failure-forensic-ledger.jsonl').open('xb') as stream: stream.write(data)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Run the single committed diagnostic')
    args = parser.parse_args(argv)
    if not args.execute:
        print('Dry run: no inputs loaded, no preflight consumed, no output created. Use --execute after source review.')
        return 0
    execute()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
