import ast,hashlib,json,os,stat,time
from pathlib import Path
D=Path(__file__).parent;F=D.parent;M=F.parents[2];B=M/'research/onchain-paper-replication-2026-09-24';S=B/'storage/real-pilot-third-graph-preservation-20261006-01'
evidence={}
# This file must be created only after Root reports the actual terminal.
EXPECTED=json.loads((D/'ACTUAL_TERMINAL_BINDING01.json').read_bytes())
assert EXPECTED['identity']=='real-pilot-third-graph-preservation-20261006-01' and EXPECTED['root_session']==61305 and EXPECTED['root_exit_code']==0
assert EXPECTED['source'].startswith('40b8d643') and len(EXPECTED['source'])==40
def raw(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p
 b=p.read_bytes();assert all(getattr(p.lstat(),k)==getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')); evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
assert not (D/'RECOVERED_PAYLOAD_HASH01.json').exists(),'never repeat completed independent payload pass'
c=read(S/'selection01.json');assert evidence[str((S/'selection01.json').relative_to(M))]=='414c7cc42118d1f1fabd352dce7d3dba14cfe140ad40aa32aa8f8a20b1736151';complete_raw=raw(S/'complete.json');complete=json.loads(complete_raw)
assert evidence[str((S/'complete.json').relative_to(M))]==EXPECTED['complete_sha256']
assert complete_raw==raw(S/'completion-candidate.json')==raw(S/'recovered-complete.json')
assert complete['selection']==c and complete['count']==c['count']==36 and complete['bytes_preserved']==c['total_bytes']==3855758671 and complete['originals_retained'] is True and complete['recoveries_retained'] is True
intent=read(S/'intent.json');assert intent['selection']==c and intent['no_automatic_retry'] is True
basis=read(M/c['independent_body_hash']['path']);assert evidence[c['independent_body_hash']['path']]==c['independent_body_hash']['sha256']=='2bf6627ac13cd5d91bc42515809af5efdcd9e626b373776e9c68385e7ca995f7'; payloads={r['path']:r for r in basis['files']};assert len(payloads)==6
read(M/c['graph_outcome_review']['path']);assert evidence[c['graph_outcome_review']['path']]==c['graph_outcome_review']['sha256']=='3de45221f0d1cd8571c0b4e92a71a9f9295271c87a69b8cd820af2f1fe777347'
final=read(S/'guard01/final.json');outer=read(S/'outer-exit01.json');terminal=read(S/'ROOT_TERMINAL01.json');child=read(S/'guard01/child_exit.json');ready=read(S/'guard01/cpu_ready.json');running=read(S/'ROOT_RUNNING01.json')
assert terminal['actual_root_tool_session']==EXPECTED['root_session'] and terminal['actual_root_tool_chunk']==EXPECTED['root_completion_chunk'] and terminal['actual_root_tool_exit_code']==0
assert terminal['identity']==outer['identity']==EXPECTED['identity'] and terminal['complete_sha256']==EXPECTED['complete_sha256'] and terminal['guard_final_sha256']==evidence[str((S/'guard01/final.json').relative_to(M))] and outer['guard_child_exit_code']==0 and outer['cleanup_verified'] is True and final['phase']=='complete' and final['child_exit_code']==child['exit_code']==outer['entry_selected_exit_code']==0 and final['cleanup_verified'] is True and outer['fatal_type'] is None and final['limit_reason'] is None
assert final['cleanup_unit_properties']['ActiveState']=='inactive' and final['cleanup_unit_properties']['SubState']=='dead'
assert not Path(final['cgroup']).exists()
assert final['memory_max_bytes']==256*1024**2 and final['memory_high_bytes']==192*1024**2 and final['memory_swap_max_bytes']==0 and final['wall_seconds']==14400 and final['disk_floor_bytes']==10*1024**3 and final['storage_budget']['limits']['max_allocated_bytes']==5*1024**3
assert final['elapsed_seconds']<final['wall_seconds'] and all(final['memory_events'][k]==0 for k in ('max','oom','oom_kill'))
assert final['owner_identity'] is None
pids={int(p) for p in final['cpu_thread_readback']}|{final['monitor_pid'],child['workload_pid'],ready['pid']}
assert terminal['selected_recorded_pids_absent'] is True and terminal['actual_current_cgroup_absent'] is True
recorded=set(map(int,terminal['actual_selected_recorded_pids']))
assert pids<=recorded and recorded and all(not Path('/proc',str(pid)).exists() for pid in recorded);pids|=recorded
assert final['command'][-2:]==[str(S/'entry01.py'),'--worker'] and running['source_commit']==terminal['source_commit']==EXPECTED['source']
for name in ['preflight01.json','launch-attempt01.json','ROOT_REMOTE_CONFIRMATION01.json','guard01/release.json','guard01/child.log','entry01.py','envelope01.json','RELEASE_REVIEW01.json']:
 raw(S/name)
assert evidence[str((S/'entry01.py').relative_to(M))]=='87d4fa670613485a518f7a6399ee5f2455723a068bdb60d2ed085256f2936fc6'
assert evidence[str((S/'envelope01.json').relative_to(M))]=='b29b74270b4fbe44bcd03721cdf82ae9a12d072b2732ef436174ab944819ed6e'
assert evidence[str((S/'RELEASE_REVIEW01.json').relative_to(M))]==EXPECTED['release_sha256']
assert not (S/'failed.json').exists()
get_count=0; recovered_rows=[]; original_stats={};all_rows=[]
def getcheck(path,n):
 global get_count
 r=read(path);assert r['status']=='complete' and r['error_type'] is None and r['returncode']==0 and r['received_bytes']==r['expected_bytes']==n
 assert type(r['pid']) is int and r['elapsed_seconds']>=0;pids.add(r['pid']);get_count+=1
for i,row in enumerate(c['files']):
 original=M/row['path'];st=original.lstat();assert original.resolve()==original and stat.S_ISREG(st.st_mode) and st.st_nlink==row['nlink']==1 and stat.S_IMODE(st.st_mode)==row['mode'] and identity(st)==row['stat_identity'];original_stats[original]=identity(st)
 recovered=S/f'{i:02d}-recovered.bin';rst=recovered.lstat();assert recovered.resolve()==recovered and stat.S_ISREG(rst.st_mode) and rst.st_nlink==1 and rst.st_size==row['bytes']
 attempt=read(S/f'{i:02d}-attempted.json');assert attempt=={'number':i,'row':row}
 kept=read(S/f'{i:02d}-kept.json');assert kept==read(S/f'{i:02d}-verified.json')==complete['files'][i]
 for k,v in row.items():assert kept[k]==v
 assert kept['remote_object']==c['remote']+f'/{i:02d}.bin' and kept['remote_restore']==c['remote']+f'/{i:02d}-restore.json'
 assert kept['original_retained'] is True and kept['recovered_body_retained'] is True and kept['body_roundtrip_verified'] is True
 restore=raw(S/f'{i:02d}-restore.json');assert restore==raw(S/f'{i:02d}-recovered-restore.json');rv=json.loads(restore)
 assert rv=={k:v for k,v in kept.items() if k not in ('original_retained','recovered_body_retained')}
 getcheck(S/f'{i:02d}-recovered.bin.transport.json',row['bytes']);getcheck(S/f'{i:02d}-recovered-restore.json.transport.json',len(restore))
 assert not original.with_name(original.name+'.remote.json').exists()
 if row['path'] in payloads:
  prior=payloads[row['path']];assert prior['sha256']==row['sha256'] and prior['bytes']==row['bytes'] and prior['stat_identity']==[st.st_dev,st.st_ino,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns]
  recovered_rows.append((i,row,recovered,identity(rst)))
 else:
  ob=raw(original);rb=raw(recovered);assert ob==rb and hashlib.sha256(rb).hexdigest()==row['sha256']
 all_rows.append({'index':i,'path':row['path'],'bytes':row['bytes'],'sha256':row['sha256'],'original_mode':row['mode'],'recovered_mode':stat.S_IMODE(rst.st_mode),'recovered_stat_identity':identity(rst),'restoration_name_mode_verified':True})
assert len(recovered_rows)==6 and sum(r['bytes'] for r in c['files'])==3855758671
assert len(c['directories'])==8
for d in c['directories']:
 p=M/d['path'];st=p.lstat();assert stat.S_ISDIR(st.st_mode) and p.resolve()==p and stat.S_IMODE(st.st_mode)==d['mode']
getcheck(S/'recovered-complete.json.transport.json',len(complete_raw));assert get_count==73
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
assert len(list(S.glob('*-attempted.json')))==len(list(S.glob('*-kept.json')))==len(list(S.glob('*-verified.json')))==36
# Fresh active-consumer metadata check through unchanged selector predicate; no selector execution or Git.
selector=F/'real-data-pilot-incremental-graph-retention02-2026-10-05/select01.py'; sr=raw(selector);assert hashlib.sha256(sr).hexdigest()=='d9d63840c8f4510ac4e1b784ab31762d91f74c4de8d2258bdd7011823f921205'
func=next(n for n in ast.parse(sr).body if isinstance(n,ast.FunctionDef) and n.name=='active_reference');g={'require':lambda ok,why:None if ok else (_ for _ in ()).throw(ValueError(why))};exec(compile(ast.Module(body=[func],type_ignores=[]),'accepted-active-reference-AST','exec'),g)
ledger=next(r for r in c['files'] if r['path'].endswith('/ledger.sqlite'));producer=(M/ledger['path']).parent.parent;active=[]
for claim in (M/'research_runs').glob('*/claim.json'):
 if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists():continue
 cv=read(claim);g['active_reference'](M,[M/ledger['path']],cv['experiment']['inputs'],producer);active.append(str(claim.relative_to(M)))
retire=F/'real-data-pilot-third-graph-post-recovery-retirement-preparation01-2026-10-06/retire01.py';assert hashlib.sha256(raw(retire)).hexdigest()=='87cbe18ecb421b5850e3cbed8a4f5d3f9516b2129d3d0cc034197c9f5f6ff035'
assert not any((retire.parent/n).exists() for n in ('attempt01.json','complete01.json','failed01.json'))
for p in [F/'real-data-pilot-third-graph-preservation-preparation01-2026-10-06/keep.py',B/'storage/cold-offload-2026-09-29-03/offload.py']:raw(p)
assert hashlib.sha256(raw(F/'real-data-pilot-third-graph-preservation-preparation01-2026-10-06/keep.py')).hexdigest()=='fd310528a42f16e1c4590e282622340faaefc99d9e30645f5082a85969b79bfa'
# Exactly one independent streamed pass over only the six recovered scientific bodies.
began=time.monotonic(); hashes=[]
for i,row,p,before in recovered_rows:
 dg=hashlib.sha256();n=0
 with p.open('rb') as stream:
  while block:=stream.read(1024**2):dg.update(block);n+=len(block)
 assert identity(p.lstat())==before and n==row['bytes'] and dg.hexdigest()==row['sha256']
 hashes.append({'index':i,'original_path':row['path'],'recovered_path':str(p.relative_to(M)),'bytes':n,'sha256':dg.hexdigest(),'stat_identity':before})
for p,sig in original_stats.items():assert identity(p.lstat())==sig
hash_result={'kind':'single-independent-six-recovered-payload-streamed-hash-pass','files':hashes,'total_bytes':sum(r['bytes'] for r in hashes),'elapsed_seconds':time.monotonic()-began,'original_body_pass_reused':c['independent_body_hash'],'arrays_decoded':False}
(D/'RECOVERED_PAYLOAD_HASH01.json').write_text(json.dumps(hash_result,indent=2,sort_keys=True)+'\n')
# Active unrelated claim is only a sampled observation; do not require its mutable path as release evidence.
for path in active:evidence.pop(path,None)
result={'decision':'accepted-actual-full-byte-recovery','count':36,'bytes':3855758671,'directories':c['directories'],'rows':all_rows,'get_receipts':73,'known_recorded_pids_absent':sorted(pids),'unknown_complete_lifetime_pid_history':True,'active_consumer_check':{'unrelated_active_claims_checked':active,'references_selected_producer':False},'retirement_only_paths':[ledger['path'],str((S/f"{next(i for i,r in enumerate(c['files']) if r==ledger):02d}-recovered.bin").relative_to(M))],'retirement_payload_bytes':2*ledger['bytes'],'retirement_executed':False,'evidence':evidence,'qualification':'BYTE full recovery plus original path/name/mode descriptors; no POSIX reconstruction/runtime/scientific capacity claim. Original raw nulls and failed source history preserved.'}
(D/'OUTCOME_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'rows':36,'bytes':result['bytes'],'six_payload_bytes':hash_result['total_bytes'],'hash_seconds':hash_result['elapsed_seconds'],'get_receipts':73,'known_pids':len(pids),'retirement_bytes':result['retirement_payload_bytes'],'compact_evidence':len(evidence)},sort_keys=True))
