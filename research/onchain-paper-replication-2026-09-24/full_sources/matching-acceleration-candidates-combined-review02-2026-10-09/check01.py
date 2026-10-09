import os,resource,signal,sys,json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parent;F=R.parent;ROOT=Path.cwd();os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30);(R/'LIMITS01.json').write_text(json.dumps({'affinity':list(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall':signal.getitimer(signal.ITIMER_REAL)[0],'threads':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}})+'\n');sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('sealed04',F/'matching-compiled-small-pair-prototype04-2026-10-09/compiled_small_lse.py');assert h._live()
realclose=os.close;closed=[];failure=OSError('synthetic source close reports failure after actual close')
def closing(fd):
 realclose(fd);closed.append(fd)
 if len(closed)==1:raise failure
try:
 os.close=closing
 try:h._load_sealed()
 except OSError as e:assert e is failure
 else:raise AssertionError('cleanup ambiguity masked')
finally:os.close=realclose
assert len(closed)==2
for fd in closed:
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('acquired fd leaked')
assert h._live();h.close()
b=load('full_batch02',F/'matching-batched-small-pair-prototype02-2026-10-09/full_advance.py');engine=b.engine
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication import compact_policy,matching_pair
c=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes());pc=json.loads((F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_bytes())['stage_policy']['pair'];c=compact_policy.effective_matching(c,pc);p=compact_policy.pair_policy(pc);policy={k:p[k] for k in matching_pair.ENGINE_FIELDS}
def graph(n,shift):
 ids=tuple('v'+str(i) for i in range(n));return AttributedGraph(ids,np.array([[shift+.06*i,shift-.03*i] for i in range(n)]),np.array([(i,(i+1)%n) for i in range(n)],dtype=np.int64).T.copy(),np.array([[shift+.02*i] for i in range(n)]),'d'*64,ids[0])
pairs=[(graph(3,.03+k*.009),graph(2,.06+k*.01)) for k in range(3)];old=[engine.create(a,z,c,**policy) for a,z in pairs];new=[engine.create(a,z,c,**policy) for a,z in pairs]
def equal(a,z):
 if isinstance(a,np.ndarray):assert a.dtype==z.dtype and a.shape==z.shape and a.flags.writeable==z.flags.writeable and a.tobytes()==z.tobytes()
 elif type(a)is dict:
  assert a.keys()==z.keys()
  for k in a:equal(a[k],z[k])
 elif type(a)in (tuple,list):
  assert type(a)==type(z) and len(a)==len(z)
  for x,y in zip(a,z):equal(x,y)
 else:assert a==z
try:
 budgets=[1000000,1000000,7];expected=[engine.advance(s,a,z,c,max_operations=n) for s,(a,z),n in zip(old,pairs,budgets)];actual,diag=b.advance_batch(new,pairs,c,budgets);assert actual==expected==[534,534,7] and len(diag['fast_groups'])==1
 for x,y in zip(old,new):equal(x,y)
 dest=R/'checkpoint';layout={'format':'sharded-npy-v1','chunk_entries':262144};digest=engine.save(new[0],dest,*pairs[0],c,max_checkpoint_bytes=p['max_checkpoint_bytes'],checkpoint_layout=layout);restored=engine.load(dest,*pairs[0],c,expected_sha256=digest,**policy,checkpoint_layout=layout);equal(restored,new[0]);engine.close(new[0]);new[0]=restored
 for states in (old,new):
  for s,(a,z) in zip(states,pairs):
   while s['phase']!='done':engine.advance(s,a,z,c,max_operations=1000000)
 for x,y,(a,z) in zip(old,new,pairs):
  equal(x,y);xr=engine.result(x,a,z,c);yr=engine.result(y,a,z,c);assert xr.assignment.tobytes()==yr.assignment.tobytes() and xr.score==yr.score and xr.iterations==yr.iterations
finally:b.close_all(old);b.close_all(new)
(R/'RESULT01.json').write_text(json.dumps({'loader_source_close_error_identity_preserved':True,'all_two_new_descriptors_closed':True,'existing_lifetime_unaffected':True,'shape':[3,2],'pairs':3,'budgets':budgets,'used':actual,'diagnostic':diag,'all_original_states_bitwise_equal':True,'checkpoint_sha256':digest,'checkpoint_original_load_equal':True,'post_checkpoint_completion_results_equal':True},indent=2)+'\n')
