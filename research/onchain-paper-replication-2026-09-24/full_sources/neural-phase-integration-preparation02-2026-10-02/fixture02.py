"""Unexecuted synthetic phase/physical integration; launch only after review."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import subprocess

CASES=('success','fatal','publication_refusal','near_cap','entry_cap')
GIB=1024**3
POLICY={'schema_version':1,'max_file_bytes':4*1024**2,'max_json_bytes':256*1024,
        'max_allocated_bytes':160*1024**2,'max_logical_bytes':128*1024**2,
        'max_entries':128,'tail_reserve_bytes':32*1024**2}
SOURCE='e0cb08b6bf763ffec0bb4058d5d1d89bd3977486'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path,value):
    data=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if len(data)>1024**2:raise ValueError('fixture external receipt exceeds1MiB')
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def inventory(roots):
    members={};allocated=logical=entries=0
    for role,root in roots.items():
        for path in [root,*sorted(root.rglob('*'))]:
            info=path.lstat();entries+=1;allocated+=info.st_blocks*512
            if path.is_symlink() or not (path.is_file() or path.is_dir()):raise ValueError('unexpected fixture member')
            if path.is_file():
                if info.st_nlink!=1:raise ValueError('fixture final hardlink')
                logical+=info.st_size;members[role+'/'+str(path.relative_to(root))]={'bytes':info.st_size,'sha256':sha(path)}
    return {'allocated_bytes':allocated,'logical_bytes':logical,'entries':entries,'files':len(members),'members':members}


def standin(path,size=128):
    if not 0<size<=4*1024**2:raise ValueError('finite fixture stand-in size required')
    with path.open('xb') as stream:
        remaining=size
        while remaining:
            n=min(65536,remaining);stream.write(b'X'*n);remaining-=n
        stream.flush();os.fsync(stream.fileno())


def fill_near_cap(scope):
    # Refuse a reserved active publication while preserving complete closure headroom.
    target=POLICY['max_logical_bytes']-POLICY['tail_reserve_bytes']-128*1024
    before=scope.check();remaining=target-before['logical_bytes'];count=0
    while remaining>0:
        size=min(POLICY['max_file_bytes'],remaining)
        standin(scope.roots['producer']/f'near-cap-{count:02d}.bin',size)
        count+=1;remaining-=size
        if count>25:raise ValueError('fixture padding file bound exceeded')
    result=scope.check()
    assert result['logical_bytes']==target and result['entries']<112
    return {'before':before,'after':result,'target_logical_bytes':target,'padding_files':count}


def child_bridge(scope,root,cgroup):
    script=Path(__file__).resolve().with_name('child_scope.py')
    command=[sys.executable,'-B',str(script),str(root),scope.anchor['experiment'],SOURCE,scope.anchor_hash,str(cgroup),sha(script),str(os.getpid())]
    stdout=root/'child.stdout';stderr=root/'child.stderr'
    immutable(root/'child-command.json',{'command':command,'source_sha256':sha(script),'timeout_seconds':10,'inherited_unit':str(cgroup),'kernel_per_stream_file_limit_bytes':4194304,'accepted_readback_bytes_per_stream':8192,'qualification':'raw streams retained under inherited file-size cap; oversized result is failure, never truncated into success'})
    with stdout.open('xb') as out,stderr.open('xb') as err:
        result=subprocess.run(command,stdout=out,stderr=err,timeout=10,check=False)
    for path in (stdout,stderr):
        if path.stat().st_size>8192:raise ValueError('child output exceeds bounded result envelope')
    if result.returncode!=0:raise ValueError('child authority command failed; captured streams retained')
    raw=stdout.read_bytes();value=json.loads(raw)
    receipt=scope.roots['producer']/'child-authority.json';record=json.loads(receipt.read_bytes())
    assert value['status']=='published' and value['receipt_sha256']==sha(receipt)
    assert record['pid']==value['pid'] and record['pid']!=os.getpid() and record['ppid']==os.getpid()
    assert record['original_authority_pid']==os.getpid() and record['cgroup']==str(cgroup)
    assert record['file_size_limit']==[4194304,4194304] and record['claim_sha256']==scope.check()['claim_sha256']
    return {'command':command,'child_pid':value['pid'],'receipt_sha256':sha(receipt),'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'exit_code':result.returncode,'timeout_seconds':10,'same_unit':True,'same_file_limit':True}


def fill_entry_cap(scope):
    before=scope.check();target=POLICY['max_entries']-18
    count=0
    while scope.check()['entries']<target:
        standin(scope.roots['producer']/f'entry-cap-{count:03d}.bin',1);count+=1
        if count>111:raise ValueError('finite entry padding exceeded')
    after=scope.check();assert after['entries']==110
    return {'before':before,'after':after,'target_entries':target,'padding_files':count,'next_publication_reserved_entries':2}


def run_case(root,case,cgroup):
    from tradingagents.research import lifecycle
    from tradingagents.research.onchain_replication import neural_physical as physical
    from tradingagents.research.onchain_replication.neural_phases import PhaseJournal,EVENTS,WEEKS
    if case not in CASES:raise ValueError('unknown case')
    identity='phase-integration-01-'+case
    root.mkdir(exist_ok=False)
    base=root/physical.PREFIX/'runs'/identity;base.mkdir(parents=True)
    (root/'research_runs').mkdir();(root/physical.PREFIX/'sources').mkdir()
    scope=physical.Scope.create(root,identity,SOURCE,POLICY,{'synthetic':True,'case':case,'pid':os.getpid()})
    primary=None;answer=None;closed=False
    try:
        # Open a separate view: every operation uses the real original socket authority.
        client=physical.Scope.open(root,identity,SOURCE,POLICY,original_anchor=scope.anchor_hash)
        with lifecycle.metadata_scope(client):
            life=client.birth('lifecycle');(life/'outputs').mkdir()
            lifecycle._immutable(life/'claim.json',{'experiment_id':identity,'source':SOURCE,'synthetic_engineering_only':True,'financial_claim':False})
            producer=client.birth('producer')
            claim_sha=sha(life/'claim.json')
            client.immutable(producer/'intent.json',{'case':case,'claim_sha256':claim_sha,'synthetic':True})
            bridge=child_bridge(client,root,cgroup) if case=='success' else None
            rows=[];failure=None;last_journal=None;saved_prefix=None;cap=None;scratch=None
            for index,week in enumerate(WEEKS):
                cell='neural_checkpoint-'+week
                row={'id':cell,'status':'unavailable','reason':'earlier synthetic cell failed; no retry'}
                if failure is None:
                    sub=producer/f'cell-{index:02d}';sub.mkdir();physical._sync(producer)
                    bound={'source_commit':SOURCE,'claim_sha256':claim_sha,'cell_id':cell,
                           'plan_sha256':'a'*64,'model_config_sha256':'b'*64,'graph_manifest_sha256':'c'*64}
                    journal=PhaseJournal(client,sub,bound,cgroup);last_journal=journal
                    try:
                        for event in EVENTS:
                            if event=='checkpoint_after':standin(sub/'checkpoint.pt')
                            journal.record(event)
                            if case!='success' and event=='forward_before':
                                saved_prefix=(sub/'phase-journal.json').read_bytes()
                                if case=='fatal':raise SystemExit('controlled fatal after durable forward_before')
                                if case=='publication_refusal':
                                    # A real retained incomplete replacement is never silently removed.
                                    scratch=sub/'.physical-phase-journal.json';standin(scratch,37)
                                    journal.record('forward_after')
                                    raise AssertionError('publication unexpectedly accepted existing scratch')
                                cap=fill_entry_cap(client) if case=='entry_cap' else fill_near_cap(client)
                                journal.record('forward_after')
                                raise AssertionError('active reserved publication unexpectedly accepted near cap')
                        row={'id':cell,'status':'complete','result':{'synthetic_checkpoint_standin':True,'events':len(EVENTS)}}
                    except (SystemExit,FileExistsError,ValueError) as error:
                        expected=(case=='fatal' and type(error) is SystemExit) or (case=='publication_refusal' and type(error) is FileExistsError) or (case in ('near_cap','entry_cap') and type(error) is ValueError and 'budget' in str(error))
                        if not expected:raise
                        failure={'type':type(error).__name__,'message':str(error)}
                        row={'id':cell,'status':'failed','reason':failure}
                        assert (sub/'phase-journal.json').read_bytes()==saved_prefix
                        if case!='fatal':
                            try:journal.record('forward_after')
                            except ValueError as stopped:assert 'no retry' in str(stopped)
                            else:raise AssertionError('poisoned journal retried')
                rows.append(row)
                with client.terminal_tail() if failure else null_context():
                    lifecycle._immutable(producer/(cell+'.json'),row)
            with client.terminal_tail():
                summary={'synthetic':True,'complete':sum(x['status']=='complete' for x in rows),'failed':sum(x['status']=='failed' for x in rows),'unavailable':sum(x['status']=='unavailable' for x in rows),'failure':failure}
                if failure:client.immutable(producer/'failure-ledger.json',rows)
                client.immutable(producer/'result.json',summary)
                client.immutable(life/'outputs/cell-ledger.json',rows)
                client.immutable(life/'outputs/resource-summary.json',summary)
                artifacts={str(p.relative_to(root)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in producer.rglob('*') if p.is_file()}
                client.immutable(life/'outputs/artifact-index.json',artifacts)
                actual={str(p.relative_to(root)) for p in producer.rglob('*') if p.is_file()}
                assert set(artifacts)==actual
                assert set(p.name for p in (life/'outputs').iterdir())=={'cell-ledger.json','resource-summary.json','artifact-index.json'}
                journals=sorted(producer.glob('cell-*/phase-journal.json'))
                if case=='success':
                    assert len(journals)==9 and summary['complete']==9
                    for path in journals:assert [x['event'] for x in json.loads(path.read_bytes())['events']]==list(EVENTS)
                else:
                    assert len(journals)==1 and [x['status'] for x in rows]==['failed']+['unavailable']*8
                    assert not (producer/'cell-01').exists()
                if bridge:assert str((producer/'child-authority.json').relative_to(root)) in artifacts
                if scratch:assert scratch.read_bytes()==b'X'*37 and str(scratch.relative_to(root)) in artifacts
                terminal='complete' if failure is None else 'failed'
                client.immutable(life/(terminal+'.json'),{'status':terminal,'synthetic':True,'claim_sha256':claim_sha,'cells':rows})
                client.immutable(base/'observer.json',{'status':terminal,'synthetic':True,'no_empirical_admission':True})
                final=client.finish();measured=inventory(client.roots)
                assert all(final[k]==measured[k] for k in ('allocated_bytes','logical_bytes','entries','files'))
                assert final['entries']<=128 and final['allocated_bytes']<=POLICY['max_allocated_bytes'] and final['logical_bytes']<=POLICY['max_logical_bytes']
            if case=='fatal':
                # Complete tail first: irrevocable loss of authority cannot publish another tail.
                scope.close_authority();closed=True
                try:last_journal.record('forward_after')
                except RuntimeError as stopped:assert 'authority unavailable' in str(stopped)
                else:raise AssertionError('journal wrote after original parent authority closed')
                assert inventory(client.roots)==measured
            answer={'child_bridge':bridge,'case':case,'status':'expected_behavior_verified','summary':summary,'three_root_final':measured,'scope_final':final,'near_cap':cap,'retained_last_prefix_sha256':None if saved_prefix is None else hashlib.sha256(saved_prefix).hexdigest(),'authority_revocation_checked_after_tail':case=='fatal'}
    except BaseException as error:primary=error
    finally:
        if not closed:
            try:scope.close_authority()
            except BaseException as error:
                if primary is None:primary=error
                elif isinstance(primary,Exception) and not isinstance(primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):error.__cause__=primary;primary=error
                else:primary.add_note('authority closure failure: '+repr(error))
    if primary is not None:
        try:immutable(root/'case-error.json',{'case':case,'type':type(primary).__name__,'message':str(primary)[:2048],'retry':False})
        except BaseException as error:
            primary.add_note('case error receipt failed: '+repr(error))
            if isinstance(primary,Exception) and not isinstance(primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):raise error from primary
        raise primary
    assert not scope._server.thread.is_alive() and scope._server.closed
    answer['parent_authority_thread_closed']=True
    immutable(root/'case-result.json',answer)
    return answer


def null_context():
    from contextlib import nullcontext
    return nullcontext()


def run(spec):
    if spec['status']!='released_single_isolated_synthetic_attempt':raise ValueError('reviewed release required')
    if any(n in sys.modules for n in ('torch','numpy')):raise ValueError('numerical module already imported')
    class NoNumerics:
        def find_spec(self,fullname,path=None,target=None):
            if fullname.split('.')[0] in ('torch','numpy'):raise ImportError('numerical imports prohibited by synthetic fixture')
            return None
    sys.meta_path.insert(0,NoNumerics())
    from tradingagents.research.onchain_replication import resources
    if resource.getrlimit(resource.RLIMIT_FSIZE)!=(4*1024**2,4*1024**2):raise ValueError('kernel finite file limit differs')
    cgroup=resources._own_cgroup()
    results=[]
    for case in CASES:
        result=run_case(Path(spec['attempt_root'])/case,case,cgroup);results.append({'case':case,'status':result['status']})
    if any(n in sys.modules for n in ('torch','numpy')):raise ValueError('numerical imports prohibited')
    origins={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items() if name=='tradingagents' or name.startswith('tradingagents.') if getattr(module,'__file__',None)}
    if any(not Path(path).is_relative_to(Path(spec['isolated_source_root'])) for path in origins.values()):raise ValueError('imported package escaped isolated source')
    immutable(Path(spec['attempt_root'])/'fixture-result.json',{'cases':results,'financial_fits':0,'numerical_imports':False,'import_origins':origins})
    return 0
