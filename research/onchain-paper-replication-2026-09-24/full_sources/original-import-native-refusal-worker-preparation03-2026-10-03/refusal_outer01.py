"""Prospective one-use genuine job controller. Root release is mandatory."""
import argparse,hashlib,importlib.util,json,os,re,resource,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
from raw_receipts01 import authenticate_post_tail as authenticate_native_post_tail,body,metadata,require
import refusal_inventory03 as inventory_tools
from refusal_native01 import authenticate
from refusal_cases import NAMES,PRECLAIM,identity as case_identity
from types import SimpleNamespace
GIB=1024**3;FILE=4*1024**2

def module(name,path,expected):
    require(hashlib.sha256(path.read_bytes()).hexdigest()==expected,'selected helper body differs')
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

def canonical_cleanup(root,expected):
    """Use the exact package module also imported by native receipt writers."""
    name='tradingagents/research/onchain_replication/owned_io.py'
    require(hashlib.sha256(body(root,name)).hexdigest()==expected,'cleanup source differs')
    value=importlib.import_module('tradingagents.research.onchain_replication.owned_io')
    require(Path(value.__file__).resolve()==root/name,'canonical cleanup module origin differs')
    require(hashlib.sha256(body(root,name)).hexdigest()==expected,'cleanup source changed at import')
    return value


def publish_post_tail(root,watch,save):
    """Sample disk before and after the final readback's own publication."""
    observation=watch.check();disk=shutil.disk_usage(root).free
    require(disk>=10*GIB,'post-tail disk floor breached')
    save('post-tail-storage.json',{'observation':observation,'disk_free_bytes':disk,
        'disk_floor_bytes':10*GIB,'excludes_own_file':True,'remaining_final_file_allowance':65536})
    watch.check()
    require(shutil.disk_usage(root).free>=10*GIB,'final disk floor breached after readback publication')


def authenticate_post_tail(root,identity,limits):
    observation=authenticate_native_post_tail(root,identity,limits)
    base='fixture_outer/'+identity;raw=body(root,base+'/authenticated-refusal.json',8192);proof=json.loads(raw)
    terminal=json.loads(body(root,base+'/terminal.json',8192))
    require(terminal['status']=='passed' and terminal['identity']==identity and terminal['proof_sha256']==hashlib.sha256(raw).hexdigest(),'inventory original outer proof/terminal join differs')
    reference=inventory_tools.authenticate(root,Path(root)/base,identity,proof['inventory'])
    return {'native_post_tail':observation,'complete_inventory':reference}


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
    require(release['program_id']=='original-import-refusal-engineering-20261003' and release['family']['mechanism_id']=='original-import-refusal-engineering-v1' and release['family']['attempt_budget']==23 and release['family']['prior_attempts']==0,'separate finite engineering family differs')
    require(case in NAMES and set(release['cases'])==set(NAMES),'finite two-case protocol differs')
    require(Path.cwd()==root and root.resolve()==root and (root/'.git').is_dir() and not (root/'.git').is_symlink(),'genuine owned capsule root required')
    require(not (root/'.git/objects/info/alternates').exists(),'external Git store forbidden')
    require(sys.executable==release['runtime']['executable'] and sys.prefix==release['runtime']['prefix'],'shared interpreter differs')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip()==release['capsule_commit'],'capsule HEAD differs')
    require(Path(__file__).resolve()==root/'fixture_tools/refusal_outer01.py','controller origin outside capsule')
    required={'fixture_tools/'+name for name in ('refusal_inventory03.py','refusal_outer01.py','refusal_preclaim01.py','refusal_native01.py','refusal_oracle_evidence01.py','guarded_formula_oracle05.py','resource_policy05.py','refusal_caller.py','refusal_cases.py','refusal_evidence.py','refusal_stage.py','refusal_pair_identity.py','original_semantics.py')}|{'tradingagents/research/onchain_replication/resource_refusal.py','tradingagents/research/onchain_replication/resource_refusal_cases.py'}
    require(required<=set(release['source_files']),'complete refusal hook/native closure missing')
    source_envelope(root,release)
    require(Path(inventory_tools.__file__).resolve()==root/'fixture_tools/refusal_inventory03.py' and release['inventory_policy']==inventory_tools.POLICY,'selected complete inventory policy/source origin differs')
    raw=body(root,release['registration']);require(hashlib.sha256(raw).hexdigest()==release['registration_sha256'],'registration bytes differ')
    registration=json.loads(raw);entry=release['cases'][case];identity=entry['identity']
    require(identity==case_identity(case) and set(registration['experiments'])=={case_identity(v) for v in NAMES},'exact27 identity denominator differs')
    require(registration['program_id']==release['program_id'] and registration['experiments'][identity]==entry['experiment'] and registration['families'][entry['experiment']['family']]==release['family'],'release/registration contract differs')
    require(not (root/'research_runs'/identity).exists() and not (root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity).exists(),'claim or launch identity already spent')
    for name,info in entry['experiment']['inputs'].items():require(hashlib.sha256(body(root,info['path'])).hexdigest()==info['sha256'],'input changed: '+name)
    expected_sources=dict(release['source_files'])
    if case in ('source','kernel','helper'):
        from mutation_inputs import selected_imported_paths
        paths=selected_imported_paths(release['source_files'],body(root,'tradingagents/research/onchain_replication/imported_mcm_identity.py'))
        selected={'source':'tradingagents/research/onchain_replication/compact_mcm.py','kernel':paths['KERNEL'],'helper':paths['HELPER']}[case];expected_sources[selected]='0'*64
    require(entry['experiment']['source_files']==expected_sources,'registered exact source mutation differs')
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

def stop_native(root,base,supervisor_pid,*,retain_observation=None,cleanup_type=()):
    """Retain each attempted action even when another action fails."""
    evidence={'native_unit_observed':False,'before':None,'stop':None,'after':None,'errors':[]}
    primary=None
    def retain(step,error):
        nonlocal primary
        primary=select(primary,error,cleanup_type)
        try:evidence['errors'].append({'step':step,'type':type(error).__name__,'message':str(error)[:1024]})
        except BaseException as later:primary=select(primary,later,cleanup_type)
    def inspected():
        command=['systemctl','--user','show',unit,'--property=ControlGroup,ActiveState,SubState,Result']
        result=subprocess.run(command,capture_output=True,text=True,timeout=10)
        require(len(result.stdout)<=16384 and len(result.stderr)<=16384,'stop inspection output bound exceeded')
        return {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
            'properties':dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)}
    try:
        if not (root/base/'guard/live.json').exists():
            evidence['pid_absence_verified']=False
        else:
            launch=metadata(root,base+'/launch.json');owner=metadata(root,base+'/owner.json');live=metadata(root,base+'/guard/live.json')
            require(launch['supervisor_pid']==supervisor_pid and live['owner_identity']==owner and all(owner[k]==v for k,v in launch.items()),'refuse stopping unjoined native owner')
            unit=live['unit'];require(re.fullmatch(r'onchain-replication-[0-9a-f]{32}\.service',unit) is not None,'unsafe native unit identity')
            evidence.update(native_unit_observed=True,unit=unit)
            try:evidence['before']=inspected()
            except BaseException as error:retain('before',error)
            try:
                stopped=subprocess.run(['systemctl','--user','stop',unit],capture_output=True,timeout=10)
                require(len(stopped.stdout)<=16384 and len(stopped.stderr)<=16384,'stop command output bound exceeded')
                evidence['stop']={'returncode':stopped.returncode,'stdout':stopped.stdout.decode('utf-8','replace'),'stderr':stopped.stderr.decode('utf-8','replace')}
            except BaseException as error:retain('stop',error)
            try:evidence['after']=inspected()
            except BaseException as error:retain('after',error)
            try:
                before=(evidence['before'] or {}).get('properties',{});after=(evidence['after'] or {}).get('properties',{})
                known=live.get('cgroup')
                if known is None and before.get('ControlGroup'):known='/sys/fs/cgroup'+before['ControlGroup']
                require(known is not None,'original cgroup unobserved; cleanup remains unresolved')
                cg=Path(known);require(cg.is_relative_to('/sys/fs/cgroup') and cg.name==unit,'unsafe cgroup identity')
                evidence.update(cgroup=str(cg),cgroup_absent=not cg.exists(),properties=after)
                require(after.get('ActiveState') in ('inactive','failed') and after.get('SubState') in ('dead','failed') and not cg.exists(),'native unit cleanup unverified')
            except BaseException as error:retain('validation',error)
    except BaseException as error:retain('original_owner',error)
    finally:
        if retain_observation is not None:
            try:retain_observation(evidence)
            except BaseException as error:retain('receipt',error)
    if primary is not None:raise primary
    return evidence


def run(release,case):
    root=Path(release['capsule_root']);entry=check_release(root,release,case);identity=entry['identity'];source=release['capsule_commit']
    resources=module('selected_resources',root/'tradingagents/research/onchain_replication/resources.py',release['source_files']['tradingagents/research/onchain_replication/resources.py'])
    storage=module('selected_storage',root/'tradingagents/research/onchain_replication/workflow_storage.py',release['source_files']['tradingagents/research/onchain_replication/workflow_storage.py'])
    runtime=module('selected_runtime_gate',root/'fixture_tools/runtime_gate01.py',release['source_files']['fixture_tools/runtime_gate01.py'])
    sys.path.insert(0,str(root))
    runtime_observation=runtime.check(root,release['runtime'])
    io=canonical_cleanup(root,release['source_files']['tradingagents/research/onchain_replication/owned_io.py'])
    env=resources._native_owned_env(root);require(env==release['native_environment'],'selected environment differs');os.environ.update(env)
    for key in ('TMPDIR','XDG_CACHE_HOME','TORCH_HOME','MPLCONFIGDIR','HF_HOME','TORCH_EXTENSIONS_DIR'):
        path=Path(env[key]);require(path.is_relative_to(root),'cache outside capsule');path.mkdir(parents=True,exist_ok=True);require(path.resolve()==path,'cache redirected')
    resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE));require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE),'coordinator file limit differs')
    watch=storage.StorageWatch(root,entry['job_resources']['storage_budget']['limits']);initial=watch.check();require(initial['allocated_bytes']<=128*1024**2 and initial['logical_file_bytes']<=128*1024**2,'capsule baseline exceeds reserved headroom')
    require(shutil.disk_usage(root).free>=10*GIB and resources.mem_available()>=6*GIB,'fresh native startup capacity unavailable')
    outer=root/'fixture_outer'/identity;outer.parent.mkdir(exist_ok=True);outer.mkdir(exist_ok=False)
    # Durable one-use namespace; every descriptor close attempted once.
    parent_fd=os.open(outer.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);birth_error=None
    try:os.fsync(parent_fd)
    except BaseException as error:birth_error=error
    finally:io._cleanup((lambda:os.close(parent_fd),),primary=birth_error)
    if birth_error is not None:raise birth_error
    # No identity retry after this point, including pre-claim failures.
    from tradingagents.research.onchain_replication import job
    require(Path(job.__file__).resolve()==root/'tradingagents/research/onchain_replication/job.py','genuine job source origin differs')
    command=job._command(SimpleNamespace(root=root,registration=release['registration'],experiment=identity,source=source),'launch')
    if case in PRECLAIM:
        from refusal_preclaim01 import run_preclaim
        return run_preclaim(root,release,case,outer,resources,watch,io)
    primary=None;process=None;fds=[];cleanup=None;result=None;signal_handlers={};started=time.monotonic();base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity
    def save(name,value):
        require(len((json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode())<=8192,'new refusal metadata exceeds8KiB');resources._native_receipt(outer,name,value)
    def retain(error):
        nonlocal primary
        primary=select(primary,error,io.CleanupFailure)
    def interrupted(number,frame):raise InterruptedError('outer native controller interrupted by signal '+str(number))
    try:
        for number in (signal.SIGINT,signal.SIGTERM):signal_handlers[number]=signal.signal(number,interrupted)
        save('intent.json',{'identity':identity,'case':case,'source_commit':source,'registration_sha256':release['registration_sha256'],'command':command,'caller_pid':os.getpid(),'caller_file_limits':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'native_environment':env,'outer_active_seconds':1840,'closure_seconds':None,'whole_outer_deadline_seconds':None,'deadline_qualification':'Native1800 and active-loop1840 are enforced; cleanup/verification has individual finite checks but no proved whole-outer wall bound','initial_storage':initial,'runtime_observation_sha256':hashlib.sha256(json.dumps(runtime_observation,sort_keys=True).encode()).hexdigest()})
        for name in ('stdout.log','stderr.log'):fds.append(os.open(outer/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600))
        process=subprocess.Popen(command,cwd=root,env=os.environ.copy(),stdout=fds[0],stderr=fds[1],start_new_session=True)
        save('supervisor.json',{'pid':process.pid,'ticks':Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]})
        while process.poll() is None:
            observation=watch.check();require(observation['allocated_bytes']<GIB-8*1024**2 and observation['logical_file_bytes']<GIB-8*1024**2,'outer tail headroom reached')
            require(shutil.disk_usage(root).free>=10*GIB,'outer disk floor breached')
            require(time.monotonic()-started<1840,'outer active deadline reached')
            require(all((outer/n).stat().st_size<FILE for n in ('stdout.log','stderr.log')),'outer log reached limit')
            time.sleep(.25)
        require(process.returncode==1,'supervisor exit differs from exact case')
    except BaseException as error:retain(error)
    finally:
        # Every independent cleanup action attempted; first actual fatal stays selected.
        if process is not None:
            try:
                if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            except BaseException as error:retain(error)
            try:cleanup=stop_native(root,base,process.pid,retain_observation=lambda value:save('stop-attempt.json',value),cleanup_type=io.CleanupFailure)
            except BaseException as error:retain(error)
            try:
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            except BaseException as error:retain(error)
        try:io._cleanup(tuple((lambda fd=fd:os.close(fd)) for fd in fds),primary=primary)
        except BaseException as error:retain(error)
        try:
            if primary is None:
                actual=authenticate(root,case,release)
                result={'status':actual['status'],'identity':actual['identity'],'claim_sha256':actual['claim_sha256'],'oracle':actual['oracle'],'evidence_sha256':hashlib.sha256(json.dumps(actual['refusal'],sort_keys=True).encode()).hexdigest(),'native_memory_peak_bytes':actual['native']['sampled_memory_peak_bytes'],'financial_completion':False}
        except BaseException as error:retain(error)
        try:save('cleanup.json',{'native':cleanup,'supervisor_reaped':process is not None and process.poll() is not None,'pid_absence_verified':result is not None,'unresolved_pid_absence':result is None})
        except BaseException as error:retain(error)
        try:
            def save_inventory(name,value):
                save(name,value);watch.check()
                require(shutil.disk_usage(root).free>=10*GIB,'inventory publication disk floor breached')
            inventory_reference=inventory_tools.publish(root,outer,inventory(root),identity,save_inventory)
            if result is not None:result=result|{'inventory':inventory_reference}
        except BaseException as error:retain(error)
        try:
            save('authenticated-refusal.json',result) if result is not None else None
            save('terminal.json',{'status':'passed' if primary is None else 'failed','identity':identity,'source_commit':source,'case':case,'proof_sha256':None if result is None else hashlib.sha256(body(root,str((outer/'authenticated-refusal.json').relative_to(root)))).hexdigest(),'error_type':None if primary is None else type(primary).__name__,'elapsed_seconds':time.monotonic()-started})
        except BaseException as error:retain(error)
        try:
            publish_post_tail(root,watch,save)
            if primary is None:result=result|{'post_tail':authenticate_post_tail(root,identity,entry['job_resources'])}
        except BaseException as error:
            retain(error)
        for number,handler in signal_handlers.items():
            try:signal.signal(number,handler)
            except BaseException as error:retain(error)
        # This additive marker follows every independently attempted restoration.
        # Preserve an already published terminal verbatim; a late failure wins.
        if primary is not None:
            try:save('post-terminal-failure.json',{'status':'failed','identity':identity,'source_commit':source,'error_type':type(primary).__name__})
            except BaseException as later:retain(later)
    if primary is not None:raise primary
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True);parser.add_argument('--release-sha256',required=True);parser.add_argument('--case',choices=NAMES,required=True);args=parser.parse_args()
    raw=args.release.read_bytes();require(len(raw)<=FILE and hashlib.sha256(raw).hexdigest()==args.release_sha256,'reviewed release body differs');release=json.loads(raw)
    require('self_reference' not in release,'release reference must come from observed CLI bytes');release['self_reference']={'path':str(args.release.resolve().relative_to(Path(release['capsule_root']))),'sha256':args.release_sha256};run(release,args.case)
