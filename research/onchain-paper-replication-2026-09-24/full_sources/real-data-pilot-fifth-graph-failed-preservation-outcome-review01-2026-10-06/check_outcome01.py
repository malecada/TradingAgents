"""Failed-parent backup outcome: metadata reconstruction and inherited streamed byte proofs."""
import hashlib,json,os,stat,sys
from pathlib import Path
from tradingagents.research.onchain_replication.environment import inventory
M=Path.cwd().resolve();D=Path(__file__).resolve().parent;F=D.parent;B=F.parent
ID='real-pilot-fifth-graph-failed-preservation-20261006-01';OLD='eth-paper-real-pilot-graph-20220530-20261005-01';S=B/'storage'/ID
EXPECTED=json.loads((D/'ACTUAL_TERMINAL_BINDING01.json').read_bytes());E={};cached={}
def sha(b):return hashlib.sha256(b).hexdigest()
def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p,pin=None):
 p=Path(p);key=str(p.relative_to(M))
 if key not in cached:
  s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve(strict=True)==p
  b=p.read_bytes();assert all(getattr(p.lstat(),k)==getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'));cached[key]=b;E[key]=sha(b)
 assert pin is None or E[key]==pin,(key,E[key],pin)
 return cached[key]
def read(p,pin=None):return json.loads(raw(p,pin))
def ref(v):return read(M/v['path'],v['sha256'])
def out(name,v):
 b=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();(D/name).write_bytes(b);return {'path':str((D/name).relative_to(M)),'sha256':sha(b)}
c=read(S/'selection01.json','77e2cf588afdaea5770326a6d237978f4be2bcce992a3e64816854113f7a6d3e')
complete_raw=raw(S/'complete.json','7f990ecf44aa9d75f638a0cf2ab4142a1074341d37c82428958d2e58ccf90cc6');complete=json.loads(complete_raw)
assert complete_raw==raw(S/'completion-candidate.json')==raw(S/'recovered-complete.json')
assert complete['identity']==c['identity']==ID and complete['selection']==c and complete['count']==c['count']==30 and len(complete['files'])==30
assert complete['bytes_preserved']==c['total_bytes']==3278739082 and complete['originals_retained'] is True and complete['recoveries_retained'] is True
assert complete['no_automatic_retry'] is True
intent=read(S/'intent.json');assert intent['identity']==ID and intent['selection']==c and intent['no_automatic_retry'] is True
basis=ref(c['independent_body_hash']);assert c['independent_body_hash']['sha256']=='1f2c21fcc1751a13e0f52aa63c09df602a30b2af177816ba5ece407939c39039';payloads={r['path']:r for r in basis['files']};assert len(payloads)==3
original_review=ref(c['graph_outcome_review']);assert c['graph_outcome_review']['sha256']=='8f562d66294e6f3a90d6bb48db8b62937a41e17dc4922cbd4cdfbb1d16468240' and original_review['parent_status']=='failed'
proof=ref(EXPECTED['recovered_proof']);assert proof['decision']=='pass' and proof['total_bytes']==3278655680 and proof['original_body_pass_reused']==c['independent_body_hash'] and proof['selection_sha256']==sha(raw(S/'selection01.json'))
assert proof['one_streaming_pass_per_body'] is True and proof['arrays_decoded'] is False and proof['sqlite_queries'] is False
proofrows={r['original_path']:r for r in proof['files']};assert set(proofrows)==set(payloads)
raw(M/EXPECTED['recovered_proof']['path'].replace('RECOVERED_PAYLOAD_HASH01.json','body_check01.py'))
final=read(S/'guard01/final.json','b08ef22e340ecc84e4e29cee8b16287baaa45203bd675e2421efb962c17c1269');outer=read(S/'outer-exit01.json');terminal=read(S/'ROOT_TERMINAL01.json',EXPECTED['root_terminal_sha256']);child=read(S/'guard01/child_exit.json');ready=read(S/'guard01/cpu_ready.json');running=read(S/'ROOT_RUNNING01.json')
assert terminal['identity']==outer['identity']==ID and terminal['actual_root_tool_session']==86039 and terminal['actual_root_tool_completion_chunk']=='613f7d'
assert terminal['actual_root_tool_exit_code']==terminal['actual_parent_exit_code']==0 and terminal['complete_sha256']==sha(complete_raw) and terminal['guard_final_sha256']==sha(raw(S/'guard01/final.json'))
assert final['phase']=='complete' and final['child_exit_code']==child['exit_code']==outer['guard_child_exit_code']==outer['entry_selected_exit_code']==0
assert final['cleanup_verified'] is True and outer['cleanup_verified'] is True and final['limit_reason'] is None and outer['fatal_type'] is None
assert final['cleanup_stop_returncode']==terminal['original_cleanup_stop_returncode']==5
assert final['cleanup_unit_properties']['ActiveState']=='inactive' and final['cleanup_unit_properties']['SubState']=='dead' and not Path(final['cgroup']).exists()
assert terminal['lifetime_pid_history_complete'] is False and running['actual_root_exit_code'] is None
pids={int(p) for p in final['cpu_thread_readback']}|{final['monitor_pid'],child['workload_pid'],ready['pid']}|set(terminal['selected_recorded_pids'])
assert all(not Path('/proc',str(p)).exists() for p in pids)
assert final['command'][-2:]==[str(S/'entry01.py'),'--worker'] and running['main_commit']==terminal['source_commit']=='3e4736c68d58857c09950ebec0ec7bdca0bb3799'
assert final['memory_max_bytes']==256*1024**2 and final['memory_high_bytes']==192*1024**2 and final['memory_swap_max_bytes']==0 and final['wall_seconds']==14400 and final['disk_floor_bytes']==10*1024**3 and final['storage_budget']['limits']['max_allocated_bytes']==5*1024**3
assert final['elapsed_seconds']<14400 and all(final['memory_events'][k]==0 for k in ('max','oom','oom_kill')) and final['owner_identity'] is None
for name in ['preflight01.json','launch-attempt01.json','ROOT_PREPARATION01.json','guard01/release.json','guard01/child.log']:raw(S/name)
env=read(S/'envelope01.json','19f0141a12d661d754462e19558a882f2b685abeeda2ccffc2ad3cc225cc3343');release=read(S/'RELEASE_REVIEW01.json','37a0b7b894f612681bf9a78f2c05d283fe580decbcfd9bae966577d4c89a833e')
assert release['decision']=='accepted' and release['envelope_sha256']==sha(raw(S/'envelope01.json'))
assert len(env['source_files'])==12
for path,pin in env['source_files'].items():raw(M/path,pin)
for v in env['evidence']:ref(v)
assert inventory(M)==ref(env['environment'])
# Local connection body is deliberately not opened. Entry and Transport authenticated it.
remote=read(S/'REMOTE_CONFIRMATION01.json');assert remote['actual_push_exit_code']==remote['actual_readback_exit_code']==0 and remote['actual_remote_head']==remote['main_commit']==terminal['source_commit']
assert not os.path.lexists(S/'failed.json')
get_count=0;rows=[];original_stats={}
def getcheck(path,n):
 global get_count
 r=read(path);assert r['status']=='complete' and r['error_type'] is None and r['returncode']==0 and r['received_bytes']==r['expected_bytes']==n
 assert type(r['pid']) is int and r['pid']>0 and r['elapsed_seconds']>=0;pids.add(r['pid']);get_count+=1
for i,row in enumerate(c['files']):
 original=M/row['path'];st=original.lstat();assert original.resolve(strict=True)==original and stat.S_ISREG(st.st_mode) and st.st_nlink==row['nlink']==1 and stat.S_IMODE(st.st_mode)==row['mode'] and identity(st)==row['stat_identity'];original_stats[original]=identity(st)
 recovered=S/f'{i:02d}-recovered.bin';rst=recovered.lstat();assert recovered.resolve(strict=True)==recovered and stat.S_ISREG(rst.st_mode) and rst.st_nlink==1 and rst.st_size==row['bytes']
 assert read(S/f'{i:02d}-attempted.json')=={'number':i,'row':row}
 kept=read(S/f'{i:02d}-kept.json');assert kept==read(S/f'{i:02d}-verified.json')==complete['files'][i]
 assert all(kept[k]==v for k,v in row.items())
 assert kept['remote_object']==c['remote']+f'/{i:02d}.bin' and kept['remote_restore']==c['remote']+f'/{i:02d}-restore.json'
 assert all(kept[k] is True for k in ('original_retained','recovered_body_retained','body_roundtrip_verified'))
 restore=raw(S/f'{i:02d}-restore.json');assert restore==raw(S/f'{i:02d}-recovered-restore.json') and json.loads(restore)=={k:v for k,v in kept.items() if k not in ('original_retained','recovered_body_retained')}
 getcheck(S/f'{i:02d}-recovered.bin.transport.json',row['bytes']);getcheck(S/f'{i:02d}-recovered-restore.json.transport.json',len(restore))
 assert not original.with_name(original.name+'.remote.json').exists()
 if row['path'] in payloads:
  prior=payloads[row['path']];pr=proofrows[row['path']]
  assert prior['bytes']==pr['bytes']==row['bytes'] and prior['sha256']==pr['sha256']==row['sha256']
  assert prior['stat_identity']==[st.st_dev,st.st_ino,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns]
  assert pr['index']==i and pr['recovered_path']==str(recovered.relative_to(M)) and pr['stat_identity']==identity(rst) and pr['mode']==stat.S_IMODE(rst.st_mode)
 else:
  ob=raw(original);rb=raw(recovered);assert ob==rb and sha(rb)==row['sha256']
 rows.append({'index':i,'path':row['path'],'bytes':row['bytes'],'sha256':row['sha256'],'original_mode':row['mode'],'original_stat_identity':identity(st),'recovered_path':str(recovered.relative_to(M)),'recovered_mode':stat.S_IMODE(rst.st_mode),'recovered_stat_identity':identity(rst),'restoration_name_mode_verified':True})
assert len({r['path'] for r in c['files']})==30 and sum(r['bytes'] for r in c['files'])==3278739082
assert len(c['directories'])==9
for d in c['directories']:
 p=M/d['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==d['mode']
getcheck(S/'recovered-complete.json.transport.json',len(complete_raw));assert get_count==61
assert len(list(S.glob('*-attempted.json')))==len(list(S.glob('*-kept.json')))==len(list(S.glob('*-verified.json')))==30
assert all(not Path('/proc',str(p)).exists() for p in pids)
oldrun=M/'research_runs'/OLD;oldsrc=M/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/OLD
failed=read(oldrun/'failed.json');assert failed['status']=='failed' and failed['output_sha256']=={}
assert not any(os.path.lexists(p) for p in [oldrun/'complete.json',oldrun/'outputs/artifact-index.json',oldsrc/'aggregation/complete.json',oldsrc/'graph-2022-05-30/manifest.json'])
cells=c['graph_terminal_cells'];assert c['graph_terminal_status']=='failed' and cells[0]['status']=='complete' and cells[0]['rows']==7507236 and cells[1]['status']=='unavailable'
boundaries=[read(oldsrc/'aggregation'/f'source-{i:06d}.json') for i in range(7)]
oldnative=read(M/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/OLD/'guard/final.json');assert oldnative['phase']=='failed' and oldnative['child_exit_code']==125 and oldnative['cleanup_stop_returncode']==0
for p,s in original_stats.items():assert identity(p.lstat())==s
assert not any(n in sys.modules for n in ('numpy','torch','sqlite3','pyarrow'))
result={'decision':'accepted','identity':ID,'full_scope_byte_recovery':True,'count':30,'bytes':3278739082,'directories':c['directories'],'rows':rows,'get_receipts':61,'known_recorded_pids_absent':sorted(pids),'root_selected_pids_unchanged':terminal['selected_recorded_pids'],'lifetime_pid_history_complete':False,'original_preservation_cleanup_stop_returncode':5,'original_running_root_exit':None,'original_failed_parent':{'identity':OLD,'status':'failed','root_exit':1,'native_child_exit':125,'cleanup_stop_returncode':0,'source_rows':7507236,'graph_cell_status':'unavailable'},'source_pins_verified':12,'installed_runtime_metadata_equal':True,'original_body_pass':c['independent_body_hash'],'recovered_body_pass':EXPECTED['recovered_proof'],'reviewer_payload_reads':0,'retirement_release':False,'numerical_authority':False,'evidence':dict(sorted(E.items())),'qualification':'Actual full declared BYTE recovery and original path/name/mode descriptors. No POSIX reconstruction, runtime-body recovery, current remote availability, SQLite integrity, completed graph, scientific equivalence, writer exclusion or capacity inference. Failed parent remains spent; preserved raw nulls and cleanup5 unchanged.'}
review_ref=out('REVIEW01.json',result)
ledger=next(r for r in basis['files'] if r['path'].endswith('/ledger.sqlite'))
continuation={'decision':'accepted','predecessor':OLD,'parent_status':'failed','ledger_byte_recovery':True,'ledger':{k:ledger[k] for k in ('path','bytes','sha256')},'committed_source_rows':7507236,'source_boundary_count':7,'recovery_review':review_ref,'scope':'BYTE integrity and authenticated closed-source metadata only; actual read-only DB consistency/row checks remain required inside separately admitted continuation worker','graph_complete':False,'sqlite_integrity_checked':False,'numerical_authority':False}
cref=out('CONTINUATION_RECOVERY_REVIEW01.json',continuation)
out('OUTCOME_CHECK01.json',{'decision':'pass','review':review_ref,'continuation_recovery':cref,'recovered_payload_proof_inherited':EXPECTED['recovered_proof'],'known_pids':len(pids),'get_receipts':61,'payload_reads':0,'source_and_runtime_metadata_only':True})
print(json.dumps({'review':review_ref,'continuation_recovery':cref,'known_pids':len(pids),'get_receipts':61,'files':30,'bytes':3278739082}))
