import copy,json,hashlib,os,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;N=H.parent/'real-data-pilot-final23-2026-10-09'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
prior=load(H/'BINDING_REVIEW01.json');assert sha(H/'BINDING_REVIEW01.json')=='e1e965a12dadd2070b5575f683146d45dea342a7a3cb370d74877e155e936e89';name=prior['identity'];old=load(N/'gate02.json');new=load(N/'gate03.json');ex=new['experiments'][name];oe=old['experiments'][name];assert len(ex['source_files'])==354 and len(ex['inputs'])==64
expected=copy.deepcopy(old);expected['experiments'][name]['source_files']=ex['source_files'];assert new==expected
added={p:h for p,h in ex['source_files'].items() if p not in oe['source_files']};assert len(added)==5 and all(ex['source_files'][p]==h for p,h in oe['source_files'].items())
refs=ex['cumulative_budget_extension'];extension=load(R/refs['extension']['path']);required=[refs['extension'],refs['review'],extension['allocation']]
expected_paths={r['path'] for r in required}|{str((N/f).relative_to(R)) for f in ['preflight02.py','root_io02.py']};assert set(added)==expected_paths
for p,h in added.items():assert sha(R/p)==h
for ref in required:assert added[ref['path']]==ref['sha256']
s=(N/'preflight02.py').read_text()
for a,b in [('gate03.json','gate02.json'),('BINDING02.json','BINDING01.json'),('RELEASE_REVIEW02.json','RELEASE_REVIEW01.json')]:s=s.replace(a,b)
assert s==(N/'preflight01.py').read_text();assert (N/'root_io02.py').read_text().replace('from preflight02 import check','from preflight01 import check')==(N/'root_io.py').read_text()
draft=load(N/'BINDING_DRAFT03.json');old_draft=load(N/'BINDING_DRAFT02.json');expected=copy.deepcopy(old_draft);expected['gate']=draft['gate'];assert draft==expected and draft['gate']['sha256']==sha(N/'gate03.json')
admission=R/'tradingagents/research/admission.py';budget=R/'tradingagents/research/budget_extensions.py'
assert sha(admission)==ex['source_files'][str(admission.relative_to(R))] and sha(budget)==ex['source_files'][str(budget.relative_to(R))]
assert 'budget extension metadata must be source-pinned' in (N/'ADMISSION_ONLY01.stderr').read_text();assert not (R/'research_runs'/name).exists() and not (N/'launch-attempt01.json').exists()
ev=dict(prior['evidence']);ev.update(added)
for p in [N/'gate03.json',N/'BINDING_DRAFT03.json',N/'ADMISSION_ONLY01.stderr']:ev[str(p.relative_to(R))]=sha(p)
x={'schema_version':1,'decision':'accepted','identity':name,'source_count':354,'input_count':64,'opaque_evidence_count':1,'evidence':ev,'checks':['all349prior_sources_and64inputs_unchanged','exact_three_required_budget_pins_plus_two_new_callers','caller_literal_inverses','draft_gate_only_delta','actual_admission_extension_metadata_source_membership_rule','original_refusal_and_unused_identity_preserved'],'scope':'Corrected final23 binding draft only. Reuses prior accepted binding/source/metadata/budget evidence. Actual admission source requires extension, allocation and review source membership; exact three refs now present. No repeated old source/runtime checks, no admission/commit/current-capacity/remote-recovery or launch claim. Final BINDING02 and RELEASE_REVIEW02 exact sealing pending.'}
(H/'BINDING_REVIEW02.json').write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted','sha256':sha(H/'BINDING_REVIEW02.json'),'evidence':len(ev),'added':added}))
