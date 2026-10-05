from pathlib import Path
import json,hashlib,collections,io,gzip,tarfile,stat,subprocess
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-increment-preservation-review01-2026-10-05';Q=F/'held-consumer-canonical-current-capture01-2026-10-05';T=F/'held-consumer-canonical-current-flat01-2026-10-05';R=F/'held-consumer-canonical-current-remote01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-root-launch-20261005-01');S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
SOURCE='468d756c16b3825e83a931c082ab4072764a873d';ID='original-import-canonical-held-success-20261005-01'
def h(b):return hashlib.sha256(b).hexdigest()
def raw(p):return p.read_bytes()
def load(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':h(raw(p))}
def encode(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def put(n,o):
 p=D/n
 with p.open('xb') as f:f.write(encode(o)+b'\n')
 p.chmod(0o444);print(n,h(raw(p)))
 return ref(p)
def pinned(p,s):
 b=raw(p);assert h(b)==s,(str(p),h(b));return json.loads(b)
receipt=pinned(T/'RECOVERY01.json','8039f5c712ef1414f5dd1439b0630609f766ff4d6790b7bf720993c4b3d258e4')
root=pinned(T/'ACTUAL_ROOT_EXIT01.json','6d77cc45f7d48c98a9761bac4488cb4240d6188d96f3b47c1883af2f6e8c5cb7')
assert root['actual_root_exit_code']==0 and root['recovery_receipt_sha256']==h(raw(T/'RECOVERY01.json'))
for k in ('stdout','stderr'):assert h(raw(C/('CANONICAL_CURRENT_FLAT01.'+k)))==root[k+'_sha256']
assert not raw(C/'CANONICAL_CURRENT_FLAT01.stderr')
assert root['source_sha256']==h(raw(C/'CANONICAL_CURRENT_FLAT01.py'))=='cfe08470746610468ef047cf057f2cd5ec4258a68ba743445c8acb12107c47a9'
remotecheck=pinned(D/'REMOTE_CHECK01.json','88db4a0759280ba54b986d8995cb59a3e4e24932f14636562bd57824ddecd367')
assert receipt['receiver_receipt_sha256']==h(raw(R/'REMOTE_RECOVERY01.json'))=='5d314ac03e00c41c4a9a3d04c06145e0830a18d7bc04f1e3a1b704e088c5a07a'
assert receipt['actual_receiver_root_exit_sha256']==h(raw(R/'ACTUAL_ROOT_EXIT01.json'))=='b18b422d8e893ae174cc4a4b547095ee3a66d66267ef4ece8f9869b21716bf63'
meta=pinned(T/'flat/body-metadata.json','6ec77a7f8499b2b2a53ac11a699df39071217e23a6ec68c27dadd8f40c761d2d')
manifest=pinned(Q/'snapshot-manifest.json','1bf39e5fa3b15a3b77017023b0ccbd21d89d5610f10e9b9a6aa9f4b5c7da620a')
assert meta['manifest']==manifest and len(manifest['members'])==135
rows={r['path']:r for r in manifest['members']};assert set(meta['flat_members'])==set(rows) and len(set(meta['flat_members'].values()))==135
assert {p.name for p in (T/'flat').iterdir()}==set(meta['flat_members'].values())|{'body-metadata.json'}
cache={}
for name,n in meta['flat_members'].items():
 p=T/'flat'/n;st=p.lstat();assert p.parent==T/'flat' and stat.S_ISREG(st.st_mode) and st.st_nlink==1
 b=raw(p);r=rows[name];assert r['kind']=='file' and len(b)==r['bytes'] and h(b)==r['sha256'];cache[name]=b
c=json.loads(cache['COMPOSITION01.json']);assert cache['COMPOSITION01.json']==raw(Q/'snapshot/COMPOSITION01.json')
capcheck=pinned(D/'CAPTURE_CHECK01.json','a12e2c832d34fdcf08696f48e5eb038e678b4d93e5281097e837d40cbe755210')
assert ref(Q/'snapshot/COMPOSITION01.json')==capcheck['composition']
base=pinned(Path(c['original_capsule_metadata']['path']),'d8b81554205b9eeb5523fbed41ba616ffc79a0b7fb78c6779b2bcee7f4844fdb')
assert h((json.dumps(base['manifest'],sort_keys=True,indent=2,allow_nan=False)+'\n').encode())=='52d650e256c6e11d9362a215d8af50197cac6be27c951175a5837508570f20d3'
old={r['path']:r for r in base['manifest']['members'] if r['kind']=='file'};assert len(old)==716
for item in c['inherited_recovery'].values():assert ref(Path(item['path']))==item
expected={};counts={}
for label,m in c['manifests'].items():
 assert len({r['path'] for r in m['members']})==len(m['members'])
 counts[label]={'regular':sum(r['kind']=='file' for r in m['members']),'typed':len(m['members'])}
 for r in m['members']:
  assert not Path(r['path']).is_absolute() and '..' not in Path(r['path']).parts
  if r['kind']=='file':expected[label+'/'+r['path']]=r
assert counts==capcheck['scope_counts'] and set(expected)==set(c['body_joins']) and len(expected)==824
kind=collections.Counter();new=set()
for name,j in c['body_joins'].items():
 r=expected[name];assert (r['sha256'],r['bytes'])==(j['sha256'],j['bytes']);kind[j['kind']]+=1
 if j['kind']=='new-body':
  b=cache[j['snapshot_name']];assert h(b)==j['sha256'] and len(b)==j['bytes'];new.add(j['snapshot_name'])
 else:
  assert j['kind']=='inherited-original-body';prior=old[j['original_path']];assert (prior['sha256'],prior['bytes'])==(j['sha256'],j['bytes'])
assert kind=={'new-body':166,'inherited-original-body':658} and len(new)==134 and sum(len(cache[n]) for n in new)==1432931
sink=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
  for r in manifest['members']:
   t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0;t.size=len(cache[r['path']]);tf.addfile(t,io.BytesIO(cache[r['path']]))
archive_path=R/'selected'/Q.relative_to(M)/'increment.tar.gz'
archive=raw(archive_path);assert sink.getvalue()==archive and h(archive)=='5655787612895dd1fbdf6fec7f52eca2df88adb5da6ab8af1123e36b2dfcaf71'
assert c['source']==SOURCE==subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=S,text=True)
for n in ['launch_success01.py','held_outcome02.py','request-unreleased01.json','release-unreleased01.json']:
 j=c['body_joins']['Parent/'+n];assert j['kind']=='new-body' and raw(P/n)==cache[j['snapshot_name']]
check=put('FLAT_CHECK01.json',{'schema_version':1,'decision':'accepted-actual-canonical-increment-flat-byte-recovery','actual_flat_receipt':ref(T/'RECOVERY01.json'),'actual_flat_root_exit':ref(T/'ACTUAL_ROOT_EXIT01.json'),'flat_metadata':ref(T/'flat/body-metadata.json'),'remote_check':ref(D/'REMOTE_CHECK01.json'),'capture_check':ref(D/'CAPTURE_CHECK01.json'),'composition':ref(Q/'snapshot/COMPOSITION01.json'),'archive_sha256':h(archive),'deterministic_archive_byte_reencoding':True,'restored_regular_bodies':135,'new_unique_bodies':134,'new_unique_bytes':1432931,'current_logical_bodies':824,'inherited_logical_joins':658,'new_logical_joins':166,'scope_counts':counts,'current_source':SOURCE,'historical_raw_reread':False,'qualification':'135 restored payload bytes verified; reviewer first pass repeated after correcting historical manifest encoding (no historical body reread); all typed metadata and 824 declared logical joins checked using accepted 716-body historical basis. Physical Git is included in Capsule. Original nulls and failures unchanged. No POSIX reconstruction, runtime-body recovery, writer exclusion, full financial capacity, or numerical authority.'})
proof=put('FULL_CURRENT_RECOVERY_PROOF01.json',{'schema_version':1,'decision':'accepted-actual-canonical-full-current-byte-recovery','identity':ID,'capsule_commit':SOURCE,'scope_counts':counts,'composition':ref(Q/'snapshot/COMPOSITION01.json'),'detail':check,'accepted_historical_basis':c['inherited_recovery'],'historical_metadata':c['original_capsule_metadata'],'actual_remote_receipt':ref(R/'REMOTE_RECOVERY01.json'),'actual_flat_receipt':ref(T/'RECOVERY01.json'),'actual_flat_root_exit':ref(T/'ACTUAL_ROOT_EXIT01.json'),'archive_sha256':h(archive),'manifest_sha256':h(raw(Q/'snapshot-manifest.json')),'new_unique_bodies':134,'new_unique_bytes':1432931,'inherited_logical_joins':658,'new_logical_joins':166,'accounting':{'closed_failed_original_engineering':5,'highest_previous_ceiling':6,'accepted_one_identity_ceiling':7,'original_conditional_slot':'unavailable-unclaimed-nontransferable','paper_financial_fits':0},'qualification':'Complete declared frozen current byte composition: Capsule incl physical Git, unreleased Parent4, Root63 and both closed review directories. Historical 716 body basis reused with fresh 134 unique byte bodies; no historical reread. Candidate/final released envelope and new review bodies require a later direct supplement. Original unknown exits/cleanup and failures retained. No runtime package bodies, reconstructed POSIX origin, immutable writer exclusion, capacity or numerical execution authority.'})
candidate=pinned(C/'CANONICAL_RELEASE_CANDIDATE01.json','6ff27a47f4f1f35c37ba44f1733ed37bca6129fff6b43fc19c80e201abd42499')
baseline=load(P/'release-unreleased01.json');assert set(candidate)==set(baseline)
assert {k for k in candidate if candidate[k]!=baseline[k]}=={'status','remaining'}
assert candidate['status']=='released-native-engineering' and candidate['remaining']==[]
proof_fields={'release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256'}
assert all(candidate[k] is None for k in proof_fields)
contract=h(encode({k:v for k,v in candidate.items() if k not in proof_fields}));assert contract=='1b7ad898ee326ce69566cdd23d97123e0959efa84ba523d47a60f80a13c7b1ed'
request=load(P/'request-unreleased01.json');assert all(x is None for x in request['evidence'].values())
caller=h(raw(P/'launch_success01.py'));parser=h(raw(P/'held_outcome02.py'))
assert caller=='c90812faff70c431807900a118447d30711ac3eca239a4ee1ec11ec5f6139ea9' and parser=='34f7945642eac91babe1f180b70c2d42f3b04daaf3e4c556f24eecab8ede4b95'
reg=load(S/candidate['registration']);assert h(raw(S/candidate['registration']))==candidate['registration_sha256']
assert candidate['cases']['success']['identity']==ID and candidate['cases']['success']['experiment']==reg['experiments'][ID]
assert candidate['family']==reg['families']['import-engineering'] and candidate['program_id']==reg['program_id']
assert len(candidate['source_files'])==204
for n,s in candidate['source_files'].items():assert expected['Capsule/'+n]['sha256']==s
exp=reg['experiments'][ID];assert len(exp['inputs'])==33 and len(exp['outputs'])==6
for row in exp['inputs'].values():assert expected['Capsule/'+row['path']]['sha256']==row['sha256']
ex=exp['cumulative_budget_extension'];assert [n for n,e in reg['experiments'].items() if e.get('cumulative_budget_extension')==ex]==[ID]
assert ex=={'extension':{'path':'CUMULATIVE_EXTENSION05_DRAFT01.json','sha256':'c161983c753a1aa17fabbe7f3af3f4f6017b59e81d10e667075c661356ef0c1d'},'review':{'path':'CUMULATIVE_REVIEW01.json','sha256':'7ec00d22ec0edff27032cbc3328b12dbf95a5ed4d1aac4a7170704df9d61f63d'}}
extension=pinned(S/ex['extension']['path'],ex['extension']['sha256']);allocation=pinned(S/'CUMULATIVE_ALLOCATION05_DRAFT01.json','0673e21c83475cfebe48c57f3176a746fed70b6f001f2284646d3c47fe05f097')
assert extension['consumed_before']==5 and extension['cumulative_ceiling']==7 and extension['initial_experiment']==ID
assert len(allocation['new_attempts'])==1 and allocation['new_attempts'][0]['identity']==ID and allocation['new_attempts'][0]['maximum_claims']==1
assert len(allocation['retained_closed_attempts'])==5 and all(x['terminal_status']=='failed' for x in allocation['retained_closed_attempts'])
conditional=candidate['cases']['second_target_publication_failure'];assert conditional['identity']==allocation['retained_unclaimed_unavailable'][0]['identity'] and conditional['disposition']=='unavailable-original-companion-failed'
assert len(allocation['retained_unclaimed_unavailable'])==1
assert not (P/'attempt01').exists() and not (S/'research_runs'/ID).exists()
job=candidate['cases']['success']['job_resources'];assert job['memory_max_bytes']==job['memory_high_bytes']==3*2**30 and job['wall_seconds']==1800 and job['start_reserve_bytes']==6*2**30 and job['disk_floor_bytes']==10*2**30 and job['native_unit_limits']['file_size_bytes']==4*2**20
review={'schema_version':1,'decision':'accepted-native-parent-release','identity':ID,'capsule_commit':SOURCE,'caller_sha256':caller,'semantic_parser_sha256':parser,'release_contract_sha256':contract}
reviewref=put('RELEASE_EXECUTION_REVIEW01.json',review)
base_review=put('FINAL_BASELINE_RECOVERY_REVIEW01.json',{'schema_version':1,'decision':'accepted-external-final-baseline-recovery','capsule_commit':SOURCE,'caller_sha256':caller,'semantic_parser_sha256':parser,'release_contract_sha256':contract,'actual_external_recovery_sha256':proof['sha256'],'detail':check,'qualification':'Actual frozen full-current baseline recovered; candidate changes status and remaining only. This exact contract review does not claim recovery of final released request/proof bytes: direct supplement and independent complete union acceptance remain mandatory before native entry.'})
put('FINAL_PARENT_SOURCE_ENTRY_REVIEW01.json',{'schema_version':1,'decision':'accepted-exact-canonical-parent-contract-pending-final-supplement','candidate':ref(C/'CANONICAL_RELEASE_CANDIDATE01.json'),'contract_sha256':contract,'current_source':SOURCE,'caller':ref(P/'launch_success01.py'),'semantic_parser':ref(P/'held_outcome02.py'),'full_current_recovery':proof,'baseline_review':base_review,'release_review':reviewref,'accepted_parent_source_review':ref(F/'held-consumer-canonical-parent-review01-2026-10-05/SOURCE_CHECK01.json'),'accepted_gate_integration':ref(F/'held-consumer-canonical-gate-draft-review01-2026-10-05/INTEGRATION_CHECK01.json'),'source_pins':204,'inputs':33,'outputs':6,'only_candidate_deltas':['status','remaining'],'one_identity_allocation':True,'old_conditional_unavailable':True,'accounting':'Five actual FAILED; base2/prior0, prior highest6, extension7 exactlyone fresh canonical success, no refund or transfer; paper0. Closed claim metadata reused through accepted cumulative review.','native_limits_unchanged':True,'runtime_record_pins_reused_not_reread':True,'native_execution_entry':False,'remaining':['exact final Parent request/release/proof bytes and original-path metadata direct recovery','independent final complete-union acceptance','genuine prepared check and fresh namespace/process/physical/native eligibility','separate exact one-use native entry'],'not_tested':['numerical execution or arrays','financial economics/fees/funding/returns','real capacity/full population','runtime package body recovery or POSIX origin reconstruction','historical unknown process/exit facts'],'qualification':'Seven-field release review is exact source/contract evidence for assembly only. It is not a Root launch permit; final supplement and genuine prepared/eligibility remain pending. No registration or ledger mutation.'})
