import ast,contextlib,copy,hashlib,json,os,resource,signal,struct,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent;G=F/'matching-real-geometry-instrumentation01-2026-10-09';OLD=F/'matching-real-geometry-publication01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(30);started=time.monotonic_ns();(P/'LIMITER01.json').write_text(json.dumps({'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':30},indent=2)+'\n');assert os.sched_getaffinity(0)=={3}
W=P/'fixtures';W.mkdir();trace=[];failure=None
sources=json.loads((P/'SOURCE_MAP01.json').read_text())
for name,edits in json.loads((P/'CHANGES01.json').read_text()).items():
 text=(P/name).read_text()
 for a,b in reversed(edits):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(R/sources[name]['path']).read_text()
def require(ok,msg):
 if not ok:raise ValueError(msg)
# Actual observer + Binding lease; only filesystem/guard metadata doubles, no authority.
t=ast.parse((P/'matching_owner.py').read_text());nodes=[]
for n in t.body:
 if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and (a.id.startswith('_LEASE_TIMING_') or a.id=='BINDING_TIMING_POLICY') for a in n.targets):nodes.append(n)
 elif isinstance(n,ast.ClassDef) and n.name=='BindingLeaseTiming':nodes.append(n)
 elif isinstance(n,ast.FunctionDef) and n.name.startswith('binding_timing_'):nodes.append(n)
 elif isinstance(n,ast.ClassDef) and n.name=='Binding':nodes.append(ast.ClassDef(name='Binding',bases=[],keywords=[],decorator_list=[],body=[m for m in n.body if isinstance(m,ast.FunctionDef) and m.name=='lease']))
mo={'time':time,'contextmanager':contextlib.contextmanager,'require':require,'Path':Path,'json':json,'metadata':lambda p,r:({},'pin'),'ancestry':types.SimpleNamespace(verify=lambda *a,**kw:None)};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual_binding_and_observer','exec'),mo);matching=types.SimpleNamespace(**mo)
t=ast.parse((P/'compact_owner.py').read_text());cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Owner');cl.body=[n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name in ('select_binding_timing','lease')];ons={'matching_owner':matching,'require':require,'Path':Path,'cache_key':lambda x:'cfg','present':lambda p:p.exists(),'exact':lambda *a:trace.append('owner.exact')};exec(compile(ast.fix_missing_locations(ast.Module(body=[cl],type_ignores=[])),'actual_owner_methods','exec'),ons);Owner=ons['Owner']
def owner(name):
 base=W/name;base.mkdir();parent=base/'journals';parent.mkdir();journal=parent/'one';journal.mkdir();root=base/'owner';root.mkdir()
 b=mo['Binding']();b._run=types.SimpleNamespace(_active=lambda:trace.append('run.active'),admission=types.SimpleNamespace(root=base));b.record={'journal_directory':str(journal)};b._ancestry_arguments=None;b._snapshots={'x':'pin'};b._guard=lambda:trace.append('guard')
 o=Owner();o.bound=b;o.poisoned=o.closed=o.closing=False;o.check_binding=lambda:trace.append('owner.binding');o.configuration=lambda:{};o.configuration_sha256='cfg';o.reserved=o._reserved=0;o.root=root;o.inode=(root.stat().st_dev,root.stat().st_ino);o.required=('fixture',);o.start={};return o

# Synthetic authority metadata only: extracted original methods, no real Owner/Run.
import importlib
sys.path.insert(0,str(R))
import numpy as np
base='tradingagents.research.onchain_replication';package=base+'.composed_fixture';pkg=types.ModuleType(package);pkg.__path__=[str(P),str(R/'tradingagents/research/onchain_replication')];sys.modules[package]=pkg
for name in ('contracts','checkpoint_chunks','matching_identity','matching_hardening','matching_sparse'):sys.modules[package+'.'+name]=importlib.import_module(base+'.'+name)
sys.modules[package+'.matching_owner']=matching;sys.modules[package+'.compact_owner']=types.SimpleNamespace(Owner=Owner)
new=importlib.import_module(package+'.batched_numeric_execution');helper=importlib.import_module(package+'.adaptive_edge_policy')
from tradingagents.research.onchain_replication import compact_policy
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());stage=json.loads((F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_text())['stage_policy'];c=compact_policy.effective_matching(c,stage['pair']);p=compact_policy.pair_policy(stage['pair']);schedule=stage['schedule']
def graph(n,edges):
 e=np.array([(i,j) for i in range(n) for j in range(n)][:edges],dtype=np.int64).T.copy();return AttributedGraph(tuple(str(i) for i in range(n)),np.arange(n,dtype=np.float64).reshape(-1,1)*.01,e,np.arange(edges,dtype=np.float64).reshape(-1,1)*.002,'a'*64,'0')
a,b=graph(8,64),graph(16,128);selection=dict(new.reuse.engine.ann.ADAPTIVE_EDGE_POLICY)
results={};checks=[];sizes=[]
for name,selected in [('default',False),('all_selected',True)]:
 o=owner(name);root=W/name/'stream';root.mkdir();kw={}
 if selected:
  o.select_binding_timing(dict(mo['BINDING_TIMING_POLICY']));kw={'binding_timing':dict(mo['BINDING_TIMING_POLICY']),'binding_owner':o,'geometry':dict(new.geometry_publication.POLICY),'edge_cache_policy':selection}
 ex=new.NumericExecution(root,c,p,schedule,lambda *a:None,cells=2,batch_cells=2,max_origin_bytes=18,max_summary_bytes=8192,max_entries=8,max_retained_bytes=262144,max_key_bytes=131072,authority_poll=o.lease,**kw)
 try:
  out=[ex(a,b,hashlib.sha256(str(i).encode()).hexdigest()) for i in range(2)]
  assert ex.memo.computed==1 and ex.memo.reused==1
  snapshot=ex._timing_snapshot
  if selected:o.lease()
  binding=ex.finish();new.verify(root,binding);body=(root/'numeric-batches/000000000000.json').read_bytes();s=json.loads(body);sizes.append(len(body));results[name]=out
  if selected:
   assert ex._timing_snapshot is snapshot and s['counters']==binding['counters'];assert s['geometry']['computed']==1 and s['geometry']['reused']==1;assert s['edge_cache_policy']==selection
   assert o._binding_timing.snapshot()['binding_first_guard_calls']==binding['counters']['binding_first_guard_calls']+1
   bad=copy.deepcopy(binding);bad['edge_cache_policy']['chunk_entries']=512
   try:new.verify(root,bad)
   except ValueError:pass
   else:raise AssertionError('malformed policy accepted')
   (root/'numeric-batches/000000000000.json').write_bytes(body+b' ')
   try:new.verify(root,binding)
   except ValueError:pass
   else:raise AssertionError('mutated summary accepted')
  else:assert 'geometry' not in s and 'edge_cache_policy' not in s and 'binding_first_guard_calls' not in s['counters']
 finally:ex.close()
assert results['default']==results['all_selected'];checks.append('actual computed/reuse engine chain; default/all-selected score tuple equal; durable combined summary under8192; frozen timing finish; malformed policy and body mutation refused')
# Actual adapter validation, independently selectable optional policies.
t=ast.parse((P/'compact_mcm_batched.py').read_text());ns={'require':require,'adaptive_edge_policy':helper,'geometry_publication':new.geometry_publication,'matching_owner':matching,'FORMAT':'ordered-mcm-batch-closure-v2'};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('selected','validate')],type_ignores=[]),'actual_adapter','exec'),ns)
# Parent validator fixtures are inherited; strict helper selection checked here.
for validator,value in [(helper.freeze,dict(selection,chunk_entries=512)),(new.geometry_publication.policy,dict(new.geometry_publication.POLICY,max_body_bytes=1537)),(matching.binding_timing_policy,dict(mo['BINDING_TIMING_POLICY'],max_body_bytes=True))]:
 try:validator(value)
 except ValueError:pass
 else:raise AssertionError('malformed selection accepted')
o=owner('mutation');obs=o.select_binding_timing(dict(mo['BINDING_TIMING_POLICY']));obs.clock=lambda:0
try:o.lease()
except ValueError:pass
else:raise AssertionError('mutated clock accepted')
checks.append('strict independent policies and observer clock mutation refuse')
(P/'RESULT01.json').write_text(json.dumps({'status':'PASS_SYNTHETIC_NO_AUTHORITY','checks':checks,'results':results,'summary_bytes':sizes,'elapsed_ns':time.monotonic_ns()-started,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'qualification':'Actual numeric engine and durable summaries; AST-extracted Owner/Binding methods with metadata doubles are not genuine authority.'},indent=2)+'\n');print('PASS',sizes)
