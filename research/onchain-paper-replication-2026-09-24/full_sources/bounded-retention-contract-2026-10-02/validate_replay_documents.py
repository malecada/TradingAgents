"""Read-only document revision02 checks; no production code or empirical work."""
from pathlib import Path
import hashlib,json,runpy
P=Path(__file__).resolve().parent
runpy.run_path(str(P/'validate_documents.py'))
p=json.loads((P/'POLICY.draft.json').read_bytes())
v=json.loads((P/'REVIEW_ACCEPTANCE.json').read_bytes())
a=json.loads((P/'REGISTRATION_AMENDMENT.draft.json').read_bytes())
rule=p['proposed_replay_selection'];d=rule['dictionary_single_block'];m=rule['mcm']
assert d['n512_exact_count']==512*511==261632
assert d['n512_ordinals']==[0,512*511-1]
assert d['n512_sample_pairs']==[[1,0],[510,511]]
assert m['ordinals']==['0','N*K-1'] and m['one_pair']=='select_once'
assert rule['adaptive_dictionary']['claims_last_realized_whole_stage_comparison'] is False
assert rule['adaptive_dictionary']['capacity_is_exact_denominator'] is False
assert rule['force_extra_checkpoint'] is rule['outcome_based_substitution'] is False
assert rule['early_complete_disposition']=='completed_before_first_scheduled_checkpoint'
assert rule['coverage_claim']=={'empirical':'endpoints_only','max_shape_and_phase_boundaries':'fixed_independent_synthetic_corpus','maximum_shape_empirical_member_selected':False}
assert p['replay_selection_rule_sha256'] is None and a['replay_selection_sha256'] is None
pin=p['proposed_replay_rule_document_pin'];body=(P/'REPLAY_RULE.draft.md').read_bytes()
assert len(body)==pin['bytes'] and hashlib.sha256(body).hexdigest()==pin['sha256']
old=P/'revision01-before-replay-rule'
for line in (old/'SHA256SUMS').read_text().splitlines():
    sha,name=line.split('  ',1)
    assert hashlib.sha256((old/name).read_bytes()).hexdigest()==sha
for c in v['criteria']:
    assert c['status']=='NOT_RUN' and c['evidence_sha256'] is None
print(json.dumps({'status':'REPLAY_DOCUMENT_REVISION02_PASS','original_package_preserved':True,'empirical_selector':'first_last_with_adaptive_dictionary_identifier_fallback','dictionary512_exact_pairs':261632,'max_shape_empirical_claim':False,'physical_limits_adopted':False,'production_tests_run':0,'execution_admitted':False},sort_keys=True))
