import copy,hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry15-review01-2026-10-07';D=F/'real-data-pilot-final15-2026-10-07'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
draft=ld(D/'BINDING_DRAFT01.json');final=ld(D/'BINDING01.json');review=ld(H/'BINDING_REVIEW01.json');expected=copy.deepcopy(draft);expected['status']='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE';expected['binding_review']=ref(H/'BINDING_REVIEW01.json');assert final==expected and review['decision']=='accepted'
evidence=review['evidence'].copy()
for p in [D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json']:evidence[str(p.relative_to(R))]=sha(p)
opaque=final['transport'];private=[p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')];assert private==[opaque['path']] and evidence[opaque['path']]==opaque['sha256']
for p in [D/'root_io.py',D/'preflight01.py',D/'gate01.json',D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json']:assert evidence[str(p.relative_to(R))]==sha(p)
p=R/opaque['path'];st=p.lstat();assert stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and st.st_size==928 and st.st_uid==os.getuid()
a=ld(D/'ACTUAL_READONLY_ADMISSION01.json');assert a['ready'] and a['effective_attempt_budget']==86 and a['source_pins']==293 and a['input_pins']==59 and a['identity']==final['identity']
assert subprocess.check_output(['git','show',a['source']+':'+str((D/'gate01.json').relative_to(R))])==(D/'gate01.json').read_bytes()
assert not (R/'research_runs'/final['identity']).exists() and not (D/'launch-attempt01.json').exists() and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261007-15')
o=ld(F/'real-data-pilot-retry14-review01-2026-10-06/EXACT_LAUNCH_RELEASE01.json')
o.update(identity=final['identity'],reviewer='pilot14_review independent fresh15 conditional release reviewer',binding_sha256=sha(D/'BINDING01.json'),binding_review_sha256=sha(H/'BINDING_REVIEW01.json'),actual_readonly_admission=a,actual_readonly_admission_reference=ref(D/'ACTUAL_READONLY_ADMISSION01.json'),evidence=evidence,
 cardinality={'changed_package_pins':2,'gate_input_roles':59,'gate_source_pins':293,'package_pins':179,'released_unique_references':len(evidence),'sole_opaque_private_exceptions':1,'unchanged_package_pins':177},
 accounting='86=55 genuine closed spent claims (17 correlated prior plus38 actual current;33COMPLETE22FAILED)+28 unchanged pending+two permanent preclaim03reserve74 and08reserve79+one fresh fixed15. Genuine14 claim85 permanently FAILED. No fabricated preclaim, refund, transfer, reopening, cap ladder or financial-fit allowance.',
 scope='Final binding differs solely by authentic review reference and final status from accepted draft01. Genuine committed readonly86/293/59 and exact gate01 bytes joined. Prior immutable14 release and accepted changed metadata/binding evidence reused; no admission or unchanged test matrix repeated. Selected root_io/preflight01/gate01/pure preparation01/binder01 and sole15 dispatch agree.',
 source_provenance_scope='Two package changes from14: candidate archive-history Interval forced boundary completes a fresh full audit after idle before renewal; strict storage identity14→15.177 other package bodies unchanged, including16-module initialization, Lease identity/source authentication and scientific matching/model/training. Imported kernel/scalar helper narrow acceptance and original whole-fixture WITHHELD disposition remain.',
 timing_qualification='Actual14 reached first MCM production attempt then failed on history audit stale before compute. Exact historical stale age is unrecorded. Synthetic317s gap does not reconstruct that age. Forced archive-history full audits now have a fresh audit-entry duration bound; no claim of native15 completion or elimination of every later timing/resource failure.',
 private_transport_scope='SOLE selected15 protected dispatch reference is metadata/stat/public-digest bound and authenticated internally by genuine committed admission. Reviewer did not read private body. Historical opaque inputs excluded from evidence-map body entries.',
 diagnostic_scope='Existing diagnostics and original clocks/poisoning remain. Historical failed outputs and unrecorded archive-history age remain unknown.',
 policy_change='Archive-history force=True may follow idle time but renews only after a complete authenticated audit within strictly less than unchanged60000ms from its entry. Sampled history checks retain prior-age entry/completion bounds. Failure is sticky; no forced recovery after poison. This control is distinct from unchanged imported-authority60000ms policy; no native or scientific limits changed.',
 required_entry={'root_io':ref(D/'root_io.py'),'preflight':ref(D/'preflight01.py'),'gate':ref(D/'gate01.json')})
o['conditionality']=o['conditionality'].replace('fixed14','fixed15')
p=H/'EXACT_LAUNCH_RELEASE01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
