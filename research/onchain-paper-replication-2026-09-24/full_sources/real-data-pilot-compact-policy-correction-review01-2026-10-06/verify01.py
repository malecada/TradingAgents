"""Independent bounded source/metadata review. No authority, numerical or network imports."""
import ast
import copy
import difflib
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FS = HERE.parent
PROGRAM = ROOT / 'research/onchain-paper-replication-2026-09-24'
CAND = FS / 'real-data-pilot-compact-policy-correction01-2026-10-06'
REG = FS / 'real-data-pilot-resource-correction-registration01-2026-10-06'
FINAL = FS / 'real-data-pilot-final01-2026-10-06'
observed = {}

def body(path):
    assert path.is_file() and not path.is_symlink()
    data = path.read_bytes()
    assert len(data) < 4 * 1024**2
    observed[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return data

def read(path):
    return json.loads(body(path))

def pin(path, expected):
    data = body(path)
    assert hashlib.sha256(data).hexdigest() == expected
    return data

def diff(a, b, path=''):
    if type(a) is not type(b):
        return [path]
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        return sum((diff(a[k], b[k], path + '/' + k) for k in a), [])
    if isinstance(a, list):
        assert len(a) == len(b), path
        return sum((diff(x, y, path + '/' + str(i)) for i, (x, y) in enumerate(zip(a, b))), [])
    return [] if a == b else [path]

def main():
    manifest = read(CAND / 'MANIFEST01.json')
    for name, ref in manifest['files'].items():
        assert len(pin(CAND / name, ref['sha256'])) == ref['bytes']
    change = read(CAND / 'SOURCE_CHANGE01.json')
    old = pin(ROOT / change['target'], change['before_sha256']).decode()
    new = pin(CAND / 'candidate/build_inputs03.py', change['candidate_sha256']).decode()
    addition = "    selected['descriptor']['compact_execution']={'backend':compact['backend'],'policy_sha256':refs[spec['template_roles']['compact']]['sha256']}\n"
    assert new.count(addition) == 1 and new.replace(addition, '') == old
    patch = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=change['target'], tofile=change['target']))
    inverse_patch = ''.join(difflib.unified_diff(new.splitlines(True), old.splitlines(True), fromfile=change['target'], tofile=change['target']))
    assert body(CAND / 'candidate.patch').decode() == patch
    assert body(CAND / 'inverse.patch').decode() == inverse_patch

    # Execute the already-inspected focused stdlib proof once; never its writer.
    spec = importlib.util.spec_from_file_location('reviewed_metadata_check', CAND / 'check01.py')
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    check_result, _, _ = check.run()
    assert len(check_result['negative_refusals']) == 8

    # Reconstruct the actual runtime predicate from source, avoiding package imports.
    runtime = body(ROOT / 'tradingagents/research/onchain_replication/original_import_stage.py').decode()
    predicates = [n for n in ast.walk(ast.parse(runtime)) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Name) and n.func.id == 'require'
                  and len(n.args) == 2 and isinstance(n.args[1], ast.Constant)
                  and n.args[1].value == 'compact owner policy descriptor differs']
    assert len(predicates) == 1
    predicate = compile(ast.Expression(predicates[0].args[0]), '<actual attach predicate>', 'eval')
    backend_tree = ast.parse(body(ROOT / 'tradingagents/research/onchain_replication/compact_policy.py'))
    backend = next(ast.literal_eval(n.value) for n in backend_tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'BACKEND' for t in n.targets))
    refs = read(FINAL / 'INPUT_REFS02.json')
    claim = read(ROOT / 'research_runs/eth-paper-real-data-end-to-end-resource-20261005-01/claim.json')
    assert claim['inputs']['compact_policy']['sha256'] == refs['compact_policy']['sha256']
    run = SimpleNamespace(admission=SimpleNamespace(inputs=claim['inputs']))
    deltas = {}
    for role in ('execution_job', 'producer_plan'):
        historical = json.loads(pin(ROOT / refs[role]['path'], refs[role]['sha256']))
        corrected = read(CAND / 'metadata_candidate01' / (role + '.json'))
        if role == 'execution_job':
            select = lambda x: next(iter(x['payload']['representation_jobs'].values()))['descriptor']
        else:
            select = lambda x: next(iter(x['producers'].values()))['descriptor']
        namespace = dict(run=run, policy_input='compact_policy', compact_policy=SimpleNamespace(BACKEND=backend))
        assert not eval(predicate, namespace | {'descriptor': select(historical)})
        assert eval(predicate, namespace | {'descriptor': select(corrected)})
        deltas[role] = diff(historical, corrected)
        assert len(deltas[role]) == 1 and deltas[role][0].endswith('/descriptor/compact_execution/policy_sha256')
        restored = copy.deepcopy(corrected)
        select(restored)['compact_execution'] = select(historical)['compact_execution']
        assert restored == historical
        assert check.b.raw(restored) == body(ROOT / refs[role]['path'])
    for role in ('model', 'training'):
        pin(ROOT / claim['inputs'][role]['path'], claim['inputs'][role]['sha256'])
    pin(ROOT / claim['registration'], claim['registration_sha256'])

    # Actual claim population, not the proposal's count or list as authority.
    extension = read(REG / 'EXTENSION_PROPOSED73_01.json')
    allocation = read(REG / 'CUMULATIVE_ALLOCATION_PROPOSED73_01.json')
    pin(ROOT / extension['allocation']['path'], extension['allocation']['sha256'])
    actual = []
    ceilings = []
    for path in sorted((ROOT / 'research_runs').glob('*/claim.json')):
        # This shallow scan reads public claim metadata only, no run outputs.
        assert path.stat().st_size < 4 * 1024**2
        value = json.loads(path.read_bytes())
        if value.get('program_id') != 'onchain-paper-replication-2026-09-24':
            continue
        assert value['family'] == extension['base_family']
        assert value['experiment']['family'] == 'paper'
        raw = body(path)
        terminals = [path.parent / (name + '.json') for name in ('complete', 'failed') if (path.parent / (name + '.json')).is_file()]
        assert len(terminals) == 1, path
        terminal = read(terminals[0])
        sha = hashlib.sha256(raw).hexdigest()
        assert terminal['claim_sha256'] == sha
        assert terminal['status'] == terminals[0].stem
        actual.append({'experiment': value['experiment_id'], 'claim_sha256': sha,
                       'terminal_sha256': observed[str(terminals[0].relative_to(ROOT))], 'terminal_status': terminal['status']})
        ceilings.append(value.get('effective_attempt_budget', value['family']['attempt_budget']))
    actual.sort(key=lambda x: x['experiment'])
    assert actual == extension['claims'] == allocation['closed_claims']
    counts = Counter(x['terminal_status'] for x in actual)
    assert counts == {'complete': 20, 'failed': 7} and max(ceilings) == 72
    history = read(PROGRAM / 'history.json')
    prior_counts = Counter()
    for path, sha in history['metadata_hashes'].items():
        pin(ROOT / path, sha)
        if Path(path).stem in ('complete', 'failed'):
            prior_counts[Path(path).stem] += 1
    assert prior_counts == {'complete': 13, 'failed': 4}
    assert len(history['lineage']) == len(set(history['lineage'])) == 17
    assert not set(history['lineage']) & {x['experiment'] for x in actual}
    oldext_path = ROOT / claim['experiment']['cumulative_budget_extension']['extension']['path']
    oldext = json.loads(pin(oldext_path, claim['experiment']['cumulative_budget_extension']['extension']['sha256']))
    oldreview_ref = claim['experiment']['cumulative_budget_extension']['review']
    oldreview = json.loads(pin(ROOT / oldreview_ref['path'], oldreview_ref['sha256']))
    assert oldreview['decision'] == 'accepted' and oldreview['extension_sha256'] == hashlib.sha256(body(oldext_path)).hexdigest()
    oldallocation = json.loads(pin(ROOT / oldext['allocation']['path'], oldext['allocation']['sha256']))
    remaining = dict(oldallocation['unchanged_pending_allocation'])
    assert remaining.pop('real_pilot_end_to_end_resource_claims') == 1
    assert remaining.pop('unused_original_june6_full_graph') == 1
    assert remaining == allocation['unchanged_pending_allocation']
    new_claims = {x['experiment'] for x in actual} - {x['experiment'] for x in oldext['claims']}
    assert new_claims == {'eth-paper-real-data-end-to-end-resource-20261005-01', 'eth-paper-real-pilot-graph-20220606-20261005-01', 'eth-paper-real-pilot-may30-ledger-continuation-20261006-01'}
    assert allocation['consumed_before'] == extension['consumed_before'] == 27 + 17 == 44
    assert allocation['prior_adopted_cumulative_ceiling'] == oldext['cumulative_ceiling'] == 72
    assert sum(remaining.values()) == 28
    assert allocation['proposed_cumulative_ceiling'] == extension['cumulative_ceiling'] == 44 + 28 + 1 == 73
    identity = 'eth-paper-real-data-end-to-end-resource-20261006-02'
    assert allocation['identities'] == [identity] and extension['initial_experiment'] == identity
    assert not (ROOT / 'research_runs' / identity).exists()
    assert allocation['new_fixed_allocation'] == {'exact_compact_policy_binding_correction_resource_pilot_claims': 1}
    for key in ('new_financial_fits', 'refunds', 'category_transfers', 'historical_claims_reopened'):
        assert allocation[key] == 0
    assert allocation['maximum_unique_financial_fits_unchanged'] == oldallocation['maximum_unique_financial_fits_unchanged'] == 1420
    terminal = read(ROOT / 'research_runs/eth-paper-real-data-end-to-end-resource-20261005-01/failed.json')
    assert terminal['reason'] == 'ValueError: compact owner policy descriptor differs'
    root_terminal = read(FINAL / 'ROOT_TERMINAL01.json')
    assert root_terminal['actual_native']['child_exit_code'] == root_terminal['root_actual_exit']['exit_code'] == 1
    assert root_terminal['actual_native']['cleanup_verified'] is True
    assert root_terminal['actual_native']['elapsed_seconds'] == 434.466017962
    assert not any(name in sys.modules for name in ('numpy', 'torch', 'scipy', 'tradingagents'))
    return {'status': 'PASS', 'candidate_manifest_sha256': observed[str((CAND / 'MANIFEST01.json').relative_to(ROOT))],
            'source_exact_one_line_inverse': True, 'actual_runtime_predicate_old_false_new_true_both_descriptors': True,
            'output_deltas': deltas, 'focused_check': check_result,
            'current_claims': dict(counts), 'prior_claims': dict(prior_counts),
            'highest_adopted_ceiling': max(ceilings), 'spent': 44, 'unchanged_pending': 28,
            'new_correction_allowance': 1, 'proposed_ceiling': 73, 'unused_identity': identity,
            'original_terminal_preserved': True, 'extension_sha256': observed[str((REG / 'EXTENSION_PROPOSED73_01.json').relative_to(ROOT))],
            'observed_metadata_sha256': observed,
            'qualification': 'Source and metadata proposal review only; no installation, adoption, claim, numerical/native run, full capacity result or successor entry release.'}

if __name__ == '__main__':
    result = main()
    (HERE / 'CHECK01.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'observed_metadata_sha256'}, indent=2))
