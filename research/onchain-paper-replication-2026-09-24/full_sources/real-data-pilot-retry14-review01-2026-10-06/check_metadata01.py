"""Independent selected11 metadata inversion. No private contents or numerical inputs."""
import ast,copy,hashlib,json,os,stat,types,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
O=F/'real-data-pilot-final13-2026-10-06';D=F/'real-data-pilot-final14-2026-10-06';U=F/'real-data-pilot-fixed14-metadata-successor01-2026-10-06';U0=F/'real-data-pilot-fixed13-metadata-successor01-2026-10-06'
N0='eth-paper-real-data-end-to-end-resource-20261006-13';N='eth-paper-real-data-end-to-end-resource-20261006-14'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def need(v,m):
 if not v:raise ValueError(m)
evidence={};bound=ld(D/'TRANSPORT_BINDING02.json');opaque=bound['private_input']['archive_transport']
def add(r):
 p=ROOT/r['path'];assert not any(x in {'keys','apis','.env','hf_token.txt'} for x in p.parts)
 if r['path']==opaque['path']:
  s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==928==opaque['bytes'] and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(p.parent.stat().st_mode)==0o700
 else:assert sha(p)==r['sha256'],r['path']
 evidence[r['path']]=r['sha256']
for name,oldname in [('root_io.py','root_io02.py'),('preflight01.py','preflight02.py')]:
 expected=(O/oldname).read_text().replace(N0,N)
 if name=='preflight01.py':expected=expected.replace('real-data-pilot-fixed13-metadata-successor01','real-data-pilot-fixed14-metadata-successor01').replace('!=84','!=85').replace("'effective_attempt_budget':84","'effective_attempt_budget':85").replace("HERE/'gate02.json'","HERE/'gate01.json'")
 if name=='root_io.py':expected=expected.replace('from preflight02 import','from preflight01 import')
 assert (D/name).read_text()==expected;add(ref(D/name))
assert (U/'successor02.py').read_bytes()==(U0/'successor02.py').read_bytes();add(ref(U/'successor02.py'));add(ref(U/'DEPENDENCIES02.json'))
for name in ['build_inputs03.py','controls01.py']:assert (U/'candidate'/name).read_text()==(U0/'candidate'/name).read_text().replace(N0,N)
for k,r in ld(U/'DEPENDENCIES02.json').items():
 add(r)
 if k not in {'builder','controls'}:assert r==ld(U0/'DEPENDENCIES02.json')[k]
pol=ld(D/'templates/pair_policy01.json');op=ld(O/'templates/pair_policy01.json');oldadopt=ld(F/'real-data-pilot-retry13-review01-2026-10-06/METADATA_REVIEW02.json');anchor='ba6be4fac573be5c5445f6d85b6b8e3db78dea56';pins={p:sha(ROOT/p) for p in oldadopt['package_pins']};changed={p:{'before':oldadopt['package_pins'][p],'after':h} for p,h in pins.items() if h!=oldadopt['package_pins'][p]};assert set(changed)=={'tradingagents/research/onchain_replication/'+n for n in ['real_pilot_storage.py','real_pilot_import_caller.py']};adopt={'package_pins':pins,'source_anchor':anchor};assert pol['numerical_source']==dict(op['numerical_source'],files=adopt['package_pins'],commit=adopt['source_anchor']);norm=copy.deepcopy(pol);norm['numerical_source']=op['numerical_source'];assert norm==op
assert (ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py').read_bytes()==(F/'real-data-pilot-loaded-roster-fix01-2026-10-06/candidate04/real_pilot_import_caller.py').read_bytes()
for name in ['job_template01.json','job_template02.json']:
 before=json.loads((O/'templates'/name).read_text().replace(N0,N));after=ld(D/'templates'/name);before['payload']['representation_jobs']['original32']['descriptor']['pair_execution']['policy_sha256']=sha(D/'templates/pair_policy01.json');assert before==after
assert (D/'templates/pilot.json').read_text()==(O/'templates/pilot.json').read_text().replace(N0,N)
assert (D/'templates/archive_policy.json').read_text()==(O/'templates/archive_policy.json').read_text().replace('ethpilot-20261006-13','ethpilot-20261006-14')
draft=ld(D/'INPUT_DRAFT01.json');old=ld(O/'INPUT_DRAFT02.json');norm=copy.deepcopy(draft)
for k in ['physical_baseline','references','transport_limits']:norm['protocol'][k]=old['protocol'][k]
assert norm==old and draft['protocol']['transport_limits']==dict(old['protocol']['transport_limits'],namespace='ethpilot-20261006-14')
baseline=ld(D/'BASELINE02.json');rawbaseline=ld(D/'BASELINE01.json');assert baseline['result']['observation']==rawbaseline['result'];add(baseline['original_observation_receipt'])
for r in draft['protocol']['references'].values():add(r)
add(draft['protocol']['physical_baseline']['evidence'])
m=types.ModuleType('review_pure_prepare');m.__file__=str(U/'successor02.py');exec(compile((U/'successor02.py').read_bytes(),m.__file__,'exec'),vars(m));saved=ld(D/'PREPARATION_RESULT01.json');assert m.prepare(ROOT,draft)==saved
assert saved['builder03_result']['inputs']['archive_transport']['namespace']=='ethpilot-20261006-14' and saved['builder03_result']['inputs']['archive_transport']['connection'] is None
for r in saved['builder03_spec']['references'].values():add(r)
for name in ['INPUT_DRAFT01.json','PREPARATION_RESULT01.json','TRANSPORT_BINDING02.json','TRANSPORT_REQUEST02.json','INPUT_REFS01.json','BASELINE01.json','BASELINE02.json','CHARTER01.md','NUMERICAL_CONTEXT_REANCHOR01.json']:add(ref(D/name))
binder=F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';add(ref(binder));add(ref(binder.with_name('DEPENDENCIES01.json')))
for r in ld(binder.with_name('DEPENDENCIES01.json')).values():add(r)
tree=ast.parse((D/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');scope={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'review_inverse','exec'),scope)
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest();archive=ld(ROOT/saved['builder03_spec']['references']['archive_policy']['path']);scope['inverse_binding'](saved,archive,bound,opaque,raw,digest)
assert archive['remote_namespace']==bound['inputs']['archive_policy']['remote_namespace']=='ethpilot-20261006-14';add(opaque)
request=ld(D/'TRANSPORT_REQUEST02.json');assert bound['source_request']==request
assert {k:request['prepared'][k] for k in ('path','sha256')}==ref(D/'PREPARATION_RESULT01.json')
assert opaque['path']==request['private_parent']+'/'+request['private_leaf']
refs=ld(D/'INPUT_REFS01.json')
for role,doc in bound['inputs'].items():assert (ROOT/refs[role]['path']).read_bytes()==raw(doc);add(refs[role])
assert refs['archive_transport']==opaque
job=bound['inputs']['execution_job'];oldjob=ld(O/'inputs01/execution_job.json');assert json.dumps(job['resources']).replace(N,N0)==json.dumps(oldjob['resources']);assert bound['inputs']['pilot']['resource_policy']==job['resources'];assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
for name in ['original_import.json','typed_payload.json','resource_population_plan.json','mcm_output_policy.json']:assert (D/'inputs01'/name).read_bytes()==(O/'inputs01'/name).read_bytes()
assert not (ROOT/'research_runs'/N).exists() and not os.path.lexists(ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-14') and not (D/'launch-attempt01.json').exists()

C=U
for name in ['real_pilot_storage.py']:assert (ROOT/'tradingagents/research/onchain_replication'/name).read_bytes()==(C/'candidate'/name).read_bytes()
storage=ROOT/'tradingagents/research/onchain_replication/real_pilot_storage.py';before=subprocess.check_output(['git','show',oldadopt['source_anchor']+':tradingagents/research/onchain_replication/real_pilot_storage.py']);assert storage.read_bytes().replace(N.encode(),N0.encode())==before
proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for p,h in pins.items():
 proc.stdin.write((anchor+':'+p+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().split();body=proc.stdout.read(int(head[2]));assert proc.stdout.read(1)==b'\n' and hashlib.sha256(body).hexdigest()==h
proc.stdin.close();assert proc.wait()==0
G=ld(D/'gate01.json');G0=ld(O/'gate02.json');E=G['experiments'][N];E0=G0['experiments'][N0]
for k in G0:
 if k!='experiments':assert G[k]==G0[k]
for k in E0:
 if k not in {'charter','question','cumulative_budget_extension','source_files','inputs'}:assert E[k]==E0[k]
assert len(E['source_files'])==281 and len(E['inputs'])==59 and set(E['inputs'])==set(E0['inputs']) and E['parent'] is None
for role,r in E['inputs'].items():
 assert set(r)=={'dataset','path','sha256'} and r['dataset']==E0['inputs'][role]['dataset'];assert (r['path']==opaque['path'])==(role=='archive_transport');add(r)
for p,h in E['source_files'].items():add({'path':p,'sha256':h})
assert {p:h for p,h in E['source_files'].items() if p.startswith('tradingagents/')}==pins
assert set(E['charter'])=={'path','sha256'};add(E['charter']);P=F/'real-data-pilot-retry14-registration01-2026-10-06'
assert E['cumulative_budget_extension']=={'extension':ref(P/'EXTENSION_PROPOSED85_01.json'),'review':ref(HERE/'EXTENSION_REVIEW01.json')}
for p in [P/'EXTENSION_PROPOSED85_01.json',P/'CUMULATIVE_ALLOCATION_PROPOSED85_01.json',HERE/'EXTENSION_REVIEW01.json',HERE/'EXTENSION_MACHINE_REVIEW01.json']:
 assert E['source_files'][str(p.relative_to(ROOT))]==sha(p);add(ref(p))
add(ref(D/'gate01.json'));add(ref(HERE/'SOURCE_REVIEW01.json'))
assert E['inputs']['imported_authority_lease']==E0['inputs']['imported_authority_lease'] and ld(ROOT/E['inputs']['imported_authority_lease']['path'])['max_stale_ms']==60000

for r in ld(F/'real-data-pilot-retry12-review01-2026-10-06/SOURCE_REVIEW01.json')['helpers']:assert E['source_files'][r['path']]==r['sha256'];add(r)

result={'schema_version':1,'reviewer':'pilot14_review independent combined adoption/metadata reviewer','decision':'accepted','identity':N,'evidence':evidence,'findings':[],'source_anchor':anchor,'package_pins':pins,'package_count':179,'unchanged_package_count':177,'changed_package_pins':changed,'checks':['Exact adopted candidate04 and strict14 storage body,179 source pins at actual Git anchor;177 other bodies unchanged.','Selected13 root_io02/preflight02 converted by exact identity/helper/gate/budget85 changes only. Six immutable helper refs and successor body preserved.','Actual saved pure prepare equals fresh pure metadata evaluation; accepted binder inverse authenticates eight newline-serialized public bodies and sole opaque14 reference.','All59 input roles/datasets and source281pins authenticate; original graphs/motifs/matching/model/training/native caps and60s input unchanged.','Actual baseline01 direct observation equals baseline02 wrapped result.observation; no modeled or synthetic substitution.'], 'qualification':'Combined changed-source adoption and metadata review only. Pilot13 spent disposition is preserved. Initial binder refusal before publication remains retained. Concrete binding, committed admission, final release and current physical eligibility remain required.','not_tested':['No private input body, scientific arrays, numerical trial, Owner/claim/native launch.','No end-to-end success, capacity, throughput, timing leakage or financial accounting/performance claim.']}
p=HERE/'METADATA_REVIEW01.json';p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
