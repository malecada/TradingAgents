"""Four guarded real admission refusals; never ResearchRun.start or Binding."""
import argparse,hashlib,json,os,resource,shutil,signal,sys
from pathlib import Path
from types import SimpleNamespace
from raw_receipts01 import require,body,metadata,positive_native_observations,GIB,MAX
from refusal_cases import PRECLAIM,identity

def command(root,release_path,release_sha,case,guard):
    return [sys.executable,'-B',str(root/'fixture_tools/refusal_preclaim01.py'),'--root',str(root),'--release',release_path,'--release-sha256',release_sha,'--case',case,'--guard',str(guard)]

def run_preclaim(root,release,case,outer,resources,watch,io):
    require(case in PRECLAIM,'finite preclaim case required')
    # The exact released reference is part of the selected release template.
    ref=release['self_reference'];raw=body(root,ref['path']);require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'preclaim released body differs')
    # A release cannot contain its own hash. The coordinator supplies an external
    # immutable envelope containing its already frozen release reference instead.
    envelope=json.loads(raw);require(envelope=={k:v for k,v in release.items() if k!='self_reference'},'preclaim release envelope differs')
    guard=outer/'preclaim-guard';cmd=command(root,ref['path'],ref['sha256'],case,guard)
    owner={'kind':'preclaim-admission-only','identity':identity(case),'source':release['capsule_commit'],'controller_pid':os.getpid()}
    def save(name,value):
        require(len((json.dumps(value,sort_keys=True)+'\n').encode())<=8192,'preclaim metadata ceiling');resources._native_receipt(outer,name,value)
    from refusal_outer01 import select
    primary=None;result=None;handlers={}
    def interrupt(number,frame):raise InterruptedError('guarded preclaim interrupted; no retry')
    try:
        for number in (signal.SIGTERM,signal.SIGINT):handlers[number]=signal.signal(number,interrupt)
        save('preclaim-intent.json',{'owner':owner,'command':cmd,'registration_sha256':release['registration_sha256'],'claim_cardinality':0})
        result=resources.guarded_run(cmd,cwd=root,receipt_dir=guard,owner_identity=owner,memory_swap_max_bytes=0,**release['cases'][case]['job_resources'])
        child=metadata(root,str(guard.relative_to(root))+'/child_exit.json');ready=metadata(root,str(guard.relative_to(root))+'/cpu_ready.json')
        require(result==metadata(root,str(guard.relative_to(root))+'/final.json'),'actual guard return differs')
        require(result['phase']=='complete' and result['child_exit_code']==child['exit_code']==0 and result['limit_reason'] is None,'preclaim guard did not complete')
        require(result['owner_identity']==owner and result['command']==cmd and result['cwd']==str(root),'preclaim native ownership differs')
        limits=release['cases'][case]['job_resources'];require(all(result[k]==v for k,v in limits.items()) and result['memory_swap_max_bytes']==0,'preclaim actual limits differ')
        require(result['kernel_controls']=={'memory.max':str(3*GIB),'memory.high':str(3*GIB),'memory.swap.max':'0'},'preclaim kernel controls differ')
        require(result['cleanup_verified'] is True and not Path(result['cgroup']).exists(),'preclaim cgroup cleanup missing')
        require(result['cleanup_unit_properties']['ActiveState'] in ('inactive','failed') and result['cleanup_unit_properties']['SubState'] in ('dead','failed'),'preclaim unit cleanup missing')
        for pid in (ready['pid'],child['workload_pid']):require(type(pid) is int and pid>1 and not Path('/proc',str(pid)).exists(),'preclaim child still exists')
        require(ready['native_environment']==result['native_environment']==release['native_environment'] and ready['file_size_limit']==[MAX,MAX] and ready['native_unit_limits']=={'file_size_bytes':MAX},'preclaim native environment/file limit differs')
        require(len(ready['cpus'])==len(set(ready['cpus']))==2 and ready['cpus']==result['cpus'] and all(type(v) is int for v in ready['cpus']),'preclaim two-CPU readback differs')
        props=result['native_unit_properties'];require(props['LimitFSIZE']==props['LimitFSIZESoft']==str(MAX) and props['RuntimeMaxUSec'] in ('30min','1800s','1800000000us'),'preclaim native file/wall policy differs')
        for key in ('storage_breach','storage_last_error','cleanup_error','elapsed_time_kill','child_log_limit_reached'):require(not result.get(key),'unexpected preclaim native breach')
        positive_native_observations(root,result,child,limits)
        observed=metadata(root,str(outer.relative_to(root))+'/preclaim-observed.json');require(observed['identity']==identity(case) and observed['source']==release['capsule_commit'] and observed['command']==cmd and observed['guard_owner']==owner and observed['file_limits']==[MAX,MAX] and observed['observation']['claim_created'] is False,'actual guarded preclaim observation differs')
        require(not (root/'research_runs'/identity(case)).exists() and not (root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity(case)).exists(),'preclaim created job/claim namespace')
    except BaseException as error:primary=error
    finally:
        try:
            current=watch.check();require(shutil.disk_usage(root).free>=10*GIB,'preclaim final floor breached');save('terminal.json',{'status':'passed' if primary is None else 'failed','case':case,'identity':identity(case),'claim_cardinality':0,'owner_cardinality':0,'error_type':None if primary is None else type(primary).__name__,'storage':current,'actual_guard_status':None if result is None else result['phase']});watch.check()
        except BaseException as later:primary=select(primary,later,io.CleanupFailure)
        for number,handler in handlers.items():
            try:signal.signal(number,handler)
            except BaseException as later:primary=select(primary,later,io.CleanupFailure)
        if primary is not None:
            try:save('post-terminal-failure.json',{'status':'failed','identity':identity(case),'error_type':type(primary).__name__,'claim_cardinality':0})
            except BaseException as later:primary=select(primary,later,io.CleanupFailure)
    if primary is not None:raise primary
    return {'status':'expected-preclaim-refusal','identity':identity(case),'claim_cardinality':0}

def worker(args):
    root=Path(args.root);raw=body(root,args.release);require(hashlib.sha256(raw).hexdigest()==args.release_sha256,'guarded released input differs');release=json.loads(raw)
    require(args.case in PRECLAIM and root==Path.cwd() and release['capsule_root']==str(root),'guarded preclaim root/case differs')
    from tradingagents.research.onchain_replication import resources,job
    guard=Path(args.guard);require(guard==root/'fixture_outer'/identity(args.case)/'preclaim-guard','preclaim guard path differs')
    cmd=command(root,args.release,args.release_sha256,args.case,guard);limits=release['cases'][args.case]['job_resources']
    live=resources.assert_guarded_worker(guard,cmd,required_paths=[root],wall_seconds=limits['wall_seconds'],memory_max_bytes=limits['memory_max_bytes'],memory_high_bytes=limits['memory_high_bytes'],disk_floor_bytes=limits['disk_floor_bytes'])
    require(all(live[k]==v for k,v in limits.items()),'preclaim live policy differs')
    require(resource.getrlimit(resource.RLIMIT_FSIZE)==(MAX,MAX),'actual preclaim file limit differs')
    from refusal_caller import preclaim
    observation=preclaim(root=root,registration=release['registration'],source=release['capsule_commit'],variant=args.case)
    value={'schema_version':1,'identity':identity(args.case),'source':release['capsule_commit'],'command':cmd,'guard_owner':live['owner_identity'],'file_limits':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'observation':observation}
    require(len(json.dumps(value).encode())<=8192,'preclaim observation metadata bound');resources._native_receipt(guard.parent,'preclaim-observed.json',value)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--release',required=True);parser.add_argument('--release-sha256',required=True);parser.add_argument('--case',choices=PRECLAIM,required=True);parser.add_argument('--guard',required=True);worker(parser.parse_args())
