"""Genuine native failed-claim joins, supplementary strict original/refusal oracle evidence."""
from pathlib import Path
import json
from raw_receipts01 import body,metadata,require,digest,positive_native_observations,GIB,MAX
def authenticate(root,case,release):
    root=Path(root);identity=release['cases'][case]['identity'];source=release['capsule_commit'];entry=release['cases'][case]
    base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity;run='research_runs/'+identity
    launch=metadata(root,base+'/launch.json');owner=metadata(root,base+'/owner.json');guard=metadata(root,base+'/guard/final.json');ready=metadata(root,base+'/guard/cpu_ready.json');exit=metadata(root,base+'/guard/child_exit.json');worker=metadata(root,base+'/worker-file-limit.json');monitor=metadata(root,base+'/monitor-file-limit.json')
    require(set(launch)=={'experiment','source_commit','supervisor_pid','nonce'} and launch['experiment']==identity and launch['source_commit']==source,'launch identity differs')
    require(set(owner)==set(launch)|{'monitor_pid','monitor_start_ticks'} and all(owner[k]==v for k,v in launch.items()),'monitor owner differs')
    command=[release['runtime']['executable'],'-B','-m','tradingagents.research.onchain_replication.job','--mode','worker','--root',str(root),'--registration',release['registration'],'--experiment',identity,'--source',source]
    require(guard['owner_identity']==owner and guard['monitor_pid']==owner['monitor_pid'] and guard['command']==command and guard['cwd']==str(root),'original native owner/command differs')
    limits=entry['job_resources']
    require(not (root/base/'guard/native-finalization-failed.json').exists(),'selected native finalization failed')
    observations=positive_native_observations(root,guard,exit,limits)
    require(all(guard[k]==v for k,v in limits.items()) and guard['memory_swap_max_bytes']==0,'registered native policy differs')
    require(guard['kernel_controls']=={'memory.max':str(3*GIB),'memory.high':str(3*GIB),'memory.swap.max':'0'},'kernel native controls differ')
    require(metadata(root,base+'/guard/release.json')=={'kernel_controls_verified':True},'native release differs')
    require(ready['cpus']==guard['cpus'] and len(guard['cpus'])==2 and len(set(guard['cpus']))==2,'CPU denominator differs')
    require(guard['native_unit_properties']['LimitFSIZE']==guard['native_unit_properties']['LimitFSIZESoft']=='4194304','native hard/soft file controls differ')
    require(guard['native_unit_properties']['RuntimeMaxUSec'] in ('30min','1800s','1800000000us'),'native wall readback differs')
    require(ready['file_size_limit']==[MAX,MAX] and ready['native_unit_limits']=={'file_size_bytes':MAX},'ready optional limits missing/differ')
    require(ready['native_environment']==guard['native_environment']==release['native_environment'],'actual native environment differs')
    for role,value,pid in [('worker',worker,exit['workload_pid']),('monitor',monitor,owner['monitor_pid'])]:
        require(value['role']==role and value['experiment']==identity and value['source_commit']==source and value['pid']==pid and value['file_size_limit']==[MAX,MAX] and value['before_claim'] is True and value['native_environment']==release['native_environment'],'process limit receipt differs')
    require(worker['native_unit']==guard['unit'] and worker['native_cgroup']==guard['cgroup'],'worker original unit/cgroup differs')
    require((root/base/'worker-file-limit.json').stat().st_mtime_ns<=(root/run/'claim.json').stat().st_mtime_ns,'worker limit receipt did not precede claim')
    require(guard['cleanup_verified'] is True and guard['cleanup_unit_properties']['ActiveState'] in ('inactive','failed') and guard['cleanup_unit_properties']['SubState'] in ('dead','failed'),'native cleanup state missing')
    for key in ('storage_breach','storage_last_error','cleanup_error','elapsed_time_kill','child_log_limit_reached'):
        require(not guard.get(key),'native boundary breach: '+key)
    require(guard['memory_events']['oom']==0 and guard['memory_events']['oom_kill']==0,'kernel OOM is not expected fixture failure')
    pids={launch['supervisor_pid'],owner['monitor_pid'],ready['pid'],exit['workload_pid']};require(all(type(p) is int and p>1 for p in pids),'exact original PID set invalid')
    require(all(not Path('/proc',str(pid)).exists() for pid in pids),'recorded process still exists; no PID reuse assumed')
    cgroup=Path(guard['cgroup']);require(cgroup.is_absolute() and cgroup.is_relative_to('/sys/fs/cgroup') and cgroup.name==guard['unit'] and not cgroup.exists(),'original native cgroup still exists/differs')
    require((root/base/'guard/child.log').stat().st_size<MAX,'child log may be truncated')
    claim_raw=body(root,run+'/claim.json');claim=json.loads(claim_raw)
    require(claim['experiment_id']==identity and claim['source']==source and claim['program_id']==release['program_id'] and claim['registration']==release['registration'] and claim['registration_sha256']==release['registration_sha256'],'claim registration/source differs')
    require(claim['family']==release['family'] and claim['experiment']==entry['experiment'] and claim['inputs']==entry['experiment']['inputs'],'engineering claim contract differs')
    outcome='failed';require(not (root/run/('failed.json' if outcome=='complete' else 'complete.json')).exists(),'ambiguous lifecycle terminals')
    terminal=metadata(root,run+'/'+outcome+'.json');require(terminal['status']==outcome and terminal['experiment_id']==identity and terminal['claim_sha256']==digest(claim_raw),'lifecycle terminal differs')
    expected_outputs=set(entry['experiment']['outputs']);directory=root/run/'outputs';require({p.name for p in directory.iterdir()}==expected_outputs,'terminal output membership differs')
    hashes={name:digest(body(root,run+'/outputs/'+name)) for name in expected_outputs};require(hashes==terminal['output_sha256'],'terminal output body hashes differ')
    cells=metadata(root,run+'/outputs/cell-ledger.json');require([r['id'] for r in cells]==['import-target-01','import-target-02'] and [r['status'] for r in cells]==['unavailable','unavailable'],'retained target dispositions differ')
    if outcome=='complete':
        require(guard['phase']=='complete' and guard['child_exit_code']==exit['exit_code']==0 and guard['limit_reason'] is None,'successful fixture guard failed')
        require(terminal['source']==source and terminal['registration_sha256']==release['registration_sha256'] and terminal['cells']==cells and terminal['cell_count']==2 and terminal['unavailable_count']==0,'complete lifecycle denominator differs')
    else:
        require(guard['phase']=='failed' and guard['child_exit_code']==exit['exit_code']==1 and guard['unit_properties']['Result']=='exit-code' and guard['limit_reason'].startswith('RuntimeError: child or unit failed:'),'expected publication failure has unrelated native failure')
        require('RefusalObserved' in terminal['reason'] and ('registered original-import refusal observed: '+case) in terminal['reason'],'wrong retained failure cause')
    from refusal_caller import terminal as refusal_terminal
    supplement=refusal_terminal(root=root,variant=case)
    from refusal_oracle_evidence01 import authenticate_oracle
    oracle=authenticate_oracle(root,case,claim_raw)
    require(launch['supervisor_pid']==metadata(root,'fixture_outer/'+identity+'/supervisor.json')['pid'],'actual outer supervisor identity differs')
    return {'status':'expected-refusal','identity':identity,'claim_sha256':digest(claim_raw),'native':observations,'refusal':supplement,'oracle':oracle,'financial_completion':False}
