"""Independent selected11 metadata inversion. No private contents or numerical inputs."""
import ast,copy,hashlib,json,os,stat,types,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
O=F/'real-data-pilot-final12-2026-10-06';D=F/'real-data-pilot-final13-2026-10-06';U=F/'real-data-pilot-fixed13-metadata-successor01-2026-10-06';U0=F/'real-data-pilot-fixed12-metadata-successor01-2026-10-06'
N0='eth-paper-real-data-end-to-end-resource-20261006-12';N='eth-paper-real-data-end-to-end-resource-20261006-13'
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
for name in ['root_io.py','preflight01.py']:
 expected=(O/name).read_text().replace(N0,N)
 if name=='preflight01.py':expected=expected.replace('real-data-pilot-fixed12-metadata-successor01','real-data-pilot-fixed13-metadata-successor01').replace('!=83','!=84').replace("'effective_attempt_budget':83","'effective_attempt_budget':84")
 assert (D/name).read_text()==expected;add(ref(D/name))
assert (D/'preflight01.py').read_text().count("HERE/'gate01.json'")==2
assert (D/'preflight02.py').read_text()==(D/'preflight01.py').read_text().replace("HERE/'gate01.json'","HERE/'gate02.json'")
assert (D/'root_io02.py').read_text()==(D/'root_io.py').read_text().replace('from preflight01 import','from preflight02 import')
add(ref(D/'preflight02.py'));add(ref(D/'root_io02.py'));add(ref(HERE/'METADATA_FINDING01.json'))
assert (U/'successor02.py').read_bytes()==(U0/'successor02.py').read_bytes();add(ref(U/'successor02.py'));add(ref(U/'DEPENDENCIES02.json'))
for name in ['build_inputs03.py','controls01.py']:assert (U/'candidate'/name).read_text()==(U0/'candidate'/name).read_text().replace(N0,N)
for k,r in ld(U/'DEPENDENCIES02.json').items():
 add(r)
 if k not in {'builder','controls'}:assert r==ld(U0/'DEPENDENCIES02.json')[k]
pol=ld(D/'templates/pair_policy01.json');op=ld(O/'templates/pair_policy01.json');oldadopt=ld(F/'real-data-pilot-retry12-review01-2026-10-06/METADATA_REVIEW01.json');anchor='b37f258932d86f6da1d503d5185b0bfce7cc2c59';pins={p:sha(ROOT/p) for p in oldadopt['package_pins']};changed={p:{'before':oldadopt['package_pins'][p],'after':h} for p,h in pins.items() if h!=oldadopt['package_pins'][p]};assert set(changed)=={'tradingagents/research/onchain_replication/'+n for n in ['real_pilot_storage.py']};adopt={'package_pins':pins,'source_anchor':anchor};assert pol['numerical_source']==dict(op['numerical_source'],files=adopt['package_pins'],commit=adopt['source_anchor']);norm=copy.deepcopy(pol);norm['numerical_source']=op['numerical_source'];assert norm==op
for name in ['job_template01.json','job_template02.json']:
 before=json.loads((O/'templates'/name).read_text().replace(N0,N));after=ld(D/'templates'/name);before['payload']['representation_jobs']['original32']['descriptor']['pair_execution']['policy_sha256']=sha(D/'templates/pair_policy01.json');assert before==after
assert (D/'templates/pilot.json').read_text()==(O/'templates/pilot.json').read_text().replace(N0,N)
assert (D/'templates/archive_policy.json').read_text()==(O/'templates/archive_policy.json').read_text().replace('ethpilot-20261006-12','ethpilot-20261006-13')
draft=ld(D/'INPUT_DRAFT02.json');old=ld(O/'INPUT_DRAFT01.json');norm=copy.deepcopy(draft)
for k in ['physical_baseline','references','transport_limits']:norm['protocol'][k]=old['protocol'][k]
assert norm==old and draft['protocol']['transport_limits']==dict(old['protocol']['transport_limits'],namespace='ethpilot-20261006-13')
baseline=ld(D/'BASELINE02.json');rawbaseline=ld(D/'BASELINE01.json');assert baseline['result']==rawbaseline['result'];add(baseline['original_observation_receipt'])
for r in draft['protocol']['references'].values():add(r)
add(draft['protocol']['physical_baseline']['evidence'])
m=types.ModuleType('review_pure_prepare');m.__file__=str(U/'successor02.py');exec(compile((U/'successor02.py').read_bytes(),m.__file__,'exec'),vars(m));saved=ld(D/'PREPARATION_RESULT02.json');assert m.prepare(ROOT,draft)==saved
assert saved['builder03_result']['inputs']['archive_transport']['namespace']=='ethpilot-20261006-13' and saved['builder03_result']['inputs']['archive_transport']['connection'] is None
for r in saved['builder03_spec']['references'].values():add(r)
for name in ['INPUT_DRAFT02.json','PREPARATION_RESULT02.json','TRANSPORT_BINDING02.json','TRANSPORT_REQUEST02.json','INPUT_REFS02.json','BASELINE01.json','BASELINE02.json','CHARTER01.md','NUMERICAL_CONTEXT_REANCHOR01.json']:add(ref(D/name))
binder=F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';add(ref(binder));add(ref(binder.with_name('DEPENDENCIES01.json')))
for r in ld(binder.with_name('DEPENDENCIES01.json')).values():add(r)
tree=ast.parse((D/'preflight02.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');scope={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'review_inverse','exec'),scope)
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest();archive=ld(ROOT/saved['builder03_spec']['references']['archive_policy']['path']);scope['inverse_binding'](saved,archive,bound,opaque,raw,digest)
assert archive['remote_namespace']==bound['inputs']['archive_policy']['remote_namespace']=='ethpilot-20261006-13';add(opaque)
request=ld(D/'TRANSPORT_REQUEST02.json');assert bound['source_request']==request
assert {k:request['prepared'][k] for k in ('path','sha256')}==ref(D/'PREPARATION_RESULT02.json')
assert opaque['path']==request['private_parent']+'/'+request['private_leaf']
old_draft=ld(D/'INPUT_DRAFT01.json');corrected=copy.deepcopy(old_draft);corrected['protocol']['transport_limits']['namespace']='ethpilot-20261006-13';assert draft==corrected
old_prepared=ld(D/'PREPARATION_RESULT01.json');corrected=copy.deepcopy(old_prepared);corrected['builder03_spec']['transport_limits']['namespace']='ethpilot-20261006-13';corrected['builder03_result']['inputs']['archive_transport']['namespace']='ethpilot-20261006-13';assert saved==corrected
assert bound['inputs']==ld(D/'TRANSPORT_BINDING01.json')['inputs']
for r in ld(HERE/'METADATA_FINDING01.json')['references']:add(r)
refs=ld(D/'INPUT_REFS02.json')
for role,doc in bound['inputs'].items():assert (ROOT/refs[role]['path']).read_bytes()==raw(doc);add(refs[role])
assert refs['archive_transport']==opaque
job=bound['inputs']['execution_job'];oldjob=ld(O/'inputs01/execution_job.json');assert json.dumps(job['resources']).replace(N,N0)==json.dumps(oldjob['resources']);assert bound['inputs']['pilot']['resource_policy']==job['resources'];assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
for name in ['original_import.json','typed_payload.json','resource_population_plan.json','mcm_output_policy.json']:assert (D/'inputs01'/name).read_bytes()==(O/'inputs01'/name).read_bytes()
assert not (ROOT/'research_runs'/N).exists() and not os.path.lexists(ROOT/'research_artifacts/archive-dispatch-ethpilot-20261006-13') and not (D/'launch-attempt01.json').exists()

C=U
for name in ['real_pilot_storage.py']:assert (ROOT/'tradingagents/research/onchain_replication'/name).read_bytes()==(C/'candidate'/name).read_bytes()
storage=ROOT/'tradingagents/research/onchain_replication/real_pilot_storage.py';before=subprocess.check_output(['git','show',oldadopt['source_anchor']+':tradingagents/research/onchain_replication/real_pilot_storage.py']);assert storage.read_bytes().replace(N.encode(),N0.encode())==before
proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for p,h in pins.items():
 proc.stdin.write((anchor+':'+p+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().split();body=proc.stdout.read(int(head[2]));assert proc.stdout.read(1)==b'\n' and hashlib.sha256(body).hexdigest()==h
proc.stdin.close();assert proc.wait()==0
G=ld(D/'gate02.json');G0=ld(O/'gate01.json');E=G['experiments'][N];E0=G0['experiments'][N0]
for k in G0:
 if k!='experiments':assert G[k]==G0[k]
for k in E0:
 if k not in {'charter','question','cumulative_budget_extension','source_files','inputs'}:assert E[k]==E0[k]
assert len(E['source_files'])==269 and len(E['inputs'])==59 and set(E['inputs'])==set(E0['inputs']) and E['parent'] is None
for role,r in E['inputs'].items():
 assert set(r)=={'dataset','path','sha256'} and r['dataset']==E0['inputs'][role]['dataset'];assert (r['path']==opaque['path'])==(role=='archive_transport');add(r)
for p,h in E['source_files'].items():add({'path':p,'sha256':h})
assert {p:h for p,h in E['source_files'].items() if p.startswith('tradingagents/')}==pins
assert set(E['charter'])=={'path','sha256'};add(E['charter']);P=F/'real-data-pilot-retry13-registration01-2026-10-06'
assert E['cumulative_budget_extension']=={'extension':ref(P/'EXTENSION_PROPOSED84_01.json'),'review':ref(HERE/'EXTENSION_REVIEW01.json')}
for p in [P/'EXTENSION_PROPOSED84_01.json',P/'CUMULATIVE_ALLOCATION_PROPOSED84_01.json',HERE/'EXTENSION_REVIEW01.json',HERE/'EXTENSION_MACHINE_REVIEW01.json']:
 assert E['source_files'][str(p.relative_to(ROOT))]==sha(p);add(ref(p))
add(ref(D/'gate02.json'));add(ref(HERE/'SOURCE_REVIEW01.json'))
newlease=ld(U/'candidate/imported_authority_lease.json');oldlease=ld(ROOT/E0['inputs']['imported_authority_lease']['path']);assert newlease==dict(oldlease,max_stale_ms=60000)
assert E['inputs']['imported_authority_lease']['path']==str((U/'candidate/imported_authority_lease.json').relative_to(ROOT)) and E['inputs']['imported_authority_lease']['sha256']==sha(U/'candidate/imported_authority_lease.json')
assert ld(ROOT/E['inputs']['imported_authority_lease']['path'])==ld(HERE/'INTERVAL_CHECK01.json')['selected_policy']

for r in ld(F/'real-data-pilot-retry12-review01-2026-10-06/SOURCE_REVIEW01.json')['helpers']:assert E['source_files'][r['path']]==r['sha256'];add(r)

result={'schema_version':1,'reviewer':'pilot09_review independent metadata reviewer','decision':'accepted','identity':N,'evidence':evidence,'findings':[],'source_anchor':anchor,'package_pins':pins,'package_count':179,'unchanged_package_count':178,'changed_package_pins':changed,'resolved_finding':'P13-NAMESPACE01 corrected by selected draft/preparation/binder02 and new protected13-r2 dispatch; original01 draft/preparation/binder/private artifacts remain preserved. New02 caller/preflight select gate02 with exact inverses.','checks':['Exact caller/preflight and two fixed helper identity inverses, budget84 predicate/receipt only.','Pure metadata prepare equals actual selected01 saved result; exact binder AST inverse matches prepared output.','Exact179-package anchor with178 unchanged bodies; graphs, original input metadata, native caps and resource policy unchanged. Both selected off-package imported kernel/scalar helper paths are now source-pinned and match accepted source review. All eight public input bodies exactly match binder canonical bytes including final newline.','Private selected01 reference inspected by stat/metadata only, no body access; actual committed admission must authenticate body.'],'policy_change':'Explicit user-authorized max_stale_ms30000→60000 ONLY; unchanged source/live100ms/fingerprint1000ms/full10000ms/call65536 contract. This increases permitted detection age, not model/numeric/native limits.','not_tested':['No financial/model/array/native/claim/ledger/private-body execution.','No fresh RAM or full capacity/throughput proof.'],'qualification':'Combined actual one-file source adoption and one-policy change and metadata/gate84 acceptance only; concrete final binding, committed admission and release remain required.'}
p=HERE/'METADATA_REVIEW02.json';p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
