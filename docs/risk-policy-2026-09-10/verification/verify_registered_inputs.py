"""Risk-policy admission using byte identities and timestamp columns only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

import verify_preservation as preservation

ROOT, OUT = preservation.ROOT, Path(__file__).resolve().parent
REGISTRATION = '67eb720305ccddff266df396e61d03dc2fa1985e'
FACTOR_SOURCE = '27640882822d812c6d0478340495e033a11d3915'
VARIANTS = ['primary','zero_execution','double_execution','zero_funding']
ARMS = [
    {'id':'A00','sizing':'saved','reentry':'immediate'},
    {'id':'A10','sizing':'daily','reentry':'immediate'},
    {'id':'A01','sizing':'saved','reentry':'new_target_episode'},
    {'id':'A11','sizing':'daily','reentry':'new_target_episode'}]


def require(condition, message):
    if not condition: raise ValueError(message)


def check_clock(path, column, expected):
    # This is the only Parquet read: price, target, PnL and return values are not loaded.
    table = pq.ParquetFile(path).read(columns=[column])
    require(column in table.column_names, f'missing timestamp column: {path}')
    clock = pd.DatetimeIndex(pd.to_datetime(table[column].to_pylist(), utc=True))
    require(not clock.hasnans and clock.is_unique and clock.is_monotonic_increasing,
            f'invalid timestamp clock: {path}')
    require(clock.equals(expected), f'incomplete or out-of-window timestamp clock: {path}')
    return {'path':str(path), 'timestamp_column':column, 'rows':len(clock),
            'start':clock.min().isoformat(), 'end':clock.max().isoformat(),
            'unique':True, 'monotonic':True, 'missing':[], 'extra':[]}


def check_gate_schema(gate):
    require(gate['arms'] == ARMS and gate['variants'] == VARIANTS
            and gate['coins'] == ['bitcoin','ethereum'], 'fixed arm/cost/sleeve identity mismatch')
    required = {'expected_configurations':18,'expected_identities':72,
                'expected_index_evaluations':288,'expected_sleeve_books':576,
                'expected_shadows':72,'expected_direct_contrasts':54,
                'expected_target_dates':1241,'expected_trace_dates':1240,
                'development_window':['2021-11-07','2025-03-31'],
                'return_window':['2021-11-08','2025-03-31'],
                'allow_holdout':False,'models_refit':False,'network_allowed':False}
    require(all(gate[k] == value for k,value in required.items()), 'fixed denominator/window/fence mismatch')
    configurations = gate['configurations']
    require(len(configurations) == 18 and len({c['name'] for c in configurations}) == 18,
            'configuration identity denominator mismatch')
    cells = [{'id':f'{config["name"]}|{arm["id"]}', 'configuration':config,
              'arm':arm['id'], 'sizing':arm['sizing'], 'reentry':arm['reentry']}
             for config in configurations for arm in ARMS]
    require(gate['cells'] == cells, 'registered cells differ from fixed ordered cross product')


def verify():
    prior = preservation.verify(registration_commit=REGISTRATION, phase='baseline')
    gate = json.loads(preservation.baseline_bytes(preservation.GATES, REGISTRATION))[preservation.KEY]
    check_gate_schema(gate)
    require(gate['baseline_commit'] == preservation.BASELINE, 'preservation baseline changed')
    require(gate['source_execution_commit'] == FACTOR_SOURCE, 'original execution commit changed')
    require(gate['financial_ledger'] == {
        'path':preservation.LEDGER,'prefix_rows':748,'prefix_bytes':preservation.LEDGER_BYTES,
        'prefix_sha256':preservation.LEDGER_SHA,'append_rows':72,'final_rows':820},
        'registered ledger contract changed')
    pins = gate['pinned_files']; require(len(pins) == 264, 'registered input denominator changed')
    checked, paths = [], {}
    for name, sha in sorted(pins.items()):
        path = preservation.safe_local(ROOT, name)
        actual = preservation.inspect_file(path)
        preservation.require_match(actual, {'sha256':sha}, name)
        paths[name] = path; checked.append({'path':name, **actual})
    original_gates = json.loads(paths[gate['original_gates']].read_text())
    require(original_gates == json.loads(preservation.baseline_bytes(preservation.GATES)),
            'original gates archive differs from whole baseline object')
    # Only provenance and declared configuration/output identities are inspected here.
    source = json.loads(paths[gate['source_result']].read_text())
    require(source['git_commit'] == FACTOR_SOURCE, 'original result execution identity mismatch')
    require([c['config'] for c in source['cells']] == gate['configurations'],
            'registered configurations differ from original saved result')
    source_dir = Path(gate['source_result']).parent
    expected_data, clocks = {}, []
    targets = pd.date_range(*gate['development_window'], freq='D', tz='UTC')
    returns = pd.date_range(*gate['return_window'], freq='D', tz='UTC')
    require(len(targets) == 1241 and len(returns) == 1240, 'daily clock declaration mismatch')
    for config in gate['configurations']:
        name = config['name']
        for coin in gate['coins']:
            expected_data[str(source_dir/f'{name}-{coin}-targets.parquet')] = ('Date',targets,'target')
        for variant in gate['variants']:
            expected_data[str(source_dir/f'{name}-{variant}-returns.parquet')] = ('Date',returns,'returns')
            for coin in gate['coins']:
                expected_data[str(source_dir/f'{name}-{variant}-{coin}-trace.parquet')] = ('date',returns,'trace')
    require({n for n in pins if n.endswith('.parquet')} == set(expected_data),
            'registered files omit or add a target/trace/return identity')
    for name, (column, expected, role) in expected_data.items():
        require(source['output_sha256'][Path(name).name] == pins[name],
                f'original result output receipt differs from current gate: {name}')
        row = check_clock(paths[name], column, expected)
        row.update(path=name, role=role); clocks.append(row)
    source_checks = [{'result':gate['source_result'],'execution_commit':FACTOR_SOURCE}]
    for name in pins:
        if not name.endswith('.py'): continue
        historical_name = preservation.ENGINE if name == preservation.ENGINE_ARCHIVE else name
        commit = FACTOR_SOURCE if historical_name in (
            preservation.ENGINE, 'tradingagents/accounting.py', 'tradingagents/strategies/v2_sizing.py',
            'scripts/audit_factor_floor_2026_09_10.py') else preservation.BASELINE
        historical_sha = preservation.digest(preservation.baseline_bytes(historical_name, commit))
        require(historical_sha == pins[name], f'pinned code differs from declared provenance: {name}')
        source_checks.append({'path':name,'historical_path':historical_name,'git_commit':commit,
                              'sha256':historical_sha})
    # Invalidate admission if any read input or gate changed while metadata was inspected.
    for row in checked:
        preservation.require_match(preservation.inspect_file(paths[row['path']]), row, row['path'])
    current = json.loads(preservation.safe_local(ROOT, preservation.GATES).read_text())
    preservation.gate_additions(json.loads(preservation.baseline_bytes(preservation.GATES)),current,gate)
    preservation.ledger_prefix(preservation.baseline_bytes(preservation.LEDGER),
        preservation.safe_local(ROOT,preservation.LEDGER).read_bytes(),phase='baseline')
    return {'status':'PASS','registration_commit':REGISTRATION,'baseline_commit':preservation.BASELINE,
            'prior_tracked_files':prior['baseline_tracked_files'],
            'prior_byte_identical_files':prior['baseline_byte_identical_files'],
            'prior_gate_objects_unchanged':prior['prior_gate_objects_unchanged'],
            'original_external_inputs_verified':prior['external_original_inputs_verified'],
            'financial_ledger':prior['financial_ledger'],
            'registered_gate_sha256':prior['registered_gate_sha256'],
            'pins':len(checked),'identities':72,'index_evaluations':288,'sleeve_books':576,'shadows':72,
            'timestamp_only_files':len(clocks),
            'clock_roles':{role:sum(c['role'] == role for c in clocks) for role in ('target','trace','returns')},
            'inputs':checked,'source_provenance':source_checks,'clocks':clocks,
            'financial_statistics_computed':False,'financial_columns_materialized':False,'network_requests':0,
            'qualification':'Static preservation and input admission only. Saved inputs remain qualified '
                'spot/mixed-provider cache proxies; no claim of executable perpetual prices or funding. '
                'Timestamp checks prove the declared development calendar, not causality of values. '
                'New executable-source review, committed preflight and control parity are still required. '
                'The one engine hook is permitted but its correctness is not certified here.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); output = args.output.absolute()
    if output.parent.resolve() != OUT or output.suffix != '.json' or output.exists():
        parser.error('output must be a new JSON file inside this verification directory')
    started = datetime.now(timezone.utc).isoformat()
    result = verify()
    result.update(started_utc=started,verified_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=preservation.inspect_file(Path(__file__))['sha256'])
    preservation.write_new(output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','clocks')},indent=2))
