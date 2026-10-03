"""One-use proof launcher; exact root-reviewed release required. No numerical imports."""
import argparse,hashlib,importlib,importlib.util,json,os,re,resource,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
from proof_raw01 import *
import proof_raw01 as raw_api
from proof_release01 import check_release,module
FILE=MAX


def select(primary,later,cleanup_type=()):
    if primary is None:return later
    isfatal=lambda e:(not isinstance(e,Exception) or isinstance(e,(MemoryError,RecursionError))) and not isinstance(e,cleanup_type)
    if isfatal(primary):return primary
    if isfatal(later):return later
    if isinstance(later,cleanup_type) and isinstance(primary,Exception):return later
    return primary

def canonical_cleanup(root,expected):
    """Use the exact package module also imported by native receipt writers."""
    name='tradingagents/research/onchain_replication/owned_io.py'
    require(hashlib.sha256(body(root,name)).hexdigest()==expected,'cleanup source differs')
    value=importlib.import_module('tradingagents.research.onchain_replication.owned_io')
    require(Path(value.__file__).resolve()==root/name,'canonical cleanup module origin differs')
    require(hashlib.sha256(body(root,name)).hexdigest()==expected,'cleanup source changed at import')
    return value

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
        require(len(result.stdout)<=1024 and len(result.stderr)<=1024,'stop inspection output bound exceeded')
        return {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
            'properties':dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)}
    try:
        if not (root/base/'guard/live.json').exists():
            evidence['pid_absence_verified']=False
        else:
            launch=metadata(root,base+'/launch.json');owner=metadata(root,base+'/owner.json');live=native_metadata(root,base+'/guard/live.json')
            require(launch['supervisor_pid']==supervisor_pid and live['owner_identity']==owner and all(owner[k]==v for k,v in launch.items()),'refuse stopping unjoined native owner')
            unit=live['unit'];require(re.fullmatch(r'onchain-replication-[0-9a-f]{32}\.service',unit) is not None,'unsafe native unit identity')
            evidence.update(native_unit_observed=True,unit=unit)
            try:evidence['before']=inspected()
            except BaseException as error:retain('before',error)
            try:
                stopped=subprocess.run(['systemctl','--user','stop',unit],capture_output=True,timeout=10)
                require(len(stopped.stdout)<=1024 and len(stopped.stderr)<=1024,'stop command output bound exceeded')
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


def pages(root,directory,prefix,values,save):
    refs=[];page=[];total=0
    def flush():
        if not page:return
        name=prefix+'-'+str(len(refs)).zfill(4)+'.json';save(name,{'schema_version':1,'rows':list(page)});refs.append(ref(root,str((directory/name).relative_to(root)),kind='metadata'));page.clear()
    for value in values:
        require(len(canonical({'schema_version':1,'rows':[value]}))<=6144,'single metadata row too large')
        if len(canonical({'schema_version':1,'rows':page+[value]}))>6144:flush()
        page.append(value);total+=len(canonical(value));require(total<=MAX and len(refs)<768,'bounded metadata page aggregate exceeded')
    flush()
    # An index can also need several compact pages. The root index only records
    # their digest/count, never a full original source map or scientific output.
    if len(canonical(refs))>6144:
        index=[]
        for i in range(0,len(refs),16):
            name=prefix+'-index-'+str(i//16).zfill(3)+'.json';save(name,{'schema_version':1,'pages':refs[i:i+16]});index.append(ref(root,str((directory/name).relative_to(root)),kind='metadata'))
        require(len(canonical(index))<=6144,'metadata index bound exceeded');return {'kind':'paged-index-v1','page_count':len(refs),'row_count':sum(1 for _ in values) if isinstance(values,(list,tuple)) else None,'indexes':index}
    return {'kind':'direct-pages-v1','page_count':len(refs),'pages':refs}


def attempt_disposition(root,phase):
    identity=IDENTITIES[phase];prefix='research_runs/'+identity
    retained=[]
    for filename in ('claim.json','complete.json','failed.json'):
        if (root/prefix/filename).exists():retained.append(ref(root,prefix+'/'+filename))
    states=[r['path'].rsplit('/',1)[-1] for r in retained]
    status='not_claimed_reserved' if 'claim.json' not in states else 'lifecycle_complete_outer_not_accepted' if 'complete.json' in states else 'lifecycle_failed' if 'failed.json' in states else 'claimed_without_terminal'
    return {'phase':phase,'identity':identity,'observed_disposition':status,'original_receipts':retained,'expected_cell':CELLS[phase],'synthetic_lifecycle_receipt':False,'automatic_retry':False}


def run(release,phase,release_reference):
    root=Path(release['root']);ctx=check_release(root,release,phase);identity=IDENTITIES[phase];source=release['source']
    require(Path(__file__).resolve()==root/'proof_tools/proof_outer01.py','outer controller outside frozen capsule')
    sources=ctx['sources'];resources=module('cold_selected_resources',root/'tradingagents/research/onchain_replication/resources.py',sources['tradingagents/research/onchain_replication/resources.py'])
    storage=module('cold_selected_storage',root/'tradingagents/research/onchain_replication/workflow_storage.py',sources['tradingagents/research/onchain_replication/workflow_storage.py'])
    runtime=module('cold_selected_runtime',root/'proof_tools/runtime_gate01.py',sources['proof_tools/runtime_gate01.py'])
    observed_runtime=runtime.check(root,ctx['runtime']);io_api=canonical_cleanup(root,sources['tradingagents/research/onchain_replication/owned_io.py'])
    supervising=metadata(root,'proof_supervise/'+identity+'/claim.json')
    require(supervising['owner_pid']==os.getppid() and supervising['release']==release_reference and supervising['source']==source and supervising['phase']==phase,'genuine one-use supervisor differs')
    require(Path('/proc',str(os.getppid()),'stat').read_text().rsplit(')',1)[1].split()[19]==supervising['owner_start_ticks'],'supervising process identity changed')
    resources.bind_parent_death(supervising['owner_pid'])
    environment=resources._native_owned_env(root);require(environment==ctx['environment'],'selected owned environment differs');os.environ.update(environment)
    # This only narrows the controller/descendant CPU set to the frozen two IDs.
    # Actual kernel/child readback is separately authenticated after execution.
    require(set(release['cpus'])<=os.sched_getaffinity(0),'frozen CPUs unavailable');os.sched_setaffinity(0,set(release['cpus']))
    require(sorted(os.sched_getaffinity(0))==sorted(release['cpus']),'outer CPU affinity readback differs')
    for key in ('TMPDIR','XDG_CACHE_HOME','TORCH_HOME','MPLCONFIGDIR','HF_HOME','TORCH_EXTENSIONS_DIR'):
        path=Path(environment[key]);require(path.is_relative_to(root),'owned cache outside capsule');path.mkdir(parents=True,exist_ok=True);require(path.resolve()==path,'owned cache redirected')
    resource.setrlimit(resource.RLIMIT_FSIZE,(MAX,MAX));require(resource.getrlimit(resource.RLIMIT_FSIZE)==(MAX,MAX),'outer actual file cap differs')
    watch=storage.StorageWatch(root,ctx['job']['resources']['storage_budget']['limits']);initial=watch.check()
    require(initial['allocated_bytes']<=128*1024**2 and initial['logical_file_bytes']<=128*1024**2,'fresh phase whole-tree baseline exceeds bound')
    require(shutil.disk_usage(root).free>=10*GIB and resources.mem_available()>=6*GIB,'native startup resources unavailable')
    outer=root/OUTER/identity;outer.parent.mkdir(exist_ok=True)
    # Exclusive reservation is permanent even if any later preparation fails.
    outer.mkdir(exist_ok=False);parentfd=os.open(outer.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    primary=None;process=None;fds=[];handlers={};started=time.monotonic();cleanup=None;result=None;accepted=False
    def save(name,value):
        require(len((json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode())<=META,'new outer compact receipt exceeds8KiB')
        resources._native_receipt(outer,name,value)
        require((outer/name).stat().st_size<=META,'actual compact receipt exceeds8KiB')
    def retain(error):
        nonlocal primary
        primary=select(primary,error,io_api.CleanupFailure)
    def interrupted(number,frame):raise InterruptedError('proof outer interrupted by signal '+str(number))
    try:
        os.fsync(parentfd)
    except BaseException as error:retain(error)
    try:os.close(parentfd)
    except BaseException as error:retain(error)
    try:
        if primary is not None:raise primary
        for number in (signal.SIGINT,signal.SIGTERM):handlers[number]=signal.signal(number,interrupted)
        origins=observed_runtime.pop('module_origins');runtime_pages=pages(root,outer,'runtime-origins',[{'module':k,'origin':v} for k,v in sorted(origins.items())],save)
        save('runtime.json',{'observed':observed_runtime,'module_origins':runtime_pages,'expected':release['runtime']})
        save('intent.json',{'schema_version':1,'phase':phase,'identity':identity,'source':source,'release':release_reference,'registration':release['registration'],'source_count':ctx['source_count'],'sources':release['sources'],'launch_command':ctx['launch_command'],'worker_command':ctx['worker_command'],'file_limits':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'cpus':sorted(os.sched_getaffinity(0)),'caller_pid':os.getpid(),'outer_active_seconds':1840,'closure_seconds':60,'initial_storage':initial})
        for name in ('stdout.log','stderr.log'):fds.append(os.open(outer/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600))
        # Obtained from genuine frozen job._command in check_release.
        process=subprocess.Popen(ctx['launch_command'],cwd=root,env=os.environ.copy(),stdout=fds[0],stderr=fds[1],start_new_session=True)
        ticks=Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19];save('supervisor.json',{'pid':process.pid,'ticks':ticks})
        while process.poll() is None:
            current=watch.check();require(current['allocated_bytes']<GIB-16*1024**2 and current['logical_file_bytes']<GIB-16*1024**2,'outer tail headroom exhausted')
            require(shutil.disk_usage(root).free>=10*GIB and time.monotonic()-started<1840,'outer disk or active deadline breached')
            require(all((outer/name).stat().st_size<MAX for name in ('stdout.log','stderr.log')),'outer child log cap reached')
            time.sleep(.25)
        require(process.returncode==0,'genuine phase supervisor did not exit0')
    except BaseException as error:retain(error)
    finally:
        closed_at=time.monotonic()
        if process is not None:
            try:
                if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
            except BaseException as error:retain(error)
            try:cleanup=stop_native(root,PREFIX+identity,process.pid,retain_observation=lambda v:save('stop-attempt.json',v),cleanup_type=io_api.CleanupFailure)
            except BaseException as error:retain(error)
            try:
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            except BaseException as error:retain(error)
        # Independent close, evidence, inventory and signal cleanup attempts.
        try:io_api._cleanup(tuple((lambda fd=fd:os.close(fd)) for fd in fds),primary=primary)
        except BaseException as error:retain(error)
        try:
            if primary is None:
                raw_api.DEADLINE=closed_at+55
                try:
                    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip()==source,'source freeze changed during execution')
                    for name,sha in sources.items():require(digest(body(root,name))==sha,'source changed during execution '+name)
                    for name,info in ctx['experiment']['inputs'].items():require(digest(body(root,info['path']))==info['sha256'],'input changed during execution '+name)
                    runtime.check(root,ctx['runtime'])
                    result=authenticate(root,phase,ctx)
                finally:raw_api.DEADLINE=None
                save('authenticated.json',result)
        except BaseException as error:retain(error)
        try:save('cleanup.json',{'native':cleanup,'supervisor_reaped':process is not None and process.poll() is not None,'pid_absence_verified':result is not None,'unresolved_pid_absence':result is None})
        except BaseException as error:retain(error)
        try:save('disposition.json',attempt_disposition(root,phase))
        except BaseException as error:retain(error)
        try:
            index=inventory(root,limit_seconds=20);index['tail_exclusion']='Controller-time byte index; its pages, later outer receipts and still-running supervisor logs/exit receipt are not recursively self-hashed. The supervisor seals final controller logs after actual wait; final storage watches include existing tails. External recovery requires a later complete byte inventory.';members=index.pop('members');refs=pages(root,outer,'inventory',members,save);save('inventory.json',index|{'members':refs})
        except BaseException as error:retain(error)
        for number,handler in handlers.items():
            try:signal.signal(number,handler)
            except BaseException as error:retain(error)
        try:
            require(time.monotonic()-closed_at<=60,'bounded closure deadline exceeded')
            current=watch.check();free=shutil.disk_usage(root).free;require(free>=10*GIB,'final disk floor breached')
            save('post-tail.json',{'schema_version':1,'storage':current,'disk_free_bytes':free,'disk_floor_bytes':10*GIB,'excludes_own_file':True,'remaining_receipt_allowance':2*META})
            if primary is None:
                tail=closure(root,phase,ctx['job']['resources']['storage_budget']['limits'])
                save('accepted.json',{'schema_version':1,'status':'accepted','phase':phase,'identity':identity,'source':source,'release':release_reference,'authentication':ref(root,OUTER+identity+'/authenticated.json',kind='metadata'),'tail':tail,'elapsed_seconds':time.monotonic()-started,'requires_outer_exit0':True});accepted=True
            else:save('failed.json',{'schema_version':1,'status':'failed','phase':phase,'identity':identity,'error_type':type(primary).__name__,'automatic_retry':False,'original_disposition':ref(root,OUTER+identity+'/disposition.json',kind='metadata') if (outer/'disposition.json').exists() else None})
            watch.check();require(shutil.disk_usage(root).free>=10*GIB,'disk floor breached after final receipt')
        except BaseException as error:retain(error)
        if primary is not None:
            try:save('late-failure.json',{'schema_version':1,'status':'failed','phase':phase,'identity':identity,'error_type':type(primary).__name__,'earlier_acceptance_revoked':accepted,'automatic_retry':False})
            except BaseException as error:retain(error)
    if primary is not None:raise primary
    return {'status':'accepted','phase':phase,'identity':identity,'receipt':ref(root,OUTER+identity+'/accepted.json',kind='metadata')}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--release',required=True);parser.add_argument('--release-sha256',required=True);parser.add_argument('--phase',choices=list(IDENTITIES),required=True);args=parser.parse_args()
    root=Path.cwd().resolve();raw=body(root,args.release,META);require(digest(raw)==args.release_sha256,'root-reviewed exact release hash differs')
    run(parse(raw),args.phase,ref(root,args.release,kind='metadata'))
