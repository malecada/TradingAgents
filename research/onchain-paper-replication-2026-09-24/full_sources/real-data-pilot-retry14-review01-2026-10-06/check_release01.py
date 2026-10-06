import copy,hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry14-review01-2026-10-06';D=F/'real-data-pilot-final14-2026-10-06'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
draft=ld(D/'BINDING_DRAFT01.json');final=ld(D/'BINDING01.json');review=ld(H/'BINDING_REVIEW01.json');expected=copy.deepcopy(draft);expected['status']='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE';expected['binding_review']=ref(H/'BINDING_REVIEW01.json');assert final==expected and review['decision']=='accepted'
evidence=review['evidence'].copy()
for p in [D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json']:evidence[str(p.relative_to(R))]=sha(p)
opaque=final['transport'];private=[p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')];assert private==[opaque['path']] and evidence[opaque['path']]==opaque['sha256']
for p in [D/'root_io.py',D/'preflight01.py',D/'gate01.json',D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json']:assert evidence[str(p.relative_to(R))]==sha(p)
p=R/opaque['path'];st=p.lstat();assert stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and st.st_size==928 and st.st_uid==os.getuid()
a=ld(D/'ACTUAL_READONLY_ADMISSION01.json');assert a['ready'] and a['effective_attempt_budget']==85 and a['source_pins']==281 and a['input_pins']==59 and a['identity']==final['identity']
assert subprocess.check_output(['git','show',a['source']+':'+str((D/'gate01.json').relative_to(R))])==(D/'gate01.json').read_bytes()
assert not (R/'research_runs'/final['identity']).exists() and not (D/'launch-attempt01.json').exists() and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261006-14')
o=ld(F/'real-data-pilot-retry13-review01-2026-10-06/EXACT_LAUNCH_RELEASE02.json')
o.update(identity=final['identity'],reviewer='pilot14_review independent fresh14 conditional release reviewer',binding_sha256=sha(D/'BINDING01.json'),binding_review_sha256=sha(H/'BINDING_REVIEW01.json'),actual_readonly_admission=a,actual_readonly_admission_reference=ref(D/'ACTUAL_READONLY_ADMISSION01.json'),evidence=evidence,
 cardinality={'changed_package_pins':2,'gate_input_roles':59,'gate_source_pins':281,'package_pins':179,'released_unique_references':len(evidence),'sole_opaque_private_exceptions':1,'unchanged_package_pins':177},
 accounting='85=54 genuine closed spent claims (17 correlated prior plus37 actual current;33COMPLETE21FAILED)+28 unchanged pending+two permanent preclaim03reserve74 and08reserve79+one fresh fixed14. Genuine13 claim84 permanently FAILED. No fabricated preclaim, refund, transfer, reopening, cap ladder or financial-fit allowance.',
 scope='Final binding differs solely by authentic review reference and final status from accepted draft01. Genuine committed readonly85/281/59 and exact gate01 bytes at c91365f4 joined. Prior immutable13 release and accepted changed metadata/binding evidence reused; no admission or unchanged test matrix repeated. Selected root_io/preflight01/gate01/pure preparation01/binder02 and sole14 dispatch agree. Original refused binder01 request/result preserved.',
 source_provenance_scope='Two package changes from13: candidate04 explicitly preloads16 selected module dependencies before immutable Lease activation, and strict storage identity13→14.177 other package bodies unchanged. Lease roster equality, compiled-source authentication, function/code pins,60s policy and native limits remain. Current imported kernel8d810af1/scalar helper30a957ad remain accepted narrowly under current Target/Owner wrapper; original bridge whole-fixture WITHHELD remains.',
 timing_qualification='Actual13 passed seven Target constructors then failed on loaded module/function snapshot equality. Exact historical changed entry is unrecorded. Independent selected-path audit and actual source import-only RED/GREEN probe demonstrate a reproducible late-import defect and fix; no claim that native14 completes or avoids all future timing/resource failures.',
 private_transport_scope='SOLE selected14 protected dispatch reference is metadata/stat/public-digest bound and authenticated internally by genuine committed admission. Reviewer did not read private body. Historical opaque inputs excluded from evidence-map body entries.',
 diagnostic_scope='Existing freshness diagnostics and original clocks/poisoning remain. Historical failed outputs and unrecorded exact loaded-roster entry remain unknown. No synthetic reconstruction of historical13 module change.',
 policy_change='No timing or scientific policy change from13. User-authorized60000ms stale bound,100ms live,1000ms fingerprint,10000ms full intervals and65536 calls remain. No postactivation baseline adoption; imports before activation are source-authenticated by unchanged Lease.',
 required_entry={'root_io':ref(D/'root_io.py'),'preflight':ref(D/'preflight01.py'),'gate':ref(D/'gate01.json')})
o['conditionality']=o['conditionality'].replace('fixed13','fixed14')
p=H/'EXACT_LAUNCH_RELEASE01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
