"""Freeze a prospective shared-store budget; no empirical admission or run."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-24'


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    body = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(body).hexdigest()}


capacity_path = F/'mcm-batched-grouped-capacity03-2026-10-09/CAPACITY01.json'
baseline_path = F/'mcm-batched-grouped-root-install01-2026-10-09/BASELINE01.json'
public_path = F/'real-data-pilot-full24-input-binding01-2026-10-09/PUBLIC_MANIFEST04.json'
capacity = load(capacity_path)['joined']
baseline = load(baseline_path)['observation']
public = load(public_path)
job_ref = load(HERE/'ALL_INPUT_REFS01.json')['execution_job']
job = load(ROOT/job_ref['path'])
resources = job['resources']
assert resources['storage_budget']['experiment'] == NAME
directory = 2*1024**3
other = 1024**3
logical = capacity['whole_logical_source_upper'] - baseline['logical_file_bytes'] + other
nondirectory = capacity['non_directory_increment_allocated_upper']
allocated = nondirectory + directory + other
assert baseline['logical_file_bytes'] + logical <= resources['storage_budget']['limits']['max_logical_bytes']
assert baseline['allocated_bytes'] + allocated <= resources['storage_budget']['limits']['max_allocated_bytes']
assert 0 < logical <= allocated
pins = public['source_pins']
assert len(pins) == 365
for path, pin in pins.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == pin, path
value = {
    'schema_version': 1, 'identity': NAME,
    'decision': 'accepted',
    'decision_scope': 'Root adopts this finite prospective resource-measurement budget; independent exact entry review remains required. This is not a capacity-success verdict.',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_anchor': '041b1b365ad46c6fa3dea99f0dd9e2ee1b31447f',
    'source_pins': pins,
    'allocation_semantics': 'prospective-headroom-sampled-aggregate-guards',
    'new_logical_growth_bytes': logical,
    'non_directory_new_allocated_growth_bytes': nondirectory,
    'new_allocated_growth_bytes': allocated,
    'directory_allocated_bound_bytes': directory,
    'other_writer_reserved_bytes': other,
    'new_entries': 650000,
    'directory_and_other_writers_included': True,
    'runtime_residuals_included': True,
    'owned_paths': resources['storage_budget']['roots'] + resources['storage_budget']['shared_files'],
    'basis': {
        'source_capacity03': ref(capacity_path),
        'capacity_source_review': ref(F/'mcm-batched-grouped-capacity-review01-2026-10-09/SOURCE_REVIEW01.json'),
        'source_baseline': ref(baseline_path),
        'public_source_manifest': ref(public_path),
        'remote_storage_sample': ref(HERE/'REMOTE_STORAGE_CHECK01.json'),
        'currentness_sample': ref(F/'real-data-pilot-full24-currentness01-2026-10-09/RESULT01.json')},
    'qualification': 'Source-derived non-directory growth plus explicit 2GiB directory and 1GiB competing-writer budgets. Directory allocation is not observed future usage; other writers are not excluded. Fresh preflight WritableUnion, filesystem free space, namespace, source/runtime and RAM observations are required at every entry. Unchanged sampled 16GiB logical/20GiB allocated union and 10GiB filesystem floor can refuse runtime breaches, without a hard quota or inter-sample growth guarantee. No empirical authority, physical preallocation, deletion permission or whole-job capacity conclusion follows.'}
with (HERE/'CAPACITY_DECLARATION01.json').open('x') as stream:
    json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({'status': 'PROSPECTIVE_BUDGET_FROZEN_NOT_RELEASED',
    'logical_growth': logical, 'allocated_growth': allocated,
    'new_entries': value['new_entries'], 'claim': False}))
