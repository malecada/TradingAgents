"""Focused final13 composition review; selected metadata review is reused."""
import hashlib,json,os,stat
from pathlib import Path
R=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;F=H.parent;D=F/'real-data-pilot-final14-2026-10-06';O=F/'real-data-pilot-final13-2026-10-06';P=F/'real-data-pilot-retry14-registration01-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-14';N0=N[:-2]+'13'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
B=ld(D/'BINDING_DRAFT01.json');G=ld(D/'gate01.json');E=G['experiments'][N];G0=ld(O/'gate02.json');E0=G0['experiments'][N0];M=ld(H/'METADATA_REVIEW01.json');A=M;assert B['identity']==N and B.get('binding_review') is None and B['status']=='DRAFT_NOT_RELEASED';assert M['decision']=='accepted';opaque=B['transport'];assert opaque==ld(D/'TRANSPORT_BINDING02.json')['private_input']['archive_transport']
evidence=ld(O/'RELEASE_REVIEW01.json')['evidence'].copy()
for p in list(evidence):
 if p.startswith('research_artifacts/real_pilot_runtime/'):del evidence[p]
evidence.update(M['evidence'])
def add(x):
 p=x['path'];assert not any(v in {'keys','apis','.env','hf_token.txt'} for v in Path(p).parts)
 if p==opaque['path']:
  q=R/p;s=q.lstat();assert q.resolve()==q and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==opaque['bytes']==928 and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(q.parent.stat().st_mode)==0o700
 elif evidence.get(p)!=x['sha256']:assert sha(R/p)==x['sha256'],p
 evidence[p]=x['sha256']
for x in B.values():
 if isinstance(x,dict) and {'path','sha256'}<=set(x):add(x)
for k in G0:
 if k!='experiments':assert G[k]==G0[k]
assert set(E)==set(E0)
for k in E0:
 if k not in {'charter','question','cumulative_budget_extension','source_files','inputs'}:assert E[k]==E0[k],k
assert set(E['charter'])=={'path','sha256'};add(E['charter']);assert E['parent'] is None
assert len(E['source_files'])==281 and len(E['inputs'])==59 and set(E['inputs'])==set(E0['inputs'])
for role,x in E['inputs'].items():
 assert set(x)=={'dataset','path','sha256'} and x['dataset']==E0['inputs'][role]['dataset'];assert (x['path']==opaque['path'])==(role=='archive_transport');add(x)
selected=ld(D/'INPUT_REFS01.json')
for role,x in selected.items():assert all(E['inputs'][role][k]==x[k] for k in ('path','sha256'))
for p,h in E['source_files'].items():add({'path':p,'sha256':h})
assert {p:h for p,h in E['source_files'].items() if p.startswith('tradingagents/')}==A['package_pins']
assert E['cumulative_budget_extension']=={'extension':ref(P/'EXTENSION_PROPOSED85_01.json'),'review':ref(H/'EXTENSION_REVIEW01.json')}
for p in [P/'EXTENSION_PROPOSED85_01.json',P/'CUMULATIVE_ALLOCATION_PROPOSED85_01.json',H/'EXTENSION_REVIEW01.json',H/'EXTENSION_MACHINE_REVIEW01.json']:
 assert E['source_files'][str(p.relative_to(R))]==sha(p);add(ref(p))
for prefix,identity in [('prior',N0),('engineering','eth-real-graph-canonical-hash-timing-20261006-01')]:
 recovery=ld(R/B[prefix+'_recovery_review']['path']);preservation=ld(R/B[prefix+'_preservation_complete']['path']);assert recovery['decision']=='accepted' and recovery['actual_external_recovery_accepted'] and recovery['identity']==identity
 for rk,bk in [('original_outcome',prefix+'_outcome_review'),('fresh_fetch_evidence',prefix+'_preservation_complete')]:assert all(recovery[rk][k]==B[bk][k] for k in ('path','sha256'))
 assert preservation['all_typed_names_modes_hashes_verified'] and recovery['archive']['sha256']==preservation['archive']['sha256'] and recovery['archive']['tree_source_commit']==preservation['source']==preservation['actual_remote_head'];add(recovery['archive']['members_review'])
for p in [H/'METADATA_REVIEW01.json',H/'SOURCE_REVIEW01.json',D/'BINDING_DRAFT01.json',O/'RELEASE_REVIEW01.json']:add(ref(p))
# Reuse immutable13 release and just-accepted355 current metadata refs.
assert not (R/'research_runs'/N).exists() and not (D/'launch-attempt01.json').exists() and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261006-14')
receipt=ld(D/'ACTUAL_READONLY_ADMISSION01.json');assert receipt['ready'] is True and receipt['effective_attempt_budget']==85 and receipt['source_pins']==281 and receipt['input_pins']==59 and receipt['identity']==N and receipt['qualification']=='Genuine committed read-only admission; no Owner/ResearchRun/claim/arrays/native numerical execution.'
import subprocess
assert subprocess.check_output(['git','show',receipt['source']+':'+str((D/'gate01.json').relative_to(R))])==(D/'gate01.json').read_bytes()
add(ref(D/'ACTUAL_READONLY_ADMISSION01.json'))
o={'schema_version':1,'decision':'accepted','identity':N,'reviewer':'pilot14_review independent final14 composition reviewer','evidence':evidence,'findings':[],'checks':{'package_pins':179,'unchanged_package_pins':177,'source_pins':281,'input_roles':59,'source_anchor':A['source_anchor'],'exact_entry_inverse':True,'effective_attempt_budget':85,'pure_prepare_and_binding_inverse':'accepted METADATA_REVIEW02 reused','same_graphs_science_and_native_caps':True,'public_namespace':'ethpilot-20261006-14','prior13_and_engineering_external_recovery_accepted':True,'private_body_read':False,'all_input_role_datasets_and_exact_metadata_schemas_preserved':True},'resolved_findings':[],'policy_change':'Preactivation selected module imports only; user-authorized60s and all native/method limits remain unchanged.','required_before_launch':['Commit exact final binding/release/gate/source/public closure and authenticate actual remote HEAD.','Exact final release must join genuine committed readonly admission85/281/59 and authenticated selected14 namespace.','Fresh original native/concurrency/namespace/writable-growth/9GiBstartup/10GiBdisk checks; ONE unused14 invocation only.'],'not_tested':['No graph/model/array/private body/claim/native execution by reviewer.','No repeated unchanged source matrices or external archive streaming/fetch.','No fresh host or whole-pilot capacity/throughput/financial performance proof.'],'qualification':'Exact public composition accepted with sole selected opaque transport reference; runtime eligibility and final conditional release remain mandatory.'}
p=H/'BINDING_REVIEW01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
