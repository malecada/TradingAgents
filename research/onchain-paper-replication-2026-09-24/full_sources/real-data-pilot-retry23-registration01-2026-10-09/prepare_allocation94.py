"""One additive same-family proposal, retaining every prior spent allowance."""
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'real-data-pilot-retry22-registration01-2026-10-08'
PREVIOUS = 'eth-paper-real-data-end-to-end-resource-20261008-22'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-23'


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
prior = load(OLD / 'EXTENSION_PROPOSED93_01.json')
allocation = load(OLD / 'CUMULATIVE_ALLOCATION_PROPOSED93_01.json')
run = ROOT / 'research_runs' / PREVIOUS
claim = load(run / 'claim.json')
terminal = load(run / 'failed.json')
assert claim['experiment_id'] == terminal['experiment_id'] == PREVIOUS
assert claim['program_id'] == prior['program_id']
assert claim['effective_attempt_budget'] == prior['cumulative_ceiling'] == 93
assert terminal['status'] == 'failed'
assert allocation['closed_claims'] == prior['claims']
assert prior['consumed_before'] == allocation['consumed_before'] == 61
assert len(prior['claims']) + prior['base_family']['prior_attempts'] == 61
assert PREVIOUS not in {row['experiment'] for row in prior['claims']}
closed = prior['claims'] + [{'experiment': PREVIOUS,
    'claim_sha256': sha(run / 'claim.json'),
    'terminal_sha256': sha(run / 'failed.json'), 'terminal_status': 'failed'}]
assert len(closed) + prior['base_family']['prior_attempts'] == 62
assert sum(allocation['unchanged_pending_allocation'].values()) == 28
assert len(allocation['preserved_reserved_preclaim_allowances']) == 3
allocation.update({
    'closed_claims': closed, 'consumed_before': 62,
    'prior_adopted_cumulative_ceiling': 93, 'prior_reviewed_reserved_ceiling': 93,
    'proposed_cumulative_ceiling': 94, 'identities': [NAME],
    'equation': '94 = 62 genuine permanently spent claims + 28 unchanged pending + 3 closed preclaim03/08/18 reserved allowances + 1 fresh fixed23 changed-source scoring measurement',
    'question': 'Measure the fixed original-order1024 prefix after reviewed exact matching reuse, authority lookup and lease subphase instrumentation; no scientific protocol or resource cap change.',
    'qualification': 'Intermediate resource measurement only. Intentional planned stop remains FAILED with zero complete-MCM/neural/financial credit; all seven whole graphs and original32motifs/512samples retained. Existing exact source reviews are reused, changed source/input joins still require independent entry acceptance. This proposal grants neither execution nor capacity. Original lower-RAM policy and all previous limits remain fixed; no refund, transfer, sample renewal or historical identity reopening.'})
save(HERE / 'CUMULATIVE_ALLOCATION_PROPOSED94_01.json', allocation)
prior.update({'claims': closed, 'consumed_before': 62, 'cumulative_ceiling': 94,
    'initial_experiment': NAME,
    'allocation': {'path': str((HERE / 'CUMULATIVE_ALLOCATION_PROPOSED94_01.json').relative_to(ROOT)),
                   'sha256': sha(HERE / 'CUMULATIVE_ALLOCATION_PROPOSED94_01.json')},
    'reason': 'One finite fresh fixed1024 measurement of the four reviewed throughput/timing changes. Preserve62spent+28pending+3closedpreclaim allowances; unchanged native caps and original protocol. No refund/transfer/cap ladder/resampling/financial-fit credit; full seven-graph MCM/GAT/attentionLSTM goal remains unchanged.'})
save(HERE / 'EXTENSION_PROPOSED94_01.json', prior)
print(json.dumps({'status': 'PROPOSED_NOT_REVIEWED_NOT_ADOPTED', 'spent': 62,
    'pending': 28, 'closed_preclaim_reserved': 3, 'fresh': 1, 'ceiling': 94,
    'claim': False, 'launch': False}))
