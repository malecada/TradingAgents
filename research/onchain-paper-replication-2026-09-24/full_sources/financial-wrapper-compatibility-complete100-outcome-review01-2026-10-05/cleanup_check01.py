from pathlib import Path
import hashlib,json,os,runpy,time
O=Path(__file__).resolve().parent;M=runpy.run_path(str(O/'verify_outcome01.py'));r=M['Reader']();C=M['C'];P=M['P'];ID=M['ID'];H=M['H'];need=M['need'];B=C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID;A=P/'attempt'
q=r.json(P/'REQUEST_FINAL01.json','cfecfd3e12d81628b9bc6f10171dd0345ac6e62c5481edccab64e5207254e03d');reg=r.json(C/q['registration'],q['registration_sha256']);job=r.json(C/reg['experiments'][ID]['inputs']['execution_job']['path']);guard=r.json(B/'guard/final.json','9e333203d1309aff85147a12f083432b65b3b7e2b87fb22ac17ea98ce45b1d33');live=r.json(B/'guard/live.json');pt=r.json(A/'parent-terminal.json','4d6dd61ecb474828f503cf2fafa90515d9bf602ded801a537b3c9dcc9cb0a50c');tree=r.json(A/'owned-tree-cleanup.json','6ae588c3afdccc4490a9cee63f7b053f253376bbf733a99b7b0996dcc75a0dbd')
for k,v in job['resources'].items():need(guard[k]==live[k]==v,'registered policy unchanged '+k)
need(guard['kernel_controls']=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'},'actual3GiB no-swap controls');need(guard['native_unit_properties']['LimitFSIZE']==guard['native_unit_properties']['LimitFSIZESoft']=='4194304','actual4MiB file limit');need(guard['cpus']==[0,1] and all(v==[0,1]for v in guard['cpu_thread_readback'].values()),'actual two CPU affinity')
need(guard['cpu_quota_controller_available'] is False,'honest unavailable CPU controller');need(guard['storage_peak_allocated_bytes']<=1073741824 and guard['storage_peak_logical_file_bytes']<=1073741824 and guard['storage_peak_entries']<=32768 and all(v>=10737418240 for v in guard['disk_free_bytes'].values()),'whole sampled caps/floor')
cleanup=pt['cleanup'];need(cleanup['subreaper_cleanup_sha256']==H(r.read(A/'owned-tree-cleanup.json')) and cleanup['unit']==guard['unit']==live['unit'] and cleanup['cgroup']==guard['cgroup']==live['cgroup'],'cleanup actual identities')
need(cleanup['native_pid_census_is_complete_history'] is False and cleanup['native_pid_start_records']==[],'no invented native PID history')
ops={};pids={};groups=set()
for label,op in cleanup['actual_control_operations'].items():
 out=r.read(A/label/'stdout');err=r.read(A/label/'stderr');ct=r.json(A/label/'owned-tree-cleanup.json');need(out.decode()==op['stdout'] and err.decode()==op['stderr'] and len(out)==op['stdout_bytes'] and len(err)==op['stderr_bytes'],'actual control streams')
 need(ct['subreaper_used'] is True and ct['remaining_original_identities']==[],'control descendants clear')
 for row in ct['owned_pid_start_records']:pids[row['pid']]=row['ticks'];groups.add(row['pgrp'])
 need(not Path('/proc',str(op['pid'])).exists(),'control PID absent');ops[label]={'exit_code':op['exit_code'],'stdout_sha256':H(out),'stderr_sha256':H(err),'cleanup_sha256':H(r.read(A/label/'owned-tree-cleanup.json'))}
need(set(ops)=={'before','stop','after'} and ops['before']['exit_code']==ops['after']['exit_code']==0 and ops['stop']['exit_code']==5,'retain actual control return values')
for label in ('before','after'):
 values=dict(line.split('=',1)for line in cleanup['actual_control_operations'][label]['stdout'].splitlines());need(values=={'Result':'success','ControlGroup':'','ActiveState':'inactive','SubState':'dead'},'actual terminal native state')
for row in tree['owned_pid_start_records']:pids[row['pid']]=row['ticks'];groups.add(row['pgrp'])
need(not Path(cleanup['cgroup']).exists(),'actual cgroup absent')
remaining=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  raw=(p/'stat').read_bytes();need(len(raw)<=65536,'bounded proc metadata');parts=raw.decode().rsplit(')',1)[1].split()
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 pid=int(p.name)
 if pid in pids:need(parts[19]!=str(pids[pid]),'original PID/start remains')
 if int(parts[2]) in groups:remaining.append(pid)
need(remaining==[],'original owned groups absent')
spawn=r.json(A/'spawn.json');intent=r.json(A/'intent.json');need(spawn['pid']==pt['supervisor_result']['pid'] and spawn['source']==q['source'] and spawn['identity']==ID and intent['identity']==ID and intent['phase']=='complete100','actual Parent dispatch joins')
need(intent['contract']==H(M['json'].dumps({k:v for k,v in q.items()if k!='final_review'},sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'),'same final contract at actual launch')
need(intent['preclaim_metadata']['metadata_bytes_read']==8267882,'launch repeated full metadata preclaim')
for name,countkey in [('stdout','stdout_bytes'),('stderr','stderr_bytes')]:need(len(r.read(A/name))==pt['supervisor_result'][countkey],'actual supervised streams')
old={
'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01':('4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'),
'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01':('d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558'),
'financial-wrapper-classification-eager-complete100-20261003-01':('2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','abdaef6f01bd02614782e442e2c102c38faa57e76061cba43b69960f3e389fa6')}
need({p.name for p in (C/'research_runs').iterdir()}==set(old)|{ID,'.lock'},'allfour genuine attempts retained')
for identity,pins in old.items():
 for name,pin in zip(('claim.json','failed.json'),pins):r.read(C/'research_runs'/identity/name,pin)
 need(not os.path.lexists(C/'research_runs'/identity/'complete.json'),'old failed remains failed')
# Hash remaining fixed source pins once; the main verifier already authenticated195.
for name,pin in q['source_files'].items():
 if not name.startswith('tradingagents/research/onchain_replication/'):r.read(C/name,pin)
r.finish();result={'decision':'ACCEPTED_ACTUAL_COMPLETE100_OWNED_CLEANUP_ONLY','identity':ID,'source':q['source'],'original_parent_exit':None,'actual_child_exit':0,'actual_root_exit_ref':{'path':str(O.parent/'heartbeat-root-checkpoint10-2026-10-04/COMPATIBLE100_ACTUAL_ROOT_EXIT01.json'),'sha256':'f308d4b11c6ac0975f586145bf2f811c632b2f8df7f1949ff36d8f84a6cdac53'},'parent_terminal_sha256':H(r.read(A/'parent-terminal.json')),'owned_cleanup_sha256':H(r.read(A/'owned-tree-cleanup.json')),'guard_final_sha256':H(r.read(B/'guard/final.json')),'actual_control_operations':ops,'owned_pid_start_records':pids,'owned_process_groups':sorted(groups),'remaining_owned_groups':remaining,'cgroup':cleanup['cgroup'],'cgroup_absent':True,'native_pid_history_complete':False,'kernel_cpu_quota_available':False,'two_cpu_affinity_observed':True,'peak_sampled_memory_bytes':guard['peak_sampled_memory_current_bytes'],'guard_elapsed_seconds':guard['elapsed_seconds'],'parent_supervisor_elapsed_seconds':pt['supervisor_result']['elapsed_seconds'],'storage_peak_logical_bytes':guard['storage_peak_logical_file_bytes'],'storage_peak_allocated_bytes':guard['storage_peak_allocated_bytes'],'storage_peak_entries':guard['storage_peak_entries'],'actual_engineering_complete':1,'actual_engineering_failed':3,'actual_engineering_attempts':4,'highest_claimed_allowance':20,'paper_financial_fits_added':0,'numerical_reexecution':False}
(O/'CLEANUP_PROOF01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
