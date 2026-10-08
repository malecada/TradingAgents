"""Prepare the changed-source throughput entry with accepted metadata tools.

No empirical inputs, admission, claim, private transport body or numerical
execution are opened here. The fixed prefix is an intermediate measurement.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import types

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = F / 'real-data-pilot-final22-2026-10-08'
PREVIOUS = 'eth-paper-real-data-end-to-end-resource-20261008-22'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-23'
NAMESPACE = 'ethpilot-20261009-23'


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
            'bytes': path.stat().st_size}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def renamed(value):
    return json.loads(json.dumps(value).replace(PREVIOUS, NAME)
                      .replace('ethpilot-20261008-22', NAMESPACE))


assert ROOT == Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
assert not (ROOT / 'research_runs' / NAME).exists()
assert not (HERE / 'launch-attempt01.json').exists()
assert not (ROOT / 'research_artifacts' / ('archive-dispatch-' + NAMESPACE)).exists()
anchor = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
pair = load(OLD / 'templates02/pair_policy01.json')
previous = pair['numerical_source']
pins = {path: sha(ROOT / path) for path in previous['files']}
request = ('\n'.join(anchor + ':' + path for path in pins) + '\n').encode()
bodies = subprocess.check_output(['git', 'cat-file', '--batch'], input=request)
offset = 0
for path, digest in pins.items():
    end = bodies.index(b'\n', offset)
    header = bodies[offset:end].split()
    assert header[1] == b'blob'
    size = int(header[2]); offset = end + 1
    assert hashlib.sha256(bodies[offset:offset + size]).hexdigest() == digest
    offset += size + 1
assert offset == len(bodies)
changed = {path: {'before': previous['files'][path], 'after': digest}
           for path, digest in pins.items() if digest != previous['files'][path]}
assert set(changed) == {'tradingagents/research/onchain_replication/' + name
                       for name in ('matching_annealing.py', 'compact_mcm.py',
                                    'imported_authority_lease.py',
                                    'real_pilot_partial_progress.py')}
pair['numerical_source'] = {'commit': anchor, 'files': pins}
templates = HERE / 'templates01'
templates.mkdir()
save(templates / 'pair_policy01.json', pair)
for name in ('job_template01.json', 'pilot.json', 'archive_policy.json', 'producer_plan.json'):
    value = renamed(load(OLD / 'templates02' / name))
    if name == 'job_template01.json':
        next(iter(value['payload']['representation_jobs'].values()))['descriptor']['pair_execution']['policy_sha256'] = sha(templates / 'pair_policy01.json')
    if name == 'producer_plan.json':
        for producer in value['producers'].values():
            producer['descriptor']['pair_execution']['policy_sha256'] = sha(templates / 'pair_policy01.json')
    save(templates / name, value)
draft = load(OLD / 'INPUT_DRAFT02.json')
for role, name in (('pair_policy', 'pair_policy01.json'), ('execution_job', 'job_template01.json'),
                   ('pilot', 'pilot.json'), ('archive_policy', 'archive_policy.json'),
                   ('producer_plan', 'producer_plan.json')):
    draft['protocol']['references'][role] = ref(templates / name)
from tradingagents.research.onchain_replication.real_pilot_storage import WritableUnion
resources = load(templates / 'job_template01.json')['resources']
observation = WritableUnion(resources['storage_budget'], ROOT, experiment=NAME).check()
save(HERE / 'BASELINE01.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'result': {'observation': observation},
    'qualification': 'Fresh sampled metadata baseline only; neither release nor whole-pilot capacity.'})
draft['protocol']['physical_baseline'] = {'evidence': ref(HERE / 'BASELINE01.json'),
    'logical_bytes': observation['logical_file_bytes'], 'allocated_bytes': observation['allocated_bytes'],
    'entries': observation['entries']}
draft['protocol']['transport_limits']['namespace'] = NAMESPACE
save(HERE / 'INPUT_DRAFT01.json', draft)
helper = F / 'real-data-pilot-storage-metadata-binding01-2026-10-08/successor04.py'
assert sha(helper) == '0ca47a98e80cae9441c3718cdff8b5b5436ab5ab1036734c830e094c77d2dfe5'
module = types.ModuleType(helper.stem)
module.__file__ = str(helper)
exec(compile(helper.read_bytes(), str(helper), 'exec'), vars(module))
prepared = module.prepare(ROOT, draft, experiment=NAME)
save(HERE / 'PREPARATION_RESULT01.json', prepared)
save(HERE / 'PREPARATION_EXIT01.json', {
    'status': 'DRAFT_NOT_REGISTERED_NOT_ADMITTED', 'identity': NAME,
    'source_anchor': anchor, 'numerical_source_pins': len(pins),
    'changed_source_pins': changed, 'incremental_explicit_annealing_scratch_bytes': 262144,
    'scratch_registration_complete': False,
    'qualification': 'Four reviewed source changes only. Original matching/model/training, source graphs, order, 1024 diagnostic stop and native limits unchanged. Next cumulative allowance and exact entry release still required; no complete-MCM or training credit.',
    'claim': False, 'reservation': False, 'launch': False})
print(json.dumps({'status': prepared['status'], 'identity': NAME, 'anchor': anchor,
                  'source_pins': len(pins), 'changed_sources': len(changed),
                  'claim': False, 'launch': False}))
