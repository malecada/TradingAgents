import copy,hashlib,importlib.util,json,os,resource,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]))
assert resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456)
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304)
assert len(os.sched_getaffinity(0))==2
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph,validate_attributed
from tradingagents.research.onchain_replication import matching_identity as realidentity
import tradingagents.research.onchain_replication as package

def load(file,name):
 spec=importlib.util.spec_from_file_location(package.__name__+'.'+name,P/file);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
B=load('baseline_matching_annealing.py','validation_baseline')
I=load('matching_identity.py','validation_identity')
package.matching_identity=I
try:C=load('matching_annealing.py','validation_candidate')
finally:package.matching_identity=realidentity
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
def graph():return AttributedGraph(('a','b'),np.array([[0.],[1.]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.2],[.3]]),'a'*64,'a')
a=graph();b=graph();seed=B.create(a,b,c,max_state_bytes=65536,max_chunk_entries=8)
def counted(mod,state,aa=a,bb=b,cc=c):
 calls=[]
 def profiler(frame,event,arg):
  if event=='call' and frame.f_code is validate_attributed.__code__:calls.append(1)
 sys.setprofile(profiler)
 try:mod.check(state,aa,bb,cc)
 finally:sys.setprofile(None)
 return len(calls)
# Actual source regression, then candidate acceptance: fresh identity is identical.
assert counted(B,seed)==4
assert counted(C,seed)==2
assert B.identity(a,b,c)==C._identity_after_pair_validation(a,b,c)
checks=0
def equal(x,y):
 global checks
 for k in x:
  if isinstance(x[k],np.ndarray):assert x[k].tobytes()==y[k].tobytes(),k
  else:assert x[k]==y[k],k
 checks+=1
x=copy.deepcopy(seed);y=copy.deepcopy(seed)
for budget in [1,7,8,31,10000]:
 assert B.advance(x,a,b,c,max_operations=budget)==C.advance(y,a,b,c,max_operations=budget);equal(x,y)
# Both checkpoint directions, including fresh validation on restored state.
for writer,reader,name in [(B,C,'baseline-to-candidate'),(C,B,'candidate-to-baseline')]:
 h=writer.save(x,P/name,a,b,c,max_checkpoint_bytes=100000)
 z=reader.load(P/name,a,b,c,expected_sha256=h,max_state_bytes=65536,max_chunk_entries=8);equal(x,z)
# Fresh hash: replace immutable feature object with a new valid immutable graph feature.
changed=graph();object.__setattr__(changed,'node_features',AttributedGraph(('a','b'),np.array([[.4],[1.]]),changed.edge_index,changed.edge_features,'a'*64,'a').node_features)
# Errors and precedence are retained, including invalid graph before invalid config.
for aa,cc in [(changed,c),(a,{**c,'solver':'bad'})]:
 errors=[]
 for mod in (B,C):
  try:mod.check(seed,aa,b,cc)
  except Exception as e:errors.append((type(e).__name__,str(e)))
  else:raise AssertionError('expected refusal')
 assert errors[0]==errors[1]
bad=graph();object.__setattr__(bad,'edge_index',np.array([[0,0],[1,1]],dtype=np.int64))
for cc in [c,{**c,'solver':'bad'}]:
 errors=[]
 for mod in (B,C):
  try:mod.check(seed,bad,b,cc)
  except Exception as e:errors.append((type(e).__name__,str(e)))
 assert len(errors)==2 and errors[0]==errors[1]
# Mutable ndarray and subclass inputs retain duplicate original validation.
mutable=graph();object.__setattr__(mutable,'edge_features',mutable.edge_features.copy());assert counted(C,seed,mutable,b)==4
class Sub(AttributedGraph):pass
sub=Sub(a.node_ids,a.node_features,a.edge_index,a.edge_features,a.parent_hash,a.center_id)
assert counted(C,seed,sub,b)==4
# Monkeypatched pair validator must not be bypassed or considered trusted.
original=C.validate_pair
C.validate_pair=lambda *args:original(*args)
assert counted(C,seed)==4
C.validate_pair=original
# Public graph_identity validation is unchanged.
assert I.graph_identity(a)==realidentity.graph_identity(a)
r={'status':'PASS','baseline_graph_validations_per_check':4,'candidate_graph_validations_per_check':2,'state_boundaries':checks,'fresh_identity_refusal':True,'error_precedence':True,'unsupported_fallback':True,'checkpoint_inverse':True,'affinity':sorted(os.sched_getaffinity(0)),'as_limit':resource.getrlimit(resource.RLIMIT_AS),'fsize_limit':resource.getrlimit(resource.RLIMIT_FSIZE),'no_benchmark':True}
(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
