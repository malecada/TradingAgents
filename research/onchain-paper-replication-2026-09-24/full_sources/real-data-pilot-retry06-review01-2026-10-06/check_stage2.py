"""Exact D6 metadata/source closure; no claim, graph/model/private body or experiment."""
import ast,copy,hashlib,json,os,stat,subprocess,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;FS=HERE.parent
D5=FS/'real-data-pilot-final05-2026-10-06';D6=FS/'real-data-pilot-final06-2026-10-06'
N5='eth-paper-real-data-end-to-end-resource-20261006-05';N6=N5[:-2]+'06'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def need(v,m):
 if not v:raise ValueError(m)
B=load(D6/'BINDING_DRAFT01.json');G=load(D6/'gate01.json');E=G['experiments'][N6];E4=load(D5/'gate01.json')['experiments'][N5]
assert B['identity']==N6 and B['binding_review'] is None
opaque=B['transport'];evidence=load(D5/'RELEASE_REVIEW01.json')['evidence'].copy()
for p in list(evidence):
 if p.startswith('research_artifacts/real_pilot_runtime/'):del evidence[p]
def add(ref):
 p=ref['path'];assert not any(x in {'keys','apis','.env','hf_token.txt'} for x in Path(p).parts)
 if p==opaque['path']:
  q=ROOT/p;s=q.lstat();assert q.resolve()==q and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==opaque['bytes'] and s.st_uid==os.getuid() and s.st_nlink==1
 else:
  assert sha(ROOT/p)==ref['sha256'],p
 evidence[p]=ref['sha256']
for v in B.values():
 if isinstance(v,dict) and {'path','sha256'}<=set(v):add(v)
assert len(E['source_files'])==202 and len(E['inputs'])==59
for p,h in E['source_files'].items():add({'path':p,'sha256':h})
for role,v in E['inputs'].items():
 assert (v['path']==opaque['path'])==(role=='archive_transport');add(v)
package={p:h for p,h in E['source_files'].items() if p.startswith('tradingagents/')}
changed={p for p,h in package.items() if E4['source_files'].get(p)!=h}
assert len(package)==179 and changed=={'tradingagents/research/onchain_replication/'+x for x in ['imported_authority_lease.py','real_pilot_storage.py']}
S=load(HERE/'SOURCE_REVIEW01.json')
for ref in S['candidates']:
 add(ref);assert package['tradingagents/research/onchain_replication/'+Path(ref['path']).name]==ref['sha256']
for n in ['root_io.py','preflight01.py']:
 expected=(D5/n).read_text().replace(N5,N6)
 if n=='preflight01.py':expected=expected.replace('packed-feature-successor06-','packed-feature-successor07-').replace('!=76','!=77').replace("'effective_attempt_budget':76","'effective_attempt_budget':77")
 assert (D6/n).read_text()==expected,n
 add(reference(D6/n))
P=load(D6/'templates/pair_policy01.json');P4=load(D5/'templates/pair_policy01.json')
assert P['numerical_source']['files']==package
p=copy.deepcopy(P);p['numerical_source']=P4['numerical_source'];assert p==P4
anchor=P['numerical_source']['commit']
for path,h in package.items():
 body=subprocess.check_output(['git','show',anchor+':'+path],cwd=ROOT);assert hashlib.sha256(body).hexdigest()==h
# Immutable successor body, identity-only adapter substitution.
SU=FS/'real-data-pilot-packed-feature-successor07-2026-10-06';SU4=FS/'real-data-pilot-packed-feature-successor06-2026-10-06'
assert (SU/'successor02.py').read_bytes()==(SU4/'successor02.py').read_bytes()
for n in ['build_inputs03.py','controls01.py']:
 assert (SU/'candidate'/n).read_text()==(SU4/'candidate'/n).read_text().replace(N5,N6),n
for q in [SU/'successor02.py',SU/'DEPENDENCIES02.json'] :add(reference(q))
for ref in load(SU/'DEPENDENCIES02.json').values():add(ref)
draft=load(D6/'INPUT_DRAFT01.json');draft4=load(D5/'INPUT_DRAFT01.json')
assert draft['graphs']==draft4['graphs']
normal=copy.deepcopy(draft);normal['protocol']['physical_baseline']=draft4['protocol']['physical_baseline'];normal['protocol']['references']=draft4['protocol']['references'];normal['protocol']['transport_limits']['namespace']='ethpilot-20261006-05';assert normal==draft4
assert draft['protocol']['transport_limits']['namespace']=='ethpilot-20261006-06'
for ref in draft['protocol']['references'].values():add(ref)
# Accepted pure metadata preparation (stdlib only), no scientific package import.
m=types.ModuleType('review_pure_metadata');m.__file__=str(SU/'successor02.py');exec(compile((SU/'successor02.py').read_bytes(),m.__file__,'exec'),vars(m))
saved=load(D6/'PREPARATION_RESULT01.json');assert m.prepare(ROOT,draft)==saved
for ref in saved['builder03_spec']['references'].values():add(ref)
assert saved['builder03_result']['inputs']['archive_transport']['namespace']=='ethpilot-20261006-06'
assert saved['builder03_result']['inputs']['archive_transport']['connection'] is None
bound=load(D6/'TRANSPORT_BINDING01.json');assert bound['private_input']=={'archive_transport':opaque}
binder=FS/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';add(reference(binder));add(reference(binder.with_name('DEPENDENCIES01.json')))
for ref in load(binder.with_name('DEPENDENCIES01.json')).values():add(ref)
# Execute only reviewed pure inverse helper; private dispatch body never opened.
tree=ast.parse((D6/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding')
scope={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'exact-entry-inverse','exec'),scope)
raw=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
hashbody=lambda b:hashlib.sha256(b).hexdigest()
archive=load(ROOT/saved['builder03_spec']['references']['archive_policy']['path'])
scope['inverse_binding'](saved,archive,bound,opaque,raw,hashbody)
assert archive['remote_namespace']==bound['inputs']['archive_policy']['remote_namespace']=='ethpilot-20261006-06'
for role,doc in bound['inputs'].items():assert load(ROOT/E['inputs'][role]['path'])==doc
job=bound['inputs']['execution_job'];job4=load(D5/'inputs01/execution_job.json')
assert json.dumps(job['resources']).replace(N6,N5)==json.dumps(job4['resources'])
assert bound['inputs']['pilot']['resource_policy']==job['resources']
assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
for n in ['original_import.json','typed_payload.json','resource_population_plan.json','mcm_output_policy.json']:assert (D6/'inputs01'/n).read_bytes()==(D5/'inputs01'/n).read_bytes()
for n in ['NUMERICAL_CONTEXT_REANCHOR01.json','ACTUAL_READONLY_ADMISSION01.json','BINDING_DRAFT01.json','CHARTER01.md']:add(reference(D6/n))
for n in ['SOURCE_REVIEW01.json','EXTENSION_REVIEW01.json']:add(reference(HERE/n))
admission=load(D6/'ACTUAL_READONLY_ADMISSION01.json');assert admission['ready'] and admission['identity']==N6 and admission['effective_attempt_budget']==77
assert hashlib.sha256(subprocess.check_output(['git','show',admission['source']+':'+B['gate']['path']],cwd=ROOT)).hexdigest()==B['gate']['sha256']
recovery=load(ROOT/B['prior_recovery_review']['path']);preservation=load(ROOT/B['prior_preservation_complete']['path']);outcome=load(ROOT/B['prior_outcome_review']['path'])
assert recovery['decision']=='accepted' and recovery['actual_external_recovery_accepted'] and recovery['identity']==N5 and all(recovery['original_outcome'][k]==B['prior_outcome_review'][k] for k in ('path','sha256')) and all(recovery['fresh_fetch_evidence'][k]==B['prior_preservation_complete'][k] for k in ('path','sha256'))
assert preservation['all_typed_names_modes_hashes_verified'] and preservation['selected_regular_files']==43 and preservation['selected_directories']==13 and preservation['selected_regular_bytes']==433402
assert recovery['archive']['sha256']==preservation['recovered_archive']['sha256'] and recovery['archive']['tree_source_commit']==preservation['source']==preservation['actual_remote_head']
assert not (ROOT/'research_runs'/N6).exists() and not os.path.lexists(ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-06')
assert (ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-02').exists()
# All inherited public accepted evidence remains exact except explicitly replaced current package files.
for p,h in evidence.items():
 if p!=opaque['path']:assert sha(ROOT/p)==h,p
result={'schema_version':1,'decision':'accepted','identity':N6,'reviewer':'namespace_review05 independent reviewer','evidence':evidence,'checks':{'package_pins':179,'changed_package_pins':sorted(changed),'source_pins':202,'input_roles':59,'exact_identity_only_entry_inverse':True,'pure_prepare_matches_saved':True,'pure_binding_inverse_matches_prepared':True,'original_science_inputs_and_caps_unchanged':True,'public_transport_namespace':'ethpilot-20261006-06','private_dispatch_checked':'metadata stat/public binder digest and preserved actual authenticated admission only; body not opened','prior05_recovery_review_accepted':True},'findings':[],'not_tested':['No financial accounting/timing/fees/funding or economic claim retested.','No graph/model/array execution, throughput or physical capacity validation.','No private dispatch body opened; actual source-authenticated admission receipt is relied upon.','No repeated external fetch/archive stream; accepted exact recovery review reused.','No launch, current runtime inventory, RAM/free-disk headroom, active-process census or future remote availability established.'],'qualification':'Exact final binding/entry metadata accepted. Source and final release must be committed and actual remote HEAD authenticated before fresh fixed06 preflight. All original entry refusals and unchanged resource limits remain mandatory; no stale/consumed identity reuse, refund, cap ladder or financial fit.'}
(HERE/'BINDING_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':result['decision'],'review_sha256':sha(HERE/'BINDING_REVIEW01.json'),'evidence_count':len(evidence),'checks':result['checks']},indent=2))
