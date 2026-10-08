"""Assemble the fixed original-order diagnostic gate; never admit or claim."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = F / 'real-data-pilot-final19-2026-10-08'
HELP = F / 'real-data-pilot-fixed20-metadata-successor01-2026-10-08'
BUDGET = F / 'real-data-pilot-retry20-registration01-2026-10-08'
NAME = 'eth-paper-real-data-end-to-end-resource-20261008-20'
OLDNAME = 'eth-paper-real-data-end-to-end-resource-20261008-19'


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    body = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))


def save(path, value):
    with path.open('xb') as out:
        out.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def main():
    oldgate = load(OLD / 'gate01.json'); gate = copy.deepcopy(oldgate)
    experiment = copy.deepcopy(oldgate['experiments'][OLDNAME])
    # Reuse the exact reviewed entry, changing only the fixed identity, helper
    # closure and already reviewed cumulative allowance. No new framework.
    preflight = (OLD / 'preflight01.py').read_text()
    oldsuccessor = F / 'real-data-pilot-fixed19-metadata-successor01-2026-10-08/successor02.py'
    before = repr({k: ref(oldsuccessor)[k] for k in ('path', 'sha256')})
    after = repr({k: ref(HELP / 'successor04.py')[k] for k in ('path', 'sha256')})
    assert preflight.count(before) == 1
    preflight = preflight.replace(before, after).replace(OLDNAME, NAME)
    assert preflight.count("dependencies=path.with_name('DEPENDENCIES02.json')") == 1
    preflight = preflight.replace("dependencies=path.with_name('DEPENDENCIES02.json')", "dependencies=path.with_name('DEPENDENCIES04.json')")
    assert preflight.count('effective_attempt_budget!=90') == 1
    assert preflight.count("'effective_attempt_budget':90") == 1
    preflight = preflight.replace('effective_attempt_budget!=90', 'effective_attempt_budget!=91').replace("'effective_attempt_budget':90", "'effective_attempt_budget':91")
    with (HERE / 'preflight01.py').open('x') as out: out.write(preflight)
    with (HERE / 'root_io.py').open('x') as out: out.write((OLD / 'root_io.py').read_text().replace(OLDNAME, NAME))

    # Historical source bodies stay preserved; the new active helpers have
    # their own exact closure, including the newly required kernel and module.
    source_paths = set(experiment['source_files'])
    source_paths.difference_update(str((OLD / x).relative_to(ROOT)) for x in ('preflight01.py', 'root_io.py'))
    source_paths.update(str((HERE / x).relative_to(ROOT)) for x in ('preflight01.py', 'root_io.py', 'register20.py', 'bind20.py'))
    source_paths.update(str(p.relative_to(ROOT)) for p in (ROOT / 'tradingagents/research/onchain_replication').glob('*.py'))
    source_paths.update(str(p.relative_to(ROOT)) for p in (HELP / 'successor04.py', HELP / 'DEPENDENCIES04.json'))
    source_paths.update(v['path'] for v in load(HELP / 'DEPENDENCIES04.json').values())
    source_paths.add(str((F / 'real-data-pilot-capacity-selection02-2026-10-08/imported_kernel.py').relative_to(ROOT)))
    reviews = {
        'source_adoption_review': F / 'real-data-pilot-diagnostic-source-adoption01-2026-10-08/SOURCE_ADOPTION01.json',
        'diagnostic_source_review': F / 'real-data-pilot-diagnostic-source-review01-2026-10-08/MANIFEST01.json',
        'selected_input_review': F / 'real-data-pilot-selected-input-control-review01-2026-10-08/MANIFEST01.json',
        'metadata_source_review': F / 'real-data-pilot-residual-metadata-review01-2026-10-08/prefix-review04/MANIFEST04.json',
        'capacity_budget_review': F / 'real-data-pilot-capacity-budget-review01-2026-10-08/MANIFEST01.json',
    }
    allowance_review = F / 'real-data-pilot-capacity-budget-review01-2026-10-08/EXTENSION91_REVIEW01.json'
    source_paths.update(str(p.relative_to(ROOT)) for p in reviews.values())
    source_paths.update(str(p.relative_to(ROOT)) for p in (BUDGET / 'EXTENSION_PROPOSED91_01.json', BUDGET / 'CUMULATIVE_ALLOCATION_PROPOSED91_01.json', allowance_review))
    experiment['source_files'] = {p: ref(ROOT / p)['sha256'] for p in sorted(source_paths)}
    refs = copy.deepcopy(experiment['inputs'])
    for role, value in load(HERE / 'INPUT_REFS05.json').items():
        refs[role] = dict(dataset='eth', **{k: value[k] for k in ('path', 'sha256')})
    refs['pair_policy'] = dict(dataset='eth', **{k: ref(HERE / 'templates02/pair_policy01.json')[k] for k in ('path', 'sha256')})
    experiment['inputs'] = refs
    experiment['charter'] = {k: ref(HERE / 'CHARTER01.md')[k] for k in ('path', 'sha256')}
    experiment['cumulative_budget_extension'] = {
        'extension': {k: ref(BUDGET / 'EXTENSION_PROPOSED91_01.json')[k] for k in ('path', 'sha256')},
        'review': {k: ref(allowance_review)[k] for k in ('path', 'sha256')},
    }
    pilot = load(HERE / 'inputs05/pilot.json')
    experiment['cells'] = [pilot['cell_id']]
    experiment['outputs'] = experiment['outputs'] + [pilot['outputs']['diagnostic']]
    assert len(experiment['outputs']) == len(set(experiment['outputs']))
    experiment['question'] = 'Measure 1024 original-order real Ethereum motif comparisons with reviewed scoring and persistence corrections; intentional incomplete FAILED stop, no MCM/neural/fit completion. Full seven-graph MCM and joint GAT/attention LSTM pilot remain pending.'
    gate['experiments'][NAME] = experiment
    assert experiment['parent'] is None and gate['families'] == oldgate['families']
    assert all(gate['experiments'][k] == v for k, v in oldgate['experiments'].items())
    save(HERE / 'gate01.json', gate); save(HERE / 'ALL_INPUT_REFS05.json', refs)

    binding = load(OLD / 'BINDING_DRAFT01.json')
    for role, name in [('gate', 'gate01.json'), ('draft', 'INPUT_DRAFT02.json'), ('preparation', 'PREPARATION_RESULT05.json'), ('baseline', 'BASELINE02.json'), ('transport_binding', 'TRANSPORT_BINDING05.json')]:
        binding[role] = ref(HERE / name)
    binding.update({role: ref(path) for role, path in reviews.items()})
    binding['transport'] = load(HERE / 'INPUT_REFS05.json')['archive_transport']
    binding['identity'] = NAME
    outcome = F / 'real-data-pilot-nineteenth-outcome-review01-2026-10-08'
    binding['prior_outcome_review'] = ref(outcome / 'OUTCOME_REVIEW01.json')
    binding['prior_preservation_complete'] = ref(F / 'real-data-pilot-nineteenth-failed-increment01-2026-10-08/FRESH_GIT_RECOVERY01.json')
    binding['prior_recovery_review'] = ref(outcome / 'returned-git-recovery01/RECOVERY_REVIEW01.json')
    binding['binding_review'] = None; binding['status'] = 'DRAFT_NOT_RELEASED'
    save(HERE / 'BINDING_DRAFT01.json', binding)
    save(HERE / 'REGISTRATION_EXIT01.json', dict(status='EXACT_GATE_DRAFT_NOT_ADMITTED', identity=NAME,
         source_pins=len(source_paths), inputs=len(refs), old_experiments_unchanged=len(oldgate['experiments']),
         proposed_allowance=91, scientific_execution=False, claim=False))
    print(json.dumps(dict(status='EXACT_GATE_DRAFT_NOT_ADMITTED', source_pins=len(source_paths), inputs=len(refs))))


if __name__ == '__main__':
    main()
