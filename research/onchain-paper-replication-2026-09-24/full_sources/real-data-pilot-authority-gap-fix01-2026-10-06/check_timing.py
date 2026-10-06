"""Actual constructor AST with explicit tiny stand-ins and a deterministic clock.
No actual Target/Owner/Lease capability, graph array, lifecycle or empirical run.
"""
import ast,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from tradingagents.research.onchain_replication import imported_authority_interval as intervals, imported_authority_lease
D=Path(__file__).resolve().parent
policy=dict(schema_version=1,kind=intervals.KIND,live_interval_ms=1000,fingerprint_interval_ms=5000,full_interval_ms=10000,max_stale_ms=30000,max_calls_between_full=1000,assumption=intervals.ASSUMPTION)
def scenario(which,hash_seconds=20,initial_gap=0,full_seconds=1,legacy=False):
 clock=[0.];scheduler=intervals.Interval(policy,clock=lambda:clock[0]);scheduler.validate(lambda:None,lambda:None,lambda:None,boundary=True);clock[0]=initial_gap;events=[]
 def advance(label,seconds):events.append(label);clock[0]+=seconds
 def checkpoint(execution,*,boundary=False):
  assert boundary;events.append('checkpoint')
  scheduler.validate(lambda:advance('full',full_seconds),lambda:None,lambda:None,boundary=boundary)
 class Execution:
  def check(self):advance('execution',8);return {'identity':'fixed'}
 class Graph:node_ids=('tiny',)
 key='a'*64;execution=Execution();graph=Graph()
 if not legacy:execution._sampled_authority_lease=object()
 execution._owner=SimpleNamespace(bound=SimpleNamespace(_run=SimpleNamespace(admission=SimpleNamespace(inputs={'graph':{'sha256':'b'*64}}))))
 execution._materialized=SimpleNamespace(_dictionary=SimpleNamespace(representatives=()))
 execution._stage=SimpleNamespace(reference='c'*64,prepared=SimpleNamespace(_selection={'selected':{'descriptor':{'required_graphs':[key],'resource_graph_inputs':{key:'graph'}}}}))
 def read(*a):advance('manifest',2);return b'fixed manifest'
 def graph_hash(g):assert g is graph;advance('hash',hash_seconds);return key
 def order(ids):advance('order',5);return 'd'*64
 tree=ast.parse((D/which/'imported_mcm_identity.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Target')
 init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
 selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_checkpoint']+[init]
 env={'__name__':'tradingagents.research.onchain_replication.synthetic_constructor','__package__':'tradingagents.research.onchain_replication','original_import_stage':SimpleNamespace(ImportedExecution=Execution),'GraphSnapshot':Graph,'require':lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg)),'canonical_bytes':lambda x:json.dumps(x,sort_keys=True).encode(),'original_dictionary':SimpleNamespace(_read_registered=read,parse=lambda x:{'graph_hash':key}),'graph_hash':graph_hash,'node_order_hash':order,'graph_identity':lambda x:'e'*64}
 exec(compile(ast.Module(body=selected,type_ignores=[]),'actual-constructor-AST','exec'),env)
 class TinyTarget:
  _arrays=lambda self:()
  def derive_scope(self):advance('scope',2);return {'fixed':True}
  def check(self):
   events.append('target-check')
   if not legacy:scheduler.validate(lambda:None,lambda:None,lambda:None,boundary=True)
 target=TinyTarget()
 try:
  with patch.object(imported_authority_lease,'check',checkpoint):env['__init__'](target,execution,graph,key)
 except ValueError as error:return {'accepted':False,'reason':str(error),'events':events,'clock':clock[0],'closed':scheduler.closed}
 return {'accepted':True,'events':events,'clock':clock[0],'closed':scheduler.closed}
results={}
results['baseline_gap']=scenario('baseline');assert not results['baseline_gap']['accepted']
results['candidate_completed_phases']=scenario('candidate');assert results['candidate_completed_phases']['accepted']
for key,kw in [('single_hash_too_slow',{'hash_seconds':31}),('already_stale',{'initial_gap':31}),('full_check_too_slow',{'full_seconds':31})]:
 results[key]=scenario('candidate',**kw);assert not results[key]['accepted'] and results[key]['closed']
results['legacy_no_sampling']=scenario('candidate',legacy=True);assert results['legacy_no_sampling']['accepted'] and 'checkpoint' not in results['legacy_no_sampling']['events']
print(json.dumps({'results':results,'qualification':'simulated durations prove control placement, not real graph throughput or genuine activation'},indent=2))
