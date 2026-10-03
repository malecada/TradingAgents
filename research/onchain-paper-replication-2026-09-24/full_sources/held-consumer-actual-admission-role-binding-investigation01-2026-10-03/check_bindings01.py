"""Metadata/source inventory only; no package imports, admission or numerical reads."""
from pathlib import Path
import ast,hashlib,json,subprocess,os
H=Path(__file__).resolve().parent;F=H.parent
S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-05/source')
OLD=F/'original-import-native-successor-preparation06-2026-10-03/capsule04/fixture_inputs/success'
REUSE=F/'held-target-input-reuse-investigation01-2026-10-03';POS=F/'held-consumer-positive-case-contract-investigation01-2026-10-03';BUD=F/'held-consumer-cumulative-admission-preparation02-2026-10-03';REV=F/'held-consumer-cumulative-admission-review02-2026-10-03'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def doc(p):return json.loads(p.read_bytes())
def pin(p,qualification):return ref(p)|{'qualification':qualification}
roles={
'runtime':pin(S/'fixture_inputs/held/runtime-role01.json','Existing copied251 RECORD/interpreter/lock metadata; current native check remains separate'),
'software_environment':pin(OLD/'environment.json','Historical numerical software inventory donor, not fresh runtime observation; compare under guard before worker'),
'native_environment':{'donor':None,'schema_source':'tradingagents/research/onchain_replication/resources.py:_native_owned_env','required':'Render exact Source05-root paths and fixed string map; no HOME replacement'},
'native_policy':pin(POS/'JOB_TEMPLATE01.json','Extract resources and change both root fields to actual Source05; whole JSON is a job template, NOT a direct native-policy role'),
'original_import_index':pin(REUSE/'ORIGINAL_IMPORT_INDEX_ROLE01.json','Exact11 original refs already copied; no re-sampling or original JSON semantic execution'),
'original_evidence':pin(REUSE/'ORIGINAL_EVIDENCE_ROLE01.json','Derived512/32/import-only metadata; historical control_reference requires present exact body'),
'matching':pin(S/'fixture_inputs/original/01-matching-stable.json','Existing original matching configuration; descriptor must use exact values'),
 'target_catalog':pin(REUSE/'TARGET_CATALOG01.json','Exact2 targets/10 opaque refs; no regenerated arrays'),
'case_contract':pin(POS/'CASE_TEMPLATE01.json','Template has null program/identity/additional_inputs; must render new case'),
'registration':{'donor':None,'required':'New schema1 gate; fixed held IDs/program/base family/current204 pins/complete inputs and six outputs; never call legacy registration()'},
'budget_extension':pin(BUD/'cumulative-extension04-proposal.json','Exact accepted accounting proposal, not adopted; preserve byte hash and allocation relative path'),
'budget_review':{'donor':None,'prose_review':ref(REV/'REVIEW_ADMISSION02.md'),'required':'Independent exact five-field accepted machine review of extension, separately issued; prose/readback not substitution'},
'charter':pin(BUD/'CHARTER_PROPOSAL01.md','Historical proposal draft, stale Source03-refusal paragraph; render exact current case-specific charter, not grant'),
'budget_allocation':pin(BUD/'successor-allocation04-proposal.json','Exact proposal accepted for accounting; preserve original bytes and extension path'),
'auxiliary_sources':{'donor':None,'required':'New per-experiment<=8192-byte declaration rendered after four metadata refs; source-map digest is199 only'},
}
gen=ast.parse((S/'fixture_tools/generate_inputs01.py').read_bytes());names=next(ast.literal_eval(n.value) for n in gen.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HELD_ROLES' for t in n.targets));assert set(names)==set(roles) and len(names)==15
ext=doc(BUD/'cumulative-extension04-proposal.json');allocation=doc(BUD/'successor-allocation04-proposal.json');assert ext['allocation']=={'path':'successor-allocation04-proposal.json','sha256':ref(BUD/'successor-allocation04-proposal.json')['sha256']};assert ext['consumed_before']==4 and ext['cumulative_ceiling']==6 and len(ext['claims'])==4
assert allocation['new_attempts'][0]['identity']==ext['initial_experiment'];assert len(allocation['new_attempts'])==2
# Check donor structural policies only, no original dictionary/sample JSON decoding.
assert doc(OLD/'mcm_policy.json')['numeric']['edge_chunk']==4096
assert doc(OLD/'compact_policy.json')['stage_policy']['score_chunk_cells']==64
index=doc(REUSE/'ORIGINAL_IMPORT_INDEX_ROLE01.json');cat=doc(REUSE/'TARGET_CATALOG01.json');refs=[x['reference'] for x in index['inputs']]+[r for t in cat['targets'] for r in [t['manifest'],*t['components'].values()]]
assert len(refs)==21 and len({r['path'] for r in refs})==21
for r in refs:
 p=S/r['path'];b=p.read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
assert len(list((S/'research_runs').iterdir()))==4
# Actual-source extracted branch, qualified metadata sentinels, never Admission/Owner.
tree=ast.parse((S/'tradingagents/research/onchain_replication/resource_fixture.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_engineering_parent')
branch=ast.Module(body=[ast.FunctionDef(name='branch',args=fn.args,body=fn.body[:4],decorator_list=[],returns=None)],type_ignores=[]);ast.fix_missing_locations(branch)
ns={};exec(compile(branch,'actual-parent-leading-branch','exec'),ns)
from types import SimpleNamespace
for row in allocation['new_attempts']:
 assert ns['branch'](SimpleNamespace(experiment_id=row['identity'],experiment={'parent':None})) is True
 assert ns['branch'](SimpleNamespace(experiment_id=row['identity'],experiment={'parent':ext['claims'][-1]['experiment']})) is False
sources=[]
for name in ['fixture_tools/generate_inputs01.py','fixture_tools/capsule_builder01.py','proof_tools/build_release_draft01.py','fixture_tools/outer_controller01.py','fixture_tools/raw_receipts01.py','fixture_tools/controller01.py','tradingagents/research/admission.py','tradingagents/research/budget_extensions.py','tradingagents/research/onchain_replication/resource_fixture.py','tradingagents/research/onchain_replication/resources.py']:
 p=S/name;t=ast.parse(p.read_bytes());sources.append(ref(p)|{'definitions':{n.name:n.lineno for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}})
policies=[pin(OLD/n,'Historical metadata donor; source/current-root/descriptor-dependent fields require explicit rebind where stated') for n in ['original_import.json','original_import_stage.json','pair_policy.json','compact_policy.json','mcm_policy.json','mcm_output_policy.json','execution_workspace.json','producer_plan.json','execution_job.json']]
policies += [pin(POS/n,'Prospective source-only template/policy; canonical held policy requires exact generator serialization') for n in ['HELD_POLICY01.json','JOB_TEMPLATE01.json','PLAN_TEMPLATE01.json']]
(H/'ROLE_DONORS01.json').write_text(json.dumps({'roles':roles,'source_references':sources,'policy_donors':policies},indent=2)+'\n')
env=os.environ|{'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'}
head=subprocess.check_output(['git','-c','protocol.allow=never','-C',str(S),'rev-parse','HEAD'],env=env).decode().strip();assert head=='6c36d073598c9949c463cf56619bb9d3b7b59329'
(H/'READBACK01.json').write_text(json.dumps({'head':head,'roles':15,'opaque_refs_checked':21,'new_identity_parent_none_controls':4,'source_packages_imported':False,'admission_executed':False,'machine_budget_review_donor_present':False,'budget_proposal_sha256':ref(BUD/'cumulative-extension04-proposal.json')['sha256'],'no_claim_or_release':True},indent=2)+'\n')
print('PASS15 installed role names; exact proposal allocation join;21 opaque refs;4096/64 metadata policy;4 extracted fresh-parent controls; no admission/numerical execution')
