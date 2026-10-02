"""Authenticate actual retained native/lifecycle/artifact joins; no numerical loads."""
import hashlib,json,os,stat
from pathlib import Path
GIB=1024**3
MAX=4*1024**2

def require(v,m):
    if not v:raise ValueError(m)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def body(root,relative,limit=MAX):
    root=Path(root);p=root/relative;require(not Path(relative).is_absolute() and '..' not in Path(relative).parts and p.resolve()==p and p.is_relative_to(root),'raw path redirected')
    before=p.lstat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'raw regular extent differs')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);primary=None
    try:
        opened=os.fstat(fd);require((opened.st_dev,opened.st_ino)==(before.st_dev,before.st_ino),'raw inode differs')
        chunks=[];left=before.st_size
        while left:
            part=os.read(fd,min(left,65536));require(part,'raw truncated');chunks.append(part);left-=len(part)
        require(not os.read(fd,1),'raw extended');after=p.lstat();require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'raw changed during read')
        return b''.join(chunks)
    except BaseException as error:primary=error;raise
    finally:
        try:os.close(fd)
        except BaseException as later:
            if primary is None:raise
            if not isinstance(primary,Exception) or isinstance(primary,MemoryError):pass
            elif not isinstance(later,Exception) or isinstance(later,MemoryError):raise
            else:raise RuntimeError('raw descriptor close uncertain') from primary

def metadata(root,name):return json.loads(body(root,name))
def target_artifact(root,row,expected):
    record=row['target'];ticket=record['output'];directory=Path(ticket['directory'])
    require(directory.is_relative_to(root) and directory.resolve()==directory,'target output directory redirected')
    prefix=str(directory.relative_to(root));receipt=body(root,prefix+'/receipt.json');require(digest(receipt)==ticket['receipt_sha256'],'target publication receipt changed')
    manifest_raw=body(root,prefix+'/artifact/manifest.json');manifest=json.loads(manifest_raw)
    require(digest(manifest_raw)==ticket['artifact_sha256'] and json.loads(receipt)['artifact_sha256']==ticket['artifact_sha256'],'artifact receipt/manifest join differs')
    matrix=body(root,prefix+'/artifact/matrix.f32',65536)
    require(record['graph_hash']==expected['graph_hash'] and record['rows']==expected['nodes'] and record['motifs']==32 and record['cells']==expected['nodes']*32,'target exact denominator differs')
    require(manifest['rows']==expected['nodes'] and manifest['motifs']==32 and manifest['dtype']=='<f4' and manifest['order']=='row-major' and len(matrix)==4*32*expected['nodes'],'target matrix extent differs')
    require(digest(matrix)==record['matrix_sha256']==manifest['array_sha256'],'target matrix hash differs')
    require(row['reference_atol']==1e-5 and row['reference_rtol']==1e-4,'scalar oracle tolerances changed')
    return {'directory':prefix,'receipt_sha256':digest(receipt),'manifest_sha256':digest(manifest_raw),'matrix_sha256':digest(matrix),'bytes':len(matrix)}

def authenticate(root,case,release):
    root=Path(root);identity=release['cases'][case]['identity'];source=release['capsule_commit'];entry=release['cases'][case]
    base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity;run='research_runs/'+identity
    launch=metadata(root,base+'/launch.json');owner=metadata(root,base+'/owner.json');guard=metadata(root,base+'/guard/final.json');ready=metadata(root,base+'/guard/cpu_ready.json');exit=metadata(root,base+'/guard/child_exit.json');worker=metadata(root,base+'/worker-file-limit.json');monitor=metadata(root,base+'/monitor-file-limit.json')
    require(set(launch)=={'experiment','source_commit','supervisor_pid','nonce'} and launch['experiment']==identity and launch['source_commit']==source,'launch identity differs')
    require(set(owner)==set(launch)|{'monitor_pid','monitor_start_ticks'} and all(owner[k]==v for k,v in launch.items()),'monitor owner differs')
    command=[release['runtime']['executable'],'-B','-m','tradingagents.research.onchain_replication.job','--mode','worker','--root',str(root),'--registration',release['registration'],'--experiment',identity,'--source',source]
    require(guard['owner_identity']==owner and guard['monitor_pid']==owner['monitor_pid'] and guard['command']==command and guard['cwd']==str(root),'original native owner/command differs')
    limits=entry['job_resources']
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
    outcome='complete' if case=='success' else 'failed';require(not (root/run/('failed.json' if outcome=='complete' else 'complete.json')).exists(),'ambiguous lifecycle terminals')
    terminal=metadata(root,run+'/'+outcome+'.json');require(terminal['status']==outcome and terminal['experiment_id']==identity and terminal['claim_sha256']==digest(claim_raw),'lifecycle terminal differs')
    expected_outputs=set(entry['experiment']['outputs']);directory=root/run/'outputs';require({p.name for p in directory.iterdir()}==expected_outputs,'terminal output membership differs')
    hashes={name:digest(body(root,run+'/outputs/'+name)) for name in expected_outputs};require(hashes==terminal['output_sha256'],'terminal output body hashes differ')
    cells=metadata(root,run+'/outputs/cell-ledger.json');require([r['id'] for r in cells]==['import-target-01','import-target-02'] and [r['status'] for r in cells]==(['complete','complete'] if outcome=='complete' else ['complete','failed']),'retained target dispositions differ')
    if outcome=='complete':
        require(guard['phase']=='complete' and guard['child_exit_code']==exit['exit_code']==0 and guard['limit_reason'] is None,'successful fixture guard failed')
        require(terminal['source']==source and terminal['registration_sha256']==release['registration_sha256'] and terminal['cells']==cells and terminal['cell_count']==2 and terminal['unavailable_count']==0,'complete lifecycle denominator differs')
    else:
        require(guard['phase']=='failed' and guard['child_exit_code']==exit['exit_code']==1 and guard['unit_properties']['Result']=='exit-code' and guard['limit_reason'].startswith('RuntimeError: child or unit failed:'),'expected publication failure has unrelated native failure')
        require('FixturePublicationFailure' in terminal['reason'] and 'second-target publication boundary' in terminal['reason'],'wrong retained failure cause')
    binding=metadata(root,run+'/outputs/resource-binding.json');journal=metadata(root,run+'/outputs/resource-journal.json')
    require(binding==journal and journal['schema_version']==2 and journal['kind']=='original-import-resource-terminal' and journal['status']==outcome and journal['resource_only'] is True and journal['financial_representation_admitted'] is False,'resource output terminal differs')
    if outcome=='complete':
        require(journal['original_dictionary']=='48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726' and journal['cells']==['import-target-01','import-target-02'] and journal['targets']==[r['target'] for r in cells],'resource completed targets differ')
        original_owner=journal['owner'];require(original_owner['experiment']==identity and original_owner['source_commit']==source,'resource journal owner differs')
        directory='research_artifacts/onchain_representations/'+original_owner['workflow_identity']+'/'+identity
        require(metadata(root,directory+'/complete.json')==journal and metadata(root,directory+'/owner.json')==original_owner,'original journal publication differs')
        compact_raw=body(root,directory+'/compact/complete.json');compact=json.loads(compact_raw)
        require(digest(compact_raw)==journal['compact_owner_sha256'] and compact['stages']==3 and compact['pairs']==160 and compact['representation_admitted'] is False,'compact resource terminal denominator differs')
    else:require('FixturePublicationFailure' in journal['reason'],'resource terminal failure differs')
    artifacts=[target_artifact(root,r,t) for r,t in zip(cells,entry['targets'],strict=True) if r['status']=='complete']
    summary=metadata(root,run+'/outputs/resource-summary.json');require(summary['resource_only'] is True and summary['financial_representation_admitted'] is False and summary['original_motifs']==32 and summary['cells']==cells,'resource terminal summary differs')
    require(summary['original_dictionary']=='48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726','original dictionary changed')
    return {'case':case,'lifecycle_status':outcome,'claim_sha256':digest(claim_raw),'artifacts':artifacts,'recorded_pids':sorted(pids),'original_cgroup':str(cgroup),'expected_failure':outcome=='failed','numerical_arrays_loaded_by_parser':False}
