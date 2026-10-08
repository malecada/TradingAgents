"""Propagate reviewed header-derived memory declarations before any reservation."""
import copy
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
F = HERE.parent
NAME = 'eth-paper-real-data-end-to-end-resource-20261008-20'


def module(path):
    value = types.ModuleType(path.stem); value.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), vars(value))
    return value


def main():
    base = module(HERE / 'bind20.py'); load, ref, save = base.load, base.ref, base.save
    assert not (HERE / 'launch-attempt01.json').exists()
    assert not (ROOT / 'research_runs' / NAME).exists()
    helper = F / 'real-data-pilot-index-capacity02-2026-10-08/candidate/index_capacity.py'
    source_review = F / 'real-data-pilot-index-capacity02-review01-2026-10-08/SOURCE_REVIEW01.json'
    assert ref(source_review)['sha256'] == 'a4619e1ccdaa34834a257c5a69e778cf490f3a61c0b9f7b879cfc29125cb45b8'
    policy = F / 'real-data-pilot-capacity-selection04-2026-10-08/mcm_policy.json'
    draft = load(HERE / 'INPUT_DRAFT02.json')
    draft['protocol']['references']['mcm_policy'] = ref(policy)
    save(HERE / 'INPUT_DRAFT03.json', draft)
    prepared = module(F / 'real-data-pilot-fixed20-metadata-successor01-2026-10-08/successor04.py').prepare(ROOT, draft)
    assert prepared['inventory'] == load(HERE / 'PREPARATION_RESULT05.json')['inventory']
    save(HERE / 'PREPARATION_RESULT06.json', prepared)
    request = load(HERE / 'TRANSPORT_REQUEST05.json')
    request['prepared'] = ref(HERE / 'PREPARATION_RESULT06.json')
    parent = ROOT / 'research_artifacts/real_pilot_runtime/pilot-transport-20261008-20-02'
    parent.mkdir(mode=0o700)
    request['private_parent'] = str(parent.relative_to(ROOT))
    save(HERE / 'TRANSPORT_REQUEST06.json', request)
    binder = module(F / 'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py')
    bound = binder.bind(ROOT, request); save(HERE / 'TRANSPORT_BINDING06.json', bound)
    directory = HERE / 'inputs06'; directory.mkdir(); inputrefs = {}
    for role, value in bound['inputs'].items():
        target = directory / (role + '.json')
        with target.open('xb') as stream: stream.write(binder.raw(value))
        inputrefs[role] = ref(target)
    inputrefs.update(bound['private_input']); save(HERE / 'INPUT_REFS06.json', inputrefs)

    preflight = (HERE / 'preflight02.py').read_text()
    original_helper = F / 'real-data-pilot-index-capacity01-2026-10-07/candidate/index_capacity.py'
    before = repr({k: ref(original_helper)[k] for k in ('path', 'sha256')})
    after = repr({k: ref(helper)[k] for k in ('path', 'sha256')})
    assert preflight.count(before) == 1
    preflight = preflight.replace(before, after)
    for before, after, count in [('gate02.json', 'gate03.json', 2), ('BINDING01.json', 'BINDING02.json', 2), ('RELEASE_REVIEW01.json', 'RELEASE_REVIEW02.json', 1)]:
        assert preflight.count(before) == count, (before, preflight.count(before))
        preflight = preflight.replace(before, after)
    with (HERE / 'preflight03.py').open('x') as out: out.write(preflight)
    rootio = (HERE / 'root_io02.py').read_text()
    assert rootio.count('from preflight02 import check') == 1
    with (HERE / 'root_io03.py').open('x') as out: out.write(rootio.replace('from preflight02 import check', 'from preflight03 import check'))

    oldgate = load(HERE / 'gate02.json'); gate = copy.deepcopy(oldgate); experiment = gate['experiments'][NAME]
    for role, value in inputrefs.items():
        experiment['inputs'][role] = dict(dataset='eth', **{k: value[k] for k in ('path', 'sha256')})
    experiment['inputs']['mcm_policy'] = dict(dataset='eth', **{k: ref(policy)[k] for k in ('path', 'sha256')})
    files = experiment['source_files']
    for before, after in [('preflight02.py', 'preflight03.py'), ('root_io02.py', 'root_io03.py')]:
        del files[str((HERE / before).relative_to(ROOT))]
        files[str((HERE / after).relative_to(ROOT))] = ref(HERE / after)['sha256']
    del files[str(original_helper.relative_to(ROOT))]
    for path in (helper, source_review, Path(__file__)):
        files[str(path.relative_to(ROOT))] = ref(path)['sha256']
    assert gate['families'] == oldgate['families']
    assert all(gate['experiments'][k] == v for k, v in oldgate['experiments'].items() if k != NAME)
    save(HERE / 'gate03.json', gate); save(HERE / 'ALL_INPUT_REFS07.json', experiment['inputs'])
    binding = load(HERE / 'BINDING01.json')
    binding['gate'] = ref(HERE / 'gate03.json'); binding['draft'] = ref(HERE / 'INPUT_DRAFT03.json')
    binding['preparation'] = ref(HERE / 'PREPARATION_RESULT06.json'); binding['transport_binding'] = ref(HERE / 'TRANSPORT_BINDING06.json')
    binding['transport'] = inputrefs['archive_transport']; binding['index_capacity_source_review'] = ref(source_review)
    binding['binding_review'] = None; binding['status'] = 'DRAFT_NOT_RELEASED'
    save(HERE / 'BINDING_DRAFT03.json', binding)
    save(HERE / 'PREPARATION_EXIT06.json', dict(status='DRAFT_NOT_ADMITTED', storage_inventory_unchanged=True,
         claim=False, launch_reservation=False, source_pins=len(files), helper_review=ref(source_review)))
    print(json.dumps(dict(status='DRAFT_NOT_ADMITTED', storage_inventory_unchanged=True, source_pins=len(files))))


if __name__ == '__main__':
    main()
