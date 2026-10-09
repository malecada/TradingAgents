import ast,contextlib,copy,hashlib,json,os,resource,signal,struct,sys,time,types
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent/'matching-adaptive-measurement-stack01-2026-10-09';R=P.parents[3];F=P.parent;G=F/'matching-real-geometry-instrumentation01-2026-10-09';OLD=F/'matching-real-geometry-publication01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(30);started=time.monotonic_ns();(D/'LIMITER01.json').write_text(json.dumps({'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':30},indent=2)+'\n');assert os.sched_getaffinity(0)=={3}
W=D/'fixtures';W.mkdir();trace=[];failure=None
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

# Independent composition cases; bootstrap above reuses original source-extraction loader only.
a,b=graph(3,5),graph(4,7)
def make(label):
 o=owner(label);root=W/label/'stream';root.mkdir();o.select_binding_timing(dict(mo['BINDING_TIMING_POLICY']))
 ex=new.NumericExecution(root,c,p,schedule,lambda *a:None,cells=2,batch_cells=2,max_origin_bytes=18,max_summary_bytes=8192,max_entries=8,max_retained_bytes=262144,max_key_bytes=131072,authority_poll=o.lease,binding_timing=dict(mo['BINDING_TIMING_POLICY']),binding_owner=o,geometry=dict(new.geometry_publication.POLICY),edge_cache_policy=dict(selection))
 return o,root,ex
o,root,ex=make('combined');downgrades={}
try:
 for i in range(2):ex(a,b,hashlib.sha256(('independent'+str(i)).encode()).hexdigest())
 frozen=ex._timing_snapshot;o.lease();binding=ex.finish();new.verify(root,binding)
 assert frozen is ex._timing_snapshot
 s=json.loads((root/'numeric-batches/000000000000.json').read_bytes());assert s['geometry']['computed']==1 and s['geometry']['reused']==1 and s['counters']==binding['counters']
 for field in ('edge_cache_policy','geometry','binding_timing'):
  altered=copy.deepcopy(binding);del altered[field]
  try:new.verify(root,altered)
  except (ValueError,KeyError) as e:downgrades[field]={'refused':True,'error':str(e)}
  else:downgrades[field]={'refused':False}
 (D/'ORIGINAL_BINDING01.json').write_text(json.dumps(binding,indent=2)+'\n')
finally:ex.close()
o,root,ex=make('cross_overlay_drift')
try:
 ex(a,b,hashlib.sha256(b'first').hexdigest());ex.memo.executor._edge_cache_policy=None
 try:ex(a,b,hashlib.sha256(b'second').hexdigest())
 except ValueError:pass
 else:raise AssertionError('cross-overlay hit mutation accepted')
 assert ex.poisoned and not list((root/'numeric-batches').iterdir()) and (root/'numeric-origins.bin').stat().st_size==0
finally:ex.close()
out={'status':'COMPLETED_FOCUSED_COMPOSITION_CHECK','downgrade_checks':downgrades,'frozen_timing_after_additional_owner_call':True,'geometry_completed_computed_reused':[1,1],'cross_overlay_edge_cache_hit_mutation_poison':True,'summary_bytes':len(new.raw(s)),'qualification':'Source-extracted actual Owner/Binding metadata doubles; no genuine authority. Original bootstrap loader reused; tests independently authored.'}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
