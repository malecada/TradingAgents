"""Check registered diagnostic inputs using hashes and timestamp columns only.

This is static data admission, not executable-source preflight or result review.
Only a newly named JSON report in this directory may be written.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

import verify_preservation as preservation

ROOT = preservation.ROOT
OUT = Path(__file__).resolve().parent
REGISTRATION = '38d9a67e6ff042cb1fd870877b3e0222f40fdc08'
FORECAST_SOURCE = 'cc6801e81e25f05cdfbae77d560b59fa43e16dd9'
FACTOR_SOURCE = '27640882822d812c6d0478340495e033a11d3915'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_clock(path, column, expected, permitted_missing=()):
    # Values from every other column, including prices and saved outcomes, are
    # never materialized by this checker. The whole file is hashed separately.
    table = pq.ParquetFile(path).read(columns=[column])
    clock = pd.DatetimeIndex(pd.to_datetime(table[column].to_pylist(), utc=True))
    require(not clock.hasnans and clock.is_unique and clock.is_monotonic_increasing,
            f'invalid timestamp clock: {path}')
    missing, extra = expected.difference(clock), clock.difference(expected)
    allowed = pd.DatetimeIndex(pd.to_datetime(list(permitted_missing), utc=True))
    require(not len(extra) and not len(missing.difference(allowed)),
            f'unregistered timestamp gap or out-of-window row: {path}')
    return {'path': str(path), 'timestamp_column': column, 'rows': len(clock),
            'expected_rows': len(expected), 'start': clock.min().isoformat(),
            'end': clock.max().isoformat(), 'missing': [x.isoformat() for x in missing],
            'extra': [], 'unique': True, 'monotonic': True}


def verify():
    prior = preservation.verify(REGISTRATION)
    gates = json.loads((ROOT / preservation.GATES).read_text())
    forecast, risk = (gates[key] for key in preservation.KEYS)
    pins = {}
    for gate, count in ((forecast, 35), (risk, 78)):
        require(len(gate['pinned_files']) == count, 'registered pin denominator changed')
        for name, sha in gate['pinned_files'].items():
            require(name not in pins or pins[name] == sha, f'conflicting shared pin: {name}')
            pins[name] = sha
    require(len(pins) == 112, 'unique input denominator changed')
    approved_external = {row['path'] for row in prior['external_inputs']}
    checked, paths = [], {}
    for name, sha in sorted(pins.items()):
        if Path(name).is_absolute():
            require(name in approved_external, f'new external input not in original receipts: {name}')
            path = Path(name)
        else:
            path = preservation.safe_local(ROOT, name)
        actual = preservation.inspect_file(path)
        preservation.require_match(actual, {'sha256': sha}, name)
        paths[name] = path
        checked.append({'path': name, **actual})

    original_gates = json.loads(paths[forecast['original_gates']].read_text())
    baseline_gates = json.loads(preservation.baseline_bytes(preservation.GATES))
    for key, value in original_gates.items():
        require(baseline_gates[key] == value, f'original gate receipt mismatch: {key}')

    source_checks = []
    for gate, expected_commit in ((forecast, FORECAST_SOURCE), (risk, FACTOR_SOURCE)):
        result = json.loads(paths[gate['source_result']].read_text())
        require(result['git_commit'] == expected_commit, 'original result execution identity changed')
        source_checks.append({'result': gate['source_result'], 'execution_commit': expected_commit})
    require(risk['source_execution_commit'] == FACTOR_SOURCE, 'risk source identity changed')
    for name in risk['pinned_files']:
        if name.endswith('.py'):
            source_sha = hashlib.sha256(preservation.baseline_bytes(name, FACTOR_SOURCE)).hexdigest()
            require(source_sha == pins[name], f'original source commit mismatch: {name}')
            source_checks.append({'path': name, 'execution_commit': FACTOR_SOURCE, 'sha256': source_sha})

    clocks = []
    require(len(forecast['cells']) == 16 and len(risk['cells']) == 36,
            'registered cell denominator changed')
    for cell in forecast['cells']:
        expected = pd.date_range(cell['clock_start'], cell['clock_end'],
                                 freq='h' if cell['horizon'] == '1h' else 'D')
        require(len(expected) == cell['expected_clock_rows'], 'forecast clock declaration mismatch')
        missing = ([cell['known_unavailable_origin']] if cell['known_unavailable_origin'] else [])
        for field in ('corrected_path', 'baseline_path'):
            row = check_clock(paths[cell[field]], 'ts', expected, missing)
            row.update(cell=cell['cell'], role=field)
            clocks.append(row)
    targets = pd.date_range('2021-11-07', '2025-03-31', freq='D', tz='UTC')
    require(len(targets) == risk['expected_target_dates'] == 1241, 'target clock declaration mismatch')
    require(len(targets[1:]) == risk['expected_trace_dates'] == 1240, 'trace clock declaration mismatch')
    for cell in risk['cells']:
        for field, column, expected in (('target_path', 'Date', targets),
                                        ('trace_path', 'date', targets[1:])):
            row = check_clock(paths[cell[field]], column, expected)
            row.update(cell=cell['id'], role=field)
            clocks.append(row)

    # Rehash after timestamp reads; a changed original invalidates this report.
    for row in checked:
        preservation.require_match(preservation.inspect_file(paths[row['path']]), row, row['path'])
    preservation.require_ledger((ROOT / preservation.LEDGER).read_bytes(),
                                preservation.baseline_bytes(preservation.LEDGER))
    return {'status': 'PASS', 'registration_commit': REGISTRATION,
            'baseline_commit': preservation.BASELINE,
            'prior_tracked_files': prior['baseline_tracked_files'],
            'prior_byte_identical_files': prior['baseline_byte_identical_files'],
            'prior_gate_objects_unchanged': prior['prior_gate_objects_unchanged'],
            'original_external_inputs_verified': prior['external_original_inputs_verified'],
            'financial_ledger': prior['financial_ledger'],
            'registered_gate_sha256': prior['registered_gate_sha256'],
            'forecast_pins': 35, 'risk_pins': 78, 'unique_pins': len(checked),
            'forecast_cells': 16, 'risk_sleeves': 36,
            'timestamp_only_files': len(clocks), 'inputs': checked,
            'source_provenance': source_checks, 'clocks': clocks,
            'financial_statistics_computed': False, 'network_requests': 0,
            'qualification': 'Static immutable-input admission only. Values and eligibility masks are '
              'not analyzed. Financial ledger has no new records. Final executable-source preflight, '
              'mask reconciliation, separate forensic-ledger completeness and result review remain '
              'required. This report does not authorize execution or certify Git inclusion.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    if output.parent.resolve() != OUT or output.suffix != '.json' or output.exists():
        parser.error('output must be a new JSON file inside this verification directory')
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = verify()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        result = {'status': 'FAIL', 'error': f'{type(error).__name__}: {error}'}
    result.update(started_utc=started, verified_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=preservation.inspect_file(Path(__file__))['sha256'])
    preservation.write_new(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'clocks')}, indent=2))
    raise SystemExit(result['status'] != 'PASS')
