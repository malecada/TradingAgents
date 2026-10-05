"""Immutable source-phase acceptance; future concrete Parent bindings excluded."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;F=H.parent
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import R
r=json.loads(R.read(H,'SOURCE_READBACK01.json'))
def ref(name):return {'path':str(H/name),'sha256':R.digest(R.read(H,name))}
report='''# Canonical historical plan alias — source phase

Accepted exactly the two candidate metadata files. The original public preflight failed at preclaim01.py:318 because prior.parent_plan_input was historical_wrapper_plan while the immutable policy required historical_plan. The unchanged actual AST loop reproduces the original refusal; the corrected descriptor passes it. This is a correction of the registered alias, not a relaxed preclaim predicate.

The original failed claim selects its execution job, whose plan input selects the same original wrapper_plan.json. Its636-byte body, path, dataset and SHA15fd8a363806a15b68a6ff23b029847727b5ddbeb9e945454a1f9b5d4c4ac729 match both old and corrected registrations. Actual unchanged Inputs methods reject the old missing role, a wrong expected path and a wrong registered hash. No checkpoint body is deserialized or numerical module imported.

Independent complete literal and semantic inverses admit exactly: prior.parent_plan_input's alias; continuation input key rename; continuation prior input hash; prior source-file hash in both new consumer maps. Both historical definitions remain identical. Continuation29 and prediction17 registered roles remain unchanged in count; all other prediction data, including its null prior, remain identical. Scientific code, plan bodies, budgets, tolerances, modes of old files and old failures are untouched by this review.322 bounded checks authenticate the complete author seal and these actual body/predicate joins; no old818-body scan was repeated.

The genuine source-only release permits Root to adopt precisely these two metadata bodies while preserving the original bodies and failed read-only preflights. It grants no financial claim or numerical entry. Fresh actual committed source, updated gate/prior pins, honest source/input/runtime and recovery bindings, exact newly bound Parent contract/release and a successful complete public preflight remain required. The previous Parent release binds the previous source and cannot be silently reused for changed metadata. Further exact binding checks can be recorded as later files in this same consolidated review; the source snapshot is immutable.

Not tested: a full corrected public preflight, fresh genuine Admission or Parent installation, numerical continuation, financial economics, scientific capacity, installed-runtime body recovery or continuous writer exclusion. No authority is inferred from a component pass.
'''
with (H/'SOURCE_REPORT01.md').open('x') as f:f.write(report)
release={'schema_version':1,'decision':'ACCEPTED_EXACT_TWO_FILE_METADATA_CORRECTION_ONLY','source_before':r['source_before'],'capsule_root':'/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source','files':[{'path':'fixture_inputs/financial_wrapper_continuation01/'+n,'before_sha256':r['old_pins'][n],'candidate_path':str(F/'financial-wrapper-continuation-canonical-plan-preparation01-2026-10-05'/n),'sha256':h} for n,h in r['candidate_pins'].items()],'preserve_original_bodies_and_failed_preflights':True,'scientific_code_or_limit_changes_allowed':False,'source_readback':ref('SOURCE_READBACK01.json'),'full_public_preflight_passed':False,'numerical_authority':False}
R.put(H/'SOURCE_CORRECTION_RELEASE01.json',release)
R.put(H/'SOURCE_MACHINE01.json',{'schema_version':1,'decision':r['decision'],'reviewer':'/root/storage_watch_review','source_readback':ref('SOURCE_READBACK01.json'),'release':ref('SOURCE_CORRECTION_RELEASE01.json'),'report':ref('SOURCE_REPORT01.md'),'author_manifest_sha256':r['author_manifest_sha256'],'actual_old_RED_corrected_component_GREEN':True,'literal_and_semantic_inverse':True,'full_public_preflight_passed':False,'future_Parent_binding_reviewed':False,'numerical_authority':False})
m=R.scan(H);m['self_excluded']='SOURCE_PHASE_MANIFEST01.json';m['scope']='Immutable exact correction source-phase snapshot. Later actual Root adoption and Parent-binding evidence are outside this snapshot.';R.put(H/'SOURCE_PHASE_MANIFEST01.json',m)
print(json.dumps({'release':ref('SOURCE_CORRECTION_RELEASE01.json'),'machine':ref('SOURCE_MACHINE01.json'),'manifest':ref('SOURCE_PHASE_MANIFEST01.json'),'members':len(m['members'])}))
