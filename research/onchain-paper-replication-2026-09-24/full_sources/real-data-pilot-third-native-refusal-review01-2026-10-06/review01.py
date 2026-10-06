"""Exact03 native setup refusal and tiny public incremental evidence only."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-third-native-refusal-review01-2026-10-06';D=F/'real-data-pilot-final03-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-03';SOURCE='2f5f855b26b75dea541dfa26ee9dd03917b8a58a'
P=Path('research_artifacts/onchain-paper-replication-2026-09-24');A=P/'runs'/N;L=P/'pilot-parent'/N
cache={}
def raw(p):
 p=Path(p)
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);cache[p]=b
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
files=[];dirs=[]
for root in (A,L):
 for p in sorted([root,*root.rglob('*')]):
  s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):dirs.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('launch-attempt01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json','REMOTE_CONFIRMATION02.json')
files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==16 and len(dirs)==3
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
root=read(D/'ROOT_TERMINAL01.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');remote=read(D/'REMOTE_CONFIRMATION02.json')
guard=read(A/'guard/final.json');live=read(A/'guard/live.json');owner=read(A/'owner.json');launch=read(A/'launch.json');obs=read(A/'observer.json');child=read(A/'guard/child_exit.json');cpu=read(A/'guard/cpu_ready.json')
assert root['identity']==launch['experiment']==owner['experiment']==N
assert root['source']==launch['source_commit']==owner['source_commit']==storage['source']==SOURCE
assert root['root_session']==62222 and root['root_terminal_chunk']=='36e8c2'
assert root['actual_root_exit']==root['actual_parent_exit']==io['actual_parent_exit_code']==1
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']==143840 and io['outer_log_handles_closed'] is True and io['supervisor_reaped'] is True
assert owner['monitor_pid']==guard['monitor_pid']==144105 and owner['nonce']==launch['nonce'] and guard['owner_identity']==owner
assert sha(A/'guard/final.json')==sha(A/'guard/live.json')==root['guard_sha256']=='3e7cc2dd933dd8d8286416d2814e7523f1079ba74eb241ed773d9c0760763306'
assert guard['phase']==root['native_phase']=='failed' and guard['elapsed_seconds']==root['native_elapsed_seconds']==4.44281520200002
assert guard['child_exit_code'] is None and root['original_child_exit'] is None
assert child['exit_code']==125 and child['workload_pid'] is None and child['reason']=='signal before release'
assert guard['limit_reason']==root['limit_reason']=='RuntimeError: host reserve fell during cgroup setup'
assert guard['host_mem_available_bytes']==root['original_host_mem_available_bytes']==9658896384
assert guard['start_reserve_bytes']==root['startup_requirement_bytes']==9663676416
assert guard['host_mem_available_bytes']<guard['start_reserve_bytes']
assert guard['cleanup_verified'] is True and root['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert guard['cleanup_unit_properties']['ControlGroup']=='' and guard['cleanup_unit_properties']['ExecMainStatus']=='125'
assert root['actual_unit_properties']['MainPID']=='0' and root['actual_unit_properties']['ControlGroup']=='' and root['actual_unit_properties']['ExecMainStatus']=='125'
assert not Path(guard['cgroup']).exists()
assert root['recorded_pids_absent']=={'143840':True,'144105':True,'144425':True}
assert cpu['pid']==144425 and all(not Path('/proc',p).exists() for p in root['recorded_pids_absent'])
for k,n in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][k]==sha(A/n)
assert storage['actual_current_cgroup_absent'] is True and storage['original_monitor_process_absent'] is True and storage['outer_log_handles_closed'] is True and storage['supervisor_reaped'] is True
assert obs['status']=='not_admitted' and obs['owner_sha256']==sha(A/'owner.json')
for p,pin in obs['evidence_sha256'].items():assert sha(A/p)==pin
assert not (Path('research_runs')/N).exists() and not (Path('research_runs')/N).is_symlink()
assert not (P/'sources'/N).exists() and not (P/'sources'/N).is_symlink()
assert not (A/'guard/release.json').exists() and len(raw(A/'guard/child.log'))==0
assert root['researchrun_namespace_absent'] is True and all(root[k]==0 for k in ('features_completed','training_updates','financial_fits'))
assert remote['actual_remote_head']==remote['local_source']==SOURCE and remote['push_exit']==remote['readback_exit']==0
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':dirs,
 'regular_count':16,'directory_count':3,'original_regular_bytes':sum(r['bytes'] for r in rows),
 'dynamic_entry_records':[str(D/n) for n in dynamic],
 'absent_namespaces':[str(Path('research_runs')/N),str(P/'sources'/N)],
 'scope':'Exact03 closed native-refusal public increment: actual runs03 tree, pilot-parent03 logs and five designated final03 dynamic records. Include all16regular bodies and3typed directories.',
 'exclusions':['Private connection and runtime bodies','Scientific/raw/graph stores','Earlier committed source/input/preparation records','Other attempt/backup stores','Shared parent directories outside selected roots'],
 'qualification':'Current canonical singly-linked bodies authenticated. Suitable exact archive selection; no archive capture/external recovery/deletion or retry authority granted.'}
sp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','identity':N,'source':SOURCE,'evidence':{str(p):sha(p) for p in sorted(files)},'increment_selection':ref(sp),
 'disposition':'TERMINAL_NATIVE_SETUP_REFUSAL_BEFORE_RESEARCHRUN_CLAIM; reserved launch and monitor-owner identity is closed and must never be reused.',
 'root_actual_exit':{'exit_code':1,'session':62222,'terminal_chunk':'36e8c2'},'parent':io,
 'native':{'phase':'failed','elapsed_seconds':guard['elapsed_seconds'],'original_child_exit_code':None,
 'separate_launcher_child_receipt':{'exit_code':125,'workload_pid':None,'reason':child['reason']},
 'separate_original_unit_properties':guard['cleanup_unit_properties'],'cleanup_verified':True,'cleanup_stop_returncode':0,
 'limit_reason':guard['limit_reason'],'observed_host_mem_available_bytes':9658896384,'unchanged_start_reserve_bytes':9663676416,'shortfall_bytes':9663676416-9658896384},
 'attempt_extent':{'native_setup_attempted':True,'launch_reserved':True,'monitor_owner_reserved':True,'researchrun_namespace_exists':False,'researchrun_claim':None,'source_namespace_exists':False,'guard_release_marker_exists':False,'observer_status':'not_admitted','MCM_work_completed':0,'training_updates':0,'financial_fits':0},
 'current_cleanup':{'recorded_pid_exists':{p:False for p in root['recorded_pids_absent']},'recorded_cgroup_absent':True,'lifetime_process_history':None,'qualification':'Three selected recorded PIDs absent now; original actual unit/guard/storage closure evidence joined. No lifetime inventory or fresh native command.'},
 'qualification':'Original guard child-exit null and workload-pid null remain unknown. Root/parent1 and launcher/systemd125 are separate fields, never substituted. No scientific claim, financial-ledger row, budget count, refund or trial outcome fabricated. This closed reserved identity must not be reused.',
 'not_tested':['No scientific timing/leakage/return/cashflow/fees/funding or capacity claim tested.','No private/runtime/scientific/raw/array bodies read; no numerical imports, network/native calls or experiment rerun.','No archive or external recovered-byte proof yet; later exact returned archive/member acceptance required.']}
op=write('OUTCOME_REVIEW01.json',outcome);mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':N,'files':[ref(H/'review01.py'),ref(sp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(sp),'manifest':ref(mp),'regulars':16,'directories':3,'bytes':selection['original_regular_bytes'],'decision':'accepted'},sort_keys=True))
