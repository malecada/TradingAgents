import copy,hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry12-review01-2026-10-06';D=F/'real-data-pilot-final12-2026-10-06'
def ld(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
draft=ld(D/'BINDING_DRAFT01.json');final=ld(D/'BINDING01.json');review=ld(H/'BINDING_REVIEW01.json');expected=copy.deepcopy(draft);expected['status']='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE';expected['binding_review']=ref(H/'BINDING_REVIEW01.json');assert final==expected and review['decision']=='accepted' and sha(D/'BINDING01.json')=='6e464a221767c7dae5f1156bbe4d934fb82fdf5e8245c73aacc08e1af9803971'
evidence=review['evidence'].copy()
for p in [D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json']:evidence[str(p.relative_to(R))]=sha(p)
opaque=final['transport'];private=[p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')];assert private==[opaque['path']] and evidence[opaque['path']]==opaque['sha256']
# Authenticate only the new final seams here; all other public refs were authenticated in the accepted binding review.
for p in [D/'root_io.py',D/'preflight01.py',D/'gate01.json',D/'BINDING01.json',H/'BINDING_REVIEW01.json',D/'ACTUAL_READONLY_ADMISSION01.json']:assert evidence[str(p.relative_to(R))]==sha(p)
p=R/opaque['path'];st=p.lstat();assert stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and st.st_size==928 and st.st_uid==os.getuid()
a=ld(D/'ACTUAL_READONLY_ADMISSION01.json');assert a['ready'] and a['effective_attempt_budget']==83 and a['source_pins']==256 and a['compact_input_pins']==59 and not a['research_run_start_called'] and not a['scientific_owner_created']
assert subprocess.check_output(['git','show',a['source']+':'+str((D/'gate01.json').relative_to(R))])==(D/'gate01.json').read_bytes()
assert not (R/'research_runs'/final['identity']).exists() and not (D/'launch-attempt01.json').exists() and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261006-12')
o=ld(F/'real-data-pilot-retry11-review01-2026-10-06/EXACT_LAUNCH_RELEASE01.json')
o.update(identity=final['identity'],reviewer='pilot09_review independent fresh12 conditional release reviewer',binding_sha256=sha(D/'BINDING01.json'),binding_review_sha256=sha(H/'BINDING_REVIEW01.json'),actual_readonly_admission=a,actual_readonly_admission_reference=ref(D/'ACTUAL_READONLY_ADMISSION01.json'),evidence=evidence,
 cardinality={'changed_package_pins':2,'gate_input_roles':59,'gate_source_pins':256,'package_pins':179,'released_unique_references':len(evidence),'sole_opaque_private_exceptions':1,'unchanged_package_pins':177},
 accounting='83=52 genuine closed spent claims (17 correlated prior plus35 actual current;33COMPLETE19FAILED)+28 unchanged pending+two permanent preclaim03reserve74 and08reserve79+one fresh fixed12. Genuine11 claim82 permanently FAILED. No fabricated preclaim, refund, transfer, reopening, cap ladder or financial-fit allowance.',
 scope='Final binding differs solely by authentic review reference and final status from accepted draft. Genuine committed readonly83/256/59 and exact gate bytes atf399d1f7 joined without synthetic fields. Accepted binding760 refs reused; no admission or unchanged matrix repeated. Both unchanged numerical helper source paths are explicitly registered and the fresh caller validates the exact Target source closure and actual hashes before downstream scientific work.',
 source_provenance_scope='Current exact imported kernel8d810af1 and scalar helper30a957ad accepted narrowly in SOURCE_REVIEW01 under current Target/Owner wrapper; complete n*32 coverage and scoped callback joins inspected. Original bridge whole-fixture WITHHELD disposition remains, and historical pair-workload acceptance remains isolated purpose/scalar scope. No helper-body mutation, sampling, clustering, tolerance or architecture change.',
 timing_qualification='Actual11 passed all seven Target constructors and then failed before MCM computation on missing helper source registration; this does not prove full MCM or training capacity. Earlier timing boundaries and30s mandatory refusal remain unchanged.',
 private_transport_scope='SOLE selected12 protected dispatch reference is metadata/stat/public-digest bound and authenticated internally by genuine committed admission. Reviewer did not read private body. Historical opaque inputs excluded from evidence-map body entries.')
o['conditionality']=o['conditionality'].replace('fixed11','fixed12');o['not_tested'][2]='No fresh host eligibility, full pair workspace, complete seven-graph/MCM/training capacity, throughput or ETA.'
p=H/'EXACT_LAUNCH_RELEASE01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
