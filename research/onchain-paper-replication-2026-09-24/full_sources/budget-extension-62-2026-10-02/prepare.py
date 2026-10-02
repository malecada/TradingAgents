"""Freeze exact prospective budget metadata; never admit, reserve or execute."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
STUDY = ROOT / 'research/onchain-paper-replication-2026-09-24'
INITIAL = 'eth-paper-neural-resource-20261002-01'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


original = STUDY / 'full_sources/neural-resource-registration-2026-10-02/extension.draft.json'
extension = read(original)
recount_path = STUDY / 'full_sources/budget-recount-2026-10-02/recount01.json'
recount = read(recount_path)
checked = []
for record in recount['claims']:
    claim_path, terminal_path = ROOT / record['claim'], ROOT / record['terminal']
    assert sha(claim_path) == record['claim_sha256']
    assert sha(terminal_path) == record['terminal_sha256']
    claim, terminal = read(claim_path), read(terminal_path)
    assert terminal['claim_sha256'] == record['claim_sha256']
    assert terminal['experiment_id'] == claim['experiment_id'] == record['experiment']
    assert terminal['status'] == record['status']
    checked.append({'experiment': record['experiment'], 'group': record['group'],
                    'claim': pin(claim_path), 'terminal': pin(terminal_path),
                    'status': record['status']})
assert len(checked) == 33 and len({r['experiment'] for r in checked}) == 33
assert sum(r['status'] == 'complete' for r in checked) == 27
assert sum(r['status'] == 'failed' for r in checked) == 6

# Match the live admission mechanism, inspecting claim metadata only.
relevant = []
for directory in sorted((ROOT / 'research_runs').iterdir()):
    path = directory / 'claim.json'
    if not path.is_file():
        continue
    claim = read(path)
    if claim['family']['mechanism_id'] == extension['base_family']['mechanism_id']:
        assert claim['family'] == extension['base_family']
        relevant.append(claim['experiment_id'])
assert set(relevant) == {r['experiment'] for r in extension['claims']}
assert len(relevant) == 16
absent = [ROOT / 'research_runs' / INITIAL,
          ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' / INITIAL,
          ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / INITIAL]
assert all(not p.exists() and not p.is_symlink() for p in absent)
split_path = STUDY / 'full_sources/neural-resource-readiness-2026-10-02/budget-split.draft.json'
split = read(split_path)
assert split['proposed_cumulative_ceiling'] == 62 == 33 + 12 + 15 + 2
assert split['maximum_unique_fits_unchanged'] == 1420
assert [s['requirement_count'] for s in split['claim_slots']] == [9, 23]
allocation = {
    'schema_version': 1,
    'status': 'frozen prospective allocation; no execution admission or namespace reservation',
    'execution_admitted': False,
    'original_family': extension['base_family'],
    'cumulative_ceiling': 62, 'consumed_before': 33,
    'pending_allocation': {'missing_body_batches': 12, 'financial_fit_batches': 15,
                           'neural_resource_only': 1, 'remaining_graph_matching_mcm_resource': 1},
    'initial_experiment': INITIAL,
    'neural_requirement_ids': [r['original_id'] for r in split['claim_slots'][0]['original_requirements']],
    'other_resource_requirement_ids': [r['original_id'] for r in split['claim_slots'][1]['original_requirements']],
    'reviewed_split': pin(split_path), 'prior_recount': pin(recount_path),
    'maximum_unique_fits_unchanged': 1420, 'new_financial_fits': 0,
    'refunds': 0, 'historical_claims_reopened': 0,
    'qualification': 'Two resource attempts are finite allocations, not a success guarantee. Failures consume claims. Any successor beyond this allocation requires new cumulative reconciliation and review. Exact source, scientific/resource gates and physical admission remain required.'}
save('allocation.json', allocation)
extension['initial_experiment'] = INITIAL
extension['allocation'] = pin(OUT / 'allocation.json')
save('extension.json', extension)
save('preparation01.json', {
    'schema_version': 1, 'execution_admitted': False, 'namespace_reserved': False,
    'initial_experiment': INITIAL, 'absent_namespaces': [str(p) for p in absent],
    'original_draft': pin(original), 'extension': pin(OUT / 'extension.json'),
    'all_33_claims_and_terminals_verified': checked,
    'live_same_mechanism_claims': relevant, 'consumed_before': 33,
    'cumulative_ceiling': 62, 'complete': 27, 'failed': 6,
    'array_bodies_read': False,
    'limitation': 'Metadata-only point-in-time reconciliation; repeat fresh admission before launch. No source/runtime/resource/financial admission, budget adoption or old outcome replay.'})
print('PASS:33 unchanged terminal claim/receipt bindings; exact16 live same-mechanism claims;62=33+12+15+2; initial identity absent at all3 namespaces; no reservation/admission/execution.')
