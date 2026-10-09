import ast,contextlib,copy,hashlib,json,os,resource,signal,struct,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent;G=F/'matching-real-geometry-instrumentation01-2026-10-09';OLD=F/'matching-real-geometry-publication01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(k,(v,v))
signal.alarm(30);started=time.monotonic_ns();(P/'LIMITER01.json').write_text(json.dumps({'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':30},indent=2)+'\n');assert os.sched_getaffinity(0)=={3}
W=P/'fixtures';W.mkdir();trace=[];failure=None
changes=json.loads((P/'CHANGES01.json').read_text());sources=json.loads((P/'SOURCE_MAP01.json').read_text())
for name,edits in changes.items():
 text=(P/name).read_text()
 for a,b in reversed(edits):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(R/sources[name]).read_text()
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
geom=types.ModuleType('geometry');exec(compile((G/'geometry_summary.py').read_text(),str(G/'geometry_summary.py'),'exec'),geom.__dict__)
pub=types.ModuleType('pub');pub.__dict__.update({k:getattr(geom,k) for k in ('BINS','NAMES','LIMIT','raw','require')});tree=ast.parse((P/'geometry_publication.py').read_text());tree.body=[n for n in tree.body if not isinstance(n,ast.ImportFrom)];exec(compile(tree,'actual_geometry_publication','exec'),pub.__dict__)
ct=ast.parse((G/'batched_numeric_reuse.py').read_text());cl=next(n for n in ct.body if isinstance(n,ast.ClassDef));end=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='end_batch');ns={'require':require,'attest':lambda counters:trace.append('attest')};exec(compile(ast.Module(body=[end],type_ignores=[]),'actual_end_batch','exec'),ns)
active_owner=None
class Memo:
 def __init__(self,*args,geometry=False,max_geometry_summary_bytes=8192,**kw):
  self._geometry=geom.Geometry(max_geometry_summary_bytes) if geometry else None;self.last_geometry_summary=None;self.counters={'source_guard_calls':0};self.occurrences=self.computed=self.reused=0;self.active=self.poisoned=self.closed=False;self.last_receipt=None
 def _current(self):
  if active_owner is not None:active_owner.lease()
  trace.append('current')
  if failure=='attest':raise ValueError('fixture attestation refused')
 def begin_batch(self):
  self.active=True
  if self._geometry:self._geometry_counts=(self.computed,self.reused);self.last_geometry_summary=None;self._geometry.begin(self.occurrences)
 end_batch=ns['end_batch']
 def __call__(self,a,b,purpose):
  i=self.occurrences;v=(.5,48,'temperature_complete');self.last_receipt={'schema_version':2,'kind':'engineering_numeric_occurrence','ordinal':i,'purpose_sha256':purpose,'mode':'computed','origin_purpose_sha256':purpose,'origin_ordinal':i,'score_f64_be':struct.pack('>d',.5).hex(),'iterations':48,'convergence':v[2],'cached':True,'checkpoint_attempt_delta':0,'checkpoint_reserved_byte_delta':0,'retained_cache_bytes':1024,'old_per_occurrence_execution_credit':False,'boundary_validated_batch_complete':False}
  if self._geometry:self._geometry.add(a,b,self.last_receipt)
  self.occurrences+=1;self.computed+=1;return v
 def _poison(self):
  self.poisoned=True;self.active=False;self.last_geometry_summary=None
  if self._geometry:self._geometry.poison()
 def close(self):self.closed=True
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None if n.level else n
def module(path):
 t=Strip().visit(ast.parse(path.read_text()));n={'reuse':types.SimpleNamespace(NumericReuseExecutor=Memo),'geometry_publication':pub,'matching_owner':matching,'compact_owner':types.SimpleNamespace(Owner=Owner)};exec(compile(t,str(path),'exec'),n);n['time']=types.SimpleNamespace(perf_counter=lambda:1.0);return types.SimpleNamespace(**n)
old=module(OLD/'batched_numeric_execution.py');new=module(P/'batched_numeric_execution.py');a=types.SimpleNamespace(node_ids=('a','b'),edge_index=types.SimpleNamespace(shape=(2,2)));b=a
policy=dict(mo['BINDING_TIMING_POLICY'])
def create(name,mod,timed=False,geometry=False,allowance=16384):
 global active_owner
 o=owner(name);active_owner=o
 if timed:o.select_binding_timing(policy)
 root=W/name/'stream';root.mkdir();kw={}
 if timed:kw.update(binding_timing=policy,binding_owner=o)
 if geometry:kw['geometry']=pub.POLICY
 return root,o,mod.NumericExecution(root,{}, {}, {},lambda *a:None,cells=4,batch_cells=2,max_origin_bytes=36,max_summary_bytes=allowance,max_entries=8,max_retained_bytes=65536,max_key_bytes=32768,**kw)
outputs={};checks=[]
for name,mod,timed,geometry in [('baseline',old,False,False),('none',new,False,False),('selected',new,True,True)]:
 root,o,ex=create(name,mod,timed,geometry)
 try:
  for i in range(4):ex(a,b,hashlib.sha256(str(i).encode()).hexdigest())
  before=ex._timing_snapshot if timed else None
  if timed:o.lease() # Counters accrue after final end_batch, must not alter finish snapshot.
  binding=ex.finish();mod.verify(root,binding);outputs[name]=[(root/'numeric-batches'/f'{i:012d}.json').read_bytes() for i in range(2)]
  if timed:
   assert ex._timing_snapshot is before and binding['counters']['binding_first_guard_calls']==2 and o._binding_timing.snapshot()['binding_first_guard_calls']==3
   assert all(len(x)<=8192 and 'geometry' in json.loads(x) for x in outputs[name]);(P/'SELECTED_BINDING01.json').write_text(json.dumps(binding,indent=2)+'\n')
 finally:ex.close()
assert outputs['baseline']==outputs['none'];checks.append('default summaries byte-identical; selected actual publisher/verifier closes combined geometry/timing under8192')
checks.append('actual end_batch precedes snapshot; finish retains last snapshot despite later owner lease')
for mutation in ('clock','counters'):
 o=owner('mutate-'+mutation);obs=o.select_binding_timing(policy)
 if mutation=='clock':obs.clock=lambda:0
 else:obs._totals=(1,)*12
 try:o.lease()
 except ValueError:pass
 else:raise AssertionError('mutation accepted')
checks.append('actual Owner forwarding rejects observer clock and valid-shaped counter replacement')
for bad in (False,{'format':policy['format'],'max_body_bytes':True},{**policy,'extra':1},{**policy,'max_body_bytes':641}):
 try:mo['binding_timing_policy'](bad)
 except ValueError:pass
 else:raise AssertionError('selection accepted')
checks.append('strict fixed selected policy refuses false/bool/extra/cap widening')
# Actual constructor reserve check occurs before opening any numeric files.
o=owner('underreserved');o.select_binding_timing(policy);root=W/'underreserved'/'stream';root.mkdir()
try:new.NumericExecution(root,{}, {}, {},None,cells=4,batch_cells=2,max_origin_bytes=36,max_summary_bytes=16383,max_entries=8,max_retained_bytes=65536,max_key_bytes=32768,binding_timing=policy,binding_owner=o)
except ValueError:pass
else:raise AssertionError('underreserved accepted')
assert not list(root.iterdir());checks.append('8192 per batch reservation refused before numeric allocation')
for name,kind in [('failed-attestation','attest'),('combined-cap','cap')]:
 root,o,ex=create(name,new,True,True)
 try:
  ex(a,b,hashlib.sha256(b'0').hexdigest())
  if kind=='attest':failure='attest'
  else:ex.memo.counters['x'*8200]=0
  try:ex(a,b,hashlib.sha256(b'1').hexdigest())
  except ValueError:pass
  else:raise AssertionError('refusal missing')
  assert not list((root/'numeric-batches').iterdir()) and (root/'numeric-origins.bin').stat().st_size==0
  if kind=='attest':assert ex._timing_snapshot is None
 finally:failure=None;ex.close()
checks.append('failed end attestation and combined body cap refuse before origin/summary writes')
# Strict adapter policy branch executed with metadata only; no actual producer/Owner.
t=ast.parse((P/'compact_mcm_batched.py').read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('selected','validate')];vn={'require':require,'geometry_publication':pub,'matching_owner':matching,'FORMAT':'ordered-mcm-batch-closure-v2'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_adapter_policy','exec'),vn)
bounds={'format':vn['FORMAT'],'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':2,'group_batches':16,'max_journal_bytes':10000,'max_body_bytes':1024,'max_closure_token_bytes':336,'max_checkpoint_bytes':1,'retention':'typed-grouped-recover-before-retire-v1','max_spool_bytes':16,'max_offload_metadata_bytes':1,'max_offload_entries':1,'max_offload_anchor_bytes':32,'execution':{'route':'immutable-input-session+exact-byte-reuse-v1','max_entries':8,'max_retained_bytes':65536,'max_key_bytes':32768,'max_origin_bytes':36,'max_summary_bytes':16384,'geometry':dict(pub.POLICY),'binding_timing':policy}}
v={'schema_version':6,'max_entries':1,'max_workflow_metadata_bytes':1,'numeric':{},'batched':bounds};vn['validate'](v,4)
w=copy.deepcopy(v);w['batched']['execution']['binding_timing']=False
try:vn['validate'](w,4)
except ValueError:pass
else:raise AssertionError('adapter invalidselection accepted')
checks.append('actual selected schema6 adapter metadata branch verified')
result={'status':'PASS_SYNTHETIC_CONNECTED_METADATA_ONLY','checks':checks,'combined_summary_bytes':[len(x) for x in outputs['selected']],'elapsed_ns':time.monotonic_ns()-started,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'qualification':'Actual extracted Owner/Binding methods and actual summary/verify I/O; controlled synthetic object fields/Memo/currentness doubles, NOT genuine authority/numerical evidence.'};(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
