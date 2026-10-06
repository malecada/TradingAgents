"""Bounded fixed08 metadata composition review; no array or private body access."""
import ast,copy,hashlib,json,os,stat,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;FS=HERE.parent
OLD=FS/'real-data-pilot-final07-2026-10-06';NEW=FS/'real-data-pilot-final08-2026-10-06'
N7='eth-paper-real-data-end-to-end-resource-20261006-07';N8=N7[:-2]+'08'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def need(v,m):
 if not v:raise ValueError(m)
B=load(NEW/'BINDING_DRAFT01.json');G=load(NEW/'gate01.json');E=G['experiments'][N8];P=load(OLD/'gate01.json')['experiments'][N7]
assert B['identity']==N8 and B['binding_review'] is None
opaque=B['transport'];evidence=load(OLD/'RELEASE_REVIEW01.json')['evidence'].copy()
for p in list(evidence):
 if p.startswith('research_artifacts/real_pilot_runtime/'):del evidence[p]
def add(r):
 p=r['path'];assert not any(x in {'keys','apis','.env','hf_token.txt'} for x in Path(p).parts)
 if p==opaque['path']:
  q=ROOT/p;s=q.lstat();assert q.resolve()==q and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==928==opaque['bytes'] and s.st_uid==os.getuid() and s.st_nlink==1
  assert stat.S_IMODE(q.parent.stat().st_mode)==0o700
 else:assert sha(ROOT/p)==r['sha256'],p
 evidence[p]=r['sha256']
for r in B.values():
 if isinstance(r,dict) and {'path','sha256'}<=set(r):add(r)
assert len(E['source_files'])==210 and len(E['inputs'])==59
for k in P:
 if k not in {'charter','cumulative_budget_extension','inputs','question','source_files'}:assert E[k]==P[k],k
oldgate=load(OLD/'gate01.json')
for k in ['datasets','families','program_id','schema_version']:assert G[k]==oldgate[k],k
for p,h in E['source_files'].items():add({'path':p,'sha256':h})
for role,r in E['inputs'].items():
 assert (r['path']==opaque['path'])==(role=='archive_transport');add(r)
package={p:h for p,h in E['source_files'].items() if p.startswith('tradingagents/')};adopt=load(HERE/'SOURCE_ADOPTION_REVIEW01.json');assert package==adopt['package_pins'] and len(package)==179
for n in ['root_io.py','preflight01.py']:
 expected=(OLD/n).read_text().replace(N7,N8)
 if n=='preflight01.py':expected=expected.replace('real-data-pilot-packed-feature-successor08-2026-10-06','real-data-pilot-fixed08-metadata-successor01-2026-10-06').replace('!=78','!=79').replace("'effective_attempt_budget':78","'effective_attempt_budget':79")
 assert (NEW/n).read_text()==expected,n
 add(ref(NEW/n))
pol=load(NEW/'templates/pair_policy01.json');oldpol=load(OLD/'templates/pair_policy01.json');assert pol['numerical_source']['files']==package and pol['numerical_source']['commit']==adopt['source_anchor'];normal=copy.deepcopy(pol);normal['numerical_source']=oldpol['numerical_source'];assert normal==oldpol
SU=FS/'real-data-pilot-fixed08-metadata-successor01-2026-10-06';SU7=FS/'real-data-pilot-packed-feature-successor08-2026-10-06'
assert (SU/'successor02.py').read_bytes()==(SU7/'successor02.py').read_bytes()
for n in ['build_inputs03.py','controls01.py']:assert (SU/'candidate'/n).read_text()==(SU7/'candidate'/n).read_text().replace(N7,N8)
for key,r in load(SU/'DEPENDENCIES02.json').items():
 add(r)
 if key not in {'builder','controls'}:assert r==load(SU7/'DEPENDENCIES02.json')[key]
for n,h in load(SU/'MANIFEST01.json').items():
 if isinstance(h,str):assert sha(SU/n)==h,n
add(ref(SU/'MANIFEST01.json'));add(ref(SU/'successor02.py'));add(ref(SU/'DEPENDENCIES02.json'))
draft=load(NEW/'INPUT_DRAFT01.json');old=load(OLD/'INPUT_DRAFT01.json');normal=copy.deepcopy(draft)
for k in ['physical_baseline','references','transport_limits']:normal['protocol'][k]=old['protocol'][k]
assert normal==old and draft['protocol']['transport_limits']==dict(old['protocol']['transport_limits'],namespace='ethpilot-20261006-08')
for r in draft['protocol']['references'].values():add(r)
baseline=load(NEW/'BASELINE02.json');rawbaseline=load(NEW/'BASELINE01.json');add(baseline['original_observation_receipt']);assert baseline['result']['observation']==rawbaseline['result']
m=types.ModuleType('review_pure_prepare');m.__file__=str(SU/'successor02.py');exec(compile((SU/'successor02.py').read_bytes(),m.__file__,'exec'),vars(m));saved=load(NEW/'PREPARATION_RESULT01.json');assert m.prepare(ROOT,draft)==saved
for r in saved['builder03_spec']['references'].values():add(r)
assert saved['builder03_result']['inputs']['archive_transport']['namespace']=='ethpilot-20261006-08' and saved['builder03_result']['inputs']['archive_transport']['connection'] is None
bound=load(NEW/'TRANSPORT_BINDING01.json');assert bound['private_input']=={'archive_transport':opaque}
binder=FS/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';add(ref(binder));add(ref(binder.with_name('DEPENDENCIES01.json')))
for r in load(binder.with_name('DEPENDENCIES01.json')).values():add(r)
tree=ast.parse((NEW/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');scope={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'review_exact_inverse','exec'),scope)
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest();archive=load(ROOT/saved['builder03_spec']['references']['archive_policy']['path']);scope['inverse_binding'](saved,archive,bound,opaque,raw,digest)
assert archive['remote_namespace']==bound['inputs']['archive_policy']['remote_namespace']=='ethpilot-20261006-08'
for role,doc in bound['inputs'].items():assert load(ROOT/E['inputs'][role]['path'])==doc
job=bound['inputs']['execution_job'];oldjob=load(OLD/'inputs01/execution_job.json');assert json.dumps(job['resources']).replace(N8,N7)==json.dumps(oldjob['resources']);assert bound['inputs']['pilot']['resource_policy']==job['resources'];assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
for n in ['original_import.json','typed_payload.json','resource_population_plan.json','mcm_output_policy.json']:assert (NEW/'inputs01'/n).read_bytes()==(OLD/'inputs01'/n).read_bytes()
assert E['cumulative_budget_extension']['extension']==ref(FS/'real-data-pilot-retry08-registration01-2026-10-06/EXTENSION_PROPOSED79_01.json') and E['cumulative_budget_extension']['review']==ref(HERE/'EXTENSION_REVIEW01.json')
for r in E['cumulative_budget_extension'].values():add(r)
ext=load(ROOT/E['cumulative_budget_extension']['extension']['path']);add(ext['allocation'])
for prefix,identity in [('prior',N7),('engineering','eth-real-graph-canonical-hash-timing-20261006-01')]:
 recovery=load(ROOT/B[prefix+'_recovery_review']['path']);preservation=load(ROOT/B[prefix+'_preservation_complete']['path']);assert recovery['decision']=='accepted' and recovery['actual_external_recovery_accepted'] and recovery['identity']==identity
 for rk,bk in [('original_outcome',prefix+'_outcome_review'),('fresh_fetch_evidence',prefix+'_preservation_complete')]:assert all(recovery[rk][k]==B[bk][k] for k in ('path','sha256'))
 assert preservation['all_typed_names_modes_hashes_verified'];assert recovery['archive']['sha256']==preservation['archive']['sha256'] and recovery['archive']['tree_source_commit']==preservation['source']==preservation['actual_remote_head'];add(recovery['archive']['members_review'])
for n in ['SOURCE_REVIEW01.json','SOURCE_ADOPTION_REVIEW01.json','EXTENSION_REVIEW01.json','EXTENSION_MACHINE_REVIEW01.json','BYTE_STREAM_REVIEW01.json','HASH_PROFILE_ENTRY_REVIEW01.json','HASH_PROFILE_ENTRY_REVIEW02.json']:add(ref(HERE/n))
for n in ['BINDING_DRAFT01.json','CHARTER01.md','NUMERICAL_CONTEXT_REANCHOR01.json','TRANSPORT_PREPARATION_REFUSAL01.json','gate-draft00.json']:add(ref(NEW/n))
assert not (ROOT/'research_runs'/N8).exists() and not os.path.lexists(ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-08');assert (ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-02').exists()
for p,h in evidence.items():
 if p!=opaque['path']:assert sha(ROOT/p)==h,p
result={'schema_version':1,'decision':'accepted','identity':N8,'reviewer':'namespace_review05 independent final08 composition reviewer','evidence':evidence,'findings':[],'checks':{'package_pins':179,'unchanged_package_pins':176,'source_pins':210,'input_roles':59,'source_anchor':adopt['source_anchor'],'exact_entry_inverse':True,'effective_attempt_budget':79,'pure_prepare_matches_saved':True,'pure_binding_inverse_matches_prepared':True,'same_graphs_science_and_native_caps':True,'public_namespace':'ethpilot-20261006-08','prior07_and_engineering_external_recovery_accepted':True,'private_body_read':False},'resolved_findings':['Initial preflight retained78 budget check/receipt despite79 extension; exact final entry now uses79 in both locations.','Initial gate used diagnostic machine receipt instead of required standard five-field accounting review; corrected gate selects accepted EXTENSION_REVIEW01.'],'required_before_launch':['Commit exact final binding/review/release/gate/source/public evidence closure and authenticate actual remote HEAD readback.','Run genuine committed readonly admission proving79/210sources/59inputs and actual authenticated selected private08 namespace=public remote08=fixed08, with local absence; this review does not substitute for that private authentication.','Fresh original native/concurrency/namespace/writable-growth/9GiBstartup/10GiBdisk checks must pass. Only one fresh08 invocation, no reuse or relaunch after an attempt.'],'not_tested':['No actual graph/model/array/private body/claim/native execution by reviewer.','No full seven-graph lease, constructor/fullcallback timing, MCM/training capacity or financial validation.','No repeat external archive fetch/stream; exact accepted independent recovery evidence reused.'],'qualification':'Accepted exact public composition with sole opaque transport reference. Runtime committed admission and exact conditional release remain mandatory; no automatic eligibility from single-graph engineering timing.'}
(HERE/'BINDING_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(HERE/'BINDING_REVIEW01.json'),'evidence_count':len(evidence)}))
