"""Bounded actual-source extraction with synthetic loaders/ordinary FDs only."""
import ast,builtins,copy,hashlib,importlib.util,json,os,resource,signal,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'matching-compiled-normalization-connected02-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(30)
assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];observations=[]
def ok(name,value=True):assert value,name;checks.append(name)
original_import=builtins.__import__
def safe_import(name,*a,**kw):
    assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes'},name
    return original_import(name,*a,**kw)
builtins.__import__=safe_import
spec=importlib.util.spec_from_file_location('synthetic_policy',HERE/'compiled_normalization_policy.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
policy=dict(format=p.FORMAT,library_path='/synthetic/library',library_sha256=p.LIBRARY_SHA256,source_path='/synthetic/source',source_sha256=p.SOURCE_SHA256,runtime_path='/synthetic/runtime',runtime_sha256='a'*64,runtime_bytes=32)
fixture=HERE/'ordinary-fixture.txt';fixture.write_text('ordinary descriptor; not a library\n')
def extract(name,cls,namespace,method=None,root=HERE):
    node=next(n for n in ast.parse((root/name).read_text()).body if isinstance(n,ast.ClassDef) and n.name==cls)
    if method:node=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name==method)
    exec(compile(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]),str(root/name),'exec'),namespace)
    return namespace[method or cls]
def noop(*a,**kw):pass
edge=types.SimpleNamespace(attach=noop,current=noop,options=lambda *a:{},join=noop)

def scenario(mode,root=HERE):
    events=[];fds=[];backend=None;armed=False;refs=0;reads=0;opens=0;fail=MemoryError('post-acquisition pin failure');fatal=KeyboardInterrupt('engine fatal');cleanup=OSError('ambiguous close');sessions=[]
    def open_fake(*a):
        nonlocal backend,armed,opens
        opens+=1;events.append('open')
        if mode=='loader_fatal':raise fatal
        fd=os.open(fixture,os.O_RDONLY);fds.append(fd)
        def close():
            events.append('backend_close')
            if mode in ('fatal_cleanup','close_failure'):raise cleanup
            os.close(fd)
        backend=types.SimpleNamespace(lse=lambda *a,**kw:'synthetic',close=close,current=lambda:True)
        armed=True;return backend
    helper=types.SimpleNamespace(open_backend=open_fake)
    def references(owner):
        nonlocal refs
        p.current(owner);refs+=1;events.append('fresh_references')
        if mode=='later_reference' and refs==2:raise fatal
        return policy,helper
    def read(*a,**kw):
        nonlocal reads
        assert kw=={'owned':True};reads+=1;events.append('fresh_library')
    def tuple_seam(values=()):
        if mode=='owner_pin_failure' and armed:raise fail
        return tuple(values)
    ns=dict(attach=p.attach,current=p.current,join=p.join,require=p.require,_backend_references=references,read_reference=read,tuple=tuple_seam)
    Owner=extract('compiled_normalization_policy.py','BackendOwner',ns)
    seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,BackendOwner=Owner,open_backend=lambda obj:None if obj._compiled_normalization_policy is None else open_fake())
    ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
    hard=types.SimpleNamespace(check=noop,create=noop,advance=noop)
    def advance(state,*a,**kw):
        events.append('advance')
        if mode in ('engine_fatal','fatal_cleanup'):raise fatal
        state['phase']='done'
    engine=types.SimpleNamespace(ann=ann,hard=hard,np=ann.np,policy=noop,_check_owned=noop,_advance_owned=advance,matrix_identity=noop,create=lambda *a,**kw:{'phase':'annealing'},score_only=lambda *a,**kw:types.SimpleNamespace(score=.5,iterations=1,convergence='iteration_cap'),close=lambda state:events.append('engine_close'))
    def session_tuple(values=()):
        if mode=='session_pin_failure' and armed:raise fail
        return tuple(values)
    Session=extract('matching_immutable_session.py','ImmutablePairSession',dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType,tuple=session_tuple),root=root)
    def make_session(*a,**kw):
        s=Session(*a,**kw);sessions.append(s);return s
    pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=())
    Executor=extract('batched_pair_executor.py','PairExecutor',dict(copy=copy,adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=pair,engine=engine,annealing=ann,ImmutablePairSession=make_session,CheckpointStop=RuntimeError),root=root)
    executor=Executor({},dict(max_publications=1,max_checkpoint_bytes=100,max_score_buffer_bytes=100,chunk_edges=1),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=3,max_total_checkpoints=1,max_total_checkpoint_bytes=200),noop,compiled_normalization_policy_value=None if mode=='default' else policy)
    error=None
    try:
        for i in range(3):
            if i==1 and mode=='backend_replaced':backend.close=noop
            if i==1 and mode=='owner_replaced':executor._normalization_owner=None
            if i==1 and mode=='policy_replaced':executor._compiled_normalization_policy=tuple(list(executor._compiled_normalization_policy))
            ok('pair result '+mode+str(i),executor('a','b','purpose')==(.5,1,'iteration_cap'))
        if root==HERE:
            ok('backend retained until parent close '+mode,events.count('backend_close')==0)
            # Actual NumericExecution.close -> actual NumericReuse.close -> actual
            # PairExecutor.close -> captured backend close, no invented authority.
            memo=types.SimpleNamespace(active=False,poisoned=False,closed=False,_clear=lambda:events.append('memo_clear'),last_receipt=None,_executor_cleanup=executor.close)
            memo.close=types.MethodType(extract('batched_numeric_reuse.py','NumericReuseExecutor',dict(),method='close'),memo)
            numeric=types.SimpleNamespace(closed=False,memo=memo,finished=True,origins_fd=None,batches_fd=None,fd=None,buffer=bytearray())
            extract('batched_numeric_execution.py','NumericExecution',dict(os=os),method='close')(numeric)
            ok('numeric close reaches memo and executor '+mode,numeric.closed and memo.closed and executor.closed)
            executor.close()
    except BaseException as e:error=e
    survivors=[]
    for fd in fds:
        try:os.fstat(fd);survivors.append(fd)
        except OSError:pass
    if root==OLD:
        ok('RED02 per-computed-pair opens',opens==3 and events.count('backend_close')==3 and error is None)
    elif mode in ('success','default'):
        ok('one open per owner or default zero '+mode,error is None and opens==(0 if mode=='default' else 1) and refs==(0 if mode=='default' else 3) and reads==refs and not survivors)
    elif mode=='close_failure':
        ok('ambiguous close reported without retry',error is cleanup and events.count('backend_close')==1 and len(survivors)==1)
    else:
        expected=fail if mode in ('owner_pin_failure','session_pin_failure') else fatal if mode in ('loader_fatal','engine_fatal','fatal_cleanup','later_reference') else None
        ok('failure retains original identity '+mode,error is expected if expected else isinstance(error,ValueError))
        ok('independent engine cleanup '+mode,events.count('engine_close')>=1)
        ok('poison closes original owner '+mode,executor.poisoned and executor.closed and events.count('backend_close')==(0 if mode=='loader_fatal' else 1))
        ok('no hidden fd closure claim '+mode,len(survivors)==(1 if mode=='fatal_cleanup' else 0))
    observations.append(dict(case=mode,version=root.name,opens=opens,fresh_references=refs,fresh_library_reads=reads,events=events,error=None if error is None else type(error).__name__,residual_fds=len(survivors)))
    for fd in survivors:os.close(fd)
scenario('success',OLD)
for mode in ('success','default','backend_replaced','owner_replaced','policy_replaced','owner_pin_failure','session_pin_failure','loader_fatal','engine_fatal','fatal_cleanup','later_reference','close_failure'):scenario(mode)

# Owner/lease terminal behavior independent of numerical facade.
for mode in ('double_borrow','lease_replaced','parent_closed','owner_method','backend_current','client_policy','ambiguous','fallback'):
    events=[];fd=os.open(fixture,os.O_RDONLY);err=OSError('ambiguous');backend=None
    def close():
        events.append('close')
        if mode=='ambiguous':raise err
        os.close(fd)
    backend=types.SimpleNamespace(close=close,lse=lambda *a,**kw:kw['fallback']() if mode=='fallback' else 1,current=lambda:True)
    Owner=extract('compiled_normalization_policy.py','BackendOwner',dict(attach=p.attach,current=p.current,join=p.join,require=p.require,_backend_references=lambda owner:(policy,types.SimpleNamespace(open_backend=lambda *a:backend)),read_reference=noop))
    owner=Owner(policy);original_close=owner.close;client=types.SimpleNamespace();p.attach(client,policy);lease=owner.borrow(client);release=lease.close
    if mode=='double_borrow':action=lambda:owner.borrow(client)
    elif mode=='lease_replaced':lease.lse=noop;action=lease.current
    elif mode=='parent_closed':original_close();action=lease.current
    elif mode=='owner_method':owner.current=noop;action=lease.current
    elif mode=='backend_current':backend.current=lambda:False;action=lease.current
    elif mode=='client_policy':client._compiled_normalization_policy=();action=lease.current
    elif mode=='fallback':
        ok('clean unsupported fallback retained',lease.lse(None,axis=0,keepdims=True,fallback=lambda:'fallback')=='fallback');release();original_close();continue
    else:action=original_close
    caught=None
    try:action()
    except BaseException as e:caught=e
    ok('lease/owner refuses '+mode,caught is err if mode=='ambiguous' else isinstance(caught,ValueError))
    release()
    for i in range(2):
        try:original_close()
        except BaseException as e:ok('ambiguous same object',mode=='ambiguous' and e is err)
    ok('one retained original close '+mode,events==['close'])
    if mode=='ambiguous':os.close(fd)

# Actual memo cleanup errors must still reach executor cleanup; original primary
# and fatal identities are checked, not string equivalence.
for method in ('close','_poison'):
    events=[];primary=KeyboardInterrupt('cache failure');cleanup=OSError('backend failure')
    def clear():events.append('clear');raise primary
    def cleanup_fn():events.append('backend');raise cleanup
    obj=types.SimpleNamespace(closed=False,active=False,poisoned=False,_geometry=None,_executor_pin=types.SimpleNamespace(poisoned=False),_executor_cleanup=cleanup_fn,_clear=clear,last_receipt=None)
    fn=extract('batched_numeric_reuse.py','NumericReuseExecutor',dict(sys=sys),method=method)
    error=None
    try:fn(obj)
    except BaseException as e:error=e
    ok('memo independent primary cleanup '+method,error is primary and events==['clear','backend'] and bool(getattr(error,'__notes__',[])))

# Bounded real regular-file reference checks, no native loading.
body=fixture.read_bytes();digest=hashlib.sha256(body).hexdigest()
ok('owned regular reference read',p.read_reference(fixture,digest,1024,owned=True)==body)
try:p.read_reference(fixture,'0'*64,1024,owned=True)
except ValueError:ok('fresh wrong library digest refuses')
else:raise AssertionError('digest accepted')

def apply(text,patch):
    if not patch:return text
    lines=text.splitlines(True);out=[];cursor=0;body=patch.splitlines(True);i=2
    while i<len(body):
        header=body[i];assert header.startswith('@@ ');i+=1;pos=int(header.split()[1][1:].split(',')[0])-1;out.extend(lines[cursor:pos]);cursor=pos
        while i<len(body) and not body[i].startswith('@@ '):
            line=body[i];i+=1
            if line[0] in ' -':assert lines[cursor]==line[1:];cursor+=1
            if line[0] in ' +':out.append(line[1:])
    out.extend(lines[cursor:]);return ''.join(out)
for path in HERE.glob('*.to02.inverse.patch'):
    name=path.name[:-len('.to02.inverse.patch')];s=(HERE/name).read_text();ast.parse(s)
    ok('exact inverse02 '+name,apply(s,path.read_text())==(OLD/name).read_text())
for name in ('matching_annealing.py','matching_checkpoint.py','batched_numeric_execution.py'):
    ok('unchanged numerical/source body '+name,(HERE/name).read_bytes()==(OLD/name).read_bytes())
for name in ('compiled_normalization_policy.py','batched_pair_executor.py','matching_immutable_session.py'):
    ok('dependent exact source pin '+name,hashlib.sha256((HERE/name).read_bytes()).hexdigest() in (HERE/'batched_numeric_reuse.py').read_text())
ok('helper exact source pin',p.HELPER_SHA256==hashlib.sha256((HERE/'compiled_small_lse.py').read_bytes()).hexdigest())
# Loader and numerical code are unchanged inside the helper's sole factory,
# except the new read-only current() and namespace publication field.
a=(HERE/'compiled_small_lse.py').read_text();b=(OLD/'compiled_small_lse.py').read_text()
a=a[:a.index('    def current():')]+a[a.index('    try:return SimpleNamespace(lse=lse,close=close,current=current)'):]
ok('helper unchanged outside current capability',a.replace('SimpleNamespace(lse=lse,close=close,current=current)','SimpleNamespace(lse=lse,close=close)')==b)
# Compose successor inverse with accepted02 installed-baseline inverse.
for path in OLD.glob('baseline_*.py'):
    name=path.name[len('baseline_'):]
    restored=apply((HERE/name).read_text(),(HERE/(name+'.to02.inverse.patch')).read_text())
    ok('exact installed inverse composition '+name,apply(restored,(OLD/(name+'.inverse.patch')).read_text())==path.read_text())
# Exact AST preservation outside enumerated ownership/currentness scopes.
for name,cls,changed in (
    ('matching_immutable_session.py','ImmutablePairSession',{'__init__','current','advance'}),
    ('batched_numeric_reuse.py','NumericReuseExecutor',{'__init__','_current','_poison','close'})):
    before=(OLD/name).read_text();after=(HERE/name).read_text()
    if name=='batched_numeric_reuse.py':
        for pinned in ('compiled_normalization_policy.py','batched_pair_executor.py','matching_immutable_session.py'):
            after=after.replace(hashlib.sha256((HERE/pinned).read_bytes()).hexdigest(),hashlib.sha256((OLD/pinned).read_bytes()).hexdigest())
    trees=[ast.parse(before),ast.parse(after)]
    for tree in trees:
        c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
        c.body=[n for n in c.body if getattr(n,'name',None) not in changed]
    ok('unchanged outside declared ownership scopes '+name,ast.dump(trees[0])==ast.dump(trees[1]))
result=dict(status='PASS_FOCUSED_STDLIB_OWNERSHIP',checks=checks,count=len(checks),observations=observations,elapsed_ns=time.perf_counter_ns()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,affinity=sorted(os.sched_getaffinity(0)),native_or_numerical_execution=False,actual_authority=False)
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','count','elapsed_ns','peak_rss_kib')}))
