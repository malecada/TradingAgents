import ast,copy,hashlib,importlib.util,json,os,resource,signal,sys
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;C=H.parent/'matching-immutable-session01-2026-10-09';sys.path.insert(0,str(R));P='tradingagents.research.onchain_replication.'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,file):
 sp=importlib.util.spec_from_file_location(P+name,C/file);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
import numpy as np
from tradingagents.research.onchain_replication import matching_checkpoint as baseline
from tradingagents.research.onchain_replication.contracts import AttributedGraph
ann=load('_independent_immutable_ann','matching_annealing.py');engine=load('_independent_immutable_checkpoint','matching_checkpoint.py');engine.ann=ann;adapter=load('_independent_immutable_pair','immutable_pair.py')
a=AttributedGraph(node_ids=('x','y'),node_features=np.array([[.1],[.7]]),edge_index=np.array([[0],[1]],dtype=np.int64),edge_features=np.array([[.2]]),parent_hash='a'*64,center_id='x')
b=AttributedGraph(node_ids=('z',),node_features=np.array([[.3]]),edge_index=np.empty((2,0),dtype=np.int64),edge_features=np.empty((0,1)),parent_hash='b'*64,center_id='z')
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());policy=dict(max_state_bytes=1048576,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=1048576)
s=adapter.ImmutablePairSession(a,b,c,engine=engine,annealing=ann);state=engine.create(a,b,c,**policy);left=baseline.create(a,b,c,**policy);calls=[]
original=engine.ann;proxy=SimpleNamespace(**vars(ann))
def skipped(inner,a,b,c,*,max_operations):calls.append(max_operations);return max_operations
proxy._advance_checked=skipped;engine.ann=proxy
before=(state['annealing']['phase'],state['annealing']['cursor'],tuple(state['annealing'][k].tobytes() for k in ('V','M','Q')))
try:
 try:result=s.advance(state,max_operations=1)
 except ValueError as error:outcome={'refused':True,'error':str(error)}
 else:
  baseline.advance(left,a,b,c,max_operations=1)
  after=(state['annealing']['phase'],state['annealing']['cursor'],tuple(state['annealing'][k].tobytes() for k in ('V','M','Q')))
  assert before==after and calls==[1] and left['annealing']['cursor']!=state['annealing']['cursor']
  outcome={'refused':False,'replacement_function_called':True,'returned_operations':result,'candidate_cursor':state['annealing']['cursor'],'baseline_cursor':left['annealing']['cursor'],'safe':state['safe'],'numeric_state_unchanged':True}
finally:engine.ann=original;engine.close(state);baseline.close(left);s.close()
# Private numerical body extraction is AST-identical after removing its docstring.
x=ast.parse((R/'tradingagents/research/onchain_replication/matching_checkpoint.py').read_text());y=ast.parse((C/'matching_checkpoint.py').read_text())
f=lambda t,n:next(k for k in t.body if isinstance(k,ast.FunctionDef) and k.name==n)
assert [ast.dump(k) for k in f(x,'advance').body[2:]]==[ast.dump(k) for k in f(y,'_advance_owned').body[1:]]
result={'candidate_sources':{p.name:sha(p) for p in C.glob('*.py') if p.name in ['matching_annealing.py','matching_checkpoint.py','immutable_pair.py']},'baseline_checkpoint_sha256':sha(R/'tradingagents/research/onchain_replication/matching_checkpoint.py'),'numerical_body_AST_identical':True,'module_rebinding_reproducer':outcome,'scope':'Synthetic one-operation source seam only; no authority, empirical workload or timing claim.'}
(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
