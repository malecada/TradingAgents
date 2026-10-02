"""Read-only consistency/hash checks of unadopted documents; not production tests."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
R=P.parents[3]
files=['POLICY.draft.json','REVIEW_ACCEPTANCE.json','REGISTRATION_AMENDMENT.draft.json','SOURCE_OWNERSHIP.json']
p,v,a,o=[json.loads((P/n).read_bytes()) for n in files]
for x in [p,v,a,o]:
    assert x['status']=='NONEXECUTABLE_UNADOPTED_DRAFT' and x['execution_admitted'] is False
    assert x['prospective_variant']=='bounded-matching-restart-v1'
assert set(p['objects'])=={'scientific_outputs','replay_evidence','active_restart_scratch','failed_evidence','control_evidence'}
assert [k for k,x in p['objects'].items() if x['retirement_allowed']]==['active_restart_scratch']
assert p['rotation']['max_saved_active_generations']==2 and p['rotation']['max_active_pairs']==1
assert p['objects']['active_restart_scratch']['logical_only'] is True
assert p['rotation']['third_generation_before_retirement_completion'] is False
assert p['rotation']['hash_only_recoverability_claim_allowed'] is False
assert all(x is False for x in p['rotation']['retired_flags'].values())
for k in ['reuse_failed_identity','automatic_resume','automatic_retry','attempt_refund']:
    assert p['failure'][k] is False
for x in p['limits'].values():
    assert x['value'] is None and isinstance(x['reason'],str) and x['reason']
for k in ['physical_upper_bound_bytes','replay_selection_rule_sha256','prospective_source_sha256','adopted_policy_sha256']:
    assert p[k] is None and p[k+'_reason']
for pin in [*p['authority_pins'],a['existing_resource_proposal_pin']]:
    raw=(R/pin['path']).read_bytes()
    assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
assert p['preserved_current_local_score_matrix_payload_bytes']==50819833856+4619984896
assert p['user_minimum_local_free_bytes']==10*2**30
assert len(v['criteria'])==14 and {x['id'] for x in v['criteria']}=={f'BR{i:02d}' for i in range(1,15)}
assert v['tests_run'] is False
for c in v['criteria']:
    assert c['status']=='NOT_RUN' and c['evidence_sha256'] is None and c['evidence_sha256_reason']
assert set(v['criteria_authority'])=={'C11','C13','C14','C16','C18'}
b=a['budget']
assert b['spent_preserved']+b['body_batches_preserved']+b['financial_batches_preserved']+b['resource_slots_already_proposed']==b['proposed_cumulative_ceiling_unchanged']==61
assert b['additional_slots_requested_here']==b['refunds']==0 and b['maximum_unique_fits_unchanged']==1420
assert a['scientific_changes']==[] and a['old_artifacts_edited_or_deleted'] is False
assert a['current_archived_variant_preserved'] is True and a['adoption'] is False
assert o['active_assignment'] is False
assert len(set(o['integration_owner']['existing_modules_candidate_scope']))==10
assert 'score-tail/batch retention' in o['out_of_scope']
print(json.dumps({'status':'DOCUMENT_CONSISTENCY_PASS','draft_json_files':4,'acceptance_requirements':14,'production_tests_run':0,'empirical_runs':0,'execution_admitted':False,'adoption':False,'source_pins_verified':5,'physical_upper_bound_invented':False},sort_keys=True))
