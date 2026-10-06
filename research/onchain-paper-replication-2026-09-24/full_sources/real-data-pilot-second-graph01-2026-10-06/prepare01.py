"""Freeze the unused May 9 graph; metadata only, no claim or raw body read."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

from tradingagents.research.admission import runtime_hashes
from tradingagents.research.onchain_replication.job import required_sources
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
STUDY = ROOT / 'research/onchain-paper-replication-2026-09-24'
FULL = STUDY / 'full_sources'
OLD = FULL / 'real-data-pilot-first-graph01-2026-10-05'
NAME = 'eth-paper-real-pilot-graph-20220509-20261005-01'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}


def write(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def main():
    for path in (HERE / 'gate01.json', HERE / 'launch-attempt01.json',
                 ROOT / 'research_runs' / NAME,
                 ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' / NAME,
                 ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / NAME):
        if path.exists() or path.is_symlink():
            raise FileExistsError(str(path))
    census_path = FULL / 'real-data-pilot-remaining-graph-inputs01-2026-10-06/RAW_EXTENTS01.json'
    case = next(item for item in json.loads(census_path.read_bytes())['cases'] if item['identity'] == NAME)
    if case['parent'] is not None or case['run_started'] is not False:
        raise ValueError('original independent unused case required')
    for day in case['daily_members']:
        if digest(ROOT / day['mapping_path']) != day['mapping_sha256']:
            raise ValueError('daily map changed')
        for segment in day['segments']:
            path = Path(segment['path'])
            info = path.lstat()
            if path.is_symlink() or not path.is_file() or (
                info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
            ) != tuple(segment[key] for key in ('device', 'inode', 'bytes', 'mtime_ns', 'ctime_ns')):
                raise ValueError('original extent changed: ' + str(path))
    at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = case['expected_rows']
    extent = {'at': at, 'week': case['week'], 'days': 7, 'declared_rows': rows,
              'daily_members': case['daily_members'],
              'segments': sum(len(day['segments']) for day in case['daily_members']),
              'stored_bytes': sum(s['bytes'] for day in case['daily_members'] for s in day['segments']),
              'largest_projected_object_logical_bytes': case['largest_projected_parquet_bytes'],
              'raw_bodies_read': False, 'census': ref(census_path),
              'qualification': 'Fresh stat joins only; original stored/raw hashes and complete row denominator remain genuine worker obligations.'}
    old_projection = json.loads((OLD / 'STORAGE_PROJECTION_DRAFT01.json').read_bytes())
    reference_rows = old_projection['retained_graph_reference']['declared_raw_rows']
    ledger = (rows * old_projection['closed_ledger_reference']['bytes'] + reference_rows - 1) // reference_rows
    arrays = (rows * old_projection['retained_graph_reference']['saved_array_bytes'] + reference_rows - 1) // reference_rows
    margin = old_projection['scratch_margin_bytes']
    growth = 2 * ledger + arrays + case['largest_projected_parquet_bytes'] + margin
    floor = 10 * 1024**3
    projection = {**old_projection, 'created_at': at, 'pilot_expected_rows': rows,
                  'density_projected_ledger_bytes': ledger, 'density_projected_arrays_bytes': arrays,
                  'largest_projected_parquet_logical_bytes': case['largest_projected_parquet_bytes'],
                  'prospective_growth_estimate_bytes': growth, 'prospective_startup_free_bytes': floor + growth,
                  'status': 'PROSPECTIVE_ESTIMATE_NOT_CAPACITY_NOT_RELEASE',
                  'qualification': 'Same preserved Graph10 density and conservative overlap formula as the accepted first graph. Complete prospective May9 rows; no numerical body or model outcome was inspected. Density and filesystem allocation may differ; preserve any actual breach.'}
    source_root = ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources'
    baseline = StorageWatch(str(source_root), {'max_allocated_bytes': 32*1024**3,
        'max_logical_bytes': 32*1024**3, 'max_entries': 20000,
        'max_depth': 16, 'max_scan_seconds': 5}).check()
    policy = json.loads((OLD / 'STORAGE_POLICY01.json').read_bytes())
    policy.update(at=at, baseline=baseline, growth_estimate_bytes=growth,
                  free_disk_observed_bytes=shutil.disk_usage(ROOT).free,
                  startup_free_requirement_bytes=floor + growth)
    policy['storage_budget']['limits'].update(
        max_allocated_bytes=baseline['allocated_bytes'] + growth,
        max_logical_bytes=baseline['logical_file_bytes'] + growth)
    job = json.loads((OLD / 'execution-job01.json').read_bytes())
    job['resources']['storage_budget'] = policy['storage_budget']
    write('RAW_EXTENT01.json', extent)
    write('STORAGE_PROJECTION01.json', projection)
    write('STORAGE_POLICY01.json', policy)
    write('execution-job01.json', job)
    gate = json.loads((OLD / 'gate02.json').read_bytes())
    old_item = next(iter(gate['experiments'].values()))
    inputs = {key: value for key, value in old_item['inputs'].items() if not key.startswith('daily_map_')}
    inputs.update(case['inputs'])
    storage = STUDY / 'storage/real-pilot-first-graph-preservation-20261006-01'
    retirement = FULL / 'real-data-pilot-first-graph-post-recovery-retirement01-2026-10-06'
    paths = {'execution_job': HERE / 'execution-job01.json', 'raw_extent': HERE / 'RAW_EXTENT01.json',
             'storage_policy': HERE / 'STORAGE_POLICY01.json', 'storage_projection': HERE / 'STORAGE_PROJECTION01.json',
             'storage_closure_review': FULL / 'real-data-pilot-first-graph-preservation-outcome-review01-2026-10-06/REVIEW01.json',
             'storage_complete': storage / 'complete.json', 'storage_native_final': storage / 'guard01/final.json',
             'storage_restore': storage / '11-restore.json', 'storage_recovered_restore': storage / '11-recovered-restore.json',
             'storage_recovered_complete': storage / 'recovered-complete.json',
             'storage_retirement_complete': retirement / 'complete01.json',
             'storage_retirement_root_exit': retirement / 'ROOT_TERMINAL01.json',
             'source_integration': FULL / 'real-data-pilot-main-live-integration02-2026-10-06/INTEGRATION02.json'}
    for key, path in paths.items():
        inputs[key] = {**ref(path), 'dataset': 'eth'}
    for number, day in enumerate(case['daily_members']):
        inputs[f'daily_map_{number:02d}'] = {**ref(ROOT / day['mapping_path']), 'dataset': 'eth'}
    pins = {path: digest(ROOT / path) for path in required_sources()}
    for path in (HERE / 'prepare01.py', HERE / 'preflight01.py', HERE / 'launch01.py', HERE / 'CHARTER01.md',
                 FULL / 'real-data-end-to-end-pilot-preparation01-2026-10-05/CUMULATIVE_ALLOCATION_PROPOSED71_01.json',
                 ROOT / old_item['cumulative_budget_extension']['extension']['path'],
                 ROOT / old_item['cumulative_budget_extension']['review']['path']):
        pins[str(path.relative_to(ROOT))] = digest(path)
    item = {**old_item, 'question': 'Build the complete preserved ETH May9–16,2022 graph for the representative real-data pilot; measure graph throughput, peak charged memory and storage.',
            'charter': ref(HERE / 'CHARTER01.md'), 'inputs': inputs, 'source_files': dict(sorted(pins.items())),
            'runtime_hashes': runtime_hashes(), 'cells': case['cells'], 'outputs': case['outputs'],
            'windows': [{'dataset': 'eth', 'start': case['week'], 'end': '2022-05-16T00:00:00Z', 'availability': 'existing'}]}
    gate['experiments'] = {NAME: item}
    write('gate01.json', gate)
    print(json.dumps({'identity': NAME, 'declared_rows': rows, 'raw_extent_count': extent['segments'],
        'startup_free_requirement_bytes': floor+growth, 'current_free_bytes': policy['free_disk_observed_bytes'],
        'source_pins': len(pins), 'input_pins': len(inputs), 'gate_sha256': digest(HERE / 'gate01.json'),
        'claim_started': False}, sort_keys=True))


if __name__ == '__main__':
    main()
