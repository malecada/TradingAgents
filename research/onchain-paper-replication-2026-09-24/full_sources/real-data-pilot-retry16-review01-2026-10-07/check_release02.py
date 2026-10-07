"""Exact final16 public binding and committed selected-source closure; no launch."""
import copy,hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry16-review01-2026-10-07';D=F/'real-data-pilot-final16-2026-10-07';O=F/'real-data-pilot-final15-2026-10-07'
N='eth-paper-real-data-end-to-end-resource-20261007-16';SOURCE='e5785017bbcf71098ae69bc9383c12da371f41f2'
cache={}
def raw(p):
 p=Path(p)
 if p not in cache:
  s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
  b=p.read_bytes();z=p.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);cache[p]=b
 return cache[p]
def ld(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
draft=ld(D/'BINDING_DRAFT01.json');final=ld(D/'BINDING01.json');review=ld(H/'BINDING_REVIEW01.json');metadata=ld(H/'METADATA_REVIEW01.json')
assert sha(H/'BINDING_REVIEW01.json')=='c31b63713d7b653b07f3b0bd474c825ebacd8dac91a303ea49381ec4172f3d2b'
assert sha(H/'METADATA_REVIEW01.json')=='bb2cf631df09f51e3905e0ab1f981ee9a78b950a82eb0069db1fe217d8ea7b57'
assert sha(D/'BINDING01.json')=='bff84688fc48af061b7ca571197622ff6e5bfbef5a3b5e7f134a5e4ff61eaeea'
expected=copy.deepcopy(draft);expected['status']='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE';expected['binding_review']={**ref(H/'BINDING_REVIEW01.json'),'bytes':len(raw(H/'BINDING_REVIEW01.json'))}
assert final==expected and review['decision']==metadata['decision']=='accepted' and final['identity']==N
evidence=review['evidence'].copy();assert len(evidence)==945
for p in (D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json'):evidence[str(p.relative_to(R))]=sha(p)
opaque=final['transport'];private=[p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')]
assert private==[opaque['path']] and evidence[opaque['path']]==opaque['sha256']
q=R/opaque['path'];s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size==opaque['bytes']==928 and s.st_uid==os.getuid()
assert q.parent.resolve(strict=True)==q.parent and stat.S_IMODE(q.parent.stat().st_mode)==0o700
admission=ld(D/'ACTUAL_READONLY_ADMISSION01.json');assert admission['source']==SOURCE and admission['ready'] is True and admission['effective_attempt_budget']==87 and admission['source_pins']==298 and admission['input_roles']==59 and admission['experiment']==N
assert admission['registration']==str((D/'gate01.json').relative_to(R))
assert admission['resource_policy']==dict(disk_floor_bytes=10737418240,memory_high_bytes=5368709120,memory_max_bytes=6442450944,reserve_bytes=2684354560,start_reserve_bytes=9126805504)
gate=ld(D/'gate01.json');experiment=gate['experiments'][N]
assert len(experiment['source_files'])==298 and len(experiment['inputs'])==59
current=dict(experiment['source_files'])
for role,r in experiment['inputs'].items():
 assert (r['path']==opaque['path'])==(role=='archive_transport')
 if role!='archive_transport':
  assert current.get(r['path'],r['sha256'])==r['sha256'];current[r['path']]=r['sha256']
 else:assert r['sha256']==opaque['sha256']
current[str((D/'gate01.json').relative_to(R))]=sha(D/'gate01.json')
for p,h in current.items():assert evidence[p]==h and sha(R/p)==h
# Current selected public closure only, no old archive/historical store body reads.
queries=[SOURCE+':'+p for p in current];batch=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(queries)+'\n').encode());pos=0
for p,h in current.items():
 end=batch.index(b'\n',pos);header=batch[pos:end].split();assert len(header)==3 and header[1]==b'blob';pos=end+1;size=int(header[2]);b=batch[pos:pos+size];pos+=size
 assert batch[pos:pos+1]==b'\n' and b==raw(R/p) and hashlib.sha256(b).hexdigest()==h;pos+=1
assert pos==len(batch)
for p in (D/'root_io.py',D/'preflight01.py',D/'gate01.json',D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json'):
 assert evidence[str(p.relative_to(R))]==sha(p)
for r in final.values():
 if isinstance(r,dict) and {'path','sha256'}<=set(r):assert evidence[r['path']]==r['sha256']
assert not (R/'research_runs'/N).exists() and not (D/'launch-attempt01.json').exists() and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261007-16')
prior=ld(O/'RELEASE_REVIEW01.json')
result={'schema_version':1,'decision':'accepted','identity':N,'reviewer':'outcome15_review independent exact final16 conditional release reviewer','financial_fit_admitted':False,'strategy_validated':False,
 'binding_sha256':sha(D/'BINDING01.json'),'binding_review_sha256':sha(H/'BINDING_REVIEW01.json'),'actual_readonly_admission':admission,'actual_readonly_admission_reference':ref(D/'ACTUAL_READONLY_ADMISSION01.json'),'evidence':evidence,
 'cardinality':{'changed_package_pins':5,'gate_input_roles':59,'gate_source_pins':298,'package_pins':179,'released_unique_references':len(evidence),'sole_opaque_private_exceptions':1,'unchanged_package_pins':174},
 'remaining_checks':{'current_committed_public_unique_byte_joins':len(current),'final_public_inverse':True,'opaque_stat_only':True,'prior_binding_references_reused':945,'source_roles':298,'input_roles':59},
 'accounting':'87=56 genuine closed spent claims(17 correlated prior+39 current)+28 unchanged pending+two permanently closed preclaim03/08 reserves+ONE unused fixed16. Original15 genuinely FAILED at86 with public increment freshly externally recovered and independently accepted. No refund, transfer, historical reopening, resampling, cap ladder or new financial-fit allowance.',
 'scope':'Final binding differs solely by authentic binding-review reference and final status from accepted draft01. Genuine committed readonly87/298/59 at e5785017 and exact selected public source/input/gate bytes joined offline. Prior15 immutable release and current source/entry/adoption/corrected02metadata/binding reviews reused; no admission or unchanged test matrix repeated. Selected root_io/preflight01/gate01, draft02/preparation02/binder02/inputs02, baseline03/jobtemplate03 and sole16-02 private dispatch agree.',
 'source_provenance_scope':'Four exact authenticated RAM validator/consumer deltas plus one strict fixed15to16 identity replacement;174 other package bodies unchanged at sourceanchorf35e983a. No index algorithm, complete-neighborhood rule, original32 motifs512 samples, seven full ETH graphs, model/training or matching precision change. Existing source authority and imported-kernel/scalar-helper acceptance boundaries remain.',
 'policy_change':'Finite metadata-derived all7graph max_buffer_bytes439582708 and max_numeric_bytes729564276 replace inherited1MiB fixture reserve; max_output_bytes289981568/chunk4096 unchanged. Exact authorized startup8.5GiB=6GiBhardcap+2.5GiBhostreserve;5GiBhigh/zeroSwap/10GiBdisk/2CPU/28800s/file1GiB unchanged. Authenticated schema2 pilot only; unrelated/default3GiBreserve unchanged. Early bounded-header capacity validation precedes explicit torch inventory; original full graph validation and native stop controls remain authoritative.',
 'resolved_findings':[ref(H/'METADATA_REJECTED01.json'),ref(H/'METADATA_ADDITIONAL_FINDING01.json'),ref(H/'GATE_BUDGET_PIN_FINDING01.json')],
 'private_transport_scope':'Sole selected16-02 protected dispatch reference checked by exact public binding, file type/mode/owner/size and internally by genuine committed admission. Reviewer never read private body. Historical opaque references excluded from release evidence map.',
 'conditionality':'Root must commit exact final binding/release/public closure, authenticate actual remote HEAD, then freshly pass original source/input/runtime, selected namespaces, competing native/process/claim, complete writable union plus projected growth,10GiBdisk and8.5GiBstartup checks. Preserve6GiBmax/5GiBhigh/swap0/2.5GiBhostreserve/twoCPU/28800s/file1GiB and original writable limits. At most ONE unused fixed16 invocation; never relaunch after any attempt. Preserve all failed/spent/reserved outputs and unknowns. Successful partial/index admission is not end-to-end scientific completion.',
 'timing_qualification':'Actual15 refused index additive demand before first matching pair;three zero-pair partial records do not estimate useful throughput. Metadata-derived reservation is not measured full-job peak. Existing60s imported-authority/archive-history controls remain unchanged; no future timing/host/capacity guarantee.',
 'control_boundary':prior['control_boundary'],'full_validation_scope':prior['full_validation_scope'],'storage_scope':prior['storage_scope'],'timing_scope':prior['timing_scope'],
 'required_entry':{'root_io':ref(D/'root_io.py'),'preflight':ref(D/'preflight01.py'),'gate':ref(D/'gate01.json')},
 'not_tested':['No reviewer claim/ledger/registration mutation, Admission/Owner/native launch, numerical payload/private body, graph/model fit or empirical run.','No replay of unchanged source/test matrices, remote fetch or archive streams.','No fresh host eligibility, seven-graph live memory/model capacity, useful feature throughput, completion ETA or numerical agreement.','No timing leakage, financial cashflows/returns, fees/funding/exposure or profitability validation.']}
p=H/'EXACT_LAUNCH_RELEASE01.json'
with p.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
m=H/'FINAL_REVIEW_MANIFEST01.json'
with m.open('x') as f:json.dump({'schema_version':1,'decision':'accepted','files':[ref(H/'check_release02.py'),ref(H/'BINDING_REVIEW01.json'),ref(p)]},f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'release':ref(p),'manifest':ref(m),'references':len(evidence),'committed_public_joins':len(current)}))
