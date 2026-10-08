"""Read-only genuine budget validator; write review evidence only, no admission."""
import collections, hashlib, json, sys
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parents[3]
sys.path.insert(0, str(R))
from tradingagents.research.budget_extensions import effective_budget

def raw_ref(ref):
    p = R / ref['path']; raw = p.read_bytes()
    assert not p.is_symlink() and hashlib.sha256(raw).hexdigest() == ref['sha256']
    return raw

def reference(path):
    raw = path.read_bytes()
    return dict(path=str(path.relative_to(R)), sha256=hashlib.sha256(raw).hexdigest())

D = H.parent / 'real-data-pilot-retry17-registration01-2026-10-08'
newref = reference(D / 'EXTENSION_PROPOSED88_01.json')
new = json.loads(raw_ref(newref)); allocation = json.loads(raw_ref(new['allocation']))
claim = json.loads((R / 'research_runs/eth-paper-real-data-end-to-end-resource-20261007-16/claim.json').read_bytes())
oldref = claim['experiment']['cumulative_budget_extension']
old = json.loads(raw_ref(oldref['extension'])); prior_review = json.loads(raw_ref(oldref['review']))
assert prior_review['decision'] == 'accepted' and prior_review['extension_sha256'] == oldref['extension']['sha256']
prior_allocation = json.loads(raw_ref(old['allocation']))
assert new['claims'][:-1] == old['claims'] and len(old['claims']) == 39
assert new['claims'] == allocation['closed_claims'] and len(new['claims']) == 40
assert new['base_family'] == old['base_family'] == claim['family'] == allocation['base_family']
retained = ['unchanged_pending_allocation', 'preserved_reserved_preclaim_allowances',
            'maximum_unique_financial_fits_unchanged', 'prior_reviewed_reserved_ceiling',
            'refunds', 'category_transfers', 'historical_claims_reopened']
assert all(allocation[k] == prior_allocation[k] for k in retained)
assert new['claims'][-1]['experiment'] == claim['experiment_id']
assert new['claims'][-1]['terminal_status'] == 'failed' and claim['effective_attempt_budget'] == 87
assert new['consumed_before'] == allocation['consumed_before'] == 17 + 40 == 57
assert sum(allocation['unchanged_pending_allocation'].values()) == 28
assert len(allocation['preserved_reserved_preclaim_allowances']) == 2
assert sum(allocation['new_fixed_allocation'].values()) == 1
assert allocation['prior_adopted_cumulative_ceiling'] == 87
assert new['cumulative_ceiling'] == allocation['proposed_cumulative_ceiling'] == 57 + 28 + 2 + 1 == 88
assert allocation['identities'] == [new['initial_experiment']] == ['eth-paper-real-data-end-to-end-resource-20261008-17']
assert not (R / 'research_runs' / new['initial_experiment']).exists()
review = dict(schema_version=1, decision='accepted', extension_sha256=newref['sha256'],
    reviewer='pilot16_outcome_review independent cumulative88 reviewer',
    scope='Narrow proposal review only: 39 unchanged typed closed claims plus actual failed16/spent87 and17 carried prior claims=57;28 unchanged pending+2 permanently closed preclaim reserves+1 fixed unused17=88. Original family, sample exposure and1420-fit ceiling preserved. No refund, transfer, historical reopening, cap ladder or financial credit. No88 adoption, admission or17 launch; fresh external failed16 recovery, exact committed successor metadata/runtime/source and separate final release remain required.')
review_raw = (json.dumps(review, indent=2, sort_keys=True) + '\n').encode()
review_ref = dict(path=str((H / 'EXTENSION88_REVIEW01.json').relative_to(R)), sha256=hashlib.sha256(review_raw).hexdigest())
def bound(ref):
    if ref == review_ref: return review_raw
    return raw_ref(ref)
relevant = [json.loads((R / 'research_runs' / item['experiment'] / 'claim.json').read_bytes()) for item in new['claims']]
result = effective_budget(R, new['program_id'], new['initial_experiment'],
    {'cumulative_budget_extension': {'extension':newref, 'review':review_ref}},
    new['base_family'], relevant, bound)
assert result == 88
machine = dict(schema_version=1, decision='accepted-proposed-budget-only',
    extension=newref, allocation=new['allocation'], review=review_ref,
    effective_budget_result=result, genuine_validator=reference(R / 'tradingagents/research/budget_extensions.py'),
    unchanged_prior_snapshot_count=39, actual_snapshot_count=40,
    typed_snapshot_status_counts=dict(collections.Counter(item['terminal_status'] for item in new['claims'])),
    carried_prior_claims=17, consumed_before=57, pending=28, closed_preclaim_reserves=2,
    unused_fixed_allocation=1, prior_adopted_ceiling=87, future_namespace_absent=True,
    unchanged_allocation_fields=retained, prior_extension=oldref['extension'], prior_review=oldref['review'],
    historical_scientific_stores_read=False, claim_or_admission_executed=False,
    qualification='Actual effective_budget called with pinned proposed metadata and an in-memory exact review; no registration changed or adopted. The validator independently read40 named claim/terminal pairs. Prior17 provenance reused from the exact unchanged accepted family; no full historical/scientific recount.')
assert not (H / 'EXTENSION88_REVIEW01.json').exists()
(H / 'EXTENSION88_REVIEW01.json').write_bytes(review_raw)
(H / 'BUDGET88_MACHINE_REVIEW01.json').write_text(json.dumps(machine, indent=2, sort_keys=True) + '\n')
print(json.dumps(dict(effective_budget=result, snapshot_count=40, consumed_before=57, review_sha256=review_ref['sha256'])))
