import ast,copy,hashlib,importlib.util,json,os,resource,signal,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;P=H.parent/'matching-validation-once01-2026-10-09';sys.path.insert(0,str(R));checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,v):
 assert v,n
 checks.append(n)
manifest=json.loads((P/'MANIFEST.json').read_bytes())
for f in ['matching_identity.py','matching_annealing.py','baseline_matching_identity.py','baseline_matching_annealing.py']:ck('sourcepin_'+f,sha(P/f)==manifest[f])
ck('accepted_annealing_baseline',manifest['baseline_matching_annealing.py']=='1d1377bd1faab3b563ff6d07c2e55908c556b71fb5add4126d5860d481a099fe')
# Reverse every actual diff hunk in memory, including context checks.
for block in (P/'inverse.patch').read_text().split('--- ')[1:]:
 header,rest=block.split('\n',1);fn=header.strip();parts=rest.split('@@ ');lines=(P/fn).read_text().splitlines(True);out=[];pos=0
 for part in parts[1:]:
  if not part.startswith('-'):continue
  hdr,body=part.split(' @@',1);start=int(hdr.split()[0][1:].split(',')[0])-1;out+=lines[pos:start];pos=start
  for line in body.splitlines(True)[1:]:
   if line.startswith(' '):assert lines[pos]==line[1:];out.append(line[1:]);pos+=1
   elif line.startswith('-'):assert lines[pos]==line[1:];pos+=1
   elif line.startswith('+'):out.append(line[1:])
 out+=lines[pos:];ck('full_inverse_'+fn,''.join(out)==(P/('baseline_'+fn)).read_text())
for f,changed in [('matching_annealing.py',{'check'}),('matching_identity.py',{'graph_identity'})]:
 a={n.name:ast.dump(n) for n in ast.parse((P/('baseline_'+f)).read_text()).body if isinstance(n,ast.FunctionDef)};b={n.name:ast.dump(n) for n in ast.parse((P/f).read_text()).body if isinstance(n,ast.FunctionDef)}
 ck('unchanged_functions_'+f,all(b[k]==v for k,v in a.items() if k not in changed))
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph,validate_attributed
import tradingagents.research.onchain_replication as package
from tradingagents.research.onchain_replication import matching_identity as installed

def load(f,n):
 spec=importlib.util.spec_from_file_location(package.__name__+'.'+n,P/f);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
B=load('baseline_matching_annealing.py','review_validation_base');I=load('matching_identity.py','review_validation_identity');package.matching_identity=I
try:C=load('matching_annealing.py','review_validation_candidate')
finally:package.matching_identity=installed
cfg=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=2,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
def graph():return AttributedGraph(('x','y','z'),np.zeros((3,1)),np.array([[0,1,2],[1,2,0]],dtype=np.int64),np.array([[.1],[.2],[.3]]),'a'*64,'x')
a,b=graph(),graph();seed=B.create(a,b,cfg,max_state_bytes=65536,max_chunk_entries=8)
def count(m,s=seed,aa=a,cc=cfg):
 hits=[]
 def observe(frame,event,arg):
  if event=='call' and frame.f_code is validate_attributed.__code__:hits.append(1)
 sys.setprofile(observe)
 try:m.check(s,aa,b,cc)
 finally:sys.setprofile(None)
 return len(hits)
ck('four_to_two_same_call',count(B)==4 and count(C)==2)
ck('public_fresh_identity_bytes',I.graph_identity(a)==installed.graph_identity(a))
class Sub(AttributedGraph):pass
class Dict(dict):pass
mutable=graph();object.__setattr__(mutable,'edge_features',mutable.edge_features.copy())
sub=Sub(a.node_ids,a.node_features,a.edge_index,a.edge_features,a.parent_hash,a.center_id)
for label,g,conf,state in [('mutable',mutable,cfg,seed),('graph_subclass',sub,cfg,seed),('config_subclass',a,Dict(cfg),seed),('state_subclass',a,cfg,Dict(seed))]:ck('fallback_'+label,count(C,state,g,conf)==4)
original=C.validate_pair;C.validate_pair=lambda *args:original(*args)
try:ck('replacement_pair_fallback',count(C)==4)
finally:C.validate_pair=original
original=I.validate_attributed;calls=[]
def wrapped(g):calls.append(1);return original(g)
I.validate_attributed=wrapped
try:C.check(seed,a,b,cfg);ck('replacement_identity_validator_fallback',len(calls)==2)
finally:I.validate_attributed=original
# Exact corruption/error precedence, including graph failure before bad config/state.
def error(m,s,g,c):
 try:m.check(s,g,b,c)
 except Exception as e:return type(e).__name__,str(e)
 return None
bad=graph();object.__setattr__(bad,'edge_index',np.array([[0,0,2],[1,1,0]],dtype=np.int64))
fresh=graph();object.__setattr__(fresh,'node_features',AttributedGraph(fresh.node_ids,np.ones((3,1)),fresh.edge_index,fresh.edge_features,fresh.parent_hash,fresh.center_id).node_features)
for label,g,c,s in [('graph_first',bad,{**cfg,'solver':'bad'},{}),('config',a,{**cfg,'solver':'bad'},seed),('fresh_bytes',fresh,cfg,seed),('state',a,cfg,{**seed,'safe':False})]:
 e=error(B,s,g,c);ck('error_'+label,e is not None and e==error(C,s,g,c))
try:I.graph_identity(bad)
except ValueError as e:ck('public_graph_validation_preserved','duplicate' in str(e))
else:raise AssertionError('public invalid graph accepted')
x=copy.deepcopy(seed);y=copy.deepcopy(seed)
for limit in [10,1000]:
 u=B.advance(x,a,b,cfg,max_operations=limit);v=C.advance(y,a,b,cfg,max_operations=limit)
 ck('operations_state_'+str(limit),u==v and all(x[k].tobytes()==y[k].tobytes() if isinstance(x[k],np.ndarray) else x[k]==y[k] for k in x))
ck('no_persistent_state',x.keys()==seed.keys()==y.keys())
out={'decision':'accepted-source-only','source_sha256':{f:manifest[f] for f in ['matching_identity.py','matching_annealing.py','baseline_matching_identity.py','baseline_matching_annealing.py']},'checks':checks,'qualification':'Exact public validation and current-byte encoding retained; check reuses only its immediately preceding pair validation in exact immutable graph/plain config/state domain. No cross-call cache or changed arithmetic/RNG/checkpoint functions. Observational profiling used only to count original validator calls. Existing exclusive ownership/frozen runtime assumption required: arbitrary transitive global/helper/code mutation, malicious state field callbacks, concurrent mutation and fenv changes are not certified. Removed duplicate validation allocations and added eligibility operations alter resource/asynchronous failure boundaries; no universal MemoryError/error-trace equivalence or speedup claim. No scientific data, source installation, entry release, authority or launch.' ,'resources':{'seconds':30,'AS_bytes':256*1024**2,'FSIZE_bytes':4*1024**2,'affinity':sorted(os.sched_getaffinity(0)),'nice':10}}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(checks),'sha256':sha(H/'SOURCE_REVIEW01.json')}))
