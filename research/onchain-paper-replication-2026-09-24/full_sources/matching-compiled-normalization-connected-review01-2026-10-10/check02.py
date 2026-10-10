"""Independent bounded source/metadata review. No candidate numeric imports."""
import ast, builtins, copy, difflib, hashlib, json, os, resource, signal, stat, time, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
CAND=HERE.parent/'matching-compiled-normalization-connected01-2026-10-10'
ROOT=HERE.parents[3]
SRC=ROOT/'tradingagents/research/onchain_replication'
OLD=HERE.parent/'matching-compiled-small-pair-prototype04-2026-10-09'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
signal.alarm(30)
assert os.sched_getaffinity(0)=={3}
started=time.perf_counter_ns(); checks=[]; reds=[]; refs={}
def sha(body): return hashlib.sha256(body).hexdigest()
def ok(name,value=True):
    assert value,name
    checks.append(name)
def record(path):
    b=path.read_bytes();refs[str(path.relative_to(ROOT))]={'sha256':sha(b),'bytes':len(b)};return b
def reject(name,fn):
    try:fn()
    except (ValueError,TypeError,OSError) as e:ok(name);return type(e).__name__
    raise AssertionError(name+' accepted')
original_import=builtins.__import__
def guarded_import(name,*args,**kw):
    if name.split('.')[0] in {'numpy','scipy','torch','ctypes'}:raise AssertionError('prohibited import '+name)
    return original_import(name,*args,**kw)
builtins.__import__=guarded_import
manifest_body=record(CAND/'MANIFEST01.json')
ok('frozen manifest digest',sha(manifest_body)=='ebf102545bb67ba59856b09e43746552311558f3c57c5e53d8f68573c4dba151')
manifest=json.loads(manifest_body)
for name,expected in manifest['artifacts'].items():
    body=record(CAND/name);ok('manifest '+name,sha(body)==expected['sha256'] and len(body)==expected['bytes'])
names=['batched_numeric_execution.py','batched_numeric_reuse.py','batched_pair_executor.py','matching_immutable_session.py','matching_checkpoint.py','matching_annealing.py']
for name in names:
    baseline=record(CAND/('baseline_'+name));installed=record(SRC/name);candidate=(CAND/name).read_bytes()
    ok('current installed baseline '+name,baseline==installed)
    for reverse in (False,True):
        a,b=(candidate,baseline) if reverse else (baseline,candidate)
        fa,fb=(name,'baseline_'+name) if reverse else ('baseline_'+name,name)
        expected=''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile=fa,tofile=fb)).encode()
        ok(('inverse' if reverse else 'forward')+' exact patch '+name,(CAND/(name+('.inverse.patch' if reverse else '.patch'))).read_bytes()==expected)
    ast.parse(candidate)
def tree(name):return ast.parse((CAND/name).read_text())
def fn(name,func,namespace,cls=None):
    body=tree(name).body
    if cls:body=next(n for n in body if isinstance(n,ast.ClassDef) and n.name==cls).body
    node=copy.deepcopy(next(n for n in body if isinstance(n,ast.FunctionDef) and n.name==func))
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(CAND/name),'exec'),namespace)
    return namespace[func]
p=types.ModuleType('review_policy');p.__file__=str(CAND/'compiled_normalization_policy.py')
exec(compile((CAND/'compiled_normalization_policy.py').read_text(),p.__file__,'exec'),p.__dict__)
policy=dict(format=p.FORMAT,library_path='/review/reduction.so',library_sha256=p.LIBRARY_SHA256,source_path='/review/reduction.c',source_sha256=p.SOURCE_SHA256,runtime_path='/review/runtime.json',runtime_sha256='e'*64,runtime_bytes=400)
owner=types.SimpleNamespace();p.attach(owner,policy)
ok('policy copies caller metadata',dict(owner._compiled_normalization_policy)==policy)
policy['runtime_bytes']=401
ok('caller mutation does not change selection',dict(owner._compiled_normalization_policy)['runtime_bytes']==400)
policy=dict(owner._compiled_normalization_policy)
for key,value in [('format','other'),('library_sha256','0'*64),('source_sha256','0'*64),('runtime_sha256','E'*64),('runtime_bytes',True),('runtime_bytes',0),('runtime_bytes',4097),('library_path','relative'),('source_path','/a/../x'),('runtime_path','/x//y'),('runtime_path','/x\x00')]:
    reject('policy refuses '+key+'='+repr(value),lambda k=key,v=value:p.freeze(dict(policy,**{k:v})))
reject('policy refuses extra fields',lambda:p.freeze(dict(policy,extra=1)))
for value in (None,False):
    blank=types.SimpleNamespace();p.attach(blank,value)
    old_read=p.read_reference
    p.read_reference=lambda *a,**k:(_ for _ in ()).throw(AssertionError('default attempted IO'))
    try:ok('unselected no read/load '+repr(value),p.open_backend(blank) is None and p.options(blank)=={})
    finally:p.read_reference=old_read
child=types.SimpleNamespace();p.attach(child,dict(policy,runtime_bytes=402))
reject('chain policy divergence refused',lambda:p.join(owner,child))
owner._compiled_normalization_policy=tuple(list(owner._compiled_normalization_policy))
reject('equal but replaced identity refused',lambda:p.current(owner))
runtime=dict(format='compiled-small-lse-runtime-reference-v1',python='3.13.13',numpy='2.3.0',scipy='1.17.1',platform='linux',machine='x86_64',byteorder='little',executable='/synthetic/python',runtime_inventory_sha256='f'*64)
for key,value in [('python','3.13.12'),('numpy','2.3.1'),('scipy','1.17.0'),('platform','other'),('machine','other'),('byteorder','big'),('executable','relative'),('runtime_inventory_sha256','f'*63)]:
    reject('runtime refuses '+key,lambda k=key,v=value:p.runtime_metadata(json.dumps(dict(runtime,**{k:v}))))
fixture=HERE/'reference-body.bin';fixture.write_bytes(b'metadata only\n');body=fixture.read_bytes()
ok('bounded reference original',p.read_reference(str(fixture),sha(body),32,len(body))==body)
reject('reference size mismatch',lambda:p.read_reference(str(fixture),sha(body),32,len(body)+1))
reject('reference digest mismatch',lambda:p.read_reference(str(fixture),'0'*64,32))
reject('reference oversize',lambda:p.read_reference(str(fixture),sha(body),3))
link=HERE/'reference-symlink';link.symlink_to(fixture.name)
reject('symlink reference refused',lambda:p.read_reference(str(link),sha(body),32))
hardlink=HERE/'reference-hardlink';os.link(fixture,hardlink)
reject('hardlinked reference refused',lambda:p.read_reference(str(fixture),sha(body),32))
# Verify preserved helper source functions without importing or loading it.
old_tree=ast.parse(record(OLD/'compiled_small_lse.py'))
new_factory=next(n for n in tree('compiled_small_lse.py').body if isinstance(n,ast.FunctionDef) and n.name=='open_backend')
for name in ('_new_memfd','_load_sealed','_live','lse','close'):
    a=copy.deepcopy(next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name==name))
    b=copy.deepcopy(next(n for n in new_factory.body if isinstance(n,ast.FunctionDef) and n.name==name))
    if name=='close':
        for i,n in enumerate(b.body):
            if isinstance(n,ast.Nonlocal):b.body[i]=ast.Global(names=n.names)
    ok('unchanged compiled04 body '+name,ast.dump(a)==ast.dump(b))
for name,digest in [('reduction.c',p.SOURCE_SHA256),('reduction.so',p.LIBRARY_SHA256)]:ok('fixed prior body '+name,sha(record(OLD/name))==digest)
review=HERE.parent/'matching-acceleration-candidates-combined-review02-2026-10-09/SOURCE_EVIDENCE_REVIEW01.json'
ok('accepted prior review exact',sha(record(review)).startswith('6a812b81'))
# Existing checkpoint/ranking/public API bodies remain unchanged. Only private forwarding advances differ.
for name,changed in [('matching_checkpoint.py','_advance_owned'),('matching_annealing.py','_advance_checked')]:
    def unchanged(t):return [ast.dump(n) for n in t.body if not isinstance(n,ast.FunctionDef) or n.name!=changed]
    ok('unchanged public/state/ranking AST '+name,unchanged(tree(name))==unchanged(tree('baseline_'+name)))
# Actual changed composite forwarding including hardening transition and safety poisoning.
for failure in (False,True):
    events=[]
    def anneal(state,*a,**k):
        events.append(k)
        if failure:raise KeyboardInterrupt('logical advance failure')
        return 2
    edge=types.SimpleNamespace(freeze=lambda x:None if x is None else tuple(x.items()))
    advance=fn('matching_checkpoint.py','_advance_owned',dict(ann=types.SimpleNamespace(_advance_checked=anneal),adaptive_edge_policy=edge))
    s={'safe':True,'phase':'annealing','annealing':{'phase':'nodes'}};normalizer=object()
    try:
        result=advance(s,'a','b',{},max_operations=3,edge_cache_policy={'x':1},normalizer=normalizer)
        ok('composite return and safe state',not failure and result==2 and s['safe'])
    except KeyboardInterrupt:ok('composite fatal leaves unsafe state',failure and not s['safe'])
    ok('composite preserves backend/edge/budget',events==[{'max_operations':3,'edge_cache_policy':{'x':1},'normalizer':normalizer}])
# Freshly chosen ownership counterexamples. Extract full original class bodies;
# fake numerical dependencies, but backend close owns an actual ordinary fixture fd.
SessionTree=next(n for n in tree('matching_immutable_session.py').body if isinstance(n,ast.ClassDef) and n.name=='ImmutablePairSession')
for mode in ('success','normalizer_replaced','close_replaced','constructor_memoryerror','fatal_and_cleanup_failure'):
    events=[];tracked=[];opened=[];armed=False;primary=KeyboardInterrupt('original primary')
    def noop(*a,**k):return None
    hard=types.SimpleNamespace(check=noop,create=noop,advance=noop)
    ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
    def engine_advance(state,*a,**kw):
        events.append('advance')
        if mode=='fatal_and_cleanup_failure':raise primary
        state['phase']='done'
    engine=types.SimpleNamespace(ann=ann,hard=hard,np=ann.np,policy=noop,_check_owned=noop,_advance_owned=engine_advance,matrix_identity=noop,
        create=lambda *a,**k:{'phase':'annealing'},score_only=lambda *a,**k:types.SimpleNamespace(score=0.5,iterations=1,convergence='iteration_cap'),close=lambda s:events.append('state_close'))
    def open_fake(o):
        global armed
        fd=os.open(fixture,os.O_RDONLY);opened.append(fd);events.append('backend_acquired')
        def close():
            events.append('owned_close')
            if mode=='fatal_and_cleanup_failure':raise OSError('injected close uncertain')
            os.close(fd)
        backend=types.SimpleNamespace(lse=noop,close=close);armed=True;return backend
    seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,open_backend=open_fake)
    edge=types.SimpleNamespace(attach=lambda *a:None,current=noop,options=lambda *a:{},join=noop)
    def tuple_seam(value=()):
        if armed and mode=='constructor_memoryerror':raise MemoryError('pin tuple allocation failure')
        return tuple(value)
    ns=dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType,tuple=tuple_seam)
    exec(compile(ast.Module(body=[copy.deepcopy(SessionTree)],type_ignores=[]),str(CAND/'matching_immutable_session.py'),'exec'),ns)
    def make_session(*a,**kw):
        s=ns['ImmutablePairSession'](*a,**kw);tracked.append(s);return s
    altered=False
    def poll():
        global altered
        events.append('poll')
        if tracked and not altered:
            if mode=='normalizer_replaced':tracked[0]._normalizer=None
            if mode=='close_replaced':tracked[0]._normalizer.close=lambda:events.append('replacement_close')
            altered=True
    pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=())
    call=fn('batched_pair_executor.py','__call__',dict(adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=pair,engine=engine,annealing=ann,ImmutablePairSession=make_session,CheckpointStop=RuntimeError),cls='PairExecutor')
    executor=types.SimpleNamespace(poisoned=False,authority_poll=poll,config={},policy={'max_checkpoint_bytes':100,'max_score_buffer_bytes':100,'chunk_edges':1},schedule={'max_checkpoints':1,'calls_per_checkpoint':1,'operations_per_call':3,'max_total_checkpoints':1,'max_total_checkpoint_bytes':200},checkpoints=0,reserved_bytes=0,checkpoint=noop)
    p.attach(executor,policy)
    error=None
    try:result=call(executor,'a','b','purpose')
    except BaseException as e:error=e
    survivors=[]
    for fd in opened:
        try:os.fstat(fd);survivors.append(fd)
        except OSError:pass
    observation=dict(case=mode,events=events,error=None if error is None else {'type':type(error).__name__,'message':str(error),'notes':getattr(error,'__notes__',[])},executor_poisoned=executor.poisoned,ordinary_fixture_fds_left_open=len(survivors),state_close_attempted='state_close' in events,owned_backend_close_attempted='owned_close' in events)
    if mode=='success':ok('actual session/executor success closes owned fixture',error is None and events.count('owned_close')==1 and not survivors and not executor.poisoned)
    elif mode=='fatal_and_cleanup_failure':ok('original fatal preserved and state cleanup attempted',error is primary and executor.poisoned and 'state_close' in events and 'owned_close' in events and len(getattr(error,'__notes__',[]))==1)
    else:
        ok('RED reproduced '+mode,error is not None and executor.poisoned and len(survivors)==1 and 'owned_close' not in events and 'state_close' in events)
        reds.append(observation)
    # Independent harness cleanup only, explicitly NOT candidate cleanup credit.
    for fd in survivors:os.close(fd)
    observation['harness_residual_close_count']=len(survivors)
    (HERE/(mode+'.json')).write_text(json.dumps(observation,indent=2)+'\n')
ok('no numeric/native imports',not any(n.split('.')[0] in {'numpy','scipy','torch','ctypes'} for n in __import__('sys').modules))
result=dict(decision='WITHHOLD_SOURCE_ONLY_ACCEPTANCE',checks=checks,check_count=len(checks),reds=reds,body_references=refs,affinity=sorted(os.sched_getaffinity(0)),elapsed_ns=time.perf_counter_ns()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,numerical_imports=False,native_load=False,real_memfd_test=False,actual_admission=False)
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'decision':result['decision'],'checks':len(checks),'reds':[r['case'] for r in reds],'elapsed_ns':result['elapsed_ns'],'peak_rss_kib':result['peak_rss_kib']}))
