"""Actual COPY receipt/source/current-stat joins, without any payload read."""
from pathlib import Path
import datetime,hashlib,json,stat
H=Path(__file__).resolve().parent;F=H.parent.parent;R=F.parents[2];D=F/'real-data-pilot-july25-ledger-relocation01-2026-10-06';ev={}
def raw(p,pin=None):
 p=Path(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;b=p.read_bytes();assert (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==tuple(getattr(p.lstat(),k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'));digest=hashlib.sha256(b).hexdigest();assert pin is None or digest==pin;ev[str(p.relative_to(R))]=digest;return b
def read(p,pin=None):return json.loads(raw(p,pin))
def sig5(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def sig7(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
env=read(D/'copy-envelope01.json','725af097346fa2edb077a8a1c8df676257b69043ec17340941533e3c4a5578dc');sel=read(R/env['selection']['path'],env['selection']['sha256']);release=read(D/'copy-RELEASE_REVIEW01.json','c55eb1e50d9dae393be3b889980e5fa1a5d989f8886d913663365426fe96a165')
assert release['decision']=='accepted' and release['phase']=='copy' and release['envelope_sha256']==ev[str((D/'copy-envelope01.json').relative_to(R))]
for path,pin in env['source_files'].items():raw(R/path,pin)
read(R/env['environment']['path'],env['environment']['sha256'])
prior=sel['recovery_selection']['recovery_basis']['outcome_review'];accepted=read(R/prior['path'],prior['sha256']);assert accepted['decision']=='accepted' and accepted['full_scope_byte_recovery'] is True
rec=read(D/'copy-complete01.json','b008b0fc1cfb7aea702597f27d9094adbcf1c47c472717836550c03864c8f20b');root=read(D/'COPY_ROOT_TERMINAL01.json');native=read(D/'copy-guard01/final.json','9e88a18b1e4b3fa724239bed416d975624ea236d5e7e6955307fdd575af3dada');outer=read(D/'copy-outer-exit01.json','74818d8b7ee9da2acdbf23d87f2a74379a9ba9e00d38a5750589fdc44d259245')
assert rec['identity']==root['identity']==sel['identity']==env['identity'] and rec['schema_version']==1
assert rec['predecessor']=='eth-paper-resource-pilot-20260924-02' and rec['original_claim_sha256']=='05d769f6f50a65c2cf3eeed569077eb84e3871b1e7c23ad3504eed461a0565ca' and rec['original_source']=='c6b568d4b1c177ab94ac37fbad462c2decc721c0'
assert rec['recovery_review']==prior and rec['original']==sel['recovery_selection']['rows'][0]['original']
assert all(rec[k] is True for k in ('copy_readback_verified','external_byte_recovery_verified','typed_name_mode_verified')) and rec['original_retired'] is False and rec['source_retired'] is False
assert {k:rec['target'][k] for k in ('path','device','bytes','sha256')}==sel['target']
observations=[]
for row in [sel['recovery_selection']['rows'][0]['original'],sel['recovery_selection']['rows'][0]['recovered']]:
 p=R/row['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sig5(s)==row['stat_identity'] and stat.S_IMODE(s.st_mode)==row['mode'];observations.append({'path':str(p),'stat_identity7':sig7(s)})
p=Path(rec['target']['path']);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sig7(s)==rec['target']['stat_identity'] and s.st_size==3755212800 and s.st_dev==66307 and stat.S_IMODE(s.st_mode)==rec['original']['mode']
assert set(q.name for q in p.parent.iterdir())=={'events.sqlite'};observations.append({'path':str(p),'stat_identity7':sig7(s)})
assert root['actual_root_tool_session']==18532 and root['actual_root_tool_chunk']=='0d0054' and root['actual_root_tool_exit_code']==root['actual_parent_exit_code']==0
for key,leaf in [('copy_receipt_sha256','copy-complete01.json'),('native_final_sha256','copy-guard01/final.json'),('outer_exit_sha256','copy-outer-exit01.json')]:assert root[key]==ev[str((D/leaf).relative_to(R))]
assert native['phase']=='complete' and native['child_exit_code']==0 and native['cleanup_verified'] is True and native['cleanup_stop_returncode']==root['actual_retained_stop_returncode']==5
assert outer['entry_selected_exit_code']==outer['guard_child_exit_code']==0 and outer['cleanup_verified'] is True and outer['fatal_type'] is None
assert native['command']==[str(R/'.venv/bin/python'),'-B',str(D/'entry01.py'),'--copy-worker'] and native['cwd']==str(R)
assert native['kernel_controls']=={'memory.high':'201326592','memory.max':'268435456','memory.swap.max':'0'} and native['disk_paths']==[str(R),'/home/malecada/Data']
assert native['wall_seconds']==14400 and native['disk_floor_bytes']==10*1024**3 and native['reserve_bytes']==3*1024**3 and native['start_reserve_bytes']==int(3.5*1024**3)
assert native['storage_budget']=={'root':str(D),'limits':{'max_allocated_bytes':5*1024**3,'max_logical_bytes':5*1024**3,'max_entries':4096,'max_depth':16,'max_scan_seconds':5}}
child=read(D/'copy-guard01/child_exit.json');ready=read(D/'copy-guard01/cpu_ready.json');assert child['exit_code']==0
pids=set([native['monitor_pid'],child['workload_pid'],ready['pid']]+[int(k) for k in native['cpu_thread_readback']]);assert pids==set(root['selected_recorded_pids']) and all(not Path('/proc',str(p)).exists() for p in pids)
assert not Path(native['cgroup']).exists() and root['actual_current_cgroup_absent'] is True and root['selected_recorded_pids_absent'] is True
assert root['actual_current_unit_properties']['ActiveState']=='inactive' and root['actual_current_unit_properties']['MainPID']=='0' and root['actual_current_unit_properties']['ControlGroup']=='' and root['unknown_lifetime_process_history'] is None
pre=read(D/'copy-preflight01.json');assert pre==read(D/'copy-launch-attempt01.json') and pre['envelope_sha256']==release['envelope_sha256'] and pre['head']=='4f8de4f34f05369c0a04f10c0cf2844e1d933e0e'
attempt=read(D/'copy-attempt01.json');assert attempt['source']==rec['original'] and attempt['target']==sel['target'] and attempt['no_retry'] is True
assert not (D/'copy-failed01.json').exists() and not (D/'retire-attempt01.json').exists() and not (D/'relocation-receipt01.json').exists()
result={'decision':'pass','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':rec['identity'],'copy_receipt_sha256':root['copy_receipt_sha256'],'current_stats':observations,'recorded_pids_absent':sorted(pids),'cgroup_absent':True,'evidence':ev,'original_stop_returncode':5,'native_high_events':native['memory_events']['high'],'unit_last_kernel_peak_bytes':native['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'unknown_lifetime_history':None,'full_stream_method':'Exact released stream_copy hashes all original bytes while copying, fsyncs file/directory, independently opens target for full readback SHA, and joins source/destination stat before/after under advisory descriptor locks. Actual COMPLETE is published only after guards/currentness/sole-leaf checks. Reviewer authenticates this source and actual receipts; no payload reread.','reviewer_payload_reads':0}
(H/'CHECK02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','full_stream_method')},sort_keys=True))
