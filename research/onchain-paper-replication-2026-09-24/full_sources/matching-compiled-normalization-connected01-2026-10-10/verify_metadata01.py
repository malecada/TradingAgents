"""CPU3 stdlib-only extraction tests; never imports numerical candidate modules."""
import ast,builtins,copy,hashlib,importlib.util,json,os,resource,signal,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
signal.alarm(30)
assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[]
def ok(name,condition=True):
    assert condition,name
    checks.append(name)
def rejects(name,call):
    try:call()
    except (ValueError,TypeError):ok(name)
    else:raise AssertionError(name)
def tree(name):return ast.parse((HERE/name).read_text())
def extract(name,function,namespace,cls=None):
    t=tree(name)
    body=t.body if cls is None else next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls).body
    node=copy.deepcopy(next(n for n in body if isinstance(n,ast.FunctionDef) and n.name==function))
    exec(compile(ast.Module(body=[node],type_ignores=[]),name,'exec'),namespace)
    return namespace[function]
# No numerical imports are permitted even accidentally through policy paths.
original_import=builtins.__import__
def guarded_import(name,*args,**kwargs):
    assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes'},name
    return original_import(name,*args,**kwargs)
builtins.__import__=guarded_import
spec=importlib.util.spec_from_file_location('policy_fixture',HERE/'compiled_normalization_policy.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
policy=dict(format=p.FORMAT,library_path='/synthetic/reduction.so',library_sha256=p.LIBRARY_SHA256,
            source_path='/synthetic/reduction.c',source_sha256=p.SOURCE_SHA256,
            runtime_path='/synthetic/runtime.json',runtime_sha256='a'*64,runtime_bytes=512)
owner=types.SimpleNamespace();p.attach(owner,None)
ok('default has no forwarding',p.options(owner)=={})
p.read_reference_original=p.read_reference
p.read_reference=lambda *a,**k:(_ for _ in ()).throw(AssertionError('unselected read'))
ok('default does not read/import/load backend',p.open_backend(owner) is None)
p.read_reference=p.read_reference_original
for bad in [True,0,1,{},dict(policy,extra=1),dict(policy,runtime_bytes=True),dict(policy,runtime_bytes=4097),dict(policy,runtime_bytes=0),dict(policy,library_sha256='b'*64),dict(policy,source_sha256='c'*64),dict(policy,runtime_sha256='x'*64),dict(policy,library_path='relative'),dict(policy,source_path='/x/../z'),dict(policy,runtime_path='/x\x00')]:
    rejects('bad policy '+str(len(checks)),lambda bad=bad:p.freeze(bad))
p.attach(owner,policy);policy['runtime_bytes']=700
ok('selection detached from caller dictionary',dict(owner._compiled_normalization_policy)['runtime_bytes']==512)
child=types.SimpleNamespace();p.attach(child,dict(owner._compiled_normalization_policy));p.join(owner,child);ok('joined exact selection')
child._compiled_normalization_policy=tuple(list(child._compiled_normalization_policy))
rejects('identity pin mutation refused',lambda:p.current(child))
metadata=dict(format='compiled-small-lse-runtime-reference-v1',python='3.13.13',numpy='2.3.0',scipy='1.17.1',platform='linux',machine='x86_64',byteorder='little',executable='/synthetic/python',runtime_inventory_sha256='b'*64)
ok('runtime reference parser',p.runtime_metadata(json.dumps(metadata).encode())==metadata)
for key,val in [('python','3.14.0'),('numpy','2.5.1'),('scipy','1.15.3'),('runtime_inventory_sha256','bad'),('machine','aarch64'),('executable',1)]:
    rejects('runtime rejects '+key,lambda key=key,val=val:p.runtime_metadata(json.dumps(dict(metadata,**{key:val}))))
# Exact loader bodies inherited; only close's lexical global becomes nonlocal.
old=ast.parse((HERE.parent/'matching-compiled-small-pair-prototype04-2026-10-09/compiled_small_lse.py').read_text())
new=next(n for n in tree('compiled_small_lse.py').body if isinstance(n,ast.FunctionDef) and n.name=='open_backend')
for name in ('_new_memfd','_load_sealed','_live','lse','close'):
    a=copy.deepcopy(next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name))
    b=copy.deepcopy(next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name))
    if name=='close':
        for i,n in enumerate(b.body):
            if isinstance(n,ast.Nonlocal):b.body[i]=ast.Global(names=n.names)
    ok('accepted helper body '+name,ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False))
ok('helper import has no numeric/native import or calls',all(isinstance(n,(ast.Expr,ast.ImportFrom,ast.FunctionDef)) for n in tree('compiled_small_lse.py').body))
# Execute the actual composite logical forwarding with spies; no numerical arrays.
for selected in (None,types.SimpleNamespace(lse=object())):
    calls=[]
    ann=types.SimpleNamespace(_advance_checked=lambda *a,**k:calls.append((a,k)) or 7)
    edge=types.SimpleNamespace(freeze=lambda v:None if v is None else tuple(v.items()))
    advance=extract('matching_checkpoint.py','_advance_owned',{'ann':ann,'adaptive_edge_policy':edge})
    s={'safe':True,'phase':'annealing','annealing':{'phase':'nodes'}}
    used=advance(s,'a','b','config',max_operations=11,edge_cache_policy={'format':'fixture'},normalizer=selected)
    ok('composite keeps logical return/safety '+str(selected is None),used==7 and s['safe'] is True)
    expected={'max_operations':11,'edge_cache_policy':{'format':'fixture'}}
    if selected is not None:expected['normalizer']=selected
    ok('composite exact forwarding '+str(selected is None),calls[0][1]==expected)
# Evaluate actual normalization expressions to establish untouched original call
# and selected fallback injection. This does not calculate any numeric result.
normalization=next(n for n in tree('matching_annealing.py').body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
expressions=[n for n in ast.walk(normalization) if isinstance(n,ast.IfExp) and isinstance(n.test,ast.Compare) and ast.unparse(n.test)=='normalizer is None']
ok('all three original normalization seams connected',len(expressions)==3)
for expression in expressions:
    for selected in (False,True):
        calls=[]
        def fallback(*a,**k):calls.append(('original',a,k));return 'original'
        def lse(*a,**k):calls.append(('compiled',a,k));return 'compiled'
        block=object();padded=object();backend=types.SimpleNamespace(lse=lse) if selected else None
        value=eval(compile(ast.Expression(expression),'expression','eval'),dict(normalizer=backend,logsumexp=fallback,block=block,padded=padded))
        ok('normalization expression '+str(len(checks)),value==('compiled' if selected else 'original') and calls[0][2]['keepdims'] is True and (not selected or calls[0][2]['fallback'] is fallback))
# Execute actual constructor callsites with spies to verify keyword selection
# survives every real caller, including NumericExecution public entry.
for filename,callee in [('batched_numeric_execution.py','reuse.NumericReuseExecutor'),('batched_numeric_reuse.py','accepted.PairExecutor'),('batched_pair_executor.py','ImmutablePairSession')]:
    call=next(n for n in ast.walk(tree(filename)) if isinstance(n,ast.Call) and ast.unparse(n.func)==callee)
    keyword=next(n.value for n in call.keywords if n.arg is None and ast.unparse(n.value)=='compiled_normalization_policy.options(self)')
    ok('actual caller selection '+filename,eval(compile(ast.Expression(keyword),filename,'eval'),{'compiled_normalization_policy':p,'self':owner})==p.options(owner))
# Execute actual PairExecutor lifecycle with metadata-only engine/session spies.
for mode in ('done','checkpoint','failure'):
    events=[]
    edge=types.SimpleNamespace(current=lambda o:None,options=lambda o:{},join=lambda a,b:None)
    class Session:
        def __init__(self,a,b,c,**kw):
            events.append('session');p.attach(self,kw['compiled_normalization_policy_value'])
        def advance(self,state,**kw):
            events.append(('advance',kw))
            if mode=='failure':raise RuntimeError('synthetic advance failure')
            if mode=='done':state['phase']='done'
        def check(self,state):events.append('check')
        def close(self):events.append('session_close')
    engine=types.SimpleNamespace(create=lambda *a,**k:{'phase':'annealing'},
            score_only=lambda *a,**k:types.SimpleNamespace(score=0,iterations=3,convergence='fixture'),
            close=lambda s:events.append('state_close'))
    pair=types.SimpleNamespace(hash_string=lambda s:None,policy_check=lambda *a,**k:None,LIMIT=16,ENGINE_FIELDS=())
    class CheckpointStop(RuntimeError):pass
    invoke=extract('batched_pair_executor.py','__call__',dict(adaptive_edge_policy=edge,compiled_normalization_policy=p,
        pair=pair,engine=engine,annealing=object(),ImmutablePairSession=Session,CheckpointStop=CheckpointStop),cls='PairExecutor')
    obj=types.SimpleNamespace(poisoned=False,authority_poll=lambda:events.append('poll'),config={},
        policy={'max_checkpoint_bytes':100,'max_score_buffer_bytes':200,'chunk_edges':4},
        schedule={'max_checkpoints':1,'calls_per_checkpoint':1,'operations_per_call':11,'max_total_checkpoints':2,'max_total_checkpoint_bytes':300},
        checkpoints=0,reserved_bytes=0,checkpoint=lambda *a:events.append('checkpoint'))
    p.attach(obj,dict(owner._compiled_normalization_policy))
    if mode=='done':
        ok('executor returns original score metadata',invoke(obj,'a','b','purpose')==(0.0,3,'fixture'))
        ok('executor retains polling and full post-score session check',events.count('poll')==4 and 'check' in events)
        ok('completed executor preserves no-checkpoint counters',obj.checkpoints==obj.reserved_bytes==0 and not obj.poisoned)
    else:
        try:invoke(obj,'a','b','purpose')
        except RuntimeError as error:
            ok('executor exception propagated '+mode,(type(error) is CheckpointStop if mode=='checkpoint' else str(error)=='synthetic advance failure'))
        else:raise AssertionError(mode)
        ok('executor poisoning '+mode,obj.poisoned)
        if mode=='checkpoint':ok('checkpoint budget and callback retained',obj.checkpoints==1 and obj.reserved_bytes==132 and events.count('checkpoint')==1)
    ok('executor cleanup ordering '+mode,events[-2:]==['session_close','state_close'])
# Actual immutable session advance preserves max_operations and adaptive options.
events=[];normalizer=types.SimpleNamespace(lse=lambda:None,close=lambda:None)
edge=types.SimpleNamespace(current=lambda o:events.append('edge_current'),options=lambda o:{'edge_cache_policy':{'fixture':1}})
def engine_advance(*args,**kwargs):events.append(kwargs);return 9
obj=types.SimpleNamespace(check=lambda s:events.append('check'),engine=types.SimpleNamespace(_advance_owned=engine_advance),
        a='a',b='b',config={},_normalizer=normalizer,_normalizer_pin=normalizer,
        _normalizer_functions=tuple((n,getattr(normalizer,n),getattr(normalizer,n).__code__) for n in ('lse','close')),advances=0)
p.attach(obj,dict(owner._compiled_normalization_policy))
advance=extract('matching_immutable_session.py','advance',dict(require=p.require,adaptive_edge_policy=edge,compiled_normalization_policy=p),cls='ImmutablePairSession')
ok('session uses actual composite seam',advance(obj,{},max_operations=17)==9 and obj.advances==1)
ok('session preserves adaptive cache and budget forwarding',events[1]=={'max_operations':17,'edge_cache_policy':{'fixture':1},'normalizer':normalizer})
# Reverse each unified patch in memory and compare exact installed baseline.
def apply(text,patch):
    lines=text.splitlines(True);out=[];cursor=0
    body=patch.splitlines(True);i=2
    while i<len(body):
        header=body[i];assert header.startswith('@@ ');i+=1
        pos=int(header.split()[1][1:].split(',')[0])-1
        out.extend(lines[cursor:pos]);cursor=pos
        while i<len(body) and not body[i].startswith('@@ '):
            line=body[i];i+=1
            if line[0] in ' -':assert lines[cursor]==line[1:];cursor+=1
            if line[0] in ' +':out.append(line[1:])
    out.extend(lines[cursor:]);return ''.join(out)
for path in sorted(HERE.glob('baseline_*.py')):
    name=path.name[len('baseline_'):];candidate=(HERE/name).read_text()
    ast.parse(candidate)
    restored=apply(candidate,(HERE/(name+'.inverse.patch')).read_text())
    ok('exact inverse '+name,restored==path.read_text()==(ROOT/'tradingagents/research/onchain_replication'/name).read_text())
# No changes to model/training/state schemas are hidden in an AST replacement.
for name in ('matching_annealing.py','matching_checkpoint.py'):
    base=tree('baseline_'+name);candidate=tree(name)
    changed={'matching_annealing.py':{'_advance_checked'},'matching_checkpoint.py':{'_advance_owned'}}[name]
    a=[ast.dump(n,include_attributes=False) for n in base.body if not isinstance(n,ast.FunctionDef) or n.name not in changed]
    b=[ast.dump(n,include_attributes=False) for n in candidate.body if not isinstance(n,ast.FunctionDef) or n.name not in changed]
    ok('all other engine AST unchanged '+name,a==b)
result={'status':'PASS_STDLIB_METADATA_ONLY','checks':checks,'count':len(checks),'elapsed_ns':time.perf_counter_ns()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'numeric_backend_imported':False,'native_loaded':False,'numerical_equivalence_tested':False}
(HERE/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
