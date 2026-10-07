import ast,copy,hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry15-review01-2026-10-07';D=F/'real-data-pilot-final15-2026-10-07'
V=H/'remaining-release-review01'
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
# Remaining independent checks: preserved binding review is reused, current byte joins reauthenticated.
assert sha(H/'BINDING_REVIEW01.json')=='f854660318dce17a1d6cf9a4165a8a4391396ebc5a800d095ac56faeabe8182f'
assert sha(D/'BINDING01.json')=='ba1699384129fc812ab9543a7a2e0d0fc9b6d32a42b3a6bd16b7445b71fb6793'
assert sha(D/'ACTUAL_READONLY_ADMISSION01.json')=='e4c2869b97f5c2626750499ca91883ff6c0e1843967398644a7b28c91671a315'
assert len(review['evidence'])==898
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a['source']=='f25c106354d445f3360bbdd07ef919f75ee56d21'
g=ld(D/'gate01.json');e=g['experiments'][final['identity']]
assert len(e['source_files'])==293 and len(e['inputs'])==59
current=dict(e['source_files'])
for role,x in e['inputs'].items():
 assert evidence[x['path']]==x['sha256']
 assert (role=='archive_transport')==(x['path']==opaque['path'])
 if role!='archive_transport':current[x['path']]=x['sha256']
for x in final.values():
 if isinstance(x,dict) and {'path','sha256'}<=set(x):
  assert evidence[x['path']]==x['sha256']
  if x['path']!=opaque['path']:current[x['path']]=x['sha256']
for name in ['root_io.py','preflight01.py','gate01.json','BINDING01.json','ACTUAL_READONLY_ADMISSION01.json']:
 current[str((D/name).relative_to(R))]=evidence[str((D/name).relative_to(R))]
for rel,pin in current.items():
 q=R/rel;assert not any(v in {'keys','apis','.env','hf_token.txt'} for v in q.parts)
 assert q.resolve()==q and q.is_file() and q.stat().st_size<=4*1024**2,rel
 assert sha(q)==pin,rel
# Authenticate current source/input public bytes at the actual readonly source. New release controls are committed by Root next.
commit_refs=dict(e['source_files'])
commit_refs.update({x['path']:x['sha256'] for role,x in e['inputs'].items() if role!='archive_transport'})
commit_refs[str((D/'gate01.json').relative_to(R))]=sha(D/'gate01.json')
queries=[a['source']+':'+rel for rel in commit_refs]
out=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(queries)+'\n').encode());pos=0
for rel,pin in commit_refs.items():
 end=out.index(b'\n',pos);header=out[pos:end].split();assert len(header)==3 and header[1]==b'blob',rel
 size=int(header[2]);pos=end+1;assert hashlib.sha256(out[pos:pos+size]).hexdigest()==pin,rel
 pos+=size;assert out[pos:pos+1]==b'\n';pos+=1
assert pos==len(out)
# Independently invert the three documented public binder changes; never import the launch module.
prepared=ld(D/'PREPARATION_RESULT01.json');bound=ld(D/'TRANSPORT_BINDING01.json');archive=ld(R/prepared['builder03_spec']['references']['archive_policy']['path'])
assert bound['private_input']=={'archive_transport':opaque}
docs=copy.deepcopy(bound['inputs']);roles=prepared['builder03_spec']['template_roles'];bridge=bound['binding']
policy=docs.pop(roles['archive']);assert policy['transport_identity']==bridge['transport_identity']
raw=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
assert hashlib.sha256(raw(policy)).hexdigest()==bridge['archive_policy_sha256']
policy['transport_identity']=None;assert policy==archive
selected=next(iter(docs[roles['job']]['payload']['representation_jobs'].values()));producer=docs[roles['producer_plan']]['producers'][selected['producer']]
for value in (selected,producer):
 assert value['compact_archive_transport_input']=='archive_transport'
 assert value['descriptor']['compact_archive_execution']=={'backend':archive['backend'],'policy_sha256':bridge['archive_policy_sha256']}
 value['descriptor']['compact_archive_execution']['policy_sha256']=bridge['prior_descriptor_policy_sha256']
expected_docs=prepared['builder03_result']['inputs'];assert 'archive_transport' not in docs and expected_docs['archive_transport']['connection'] is None
docs['archive_transport']=expected_docs['archive_transport'];assert docs==expected_docs
for role,doc in bound['inputs'].items():assert (R/e['inputs'][role]['path']).read_bytes()==raw(doc)
assert p.resolve()==p and p.parent.resolve()==p.parent
parent=p.parent.lstat();assert stat.S_IMODE(parent.st_mode)==0o700 and parent.st_uid==os.getuid()
old=F/'real-data-pilot-final14-2026-10-06';n0='eth-paper-real-data-end-to-end-resource-20261006-14'
for name in ['root_io.py','preflight01.py']:
 expected_source=(old/name).read_text().replace(n0,final['identity'])
 if name=='preflight01.py':expected_source=expected_source.replace('real-data-pilot-fixed14-metadata-successor01-2026-10-06','real-data-pilot-fixed15-metadata-successor01-2026-10-07').replace('!=85','!=86').replace("'effective_attempt_budget':85","'effective_attempt_budget':86")
 assert (D/name).read_text()==expected_source
for rel in ['research_runs/'+final['identity'],'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+final['identity'],'research_artifacts/onchain-paper-replication-2026-09-24/sources/'+final['identity'],'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/'+final['identity']]:assert not os.path.lexists(R/rel)
assert not os.path.lexists(D/'outer-exit01.json')

o=ld(F/'real-data-pilot-retry14-review01-2026-10-06/EXACT_LAUNCH_RELEASE01.json')
o.update(identity=final['identity'],reviewer='pilot15_release_resume independent remaining fresh15 conditional release reviewer',binding_sha256=sha(D/'BINDING01.json'),binding_review_sha256=sha(H/'BINDING_REVIEW01.json'),actual_readonly_admission=a,actual_readonly_admission_reference=ref(D/'ACTUAL_READONLY_ADMISSION01.json'),evidence=evidence,
 cardinality={'changed_package_pins':2,'gate_input_roles':59,'gate_source_pins':293,'package_pins':179,'released_unique_references':len(evidence),'sole_opaque_private_exceptions':1,'unchanged_package_pins':177},
 accounting='86=55 genuine closed spent claims (17 correlated prior plus38 actual current;33COMPLETE22FAILED)+28 unchanged pending+two permanent preclaim03reserve74 and08reserve79+one fresh fixed15. Genuine14 claim85 permanently FAILED. No fabricated preclaim, refund, transfer, reopening, cap ladder or financial-fit allowance.',
 scope='Final binding differs solely by authentic review reference and final status from accepted draft01. Genuine committed readonly86/293/59 and exact gate01 bytes joined. Prior immutable14 release and accepted changed metadata/binding evidence reused; no admission or unchanged test matrix repeated. Selected root_io/preflight01/gate01/pure preparation01/binder01 and sole15 dispatch agree.',
 source_provenance_scope='Two package changes from14: candidate archive-history Interval forced boundary completes a fresh full audit after idle before renewal; strict storage identity14→15.177 other package bodies unchanged, including16-module initialization, Lease identity/source authentication and scientific matching/model/training. Imported kernel/scalar helper narrow acceptance and original whole-fixture WITHHELD disposition remain.',
 timing_qualification='Actual14 reached first MCM production attempt then failed on history audit stale before compute. Exact historical stale age is unrecorded. Synthetic317s gap does not reconstruct that age. Forced archive-history full audits now have a fresh audit-entry duration bound; no claim of native15 completion or elimination of every later timing/resource failure.',
 private_transport_scope='SOLE selected15 protected dispatch reference is metadata/stat/public-digest bound and authenticated internally by genuine committed admission. Reviewer did not read private body. Historical opaque inputs excluded from evidence-map body entries.',
 diagnostic_scope='Existing diagnostics and original clocks/poisoning remain. Historical failed outputs and unrecorded archive-history age remain unknown.',
 policy_change='Archive-history force=True may follow idle time but renews only after a complete authenticated audit within strictly less than unchanged60000ms from its entry. Sampled history checks retain prior-age entry/completion bounds. Failure is sticky; no forced recovery after poison. This control is distinct from unchanged imported-authority60000ms policy; no native or scientific limits changed.',
 required_entry={'root_io':ref(D/'root_io.py'),'preflight':ref(D/'preflight01.py'),'gate':ref(D/'gate01.json')})
o['remaining_checks']={'current_public_unique_byte_joins':len(current),'committed_current_unique_byte_joins':len(commit_refs),'source_roles':293,'input_roles':59,'opaque_stat_only':True,'final_public_inverse':True,'prior_binding_references_reused':898}
o['conditionality']=o['conditionality'].replace('fixed14','fixed15')
p=V/'EXACT_LAUNCH_RELEASE01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':sha(p),'references':len(evidence)}))
