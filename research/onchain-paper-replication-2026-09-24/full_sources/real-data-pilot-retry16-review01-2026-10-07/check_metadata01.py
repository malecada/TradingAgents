"""Independent actual16 corrected metadata inversion; no numerical/private bodies."""
import ast,copy,hashlib,json,os,stat,types,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
O=F/'real-data-pilot-final15-2026-10-07';D=F/'real-data-pilot-final16-2026-10-07';U=F/'real-data-pilot-fixed16-metadata-successor01-2026-10-07';U0=F/'real-data-pilot-fixed15-metadata-successor01-2026-10-07'
N0='eth-paper-real-data-end-to-end-resource-20261007-15';N='eth-paper-real-data-end-to-end-resource-20261007-16';ANCHOR='f35e983a25dc777574b653e6644f0e2badf350f5'
S=F/'real-data-pilot-fifteenth-resource-failed-review01-2026-10-07/changed-seams16-review01'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def need(v,m):
 if not v:raise ValueError(m)
evidence={};bound=ld(D/'TRANSPORT_BINDING02.json');opaque=bound['private_input']['archive_transport']
def add(r):
 p=ROOT/r['path'];assert not any(x in {'keys','apis','.env','hf_token.txt'} for x in p.parts)
 if r['path']==opaque['path']:
  s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==opaque['bytes'] and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(p.parent.stat().st_mode)==0o700
 else:assert sha(p)==r['sha256'],r['path']
 evidence[r['path']]=r['sha256']
for name,digest in [('SOURCE_REVIEW01.json','e9af09d983b3052c9e79ec25bf5e3e5ae08b43091bae4924ca341ebdc485731c'),('ENTRY_SEAM_REVIEW01.json','1bc99adde285c25fedb22de1ae3501679fd68383c6fffcebba54f3af99aca94b'),('ADOPTION_REVIEW01.json','3c88d646f01544c86e479a967e0d5591b9e47dd81273ac54e902a5f203f761f8')]:
 assert sha(S/name)==digest;add(ref(S/name))
entry=ld(S/'ENTRY_SEAM_REVIEW01.json')
for name in ('preflight01.py','root_io.py'):
 p=str((D/name).relative_to(ROOT));assert sha(D/name)==entry['evidence'][p];add(ref(D/name))
assert (U/'successor02.py').read_bytes()==(U0/'successor02.py').read_bytes();add(ref(U/'successor02.py'));add(ref(U/'DEPENDENCIES02.json'))
for name in ['build_inputs03.py','controls01.py']:assert (U/'candidate'/name).read_text()==(U0/'candidate'/name).read_text().replace(N0,N)
for k,r in ld(U/'DEPENDENCIES02.json').items():
 add(r)
 if k not in {'builder','controls'}:assert r==ld(U0/'DEPENDENCIES02.json')[k]
pol=ld(D/'templates/pair_policy01.json');op=ld(O/'templates/pair_policy01.json');oldadopt=ld(F/'real-data-pilot-retry15-review01-2026-10-07/METADATA_REVIEW01.json')
pins={p:sha(ROOT/p) for p in oldadopt['package_pins']};changed={p:{'before':oldadopt['package_pins'][p],'after':h} for p,h in pins.items() if h!=oldadopt['package_pins'][p]}
assert len(pins)==179 and len(changed)==5 and set(changed)=={'tradingagents/research/onchain_replication/'+n for n in ['real_pilot_storage.py','job.py','resources.py','real_pilot_import_caller.py','matching_owner.py']}
assert pol['numerical_source']==dict(op['numerical_source'],files=pins,commit=ANCHOR);norm=copy.deepcopy(pol);norm['numerical_source']=op['numerical_source'];assert norm==op
# This is the additive corrected template, not preserved stale01/02.
template=ld(D/'templates/job_template03.json');expected=json.loads((O/'templates/job_template02.json').read_text().replace(N0,N))
expected['resources']['reserve_bytes']=2684354560;expected['resources']['start_reserve_bytes']=9126805504
expected['payload']['representation_jobs']['original32']['descriptor']['pair_execution']['policy_sha256']=sha(D/'templates/pair_policy01.json');assert template==expected
pilot=ld(D/'templates/pilot.json');expected=json.loads((O/'templates/pilot.json').read_text().replace(N0,N));expected['resource_policy']['reserve_bytes']=2684354560;expected['resource_policy']['start_reserve_bytes']=9126805504;assert pilot==expected
assert (D/'templates/archive_policy.json').read_text()==(O/'templates/archive_policy.json').read_text().replace('ethpilot-20261007-15','ethpilot-20261007-16')
draft=ld(D/'INPUT_DRAFT02.json');old=ld(O/'INPUT_DRAFT01.json');norm=copy.deepcopy(draft)
for k in ['physical_baseline','references','transport_limits']:norm['protocol'][k]=old['protocol'][k]
assert norm==old and draft['protocol']['transport_limits']==dict(old['protocol']['transport_limits'],namespace='ethpilot-20261007-16')
assert draft['protocol']['references']['execution_job']['path']==str((D/'templates/job_template03.json').relative_to(ROOT))
baseline=ld(D/'BASELINE03.json');add(ref(D/'BASELINE03.json'))
assert draft['protocol']['physical_baseline']['evidence']['path']==str((D/'BASELINE03.json').relative_to(ROOT))
baseline_result=baseline['result'];declared=draft['protocol']['physical_baseline'];observation=baseline_result['observation']
assert all(declared[k]==observation[v] for k,v in [('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')])
for r in draft['protocol']['references'].values():add(r)
add(draft['protocol']['physical_baseline']['evidence'])
m=types.ModuleType('review_pure_prepare');m.__file__=str(U/'successor02.py');exec(compile((U/'successor02.py').read_bytes(),m.__file__,'exec'),vars(m));saved=ld(D/'PREPARATION_RESULT02.json');assert m.prepare(ROOT,draft)==saved
assert saved['builder03_result']['inputs']['archive_transport']['namespace']=='ethpilot-20261007-16' and saved['builder03_result']['inputs']['archive_transport']['connection'] is None
for r in saved['builder03_spec']['references'].values():add(r)
for name in ['INPUT_DRAFT02.json','PREPARATION_RESULT02.json','TRANSPORT_BINDING02.json','TRANSPORT_REQUEST02.json','INPUT_REFS02.json','BASELINE03.json','CHARTER01.md','NUMERICAL_CONTEXT_REANCHOR01.json']:add(ref(D/name))
binder=F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';add(ref(binder));add(ref(binder.with_name('DEPENDENCIES01.json')))
for r in ld(binder.with_name('DEPENDENCIES01.json')).values():add(r)
tree=ast.parse((D/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');scope={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'review_inverse','exec'),scope)
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest();archive=ld(ROOT/saved['builder03_spec']['references']['archive_policy']['path']);scope['inverse_binding'](saved,archive,bound,opaque,raw,digest)
assert archive['remote_namespace']==bound['inputs']['archive_policy']['remote_namespace']=='ethpilot-20261007-16';add(opaque)
request=ld(D/'TRANSPORT_REQUEST02.json');assert bound['source_request']==request
assert {k:request['prepared'][k] for k in ('path','sha256')}==ref(D/'PREPARATION_RESULT02.json')
assert opaque['path']==request['private_parent']+'/'+request['private_leaf'] and opaque['path']!=ld(D/'TRANSPORT_BINDING01.json')['private_input']['archive_transport']['path']
refs=ld(D/'INPUT_REFS02.json')
for role,doc in bound['inputs'].items():assert (ROOT/refs[role]['path']).read_bytes()==raw(doc);add(refs[role])
assert refs['archive_transport']==opaque
job=bound['inputs']['execution_job'];oldjob=ld(O/'inputs01/execution_job.json');old_resources=json.loads(json.dumps(oldjob['resources']).replace(N0,N));old_resources.update(reserve_bytes=2684354560,start_reserve_bytes=9126805504)
assert job['resources']==old_resources and bound['inputs']['pilot']['resource_policy']==job['resources'];assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
selected=job['payload']['representation_jobs']['original32'];producer=bound['inputs']['producer_plan']['producers'][selected['producer']]
assert selected['descriptor']==producer['descriptor'] and selected['descriptor']['pair_execution']['policy_sha256']==sha(D/'templates/pair_policy01.json')
for name in ['original_import','typed_payload','resource_population_plan','mcm_output_policy']:assert (ROOT/refs[name]['path']).read_bytes()==(O/'inputs01'/(name+'.json')).read_bytes()
assert not (ROOT/'research_runs'/N).exists() and not os.path.lexists(ROOT/'research_artifacts/archive-dispatch-ethpilot-20261007-16') and not (D/'launch-attempt01.json').exists()
# Authenticate the exact179 source bodies at the supplied actual Git anchor in one batch.
queries=[ANCHOR+':'+p for p in pins];batch=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(queries)+'\n').encode());pos=0
for p,h in pins.items():
 end=batch.index(b'\n',pos);header=batch[pos:end].split();assert header[1]==b'blob';pos=end+1;size=int(header[2]);body=batch[pos:pos+size];pos+=size;assert batch[pos:pos+1]==b'\n';pos+=1;assert hashlib.sha256(body).hexdigest()==h
assert pos==len(batch)
G=ld(D/'gate01.json');G0=ld(O/'gate01.json');E=G['experiments'][N];E0=G0['experiments'][N0]
for k in G0:
 if k!='experiments':assert G[k]==G0[k]
assert set(E)==set(E0)
for k in E0:
 if k not in {'charter','question','cumulative_budget_extension','source_files','inputs'}:assert E[k]==E0[k]
assert len(E['inputs'])==59 and set(E['inputs'])==set(E0['inputs']) and E['parent'] is None
for role,r in E['inputs'].items():
 assert set(r)=={'dataset','path','sha256'} and r['dataset']==E0['inputs'][role]['dataset'];assert (r['path']==opaque['path'])==(role=='archive_transport');add(r)
 if role in refs:assert all(r[k]==refs[role][k] for k in ('path','sha256'))
for p,h in E['source_files'].items():add({'path':p,'sha256':h})
assert {p:h for p,h in E['source_files'].items() if p.startswith('tradingagents/')}==pins
assert set(E['charter'])=={'path','sha256'};add(E['charter']);P=F/'real-data-pilot-retry16-registration01-2026-10-07'
assert E['cumulative_budget_extension']=={'extension':ref(P/'EXTENSION_PROPOSED87_01.json'),'review':ref(HERE/'EXTENSION_REVIEW01.json')}
for p in [P/'EXTENSION_PROPOSED87_01.json',P/'CUMULATIVE_ALLOCATION_PROPOSED87_01.json',HERE/'EXTENSION_REVIEW01.json',HERE/'EXTENSION_MACHINE_REVIEW01.json']:
 assert E['source_files'][str(p.relative_to(ROOT))]==sha(p);add(ref(p))
add(ref(D/'gate01.json'))
assert E['inputs']['imported_authority_lease']==E0['inputs']['imported_authority_lease']
assert E['inputs']['mcm_policy']['path']==str((F/'real-data-pilot-index-capacity01-2026-10-07/mcm_policy01.json').relative_to(ROOT))
assert E['inputs']['mcm_policy']['sha256']=='7a77c3818104a085e713333ce5d428ec696ff0be574cd3a8cc7d6e137ae06ed3'
for role in ('graph_20220502','graph_20220509','graph_20220516','graph_20220523','graph_20220530','graph_20220606','graph_20220613'):
 assert E['inputs'][role]==E0['inputs'][role]
result={'schema_version':1,'reviewer':'outcome15_review independent retry16 metadata reviewer','decision':'accepted','identity':N,'evidence':evidence,'findings':[],'source_anchor':ANCHOR,'package_pins':pins,'package_count':179,'unchanged_package_count':174,'changed_package_pins':changed,'source_pins':len(E['source_files']),'input_roles':59,'selected_files':{'draft':'INPUT_DRAFT02.json','preparation':'PREPARATION_RESULT02.json','binding':'TRANSPORT_BINDING02.json','inputs':'INPUT_REFS02.json','baseline':'BASELINE03.json','job_template':'templates/job_template03.json','gate':'gate01.json'},'resolved_findings':[ref(HERE/'METADATA_REJECTED01.json'),ref(HERE/'METADATA_ADDITIONAL_FINDING01.json')],'checks':['Prior accepted source/entry/adoption seams reused by exact pins; actual179package pins authenticated atf35e983a,5 changed174 unchanged.','Actual corrected pure preparation independently equals saved02; selected transport namespace16 matches public archive policy16.','Actual binder inverse authenticates eight newline-serialized public documents and distinct selected opaque02 reference; private body not read.','Actual reanchored pair policy SHA matches both selected execution and producer descriptors.','Only two authorized numeric reservation fields and two user-authorized RAM reserve fields differ from frozen15 method/resources; seven graph refs/32motifs512samples/model/training retained.','Original01 refused draft/preparation/binding/inputs preserved. New02 uses actual baseline03 observation and genuine original metadata adapters.','59 original input roles and all selected source pins authenticate; cumulative87 exact review joined.'],'qualification':'Corrected source/metadata accepted. Concrete final binding, committed read-only admission87, exact release, actual remote authentication and fresh resource eligibility remain required. No claim or native launch.','not_tested':['Private dispatch contents/credentials, graph or numerical payloads, labels, runtime or financial data.','No experiment, Owner, claim, native process, direct preflight/RootIO or unchanged test matrix.','No whole-pilot capacity/throughput/numerical agreement/leakage/accounting/fees/funding proof.']}
p=HERE/'METADATA_REVIEW01.json'
with p.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'sha256':sha(p),'references':len(evidence),'source_pins':len(E['source_files'])}))
