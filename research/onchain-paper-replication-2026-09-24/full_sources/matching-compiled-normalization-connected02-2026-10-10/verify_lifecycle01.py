"""Focused actual-source lifecycle regression; ordinary fd only, no numerics."""
import ast,builtins,copy,hashlib,importlib.util,json,os,resource,signal,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'matching-compiled-normalization-connected01-2026-10-10'
REVIEW=HERE.parent/'matching-compiled-normalization-connected-review01-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(30)
assert os.sched_getaffinity(0)=={3}
started=time.perf_counter_ns();checks=[];observations=[]
def ok(name,condition=True):assert condition,name;checks.append(name)
old_import=builtins.__import__
def safe_import(name,*a,**kw):
    assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes'},name
    return old_import(name,*a,**kw)
builtins.__import__=safe_import
spec=importlib.util.spec_from_file_location('lifecycle_policy',HERE/'compiled_normalization_policy.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
policy={'format':p.FORMAT,'library_path':'/synthetic/library','library_sha256':p.LIBRARY_SHA256,'source_path':'/synthetic/source','source_sha256':p.SOURCE_SHA256,'runtime_path':'/synthetic/runtime','runtime_sha256':'a'*64,'runtime_bytes':32}
fixture=HERE/'ordinary-fixture.txt';fixture.write_text('ordinary lifecycle fixture\n')
def extract(root,name,method,ns,cls):
    tree=ast.parse((root/name).read_text());body=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls).body
    fn=next(n for n in body if isinstance(n,ast.FunctionDef) and n.name==method)
    exec(compile(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[]),str(root/name),'exec'),ns)
    return ns[method]
review_digest=hashlib.sha256((REVIEW/'REVIEW01.json').read_bytes()).hexdigest()
ok('exact independent review reference',review_digest=='14b7da52e75035d20cdd13b1d99d35e18bbc5f49f400ce452e3bd5cfb7828ef5')

def run(root,mode):
    events=[];tracked=[];opened=[];armed=False;altered=False
    primary=MemoryError('pin tuple allocation failure') if 'constructor' in mode else KeyboardInterrupt('original primary')
    cleanup_error=KeyboardInterrupt('cleanup fatal') if mode=='constructor_cleanup_fatal' else OSError('injected close uncertain')
    def noop(*a,**k):return None
    hard=types.SimpleNamespace(check=noop,create=noop,advance=noop)
    ann=types.SimpleNamespace(normalization_policy=noop,_check_state_identity=noop,_advance_checked=noop,validate_pair=noop,identity=lambda *a:{},np=object())
    def engine_advance(state,*a,**kw):
        events.append('advance')
        if mode=='fatal_and_cleanup_failure':raise primary
        state['phase']='done'
    engine=types.SimpleNamespace(ann=ann,hard=hard,np=ann.np,policy=noop,_check_owned=noop,_advance_owned=engine_advance,matrix_identity=noop,create=lambda *a,**k:{'phase':'annealing'},score_only=lambda *a,**k:types.SimpleNamespace(score=.5,iterations=1,convergence='iteration_cap'),close=lambda s:events.append('state_close'))
    def open_fake(owner):
        nonlocal armed
        if mode=='unselected':return None
        fd=os.open(fixture,os.O_RDONLY);opened.append(fd);events.append('backend_acquired')
        def close():
            events.append('owned_close')
            if mode in ('fatal_and_cleanup_failure','constructor_cleanup_fatal','repeat_close_failure','close_state_failure_cleanup_failure'):raise cleanup_error
            os.close(fd)
        armed=True
        return types.SimpleNamespace(lse=noop,close=close)
    seam=types.SimpleNamespace(attach=p.attach,current=p.current,options=p.options,join=p.join,open_backend=open_fake)
    edge=types.SimpleNamespace(attach=lambda *a:None,current=noop,options=lambda *a:{},join=noop)
    def tuple_seam(value=()):
        if armed and mode in ('constructor_memoryerror','constructor_cleanup_fatal'):raise primary
        return tuple(value)
    ns=dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=seam,config_pin=lambda c:(),graph_pin=lambda g:(),rejoin=noop,MappingProxyType=types.MappingProxyType,tuple=tuple_seam)
    tree=ast.parse((root/'matching_immutable_session.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImmutablePairSession')
    exec(compile(ast.Module(body=[copy.deepcopy(cls)],type_ignores=[]),str(root/'matching_immutable_session.py'),'exec'),ns)
    Base=ns['ImmutablePairSession']
    failed=False
    class Session(Base):
        def __setattr__(self,name,value):
            nonlocal failed
            wanted={'constructor_attr_normalizer':'_normalizer','constructor_attr_pin':'_normalizer_pin','constructor_attr_functions':'_normalizer_functions','close_state_failure':'closed','close_state_failure_cleanup_failure':'closed'}.get(mode)
            if armed and name==wanted and not failed:
                failed=True;raise primary
            return super().__setattr__(name,value)
    def make_session(*a,**kw):
        obj=Session(*a,**kw);tracked.append(obj);return obj
    def poll():
        nonlocal altered
        events.append('poll')
        if tracked and not altered:
            if mode=='normalizer_replaced':tracked[0]._normalizer=None
            if mode=='close_replaced':tracked[0]._normalizer.close=lambda:events.append('replacement_close')
            altered=True
    pair=types.SimpleNamespace(hash_string=noop,policy_check=noop,LIMIT=16,ENGINE_FIELDS=())
    invoke=extract(root,'batched_pair_executor.py','__call__',dict(adaptive_edge_policy=edge,compiled_normalization_policy=seam,pair=pair,engine=engine,annealing=ann,ImmutablePairSession=make_session,CheckpointStop=RuntimeError),'PairExecutor')
    executor=types.SimpleNamespace(poisoned=False,authority_poll=poll,config={},policy={'max_checkpoint_bytes':100,'max_score_buffer_bytes':100,'chunk_edges':1},schedule={'max_checkpoints':1,'calls_per_checkpoint':1,'operations_per_call':3,'max_total_checkpoints':1,'max_total_checkpoint_bytes':200},checkpoints=0,reserved_bytes=0,checkpoint=noop)
    p.attach(executor,None if mode=='unselected' else policy)
    error=None
    try:invoke(executor,'a','b','purpose')
    except BaseException as caught:error=caught
    first_error=error
    if mode in ('repeat_close_success','repeat_close_failure'):
        for _ in range(2):
            try:tracked[0].close()
            except BaseException as caught:
                ok('repeat preserves close error object',mode=='repeat_close_failure' and caught is first_error)
        ok('terminal close capability invoked once',events.count('owned_close')==1)
    survivors=[]
    for fd in opened:
        try:os.fstat(fd);survivors.append(fd)
        except OSError:pass
    observation={'version':'WITHHELD01' if root==OLD else 'SUCCESSOR02','case':mode,'events':events,'error':None if error is None else {'type':type(error).__name__,'message':str(error),'notes':getattr(error,'__notes__',[])},'executor_poisoned':executor.poisoned,'open_descriptors_after_candidate':len(survivors),'primary_identity_preserved':error is primary,'cleanup_identity_preserved':error is cleanup_error}
    if root==OLD:
        ok('RED reproduced '+mode,error is not None and executor.poisoned and len(survivors)==1 and 'owned_close' not in events and 'state_close' in events)
    elif mode in ('success','repeat_close_success','unselected'):
        ok('positive '+mode,error is None and not survivors and not executor.poisoned and events.count('owned_close')==(0 if mode=='unselected' else 1))
    elif mode in ('normalizer_replaced','close_replaced'):
        ok('GREEN original owned cleanup '+mode,isinstance(error,ValueError) and executor.poisoned and not survivors and events.count('owned_close')==1 and 'replacement_close' not in events and 'state_close' in events)
    elif mode in ('fatal_and_cleanup_failure','constructor_cleanup_fatal','close_state_failure_cleanup_failure'):
        ok('primary plus cleanup identity '+mode,error is primary and executor.poisoned and len(survivors)==1 and events.count('owned_close')==1 and 'state_close' in events and len(getattr(error,'__notes__',[]))==1)
    elif mode=='repeat_close_failure':
        ok('close failure does not forge closure',error is cleanup_error and len(survivors)==1 and executor.poisoned and 'state_close' in events)
    else:
        ok('GREEN construction/state failure '+mode,error is primary and executor.poisoned and not survivors and events.count('owned_close')==1 and 'state_close' in events)
    # Explicit independent harness cleanup of uncertain/old RED descriptors.
    for fd in survivors:os.close(fd)
    observation['harness_residual_close_count']=len(survivors);observations.append(observation)
    (HERE/(observation['version']+'-'+mode+'.json')).write_text(json.dumps(observation,indent=2)+'\n')
for mode in ('normalizer_replaced','close_replaced','constructor_memoryerror'):run(OLD,mode)
for mode in ('normalizer_replaced','close_replaced','constructor_memoryerror','success','unselected','fatal_and_cleanup_failure','constructor_cleanup_fatal','constructor_attr_normalizer','constructor_attr_pin','constructor_attr_functions','repeat_close_success','repeat_close_failure','close_state_failure','close_state_failure_cleanup_failure'):run(HERE,mode)
# Only __init__/close lifecycle bodies differ. All other session methods exact.
def tree(root,name):return ast.parse((root/name).read_text())
a=tree(OLD,'matching_immutable_session.py');b=tree(HERE,'matching_immutable_session.py')
for t in (a,b):
    cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ImmutablePairSession')
    cls.body=[n for n in cls.body if getattr(n,'name',None) not in {'__init__','close'}]
ok('session unchanged outside constructor and close',ast.dump(a)==ast.dump(b))
for name in ('matching_annealing.py','matching_checkpoint.py','batched_pair_executor.py','batched_numeric_execution.py','compiled_normalization_policy.py','compiled_small_lse.py'):
    ok('byte-identical reuse '+name,(HERE/name).read_bytes()==(OLD/name).read_bytes())
oldhash=hashlib.sha256((OLD/'matching_immutable_session.py').read_bytes()).hexdigest();newhash=hashlib.sha256((HERE/'matching_immutable_session.py').read_bytes()).hexdigest()
ok('reuse only mandatory session source pin changed',(HERE/'batched_numeric_reuse.py').read_text().replace(newhash,oldhash)==(OLD/'batched_numeric_reuse.py').read_text())
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
for path in HERE.glob('baseline_*.py'):
    name=path.name[len('baseline_'):];body=(HERE/name).read_text()
    ok('exact installed inverse '+name,apply(body,(HERE/(name+'.inverse.patch')).read_text())==path.read_text())
    ok('exact withheld01 inverse '+name,apply(body,(HERE/(name+'.to01.inverse.patch')).read_text())==(OLD/name).read_text())
result={'status':'PASS_FOCUSED_LIFECYCLE_REGRESSION','checks':checks,'count':len(checks),'observations':observations,'elapsed_ns':time.perf_counter_ns()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'numerical_backend_loaded':False,'real_memfd':False,'actual_admission':False}
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','count','elapsed_ns','peak_rss_kib')}))
