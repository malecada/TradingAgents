"""Read-only failed-parent evidence and one exact recovered-payload integrity pass."""
import datetime,hashlib,json,os,stat,subprocess,time
from pathlib import Path
H=Path(__file__).parent;F=H.parent;M=F.parents[2];B=M/'research/onchain-paper-replication-2026-09-24';S=B/'storage/real-pilot-second-graph-preservation-20261006-01'
evidence={}
def sig(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p):
 p=Path(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 r=p.read_bytes();assert sig(p.lstat())==sig(s) and p.lstat().st_mode==s.st_mode;evidence[str(p.relative_to(M))]=hashlib.sha256(r).hexdigest();return r
def j(p):return json.loads(raw(p))
def put(n,q):
 with (H/n).open('x') as f:json.dump(q,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
assert not (H/'RECOVERED_PAYLOAD_HASH02.json').exists() and not (H/'RECOVERED_PASS_STARTED02.json').exists()
c=j(S/'selection01.json');assert evidence[str((S/'selection01.json').relative_to(M))]=='96f5605613d4d9c537d4d130917d3af04f9a8005cc385b5a0576c60cf673c43a'
assert c['count']==36 and c['total_bytes']==4204068745
terminal=j(S/'ROOT_TERMINAL01.json');final=j(S/'guard01/final.json');outer=j(S/'outer-exit01.json');child=j(S/'guard01/child_exit.json');ready=j(S/'guard01/cpu_ready.json');running=j(S/'ROOT_RUNNING01.json')
assert terminal['actual_root_tool_session']==39713 and terminal['actual_root_tool_completion_chunk']=='06fe38' and terminal['actual_root_tool_exit_code']==1
assert terminal['actual_outer']==outer and terminal['source']==running['source_current']=='fa9e1d03e236a3b041a5e9bbfe502545d59e2c4f'
assert final['phase']==outer['guard_phase']=='failed' and final['child_exit_code'] is None and outer['guard_child_exit_code'] is None and child['exit_code']==-15
assert final['cleanup_verified'] is True and outer['cleanup_verified'] is True and outer['entry_selected_exit_code']==1 and outer['fatal_type'] is None
assert final['limit_reason']==terminal['original_guard_limit_reason']=="FileNotFoundError: [Errno 2] No such file or directory: '.pending-04381e9817bd4e5bad76d8a749e39217'"
assert terminal['native_final_sha256']==evidence[str((S/'guard01/final.json').relative_to(M))]
assert not Path(final['cgroup']).exists()
assert final['memory_max_bytes']==268435456 and final['memory_high_bytes']==201326592 and final['memory_swap_max_bytes']==0
assert all(final['memory_events'][k]==0 for k in ('max','oom','oom_kill')) and final['disk_floor_bytes']==10737418240 and final['elapsed_seconds']<14400
assert min(final['minimum_sampled_disk_free_bytes'].values())>=final['disk_floor_bytes']
props=subprocess.run(['systemctl','--user','show',final['unit'],'--property=MainPID,Result,ExecMainStatus,ControlGroup,ActiveState,SubState'],capture_output=True,text=True,check=True).stdout
pd=dict(v.split('=',1) for v in props.splitlines());assert pd['MainPID']=='0' and pd['ControlGroup']=='' and pd['ActiveState']==pd['SubState']=='failed'
pids={int(p) for p in final['cpu_thread_readback']}|{final['monitor_pid'],child['workload_pid'],ready['pid']};assert pids==set(terminal['selected_recorded_pids_absent'])
absent=['complete.json','completion-candidate.json','recovered-complete.json','failed.json','35-kept.json','35-verified.json','35-recovered-restore.json','35-recovered-restore.json.transport.json']
assert not any(os.path.lexists(S/n) for n in absent)
assert len(list(S.glob('*-attempted.json')))==36 and len(list(S.glob('*-kept.json')))==len(list(S.glob('*-verified.json')))==35
assert j(S/'intent.json')['selection']==c
basis=j(M/c['independent_body_hash']['path']);assert evidence[c['independent_body_hash']['path']]==c['independent_body_hash']['sha256'];payload={r['path']:r for r in basis['files']};assert len(payload)==6
j(M/c['graph_outcome_review']['path']);assert evidence[c['graph_outcome_review']['path']]==c['graph_outcome_review']['sha256']
rows=[];tohash=[];getcount=0;original_stats={}
def getcheck(p,n):
 global getcount
 q=j(p);assert q['status']=='complete' and q['error_type'] is None and q['returncode']==0 and q['expected_bytes']==q['received_bytes']==n
 pids.add(q['pid']);getcount+=1
for i,r in enumerate(c['files']):
 original=M/r['path'];st=original.lstat();assert original.resolve()==original and stat.S_ISREG(st.st_mode) and st.st_nlink==r['nlink']==1 and stat.S_IMODE(st.st_mode)==r['mode'] and sig(st)==r['stat_identity'];original_stats[original]=(sig(st),st.st_mode)
 recovered=S/f'{i:02d}-recovered.bin';rs=recovered.lstat();assert recovered.resolve()==recovered and stat.S_ISREG(rs.st_mode) and rs.st_nlink==1 and rs.st_size==r['bytes']
 assert j(S/f'{i:02d}-attempted.json')=={'number':i,'row':r}
 restore=raw(S/f'{i:02d}-restore.json');rv=json.loads(restore)
 for k,v in r.items():assert rv[k]==v
 assert rv['body_roundtrip_verified'] is True and rv['remote_object']==c['remote']+f'/{i:02d}.bin' and rv['remote_restore']==c['remote']+f'/{i:02d}-restore.json'
 getcheck(S/f'{i:02d}-recovered.bin.transport.json',r['bytes'])
 if i<35:
  kept=j(S/f'{i:02d}-kept.json');assert kept==j(S/f'{i:02d}-verified.json') and kept==dict(rv,original_retained=True,recovered_body_retained=True)
  assert restore==raw(S/f'{i:02d}-recovered-restore.json');getcheck(S/f'{i:02d}-recovered-restore.json.transport.json',len(restore))
 if r['path'] in payload:
  old=payload[r['path']];assert old['sha256']==r['sha256'] and old['stat_identity']==[st.st_dev,st.st_ino,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns]
  tohash.append((i,r,recovered,sig(rs),rs.st_mode))
 else:assert raw(original)==raw(recovered) and hashlib.sha256(raw(recovered)).hexdigest()==r['sha256']
 rows.append({'index':i,'original_path':r['path'],'sha256':r['sha256'],'bytes':r['bytes'],'original_mode':r['mode'],'original_stat_identity':sig(st),'recovered_path':str(recovered.relative_to(M)),'recovered_stat_identity':sig(rs),'recovered_mode':stat.S_IMODE(rs.st_mode),'body_get_complete':True,'restoration_metadata_get_complete':i<35,'kept_marker_present':i<35})
 assert not original.with_name(original.name+'.remote.json').exists()
assert getcount==71 and len(tohash)==6
for d in c['directories']:
 p=M/d['path'];st=p.lstat();assert p.resolve()==p and stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==d['mode']
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
for n in ['preflight01.json','launch-attempt01.json','entry01.py','envelope01.json','RELEASE_REVIEW01.json','guard01/release.json','guard01/child.log']:raw(S/n)
# Inventory/hash all actual retained compact metadata and streams in this owned backup; exclude only the six huge recovered payloads.
big={p for _,_,p,_,_ in tohash};inventory=[]
for p in sorted(S.rglob('*')):
 st=p.lstat();assert p.resolve()==p and (stat.S_ISDIR(st.st_mode) or (stat.S_ISREG(st.st_mode) and st.st_nlink==1))
 row={'path':str(p.relative_to(M)),'mode':stat.S_IMODE(st.st_mode),'kind':'directory' if p.is_dir() else 'regular','bytes':st.st_size}
 if p.is_file() and p not in big:row['sha256']=hashlib.sha256(raw(p)).hexdigest()
 inventory.append(row)
put('FAILED_METADATA_CHECK02.json',{'decision':'metadata-pass-terminal-permanently-failed','original_guard_child_exit':None,'separate_worker_exit':-15,'actual_root_exit':1,'get_receipts':71,'kept_rows':35,'attempted_rows':36,'unknown_lifetime_pid_history':True,'known_recorded_pids_absent':sorted(pids),'actual_native_properties':props,'absent_worker_global_markers':absent,'rows':rows,'retained_scope':inventory,'evidence':evidence})
put('RECOVERED_PASS_STARTED02.json',{'scope':'six recovered scientific payloads only','failed_metadata_sha256':hashlib.sha256((H/'FAILED_METADATA_CHECK02.json').read_bytes()).hexdigest(),'buffer_bytes':1048576,'no_automatic_retry':True})
start=time.monotonic();hashes=[]
for i,r,p,before,mode in tohash:
 h=hashlib.sha256();count=0
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:
  opened=os.fstat(stream.fileno());assert sig(opened)==before and opened.st_mode==mode
  while part:=stream.read(1048576):h.update(part);count+=len(part)
  after=os.fstat(stream.fileno());assert sig(after)==before and after.st_mode==mode
 assert sig(p.lstat())==before and p.lstat().st_mode==mode and count==r['bytes'] and h.hexdigest()==r['sha256']
 hashes.append({'index':i,'original_path':r['path'],'recovered_path':str(p.relative_to(M)),'bytes':count,'sha256':h.hexdigest(),'stat_identity':before,'mode':stat.S_IMODE(mode)})
for p,(before,mode) in original_stats.items():assert sig(p.lstat())==before and p.lstat().st_mode==mode
put('RECOVERED_PAYLOAD_HASH02.json',{'decision':'pass-six-recovered-payload-bytes','files':hashes,'total_bytes':sum(x['bytes'] for x in hashes),'buffer_bytes':1048576,'full_body_passes':1,'elapsed_seconds':time.monotonic()-start,'original_body_hash_reused':c['independent_body_hash'],'parent_status':'failed','full_scope_completion':False,'retirement_authority':False})
put('FAILED_OUTCOME_CHECK02.json',{'decision':'accepted-failed-parent-partial-byte-evidence','actual_parent_outcome':'failed','actual_root_exit':1,'original_guard_child_exit':None,'separate_worker_exit':-15,'guard_cleanup_verified':True,'worker_complete_marker':None,'worker_failed_marker':None,'global_complete_or_metadata_full_recovery':False,'body_gets_independently_authenticated':36,'body_bytes':4204068745,'six_scientific_payload_bytes':sum(x['bytes'] for x in hashes),'complete_row_metadata_gets':35,'attempted_rows':36,'get_receipts':71,'missing_increment':{'row':35,'original_path':c['files'][35]['path'],'original_and_body_get_bytes':1936,'body_get_already_authenticated':True,'local_restore_present':True,'remote_restore_put_status':'unknown','remote_restore_fresh_get':'absent','verified_marker':'absent','kept_marker':'absent','global_worker_completion':'absent'},'no_retirement_release':True,'no_rerun_this_identity':True,'qualification':'All36 body gets exist and byte identity was checked, but row35 restoration metadata get/kept marker and whole-run completion are absent. Preserve failed source/guard/Root and all partial outputs. A new separately named successor may preserve/recover only missing metadata and an honest composition, using these existing bodies as immutable inherited evidence; never forge old markers. Whole lifetime PID history and actual atomic-rename initiator are not established.'})
print(json.dumps({'decision':'accepted-failed-parent-partial-byte-evidence','body_gets':36,'metadata_gets':35,'get_receipts':71,'known_pids_absent':len(pids),'six_recovered_payload_bytes':sum(x['bytes'] for x in hashes),'hash_seconds':time.monotonic()-start,'retirement_release':False}))
