"""Actual wrapper definitions with explicitly synthetic numerical routing dependencies."""
import array,ast,copy,hashlib,json,math,os,struct,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent; C=P.parent/'matching-exact-numeric-reuse02-2026-10-09'
source=C/'numeric_reuse.py';tree=ast.parse(source.read_text());checks=[]
def ck(name,condition):
    assert condition,name
    checks.append(name)
def noop(*a,**k):pass
def goodhash(s):assert len(s)==64 and all(c in '0123456789abcdef' for c in s)
trace=[]
def identity(a):trace.append(a);return 'fresh'
class FakeExecutor:
    def __init__(self,c,p,s,checkpoint):
        self.config=copy.deepcopy(c);self.policy=copy.deepcopy(p);self.schedule=copy.deepcopy(s);self.checkpoint=checkpoint;self.poisoned=False;self.checkpoints=0;self.reserved_bytes=0
    def __call__(self,a,b,purpose):
        if self.config.get('callback'):self.checkpoint()
        return (.25,2,'iteration_cap')
np=types.SimpleNamespace(**{k:noop for k in ['asarray','empty','zeros','exp','multiply','add']},geterr=lambda:dict(divide='warn',over='warn',under='ignore',invalid='warn'))
accepted=types.SimpleNamespace(PairExecutor=FakeExecutor)
reference=types.SimpleNamespace(validate_pair=noop)
pair=types.SimpleNamespace(policy_check=noop,hash_string=goodhash)
engine=types.SimpleNamespace(ann=types.SimpleNamespace(typed_identity=types.SimpleNamespace(graph_identity=identity)))
fixture=P/'source-fixture.txt';fixture.write_text('original\n')
mod=types.SimpleNamespace(__name__='synthetic_runtime',function=noop)
g=dict(globals(),MODULES=(mod,),ROUND=lambda:0,SOURCE_PINS={str(fixture):hashlib.sha256(fixture.read_bytes()).hexdigest()})
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]),str(source),'exec'),g)
g['ROSTER']=g['roster']();g['DIRECT']=(np.asarray,np.empty,np.zeros,np.exp,np.multiply,np.add,math.exp,math.fsum)
# Only numerical-domain helpers are replaced; changed wrapper control/cache methods are actual source.
g['immutable']=lambda a:True;g['numeric_key']=lambda a,b,c,limit:(a+b) if len(a+b)<=limit else None
Class=g['NumericReuseExecutor']
def make(callback=noop,config=None,entries=8,allowance=16384):return Class(config or {},{}, {},callback,max_entries=entries,max_retained_bytes=allowance,max_key_bytes=1024)
def refused(fn):
    try:fn()
    except ValueError:return True
    return False
x=make();ck('outside_batch_refuses',refused(lambda:x(b'a',b'b','0'*64)));x.begin_batch();r=x(b'a',b'b','1'*64);n=len(trace);guards=x.counters['source_guard_calls'];x(b'a',b'b','2'*64)
ck('fresh_identity_on_hit',len(trace)==n+2);ck('fresh_purpose_and_origin',x.last_receipt['purpose_sha256']=='2'*64 and x.last_receipt['origin_purpose_sha256']=='1'*64)
ck('provisional_not_old_credit',x.last_receipt['boundary_validated_batch_complete'] is False and x.last_receipt['old_per_occurrence_execution_credit'] is False)
ck('hit_without_source_rescan',x.counters['source_guard_calls']==guards and x.reused==1);x.end_batch();ck('final_attestation',x.counters['source_guard_calls']==guards+1);x.close();ck('close_clears',x.count==0 and x.retained_bytes==x._base_bytes and x.last_receipt is None)
x=make(entries=3)
for i,k in enumerate([b'a',b'b',b'c']):x._store(k,7,(.25,2,'iteration_cap'),'a'*64,i)
ck('collision_exact_bytes',len({x._find(k,7) for k in [b'a',b'b',b'c']})==3 and x._find(b'd',7) is None)
x._touch(x._find(b'a',7));x._store(b'd',7,(.25,2,'iteration_cap'),'a'*64,3)
ck('correct_lru_eviction',x._find(b'b',7) is None and x._find(b'a',7) is not None)
ck('actual_incremental_accounting',x.retained_bytes==x._base_bytes+sum(g['entry_size'](e) for e in x._slots if e is not None))
x.close();ck('clear_freelist_reusable',x.count==0 and all(e is None for e in x._slots))
x=make();ck('oversize_entry_no_retention',not x._store(b'x'*20000,7,(.25,2,'iteration_cap'),'a'*64,0) and x.count==0)
x.begin_batch();x(b'a',b'b','3'*64);fixture.write_text('changed\n');ck('end_source_mutation_refuses_clears',refused(x.end_batch) and x.poisoned and x.count==0 and x.last_receipt is None);fixture.write_text('original\n')
x=make();x.begin_batch();x.executor.config['mutation']=True;ck('per_call_config_refuses',refused(lambda:x(b'a',b'b','4'*64)) and x.poisoned)
primary=RuntimeError('primary fixture')
def fail():raise primary
x=make(fail,{'callback':True});x.begin_batch()
try:x(b'a',b'b','5'*64)
except RuntimeError as e:ck('primary_exception_poison_cleanup',e is primary and x.poisoned and x.count==0 and x.last_receipt is None)
else:raise AssertionError('callback failure accepted')
def mutate():mod.function=lambda:None
x=make(mutate,{'callback':True});x.begin_batch();ck('checkpoint_runtime_mutation_refuses',refused(lambda:x(b'a',b'b','6'*64)) and x.poisoned);mod.function=noop
x=make();x.begin_batch();fixture.write_text('changed again\n');ck('close_failure_still_clears',refused(x.close) and x.closed and x.poisoned and x.count==0);fixture.write_text('original\n')
old=ast.parse((C.parent/'matching-exact-numeric-reuse01-2026-10-09/numeric_reuse.py').read_text())
def funcs(t):return {n.name:ast.dump(n) for n in t.body if isinstance(n,ast.FunctionDef)}
ck('unchanged_numeric_framing',all(funcs(old)[n]==funcs(tree)[n] for n in ('numeric_key','immutable','config_bytes','raw')))
pins=json.loads((C/'SOURCE_PINS.json').read_text());mismatches={str(p):{'frozen':h,'current':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h}
result={'status':'PASS_CHANGED_CONTROL_SEAMS_SYNTHETIC_DEPENDENCIES','checks':checks,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_pin_mismatches':mismatches,'affinity':sorted(os.sched_getaffinity(0)),'numerical_runtime_imported':False,'numeric_evidence':'unchanged prior evidence reused; synthetic executor does not prove numerical execution'}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
