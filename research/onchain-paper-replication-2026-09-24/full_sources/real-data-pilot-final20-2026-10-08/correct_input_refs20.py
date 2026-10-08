"""Correct two stale policy refs in the unused draft; preserve draft01."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NAME = 'eth-paper-real-data-end-to-end-resource-20261008-20'


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    body = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))


def save(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def main():
    oldgate = load(HERE / 'gate01.json'); gate = copy.deepcopy(oldgate)
    experiment = gate['experiments'][NAME]
    draft = load(HERE / 'INPUT_DRAFT02.json')
    refs = copy.deepcopy(experiment['inputs'])
    bound_roles = set(load(HERE / 'INPUT_REFS05.json'))
    changes = {}
    for role, value in draft['protocol']['references'].items():
        if role in refs and role not in bound_roles:
            selected = dict(dataset='eth', **{k: value[k] for k in ('path', 'sha256')})
            if refs[role] != selected:
                changes[role] = dict(before=refs[role], after=selected)
                refs[role] = selected
    assert set(changes) == {'compact_policy', 'mcm_policy'}
    preflight = (HERE / 'preflight01.py').read_text()
    assert preflight.count("GATE=str((HERE/'gate01.json').relative_to(ROOT))") == 1
    preflight = preflight.replace("GATE=str((HERE/'gate01.json').relative_to(ROOT))", "GATE=str((HERE/'gate02.json').relative_to(ROOT))")
    assert preflight.count("file_hash(HERE/'gate01.json')") == 1
    preflight = preflight.replace("file_hash(HERE/'gate01.json')", "file_hash(HERE/'gate02.json')")
    with (HERE / 'preflight02.py').open('x') as stream: stream.write(preflight)
    rootio = (HERE / 'root_io.py').read_text()
    assert rootio.count('from preflight01 import check') == 1
    with (HERE / 'root_io02.py').open('x') as stream: stream.write(rootio.replace('from preflight01 import check', 'from preflight02 import check'))
    files = experiment['source_files']
    for before, after in [('preflight01.py', 'preflight02.py'), ('root_io.py', 'root_io02.py')]:
        del files[str((HERE / before).relative_to(ROOT))]
        files[str((HERE / after).relative_to(ROOT))] = ref(HERE / after)['sha256']
    files[str(Path(__file__).relative_to(ROOT))] = ref(Path(__file__))['sha256']
    experiment['inputs'] = refs
    assert all(gate['experiments'][k] == v for k, v in oldgate['experiments'].items() if k != NAME)
    assert gate['families'] == oldgate['families']
    save(HERE / 'gate02.json', gate); save(HERE / 'ALL_INPUT_REFS06.json', refs)
    binding = load(HERE / 'BINDING_DRAFT01.json'); binding['gate'] = ref(HERE / 'gate02.json')
    save(HERE / 'BINDING_DRAFT02.json', binding)
    save(HERE / 'INPUT_REFERENCE_CORRECTION01.json', dict(status='CORRECTED_DRAFT_NOT_ADMITTED',
         original_gate=ref(HERE / 'gate01.json'), corrected_gate=ref(HERE / 'gate02.json'), changes=changes,
         qualification='Only compact/MCM runtime policy references and active entry source paths changed. Original metadata refusal preserved; no empirical start or claim.'))
    print(json.dumps(dict(status='CORRECTED_DRAFT_NOT_ADMITTED', changed_input_roles=sorted(changes), source_pins=len(files))))


if __name__ == '__main__':
    main()
