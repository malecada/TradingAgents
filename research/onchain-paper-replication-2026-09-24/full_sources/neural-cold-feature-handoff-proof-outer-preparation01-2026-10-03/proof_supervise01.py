"""One-use root entry point observing the outer controller's actual wait result."""
import argparse,json,os,resource,shutil,signal,subprocess,sys,time
from pathlib import Path
from proof_raw01 import *
from proof_release01 import check_release,module


def run(root,release_path,expected_sha,phase):
    root=Path(root);raw=body(root,release_path,META);require(digest(raw)==expected_sha,'reviewed release hash differs')
    release=parse(raw);ctx=check_release(root,release,phase);identity=IDENTITIES[phase]
    require(Path(__file__).resolve()==root/'proof_tools/proof_supervise01.py','supervisor source origin differs')
    sources=ctx['sources'];resources=module('proof_supervisor_resources',root/'tradingagents/research/onchain_replication/resources.py',sources['tradingagents/research/onchain_replication/resources.py']);storage=module('proof_supervisor_storage',root/'tradingagents/research/onchain_replication/workflow_storage.py',sources['tradingagents/research/onchain_replication/workflow_storage.py'])
    environment=resources._native_owned_env(root);require(environment==ctx['environment'],'supervisor environment differs');os.environ.update(environment)
    resource.setrlimit(resource.RLIMIT_FSIZE,(MAX,MAX));require(resource.getrlimit(resource.RLIMIT_FSIZE)==(MAX,MAX),'supervisor file limit differs')
    watch=storage.StorageWatch(root,ctx['job']['resources']['storage_budget']['limits']);initial=watch.check();require(initial['allocated_bytes']<=128*1024**2 and initial['logical_file_bytes']<=128*1024**2 and shutil.disk_usage(root).free>=10*GIB,'supervisor baseline unavailable')
    directory=root/'proof_supervise'/identity;directory.parent.mkdir(exist_ok=True);directory.mkdir(exist_ok=False)
    process=None;handles=[];handlers={};primary=None;accepted=False;started=time.monotonic()
    def save(name,value):
        require(len((json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode())<=META,'supervisor receipt exceeds8KiB');resources._native_receipt(directory,name,value)
    def retain(error):
        nonlocal primary
        primary=preserve(primary,error)
    def stop(number,frame):raise InterruptedError('proof supervising process interrupted')
    try:
        fd=os.open(directory.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
        for number in (signal.SIGINT,signal.SIGTERM):handlers[number]=signal.signal(number,stop)
        command=[sys.executable,'-B',str(root/'proof_tools/proof_outer01.py'),'--release',release_path,'--release-sha256',expected_sha,'--phase',phase]
        save('claim.json',{'schema_version':1,'phase':phase,'identity':identity,'source':release['source'],'release':ref(root,release_path,kind='metadata'),'owner_pid':os.getpid(),'owner_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'command':command,'file_size_limit':[MAX,MAX],'numerical_claim':False})
        for name in ('controller.stdout','controller.stderr'):handles.append(os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600))
        process=subprocess.Popen(command,cwd=root,env=os.environ.copy(),stdout=handles[0],stderr=handles[1],start_new_session=True)
        save('child.json',{'pid':process.pid,'start_ticks':Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]})
        while process.poll() is None:
            require(time.monotonic()-started<2100,'supervisor finite deadline exceeded');current=watch.check()
            require(current['allocated_bytes']<GIB-16*1024**2 and current['logical_file_bytes']<GIB-16*1024**2 and shutil.disk_usage(root).free>=10*GIB,'supervisor storage headroom breached')
            require(all((directory/n).stat().st_size<MAX for n in ('controller.stdout','controller.stderr')),'controller logs reached hard bound')
            time.sleep(.25)
        require(process.returncode==0,'outer controller actually failed')
        require(not Path('/proc',str(process.pid)).exists(),'outer controller PID remains/reused')
        receipt=metadata(root,OUTER+identity+'/accepted.json');require(receipt['status']=='accepted' and receipt['identity']==identity and receipt['release']['sha256']==expected_sha,'controller acceptance differs')
        require(not any((root/OUTER/identity/n).exists() for n in ('failed.json','late-failure.json')),'controller late failure remains')
        accepted=True
    except BaseException as error:retain(error)
    finally:
        if process is not None:
            try:
                if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            except BaseException as error:retain(error)
            try:
                try:process.wait(timeout=65)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            except BaseException as error:retain(error)
        for fd in handles:
            try:os.close(fd)
            except BaseException as error:retain(error)
        for number,handler in handlers.items():
            try:signal.signal(number,handler)
            except BaseException as error:retain(error)
        try:
            current=watch.check();free=shutil.disk_usage(root).free;require(free>=10*GIB,'supervisor final disk floor breached')
            save('exit.json',{'schema_version':1,'phase':phase,'identity':identity,'source':release['source'],'release':ref(root,release_path,kind='metadata'),'supervisor_pid':os.getpid(),'controller_pid':None if process is None else process.pid,'controller_exit_code':None if process is None else process.returncode,'controller_pid_absent':process is not None and not Path('/proc',str(process.pid)).exists(),'status':'accepted' if primary is None and accepted else 'failed','accepted_receipt':ref(root,OUTER+identity+'/accepted.json',kind='metadata') if accepted else None,'storage':current,'disk_free_bytes':free,'error_type':None if primary is None else type(primary).__name__,'elapsed_seconds':time.monotonic()-started,'own_process_death_claimed':False,'storage_excludes_own_exit_receipt':True,'remaining_metadata_allowance':2*META,'controller_logs':{n:ref(root,str((directory/n).relative_to(root))) for n in ('controller.stdout','controller.stderr') if (directory/n).exists()}})
            watch.check();require(shutil.disk_usage(root).free>=10*GIB,'supervisor disk floor breached after receipt')
        except BaseException as error:retain(error)
        if primary is not None:
            try:save('late-failure.json',{'status':'failed','phase':phase,'identity':identity,'error_type':type(primary).__name__,'automatic_retry':False})
            except BaseException as error:retain(error)
    if primary is not None:raise primary
    return ref(root,'proof_supervise/'+identity+'/exit.json',kind='metadata')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--release-sha256',required=True);p.add_argument('--phase',choices=list(IDENTITIES),required=True);a=p.parse_args()
    run(Path.cwd().resolve(),a.release,a.release_sha256,a.phase)
