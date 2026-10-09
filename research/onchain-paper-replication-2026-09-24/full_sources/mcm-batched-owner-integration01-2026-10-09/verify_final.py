"""Synthetic integration only: real index/journal/driver/output; no Owner claims."""
import os,resource,signal,sys,importlib.util,json,hashlib,ast,gc,weakref
from pathlib import Path
from types import SimpleNamespace,ModuleType
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;sys.path.insert(0,str(R));package='tradingagents.research.onchain_replication'
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
# Isolate only heavy authority imports: no fabricated Owner/Target instances.
from tradingagents.research.onchain_replication import score_batches as io
m=ModuleType(package+'.compact_mcm_batched');m.__package__=package;m.__file__=str(H/'compact_mcm_batched.py');sys.modules[m.__name__]=m
source=ast.parse((H/'compact_mcm_batched.py').read_text())
source.body=[n for n in source.body if not (isinstance(n,ast.ImportFrom) and n.module is None and any(x.name in ('compact_owner','compact_mcm_publication') for x in n.names))]
m.io=io
exec(compile(source,m.__file__,'exec'),m.__dict__)
def actual_function(file,name,namespace):
 tree=ast.parse(file.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),str(file),'exec'),namespace);return namespace[name]
ns={'io':io,'os':os,'require':io._require};entries=actual_function(R/'tradingagents/research/onchain_replication/compact_owner.py','entries',ns)
m.owners=SimpleNamespace(entries=entries)
m.producer=SimpleNamespace(ROOT=R)
output=load(package+'.batched_output_test',H/'compact_mcm_output.py')
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,AttributedGraph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.provenance import thaw
m.producer._matrix=actual_function(R/'tradingagents/research/onchain_replication/compact_mcm.py','_matrix',{'np':np,'hashlib':hashlib,'require':io._require})
mods=m._modules(R);base=mods['driver'].ArrayNeighborhoodIndex;refs=[];indices=[]
class Index(base):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);indices.append(self)
 def neighborhood(self,*a,**kw):
  gc.collect();assert not refs or refs[-1]() is None
  x=super().neighborhood(*a,**kw);refs.append(weakref.ref(x));return x
mods['driver'].ArrayNeighborhoodIndex=Index
# Deterministic routing callback, deliberately NOT scientific engine equality.
class Executor:
 def __init__(self,c,p,s,callback):self.count=0;self.callback=callback;self.config=c;self.policy=p
 def __call__(self,a,b,purpose):
  if self.count==0:
   state=m.engine.create(a,b,self.config,**{k:self.policy[k] for k in ('max_state_bytes','normalization_chunk_entries','hardening_chunk_entries','hardening_buffer_bytes')})
   try:self.callback(purpose,0,state,a,b,self.config,self.policy)
   finally:m.engine.close(state)
  self.count+=1;return (self.count-1)/64.,1,'iteration_cap'
mods['executor']=SimpleNamespace(PairExecutor=Executor)
g=GraphSnapshot('ETH','2022-01-03T00:00:00Z','2022-01-10T00:00:00Z','2022-01-10T00:00:00Z',('a'*64,),'b'*64,('a','b'),np.ones((2,4)),np.array([[0],[1]],dtype=np.int64),np.ones((1,2)),1,1,{})
motifs=tuple(AttributedGraph(('m',),np.ones((1,4)),np.empty((2,0),dtype=np.int64),np.empty((0,2)),'c'*64,'m') for _ in range(32));dictionary=SimpleNamespace(representatives=motifs,config={'hop_depth':1,'maximum_neighborhood_nodes':2})
root=H/'final-checkpoint-stage';root.mkdir();(root/'intent.json').write_text('{}\n');st=root.stat();stage=SimpleNamespace(root=root,inode=(st.st_dev,st.st_ino));target=SimpleNamespace(dictionary=dictionary,owner=SimpleNamespace(policy={'pair':{'max_state_bytes':1048576,'normalization_chunk_entries':64,'hardening_chunk_entries':64,'hardening_buffer_bytes':1048576,'max_checkpoint_bytes':524288},'schedule':{}},matching=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text())))
scope={'graph':graph_hash(g),'node_order':node_order_hash(g.node_ids),'dictionary':'a'*64,'ordered_motifs':'b'*64,'matching':'c'*64,'workflow':'d'*64}
policy={'schema_version':3,'max_entries':64,'max_workflow_metadata_bytes':65536,'numeric':{'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3},'batched':{'format':m.FORMAT,'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':48,'max_journal_bytes':200000,'max_body_bytes':1024,'max_closure_token_bytes':336,'max_checkpoint_bytes':1000000}}
start={'rows':2,'cells':64,'motifs':32,'graph_hash':graph_hash(g),'scope':scope};boundaries=[]
binding=m._compute(target,stage,g,policy,start,mods,lambda:boundaries.append('boundary'))
assert binding['checkpoint_count']==1 and binding['checkpoint_inventory']['files']>1
contract={'owner':'e'*64,'scope':{},'policy':{},'kind':'mcm','pairs':64,'batched':binding};raw=m.io._json(contract);(root/'stage-complete.json').write_bytes(raw);reference=hashlib.sha256(raw).hexdigest()
result=m.verify_content(root,contract,reference,mods);assert result['completed_pairs']==64 and binding['batches']==2 and indices[-1].closed;gc.collect();assert refs[-1]() is None
args={'stage_root':root,'stage_sha256':reference,'contract':contract,'expected_scope':scope,'max_output_bytes':65536}
artifact=H/'final-checkpoint-output';digest=output.publish(artifact,**args,lease=lambda:None)
output.verify(artifact,expected_sha256=digest,**args,lease=lambda:None)
with output.open_verified(artifact,expected_sha256=digest,**args,lease=lambda:None) as matrix:
 assert matrix.tobytes()==np.asarray([i/64. for i in range(64)],dtype='<f4').tobytes() and matrix.shape==(2,32)
# Existing mmap can back the exact ndarray type expected by existing Produced.
f=os.open(artifact/'matrix.f32',os.O_RDONLY);mapped=m.mmap.mmap(f,0,access=m.mmap.ACCESS_READ);os.close(f);view=np.ndarray((2,32),dtype='<f4',buffer=mapped);assert m.producer._matrix(view,2,32)==hashlib.sha256(view.tobytes()).hexdigest();del view;mapped.close()
for case in ('bad-token','bad-output'):
 if case=='bad-token':p=root/'stream/closure-tokens.bin'
 else:p=artifact/'matrix.f32'
 old=p.read_bytes();p.write_bytes(b'X'+old[1:])
 try:output.verify(artifact,expected_sha256=digest,**args,lease=lambda:None)
 except ValueError:pass
 else:raise AssertionError(case+' admitted')
 p.write_bytes(old)
# Public producer's first executable authority check is retained verbatim; not
# executed with fake capabilities or imported neural dependencies in this harness.
prod=next(n for n in ast.parse((H/'compact_mcm_batched.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='produce')
assert isinstance(prod.body[0],ast.ImportFrom) and 'genuine imported Target required' in ast.unparse(prod.body[1])
# Failure after some computed cells: original error, index/journal descriptors closed.
class ThrowExecutor(Executor):
 def __call__(self,a,b,purpose):
  if self.count==3:raise RuntimeError('synthetic numeric route failure')
  return super().__call__(a,b,purpose)
mods['executor']=SimpleNamespace(PairExecutor=ThrowExecutor)
failure_root=H/'failure-stage';failure_root.mkdir();st=failure_root.stat();failure_stage=SimpleNamespace(root=failure_root,inode=(st.st_dev,st.st_ino));before=len(list(Path('/proc/self/fd').iterdir()))
try:m._compute(target,failure_stage,g,policy,start,mods,lambda:None)
except RuntimeError as error:assert str(error)=='synthetic numeric route failure'
else:raise AssertionError('failure swallowed')
assert indices[-1].closed and len(list(Path('/proc/self/fd').iterdir()))==before
assert (failure_root/'matching/00000000.pending.json').exists() and not (failure_root/'matching/00000000.complete.json').exists()
assert list((failure_root/'checkpoints').glob('*/manifest.json'))
for p in H.glob('*.py'):ast.parse(p.read_text())
report={'synthetic_only':True,'real_apis':['ArrayNeighborhoodIndex','journal03','driver03','compact_mcm_output.publish/verify/open_verified','compact_mcm._matrix'],'cells':64,'batch_count':2,'one_live_local':True,'failure_cleanup_and_checkpoint_retention':True,'boundary_calls':len(boundaries),'actual_checkpoint_count':binding['checkpoint_count'],'checkpoint_inventory':binding['checkpoint_inventory'],'corruption_refusals':['token','output'],'genuine_target_guard_source_checked':True,'genuine_owner_admission_proved':False,'numerical_equivalence_tested':False,'affinity':sorted(os.sched_getaffinity(0))}
(H/'FINAL_RESULT01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
