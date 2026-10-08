"""Check the candidate with existing bounded public metadata; no run admission."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
F = HERE.parent
CANDIDATE = F/'real-data-pilot-storage-metadata-binding01-2026-10-08'
ENTRY = F/'real-data-pilot-final21-2026-10-08'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = set(sys.modules)
    manifest = json.loads((CANDIDATE/'MANIFEST.json').read_bytes())
    for name, expected in manifest['files'].items():
        if digest(CANDIDATE/name) != expected:
            raise ValueError('candidate changed: '+name)
    binding = json.loads((ENTRY/'BINDING01.json').read_bytes())
    bodies = {}
    for role in ('draft', 'preparation'):
        ref = binding[role]
        path = ROOT/ref['path']
        if path.stat().st_size > 4*1024**2 or digest(path) != ref['sha256']:
            raise ValueError('original bounded metadata changed: '+role)
        bodies[role] = json.loads(path.read_bytes())
    path = CANDIDATE/'successor04.py'
    spec = importlib.util.spec_from_file_location('source_only_metadata_binding_check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    start = time.monotonic()
    actual = module.prepare(ROOT, bodies['draft'])
    default_elapsed = time.monotonic()-start
    if actual != bodies['preparation']:
        raise ValueError('legacy default differs from actual saved seven-graph preparation')
    explicit = module.prepare(ROOT, bodies['draft'],
                              experiment='eth-paper-real-data-end-to-end-resource-20261008-21')
    if explicit != actual:
        raise ValueError('same explicit identity differs from legacy default')
    try:
        module.prepare(ROOT, bodies['draft'],
                       experiment='eth-paper-real-data-end-to-end-resource-20261008-22')
    except ValueError as error:
        refused = str(error)
    else:
        raise ValueError('different supplied identity accepted original21 budget')
    added = sorted(set(sys.modules)-before)
    prohibited = [name for name in added if name == 'numpy' or name.startswith(('numpy.', 'torch', 'tradingagents'))]
    if prohibited:
        raise ValueError('metadata check imported numerical/research package')
    receipt = {'status': 'ACTUAL_LEGACY_METADATA_PASS_NOT_ADMISSION',
               'source_sha256': digest(path), 'manifest_sha256': digest(CANDIDATE/'MANIFEST.json'),
               'draft_sha256': binding['draft']['sha256'],
               'saved_preparation_sha256': binding['preparation']['sha256'],
               'legacy_default_equals_actual_saved_preparation': True,
               'explicit21_equals_legacy_default': True,
               'explicit22_original21_budget_refusal': refused,
               'default_prepare_seconds': default_elapsed,
               'prohibited_new_imports': prohibited,
               'qualification': 'Actual existing seven-graph public metadata preparation only. No graph arrays, dictionary sampling, numerical imports, Admission, Binding, Owner, ResearchRun, new inputs or launch. Future22 templates and genuine admission are not established.'}
    target = HERE/'CHECK01.json'
    with target.open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
