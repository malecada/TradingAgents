"""Independent selected10 metadata inversion. No private contents or numerical inputs."""
import ast,copy,hashlib,json,os,stat,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
O=F/'real-data-pilot-final09-2026-10-06';D=F/'real-data-pilot-final10-2026-10-06';U=F/'real-data-pilot-fixed10-metadata-successor01-2026-10-06';U0=F/'real-data-pilot-fixed09-metadata-successor01-2026-10-06'
N0='eth-paper-real-data-end-to-end-resource-20261006-09';N='eth-paper-real-data-end-to-end-resource-20261006-10'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def need(v,m):
 if not v:raise ValueError(m)
evidence={};bound=ld(D/'TRANSPORT_BINDING01.json');opaque=bound['private_input']['archive_transport']
def add(r):
 p=ROOT/r['path'];assert not any(x in {'keys','apis','.env','hf_token.txt'} for x in p.parts)
 if r['path']==opaque['path']:
  s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==928==opaque['bytes'] and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(p.parent.stat().st_mode)==0o700
 else:assert sha(p)==r['sha256'],r['path']
 evidence[r['path']]=r['sha256']
for name in ['root_io.py','preflight01.py']:
 expected=(O/name).read_text().replace(N0,N)
 if name=='preflight01.py':expected=expected.replace('real-data-pilot-fixed09-metadata-successor01','real-data-pilot-fixed10-metadata-successor01').replace('!=80','!=81').replace("'effective_attempt_budget':80","'effective_attempt_budget':81")
 assert (D/name).read_text()==expected;add(ref(D/name))
assert (U/'successor02.py').read_bytes()==(U0/'successor02.py').read_bytes();add(ref(U/'successor02.py'));add(ref(U/'DEPENDENCIES02.json'))
for name in ['build_inputs03.py','controls01.py']:assert (U/'candidate'/name).read_text()==(U0/'candidate'/name).read_text().replace(N0,N)
for k,r in ld(U/'DEPENDENCIES02.json').items():
 add(r)
 if k not in {'builder','controls'}:assert r==ld(U0/'DEPENDENCIES02.json')[k]
pol=ld(D/'templates/pair_policy01.json');op=ld(O/'templates/pair_policy01.json');adopt=ld(HERE/'SOURCE_ADOPTION_REVIEW01.json');assert pol['numerical_source']==dict(op['numerical_source'],files=adopt['package_pins'],commit=adopt['source_anchor']);norm=copy.deepcopy(pol);norm['numerical_source']=op['numerical_source'];assert norm==op
for name in ['job_template01.json','job_template02.json']:
 before=json.loads((O/'templates'/name).read_text().replace(N0,N));after=ld(D/'templates'/name);before['payload']['representation_jobs']['original32']['descriptor']['pair_execution']['policy_sha256']=sha(D/'templates/pair_policy01.json');assert before==after
assert (D/'templates/pilot.json').read_text()==(O/'templates/pilot.json').read_text().replace(N0,N)
assert (D/'templates/archive_policy.json').read_text()==(O/'templates/archive_policy.json').read_text().replace('ethpilot-20261006-09','ethpilot-20261006-10')
draft=ld(D/'INPUT_DRAFT01.json');old=ld(O/'INPUT_DRAFT02.json');norm=copy.deepcopy(draft)
for k in ['physical_baseline','references','transport_limits']:norm['protocol'][k]=old['protocol'][k]
assert norm==old and draft['protocol']['transport_limits']==dict(old['protocol']['transport_limits'],namespace='ethpilot-20261006-10')
baseline=ld(D/'BASELINE02.json');rawbaseline=ld(D/'BASELINE01.json');assert baseline['result']['observation']==rawbaseline['result'];add(baseline['original_observation_receipt'])
for r in draft['protocol']['references'].values():add(r)
add(draft['protocol']['physical_baseline']['evidence'])
m=types.ModuleType('review_pure_prepare');m.__file__=str(U/'successor02.py');exec(compile((U/'successor02.py').read_bytes(),m.__file__,'exec'),vars(m));saved=ld(D/'PREPARATION_RESULT01.json');assert m.prepare(ROOT,draft)==saved
assert saved['builder03_result']['inputs']['archive_transport']['namespace']=='ethpilot-20261006-10' and saved['builder03_result']['inputs']['archive_transport']['connection'] is None
for r in saved['builder03_spec']['references'].values():add(r)
for name in ['INPUT_DRAFT01.json','PREPARATION_RESULT01.json','TRANSPORT_BINDING01.json','TRANSPORT_REQUEST01.json','INPUT_REFS01.json','BASELINE01.json','BASELINE02.json','CHARTER01.md','NUMERICAL_CONTEXT_REANCHOR01.json']:add(ref(D/name))
binder=F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';add(ref(binder));add(ref(binder.with_name('DEPENDENCIES01.json')))
for r in ld(binder.with_name('DEPENDENCIES01.json')).values():add(r)
tree=ast.parse((D/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');scope={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'review_inverse','exec'),scope)
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest();archive=ld(ROOT/saved['builder03_spec']['references']['archive_policy']['path']);scope['inverse_binding'](saved,archive,bound,opaque,raw,digest)
assert archive['remote_namespace']==bound['inputs']['archive_policy']['remote_namespace']=='ethpilot-20261006-10';add(opaque)
refs=ld(D/'INPUT_REFS01.json')
for role,doc in bound['inputs'].items():assert ld(ROOT/refs[role]['path'])==doc;add(refs[role])
assert refs['archive_transport']==opaque
job=bound['inputs']['execution_job'];oldjob=ld(O/'inputs02/execution_job.json');assert json.dumps(job['resources']).replace(N,N0)==json.dumps(oldjob['resources']);assert bound['inputs']['pilot']['resource_policy']==job['resources'];assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
for name in ['original_import.json','typed_payload.json','resource_population_plan.json','mcm_output_policy.json']:assert (D/'inputs01'/name).read_bytes()==(O/'inputs02'/name).read_bytes()
assert not (ROOT/'research_runs'/N).exists() and not os.path.lexists(ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-10') and not (D/'launch-attempt01.json').exists()
result={'schema_version':1,'reviewer':'pilot09_review independent metadata reviewer','decision':'accepted','identity':N,'evidence':evidence,'findings':[],'resolved_finding':'Prior09 namespace correction reused; new10 draft/policy/prepared/bound namespace matches10.','checks':['Exact caller/preflight and two fixed helper identity inverses, budget81 predicate/receipt only.','Pure metadata prepare equals actual selected01 saved result; exact binder AST inverse matches prepared output.','Same179 numerical source anchor, graphs, original input metadata, native caps and resource policy.','Private selected01 reference inspected by stat/metadata only, no body access; actual committed admission must authenticate body.'],'not_tested':['No financial/model/array/native/claim/ledger/private-body execution.','No fresh RAM or full capacity/throughput proof.'],'qualification':'Metadata seam acceptance only; concrete final binding, cumulative81 and committed actual admission/release remain required.'}
p=HERE/'METADATA_REVIEW01.json';p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
