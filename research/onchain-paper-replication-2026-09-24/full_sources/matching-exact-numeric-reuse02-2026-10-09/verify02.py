import ast,gc,hashlib,importlib.util,json,os,resource,signal,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]));spec=importlib.util.spec_from_file_location('reuse02',P/'numeric_reuse.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal');policy=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576);schedule=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=10000,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
def graph(names):return AttributedGraph(names,np.array([[0.],[1.]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.2],[.3]]),'a'*64,names[0])
def make():return m.NumericReuseExecutor(c,policy,schedule,lambda *a:None,max_entries=4096,max_retained_bytes=4*1024**2,max_key_bytes=4096)
checks=[]
def ck(n,v):assert v,n;checks.append(n)
x=make();a=graph(('a','b'));b=graph(('x','y'))
try:x(a,b,'0'*64)
except ValueError:checks.append('outside_batch_refused')
else:raise AssertionError('unguarded occurrence')
x.begin_batch();result=x(a,b,'1'*64);before=dict(x.counters)
for i in range(32):assert x(b,a,hashlib.sha256(str(i).encode()).hexdigest())==result
ck('same_numeric_new_identity_reused',x.computed==1 and x.reused==32 and x.last_receipt['mode']=='reused')
ck('no_source_or_roster_per_hit',x.counters['source_guard_calls']==before['source_guard_calls'] and x.counters['source_hashed_bytes']==before['source_hashed_bytes'])
ck('one_probe_per_same_key_hit',x.counters['lookup_probes']-before['lookup_probes']==32)
x.end_batch();ck('final_guard_once',x.counters['source_guard_calls']==before['source_guard_calls']+1);measured=dict(x.counters);x.close()
# Engineering cache-only fixtures exercise all slots without numerical execution.
x=make();entries=[]
for i in range(4096):
 key=('synthetic-exact-key-'+str(i)).encode();hashed=int.from_bytes(hashlib.sha256(key).digest()[:8],'big');assert x._store(key,hashed,(.5,1,'iteration_cap'),'a'*64,i);entries.append((key,hashed))
ck('all4096slots_bounded',x.count==4096 and x.retained_bytes<=x.max_retained_bytes)
ck('incremental_actual_object_accounting',x.retained_bytes==x._base_bytes+sum(m.entry_size(v) for v in x._slots if v is not None))
probes=x.counters['lookup_probes']
for key,hashed in entries:assert x._find(key,hashed) is not None
probe_count=x.counters['lookup_probes']-probes;ck('hash_lookup_no_full_table_walk',probe_count<4*4096)
# Exact equality even if digest routing hash collides.
x._store(b'collision-one',7,(.5,1,'iteration_cap'),'a'*64,0);x._store(b'collision-two',7,(.25,1,'iteration_cap'),'b'*64,1)
ck('hash_collision_exact_bytes',x._find(b'collision-one',7)!=x._find(b'collision-two',7) and x._find(b'collision-absent',7) is None)
idx=x._find(b'collision-one',7);links=x.counters['lru_link_updates'];x._touch(idx);ck('constant_lru_relink',x.counters['lru_link_updates']-links==2)
ck('eviction_incremental_accounting',x.retained_bytes==x._base_bytes+sum(m.entry_size(v) for v in x._slots if v is not None));x.close()
# Deferred runtime attestation is explicit; no claim of continuous authority.
x=make();x.begin_batch();original=m.engine.ann.bound;m.engine.ann.bound=lambda *a:None
try:
 try:x.end_batch()
 except ValueError:ck('final_roster_change_refuses',x.poisoned and x.count==0)
 else:raise AssertionError('runtime changed accepted')
finally:m.engine.ann.bound=original
x=make();x.begin_batch();original=m.SOURCE_PINS;m.SOURCE_PINS={**original,next(iter(original)):'0'*64}
try:
 try:x.end_batch()
 except ValueError:ck('final_source_change_refuses',x.poisoned)
 else:raise AssertionError('source changed accepted')
finally:m.SOURCE_PINS=original
x=make();x.begin_batch();x.executor.config['alpha']=.8
try:x(a,b,'b'*64)
except ValueError:ck('light_config_refuses',x.poisoned)
else:raise AssertionError('config changed accepted')
# Checkpoint bracket checks callback-induced runtime changes; no math suite repeat.
original=m.engine.ann.bound
x=m.NumericReuseExecutor(c,policy,schedule,lambda *args:setattr(m.engine.ann,'bound',lambda *args:None),max_entries=2,max_retained_bytes=16384,max_key_bytes=4096);x.begin_batch()
try:
 try:x._checkpoint()
 except ValueError:checks.append('checkpoint_final_roster_refuses')
 else:raise AssertionError('checkpoint runtime accepted')
finally:m.engine.ann.bound=original;x.close()
# Original numeric-key/eligibility/public framing functions unchanged.
old=ast.parse((P.parent/'matching-exact-numeric-reuse01-2026-10-09/numeric_reuse.py').read_text());new=ast.parse((P/'numeric_reuse.py').read_text());od={n.name:ast.dump(n) for n in old.body if isinstance(n,ast.FunctionDef)};nd={n.name:ast.dump(n) for n in new.body if isinstance(n,ast.FunctionDef)}
ck('unchanged_exact_key_eligibility',all(od[n]==nd[n] for n in ['numeric_key','immutable','config_bytes','raw']))
r={'status':'PASS_CHANGED_SEAMS_ONLY','checks':checks,'actual33occurrence_counters':measured,'4096_lookup_probes':probe_count,'no_benchmark':True};(P/'RESULT02.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
