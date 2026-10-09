"""One full-pilot allowance proposal; metadata only, never admission or launch."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'real-data-pilot-retry23-registration01-2026-10-09'
PREVIOUS = 'eth-paper-real-data-end-to-end-resource-20261009-23'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-24'


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


assert ROOT == Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
assert not (ROOT / 'research_runs' / NAME).exists()
assert not (ROOT / 'research_artifacts/archive-dispatch-ethpilot-20261009-24').exists()
prior = load(OLD / 'EXTENSION_PROPOSED94_01.json')
allocation = copy.deepcopy(load(OLD / 'CUMULATIVE_ALLOCATION_PROPOSED94_01.json'))
assert allocation['closed_claims'] == prior['claims']
assert prior['consumed_before'] == 62
assert len(prior['claims']) + prior['base_family']['prior_attempts'] == 62
run = ROOT / 'research_runs' / PREVIOUS
claim, terminal = load(run / 'claim.json'), load(run / 'failed.json')
assert claim['experiment_id'] == terminal['experiment_id'] == PREVIOUS
assert claim['program_id'] == prior['program_id']
assert claim['effective_attempt_budget'] == prior['cumulative_ceiling'] == 94
assert terminal['status'] == 'failed'
closed = prior['claims'] + [{'experiment': PREVIOUS,
    'claim_sha256': sha(run / 'claim.json'),
    'terminal_sha256': sha(run / 'failed.json'), 'terminal_status': 'failed'}]
assert len(closed) + prior['base_family']['prior_attempts'] == 63
for row in closed:
    owned = ROOT / 'research_runs' / row['experiment']
    assert sha(owned / 'claim.json') == row['claim_sha256']
    assert sha(owned / (row['terminal_status'] + '.json')) == row['terminal_sha256']
    assert load(owned / 'claim.json')['program_id'] == prior['program_id']
    assert load(owned / (row['terminal_status'] + '.json'))['status'] == row['terminal_status']
# Check actual receipt namespace, rather than relying only on the saved list.
actual = set()
for path in (ROOT / 'research_runs').glob('*/claim.json'):
    body = load(path)
    if body.get('family', {}).get('mechanism_id') == prior['base_family']['mechanism_id']:
        actual.add(body['experiment_id'])
assert actual == {row['experiment'] for row in closed}, (actual, closed)
assert sum(allocation['unchanged_pending_allocation'].values()) == 28
assert len(allocation['preserved_reserved_preclaim_allowances']) == 3
question = ('Measure the integrated schema6 full seven-original-graph MCM '
    'generation and original GAT/attention-LSTM joint update, including '
    'throughput, memory, local/external storage and training time. No prefix stop.')
qualification = ('One fresh fixed full resource pilot, not a financial fit or '
    'confirmation. All 415968128 cells, original32 motifs/512 spent samples, '
    'matching/model/training settings and native limits remain. Grouped storage '
    'and exact-input result reuse are explicit operational changes. Source '
    'reviews do not prove real speedup, whole capacity or external recovery. '
    'This proposal requires independent review and committed exact entry before '
    'execution; no refund, transfer, old identity reopening or cap ladder.')
allocation.update({
    'closed_claims': closed, 'consumed_before': 63,
    'prior_adopted_cumulative_ceiling': 94, 'prior_reviewed_reserved_ceiling': 94,
    'proposed_cumulative_ceiling': 95, 'identities': [NAME],
    'new_fixed_allocation': {'full_seven_graph_joint_update_resource_pilot_claims': 1},
    'equation': ('95 = 63 permanently spent attempts (17 historical plus46 '
                 'actual closed receipts) +28 unchanged pending +3 closed '
                 'preclaim reserved allowances +1 fresh fixed full resource pilot'),
    'question': question, 'qualification': qualification})
destination = HERE / 'CUMULATIVE_ALLOCATION_PROPOSED95_01.json'
save(destination, allocation)
prior.update({'claims': closed, 'consumed_before': 63, 'cumulative_ceiling': 95,
    'initial_experiment': NAME,
    'allocation': {'path': str(destination.relative_to(ROOT)), 'sha256': sha(destination)},
    'reason': question + ' ' + qualification})
save(HERE / 'EXTENSION_PROPOSED95_01.json', prior)
save(HERE / 'ACCOUNTING_CHECK01.json', {
    'status': 'PROPOSED_NOT_REVIEWED_NOT_ADOPTED', 'actual_closed_receipts': len(actual),
    'historical_prior_attempts': prior['base_family']['prior_attempts'],
    'spent': 63, 'pending': 28, 'closed_preclaim_reserved': 3,
    'fresh': 1, 'ceiling': 95, 'claim': False, 'launch': False})
print(json.dumps({'status': 'PROPOSED_NOT_REVIEWED_NOT_ADOPTED',
    'spent': 63, 'ceiling': 95, 'claim': False, 'launch': False}))
