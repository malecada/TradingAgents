"""Prospective one-use genuine job controller. Root release is mandatory."""
import argparse,hashlib,importlib.util,json,os,re,resource,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
from raw_receipts01 import authenticate,body,metadata,require
GIB=1024**3;FILE=4*1024**2

def module(name,path,expected):
    require(hashlib.sha256(path.read_bytes()).hexdigest()==expected,'selected helper body differs')
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

def select(primary,later,cleanup_type=()):
    if primary is None:return later
    fatal=lambda error:(not isinstance(error,Exception) or isinstance(error,MemoryError)) and not isinstance(error,cleanup_type)
    if fatal(primary):return primary
    if fatal(later):return later
    if isinstance(later,cleanup_type) and isinstance(primary,Exception):return later
    return primary

def source_envelope(root,release):
    required={'fixture_tools/outer_controller01.py','fixture_tools/raw_receipts01.py','fixture_tools/runtime_gate01.py','tradingagents/research/onchain_replication/job.py','tradingagents/research/onchain_replication/resources.py','tradingagents/research/onchain_replication/owned_io.py','tradingagents/research/onchain_replication/workflow_storage.py'}
    require(required<=set(release['source_files']),'selected controller/helper source closure missing')
    for name,sha in release['source_files'].items():
        raw=body(root,name);require(hashlib.sha256(raw).hexdigest()==sha,'source body differs: '+name)
        committed=subprocess.check_output(['git','show',release['capsule_commit']+':'+name],cwd=root,timeout=10)
        require(committed==raw,'selected source is not in capsule HEAD: '+name)

def check_release(root,release,case):
    require(release['status']=='released-native-engineering' and release['remaining']==[],'source preparation is not released')
    require(release['program_id']=='original-dictionary-import-engineering-2026-10-02' and release['family']['mechanism_id']=='original-dictionary-import-engineering-v1' and release['family']['attempt_budget']==2 and release['family']['prior_attempts']==0,'separate finite engineering family differs')
    require(case in ('success','second_target_publication_failure') and set(release['cases'])=={'success','second_target_publication_failure'},'finite two-case protocol differs')
    require(Path.cwd()==root and root.resolve()==root and (root/'.git').is_dir() and not (root/'.git').is_symlink(),'genuine owned capsule root required')
    require(not (root/'.git/objects/info/alternates').exists(),'external Git store forbidden')
    require(sys.executable==release['runtime']['executable'] and sys.prefix==release['runtime']['prefix'],'shared interpreter differs')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip()==release['capsule_commit'],'capsule HEAD differs')
    require(Path(__file__).resolve()==root/'fixture_tools/outer_controller01.py','controller origin outside capsule')
    source_envelope(root,release)
    raw=body(root,release['registration']);require(hashlib.sha256(raw).hexdigest()==release['registration_sha256'],'registration bytes differ')
    registration=json.loads(raw);entry=release['cases'][case];identity=entry['identity']
    require(registration['program_id']==release['program_id'] and registration['experiments'][identity]==entry['experiment'] and registration['families'][entry['experiment']['family']]==release['family'],'release/registration contract differs')
    require(not (root/'research_runs'/identity).exists() and not (root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity).exists(),'claim or launch identity already spent')
    for name,info in entry['experiment']['inputs'].items():require(hashlib.sha256(body(root,info['path'])).hexdigest()==info['sha256'],'input changed: '+name)
    require(entry['job_resources']==json.loads(body(root,entry['experiment']['inputs']['execution_job']['path']))['resources'],'resource registration differs')
    p=entry['job_resources'];require(p['memory_max_bytes']==p['memory_high_bytes']==3*GIB and p['reserve_bytes']==3*GIB and p['start_reserve_bytes']==6*GIB and p['wall_seconds']==1800 and p['disk_floor_bytes']==10*GIB and p['disk_paths']==[str(root)] and p['native_unit_limits']=={'file_size_bytes':FILE},'native limits differ')
    require(p['storage_budget']=={'root':str(root),'limits':{'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}},'whole capsule storage policy differs')
    require(not any(name in sys.modules for name in ('numpy','torch')),'numerical import outside native guard')
    return entry

def inventory(root,limit_seconds=30):
    """Post-stop finite recursive body index; self/tail excluded explicitly."""
    started=time.monotonic();rows=[];total=0
    for path in root.rglob('*'):
        require(len(rows)<32768 and time.monotonic()-started<limit_seconds,'final inventory finite bound exceeded')
        relative=str(path.relative_to(root));require(len(relative)<=2048,'inventory path extent exceeds bound');info=path.lstat();require(path.resolve()==path and info.st_dev==root.stat().st_dev,'inventory path/device differs')
        row={'path':relative,'bytes':info.st_size,'allocated':info.st_blocks*512}
        if stat.S_ISREG(info.st_mode):
            require(info.st_nlink==1 and info.st_size<=FILE,'inventory file/link limit')
            row['kind']='file';row['sha256']=hashlib.sha256(body(root,relative)).hexdigest();total+=info.st_size
        else:require(stat.S_ISDIR(info.st_mode),'inventory special member');row['kind']='directory'
        rows.append(row);require(total<=GIB,'final logical stop exceeded')
    require(sum(x['allocated'] for x in rows)+root.stat().st_blocks*512<=GIB,'final allocated stop exceeded')
    rows.sort(key=lambda x:x['path'])
    return {'schema_version':1,'root':str(root),'members':rows,'root_allocated':root.stat().st_blocks*512,'tail_exclusion':'This index and subsequently written outer terminal/readback are hashed and fully counted by final post-tail storage observation; no recursive self-hash claim.'}

def stop_native(root,base,supervisor_pid):
    if not (root/base/'guard/live.json').exists():return {'native_unit_observed':False}
    launch=metadata(root,base+'/launch.json');owner=metadata(root,base+'/owner.json');live=metadata(root,base+'/guard/live.json')
    require(launch['supervisor_pid']==supervisor_pid and live['owner_identity']==owner and all(owner[k]==v for k,v in launch.items()),'refuse stopping unjoined native owner')
    unit=live['unit'];require(re.fullmatch(r'onchain-replication-[0-9a-f]{32}\.service',unit) is not None,'unsafe native unit identity')
    primary=None;before={};after={};stopped=None
    def inspect():
        result=subprocess.run(['systemctl','--user','show',unit,'--property=ControlGroup,ActiveState,SubState,Result'],capture_output=True,text=True,timeout=10)
        return dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    try:before=inspect()
    except BaseException as error:primary=select(primary,error)
    try:stopped=subprocess.run(['systemctl','--user','stop',unit],capture_output=True,timeout=10)
    except BaseException as error:primary=select(primary,error)
    try:after=inspect()
    except BaseException as error:primary=select(primary,error)
    if primary is not None:raise primary
    known=live.get('cgroup')
    if known is None and before.get('ControlGroup'):known='/sys/fs/cgroup'+before['ControlGroup']
    require(known is not None,'native stop attempted but original cgroup unobserved; cannot certify cleanup')
    cg=Path(known);require(cg.is_relative_to('/sys/fs/cgroup') and cg.name==unit,'unsafe cgroup identity')
    require(after.get('ActiveState') in ('inactive','failed') and after.get('SubState') in ('dead','failed') and not cg.exists(),'native unit cleanup unverified')
    return {'native_unit_observed':True,'unit':unit,'cgroup':str(cg),'stop_returncode':stopped.returncode,'properties':after,'cgroup_absent':True}


def run(release,case):
    root=Path(release['capsule_root']);entry=check_release(root,release,case);identity=entry['identity'];source=release['capsule_commit']
    resources=module('selected_resources',root/'tradingagents/research/onchain_replication/resources.py',release['source_files']['tradingagents/research/onchain_replication/resources.py'])
    storage=module('selected_storage',root/'tradingagents/research/onchain_replication/workflow_storage.py',release['source_files']['tradingagents/research/onchain_replication/workflow_storage.py'])
    io=module('selected_owned_io',root/'tradingagents/research/onchain_replication/owned_io.py',release['source_files']['tradingagents/research/onchain_replication/owned_io.py'])
    runtime=module('selected_runtime_gate',root/'fixture_tools/runtime_gate01.py',release['source_files']['fixture_tools/runtime_gate01.py'])
    sys.path.insert(0,str(root))
    runtime_observation=runtime.check(root,release['runtime'])
    env=resources._native_owned_env(root);require(env==release['native_environment'],'selected environment differs');os.environ.update(env)
    for key in ('TMPDIR','XDG_CACHE_HOME','TORCH_HOME','MPLCONFIGDIR','HF_HOME','TORCH_EXTENSIONS_DIR'):
        path=Path(env[key]);require(path.is_relative_to(root),'cache outside capsule');path.mkdir(parents=True,exist_ok=True);require(path.resolve()==path,'cache redirected')
    resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE));require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE),'coordinator file limit differs')
    watch=storage.StorageWatch(root,entry['job_resources']['storage_budget']['limits']);initial=watch.check();require(initial['allocated_bytes']<=128*1024**2 and initial['logical_file_bytes']<=128*1024**2,'capsule baseline exceeds reserved headroom')
    require(shutil.disk_usage(root).free>=10*GIB and resources.mem_available()>=6*GIB,'fresh native startup capacity unavailable')
    outer=root/'fixture_outer'/identity;outer.parent.mkdir(exist_ok=True);outer.mkdir(exist_ok=False)
    # No identity retry after this point, including pre-claim failures.
    command=[sys.executable,'-B','-m','tradingagents.research.onchain_replication.job','--mode','launch','--root',str(root),'--registration',release['registration'],'--experiment',identity,'--source',source]
    primary=None;process=None;fds=[];cleanup=None;result=None;signal_handlers={};started=time.monotonic();base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity
    def save(name,value):resources._native_receipt(outer,name,value)
    def retain(error):
        nonlocal primary
        primary=select(primary,error,io.CleanupFailure)
    def interrupted(number,frame):raise InterruptedError('outer native controller interrupted by signal '+str(number))
    try:
        for number in (signal.SIGINT,signal.SIGTERM):signal_handlers[number]=signal.signal(number,interrupted)
        save('intent.json',{'identity':identity,'case':case,'source_commit':source,'registration_sha256':release['registration_sha256'],'command':command,'caller_pid':os.getpid(),'caller_file_limits':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'native_environment':env,'outer_active_seconds':1840,'closure_seconds':60,'initial_storage':initial,'runtime_observation':runtime_observation})
        for name in ('stdout.log','stderr.log'):fds.append(os.open(outer/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600))
        process=subprocess.Popen(command,cwd=root,env=os.environ.copy(),stdout=fds[0],stderr=fds[1],start_new_session=True)
        save('supervisor.json',{'pid':process.pid,'ticks':Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]})
        while process.poll() is None:
            observation=watch.check();require(observation['allocated_bytes']<GIB-8*1024**2 and observation['logical_file_bytes']<GIB-8*1024**2,'outer tail headroom reached')
            require(shutil.disk_usage(root).free>=10*GIB,'outer disk floor breached')
            require(time.monotonic()-started<1840,'outer active deadline reached')
            require(all((outer/n).stat().st_size<FILE for n in ('stdout.log','stderr.log')),'outer log reached limit')
            time.sleep(.25)
        require(process.returncode==(0 if case=='success' else 1),'supervisor exit differs from exact case')
    except BaseException as error:retain(error)
    finally:
        # Every independent cleanup action attempted; first actual fatal stays selected.
        if process is not None:
            try:
                if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            except BaseException as error:retain(error)
            try:cleanup=stop_native(root,base,process.pid)
            except BaseException as error:retain(error)
            try:
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            except BaseException as error:retain(error)
        try:io._cleanup(tuple((lambda fd=fd:os.close(fd)) for fd in fds),primary=primary)
        except BaseException as error:retain(error)
        try:
            if primary is None:result=authenticate(root,case,release)
        except BaseException as error:retain(error)
        try:save('cleanup.json',{'native':cleanup,'supervisor_reaped':process is not None and process.poll() is not None})
        except BaseException as error:retain(error)
        try:
            index=inventory(root);pages=[];page=[];extent=0;total=0
            for row in index.pop('members'):
                size=len(json.dumps(row,separators=(',',':'),sort_keys=True).encode())+1
                if extent+size>48000 and page:pages.append(page);page=[];extent=0
                page.append(row);extent+=size;total+=size;require(total<=4*1024**2,'final inventory aggregate extent exceeded')
            if page:pages.append(page)
            require(len(pages)<=128,'inventory page bound exceeded')
            references=[]
            for i,page in enumerate(pages):
                name='inventory-'+str(i).zfill(3)+'.json';save(name,{'members':page});references.append({'path':name,'sha256':hashlib.sha256(body(root,str((outer/name).relative_to(root)))).hexdigest()})
            save('inventory.json',index|{'pages':references})
        except BaseException as error:retain(error)
        try:save('terminal.json',{'status':'passed' if primary is None else 'failed','identity':identity,'source_commit':source,'case':case,'proof':result,'error_type':None if primary is None else type(primary).__name__,'elapsed_seconds':time.monotonic()-started})
        except BaseException as error:retain(error)
        try:
            observation=watch.check();save('post-tail-storage.json',{'observation':observation,'excludes_own_file':True,'remaining_final_file_allowance':65536})
            # The actual final check includes the readback file; its value cannot
            # recursively contain its own durable length. Retain both semantics.
            watch.check()
        except BaseException as error:
            retain(error)
            try:save('post-terminal-failure.json',{'status':'failed','identity':identity,'source_commit':source,'error_type':type(primary).__name__})
            except BaseException as later:retain(later)
        for number,handler in signal_handlers.items():
            try:signal.signal(number,handler)
            except BaseException as error:retain(error)
    if primary is not None:raise primary
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True);parser.add_argument('--case',choices=['success','second_target_publication_failure'],required=True);args=parser.parse_args()
    run(json.loads(args.release.read_bytes()),args.case)
