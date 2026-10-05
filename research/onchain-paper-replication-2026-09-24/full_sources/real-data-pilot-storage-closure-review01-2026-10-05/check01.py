"""Independent compact actual closure only; no transferred bodies or network."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ENTRY=ROOT/'research/onchain-paper-replication-2026-09-24/storage/closed-ledger-pilot-offload-2026-10-05-01'
SOURCE='7d400380810c2aefd79e82ed2a8eabbe44119e89'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
read=lambda name:json.loads((ENTRY/name).read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SOURCE
c=read('manifest.json');row=c['files'][0];release=read('RELEASE_REVIEW.json')
assert len(c['files'])==1 and row['bytes']==c['total_bytes']==3662934016
assert sha((ENTRY/'manifest.json').read_bytes())==release['manifest_sha256']=='73cc7210e33d613ca90069a43a636a888606e3f92b97407d92bbba5288b6c166'
assert sha((ENTRY/'offload.py').read_bytes())==release['worker_sha256']=='edf1ade0f56113515316c210dea8b256e11589f9c1eda4c94b077d1bbae08e5d'
assert sha((ENTRY/'transport.py').read_bytes())==release['transport_sha256']=='ee551abbb81bec2b42355ce073c2a570d6ed0b37bd763b047b539f8c1148de16'
assert sha((ENTRY/'bindings.json').read_bytes())==release['bindings_sha256']=='bad4362b3547f6b5c10202ee35d24a2ed28a4a7600b47a25d51446e8421c4ceb'
assert release['decision']=='accepted'
bindings={**read('bindings.json'),**read('release-bindings01.json')}
committed=[]
for path,h in bindings.items():
    if path==c['connection_path']:continue # Connection contents are not opened.
    raw=(ROOT/path).read_bytes()
    assert sha(raw)==h,path
    assert subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)==raw,path
    committed.append(path)
release_path=str((ENTRY/'release-bindings01.json').relative_to(ROOT))
assert subprocess.check_output(['git','show',SOURCE+':'+release_path],cwd=ROOT)==(ENTRY/'release-bindings01.json').read_bytes()
assert len(bindings)==35 and len(committed)==34

index=json.loads((ROOT/c['closure']['artifact_index']['path']).read_bytes())
assert index[row['path']]=={'bytes':row['bytes'],'sha256':row['sha256']}
assert row['sha256']=='2543a858c9054d2fb0a7d9349610d21cfaf5de93fc1efda4d2ec6a9c12269251'
pre=read('preflight01.json');intent=read('intent.json')
assert pre['head']==SOURCE and pre['bindings_verified']==35 and pre['source_stat_identity']==row['stat_identity']
assert pre['full_recovery_scratch_required_bytes']==10*1024**3+row['bytes']+16*1024**2
assert pre['workspace_free_bytes']>=pre['full_recovery_scratch_required_bytes']
assert pre['mem_available_bytes']>=int(3.5*1024**3)
assert pre['no_active_unit'] is True and pre['no_retry'] is True
assert intent['manifest_sha256']==release['manifest_sha256'] and intent['remote']==c['remote'] and intent['bytes']==row['bytes']
assert read('launch-attempt01.json')['no_automatic_retry'] is True

evidence_names=['manifest.json','bindings.json','release-bindings01.json','offload.py','transport.py','RELEASE_REVIEW.json','RELEASE_REVIEW.md','launch-attempt01.json','preflight01.json','intent.json','00-restore.json','00-recovered-restore.json','00-verified.json','00-evicted.json','completion-candidate.json','complete.json','recovered-complete.json','recovered-manifest.json','outer-exit01.json','outer01.log']
verified=read('00-verified.json')
assert {k:verified[k] for k in row}==row
assert verified['body_roundtrip_verified'] is True
assert verified['remote_object']==c['remote']+'/00.bin'
assert verified['remote_restore']==c['remote']+'/00-restore.json'
sidecar=(ROOT/row['path']).with_name('ledger.sqlite.remote.json')
assert not (ROOT/row['path']).exists() and not (ROOT/row['path']).is_symlink()
assert sidecar.is_file() and not sidecar.is_symlink()
raw=(ENTRY/'00-verified.json').read_bytes()
for name in ('00-restore.json','00-recovered-restore.json','00-evicted.json'):assert (ENTRY/name).read_bytes()==raw
assert sidecar.read_bytes()==raw
assert (ENTRY/'recovered-manifest.json').read_bytes()==(ENTRY/'manifest.json').read_bytes()
complete=read('complete.json')
assert complete['files']==[verified] and complete['bytes_moved']==row['bytes']
for name in ('completion-candidate.json','recovered-complete.json'):assert (ENTRY/name).read_bytes()==(ENTRY/'complete.json').read_bytes()
assert not (ENTRY/'00-recovered.bin').exists() and not (ENTRY/'failed.json').exists()

transport={};pids=set()
for name,count in [('00-recovered.bin',row['bytes']),('recovered-manifest.json',3805),('00-recovered-restore.json',816),('recovered-complete.json',1172)]:
    receipt_name=name+'.transport.json';v=read(receipt_name)
    assert v['status']=='complete' and v['returncode']==0 and v['error_type'] is None
    assert v['expected_bytes']==v['received_bytes']==count
    assert 0<v['elapsed_seconds']<5400 and v['stderr_truncated'] is False
    assert str(count)+' bytes' in v['stderr_tail']
    pids.add(v['pid']);transport[name]=v;evidence_names.append(receipt_name)
guard=read('guard01/final.json');child=read('guard01/child_exit.json');ready=read('guard01/cpu_ready.json')
assert (ENTRY/'guard01/final.json').read_bytes()==(ENTRY/'guard01/live.json').read_bytes()
assert guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified'] is True and guard['limit_reason'] is None
assert guard['command']==[str(ROOT/'.venv/bin/python'),'-B',str(ENTRY/'offload.py'),'--worker']
assert guard['cwd']==str(ROOT) and guard['receipt_dir']==str(ENTRY/'guard01')
assert guard['wall_seconds']==14400 and guard['disk_floor_bytes']==10*1024**3
assert guard['kernel_controls']=={'memory.high':str(192*1024**2),'memory.max':str(256*1024**2),'memory.swap.max':'0'}
assert guard['memory_swap_max_bytes']==0 and guard['reserve_bytes']==3*1024**3 and guard['start_reserve_bytes']==int(3.5*1024**3)
assert guard['cpus']==ready['cpus']==[0,1]
assert all(v==[0,1] for v in guard['cpu_thread_readback'].values())
assert read('guard01/release.json')['kernel_controls_verified'] is True
assert child['exit_code']==0 and child['snapshot_error'] is None and child['terminal_memory_snapshot']==guard['terminal_memory_snapshot']
assert guard['memory_events']['high']==56849
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill','oom_group_kill'))
telemetry=guard['optional_memory_telemetry']
assert telemetry['unit']['kernel_peak_bytes']==204120064 and guard['peak_sampled_memory_current_bytes']==201793536
assert telemetry['unit']['swap_current_bytes']==0
pids.update([guard['monitor_pid'],child['workload_pid'],ready['pid']]);pids.update(int(k) for k in guard['cpu_thread_readback'])
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
assert not Path(guard['cgroup']).exists()
assert guard['cleanup_unit_properties']['ActiveState']=='inactive' and guard['cleanup_unit_properties']['SubState']=='dead'
assert guard['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
outer=read('outer-exit01.json');log=read('outer01.log')
assert outer=={'actual_outer_exit':0,'phase':'complete','child_exit_code':0,'cleanup_verified':True,'limit_reason':None}
assert log=={k:v for k,v in outer.items() if k!='actual_outer_exit'}
assert (ENTRY/'guard01/child.log').read_bytes()==b''
evidence_names += ['guard01/'+n for n in ('release.json','child.log','child_exit.json','cpu_ready.json','live.json','final.json')]
evidence={str((ENTRY/name).relative_to(ROOT)):sha((ENTRY/name).read_bytes()) for name in evidence_names}
evidence[str(sidecar.relative_to(ROOT))]=sha(sidecar.read_bytes())
for ref in c['closure'].values():evidence[ref['path']]=ref['sha256']
for ref in c['accepted_saved_array_verification'].values():evidence[ref['path']]=ref['sha256']
evidence[c['producer_closure_review']['path']]=c['producer_closure_review']['sha256']
out={'status':'PASS_ACTUAL_COMPACT_CLOSURE','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':SOURCE,'current_and_committed_bound_bodies':len(committed),'release_table_committed':True,'connection_file_opened':False,'source_ledger_body_read':False,'transfer_repeated':False,'evidence':evidence,'ledger_row':row,'sidecar_sha256':sha(sidecar.read_bytes()),'source_path_absent':True,'successful_recovery_scratch_absent':True,'recorded_pids_absent':sorted(pids),'cgroup_absent':guard['cgroup'],'outer_actual_exit_record':outer,'transport':transport,'resource_observation':{'elapsed_seconds':guard['elapsed_seconds'],'last_unit_kernel_peak_bytes':telemetry['unit']['kernel_peak_bytes'],'sampled_peak_bytes':guard['peak_sampled_memory_current_bytes'],'memory_events':guard['memory_events'],'unit_last_swap_bytes':telemetry['unit']['swap_current_bytes'],'ancestor_peak_not_job_bytes':telemetry['user_ancestor']['kernel_peak_bytes'],'cpu_quota_controller_available':guard['cpu_quota_controller_available'],'cpus':guard['cpus']},'current_disk_free_bytes':shutil.disk_usage(ROOT).free}
(HERE/'CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':out['status'],'source_commit':SOURCE,'committed_bodies':len(committed),'evidence_entries':len(evidence),'recorded_pids_absent':sorted(pids),'resource_observation':out['resource_observation'],'current_disk_free_bytes':out['current_disk_free_bytes']},indent=2))
