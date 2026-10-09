import os,resource,signal,sys,json,ast,importlib.util,types
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'matching-real-geometry-instrumentation01-2026-10-09';os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30);(R/'LIMITS01.json').write_text(json.dumps({'affinity':list(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall':signal.getitimer(signal.ITIMER_REAL)[0]})+'\n')
spec=importlib.util.spec_from_file_location('geometry',P/'geometry_summary.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
NS=types.SimpleNamespace
def graph(n,e):return NS(node_ids=range(n),edge_index=NS(shape=(2,e)))
x=g.Geometry(8192);x.begin(11)
for ordinal,n,m,ea,eb,mode in ((11,8,3,9,2,'computed'),(12,3,2,0,1,'reused'),(13,4,4,4,4,'computed')):x.add(graph(n,ea),graph(m,eb),{'ordinal':ordinal,'mode':mode})
assert x.data['end_batch_attested'] is False
# Actual end_batch method; synthetic control-only receiver, no authority instance.
tree=ast.parse((P/'batched_numeric_reuse.py').read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NumericReuseExecutor');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='end_batch');events=[]
def attest(c):events.append('attest')
ns={'require':g.require,'attest':attest};exec(compile(ast.Module(body=[method],type_ignores=[]),'<actual-end-batch>','exec'),ns)
class Receiver:
 closed=False;poisoned=False;active=True;occurrences=14;computed=7;reused=5;_geometry_counts=(5,4);counters={};last_geometry_summary=None
 def _current(self):events.append('current')
 def _poison(self):self.poisoned=True;self.active=False;self._geometry.poison();self.last_geometry_summary=None
r=Receiver();r._geometry=x;ns['end_batch'](r);d=json.loads(r.last_geometry_summary);assert events==['current','attest'] and d['end_batch_attested'] and d['computed']==2 and d['reused']==1 and (d['start'],d['stop'])==(11,14)
assert d['metrics']['matrix_product']['sum']==46 and d['metrics']['edge_product']['sum']==34 and d['metrics']['left_nodes']['max']==8
assert all(sum(v['histogram'])==3 for v in d['metrics'].values());assert d['static_shape_only']=={'batched02_two_pair_scratch':2,'compiled04_matrix_shape':2} and d['runtime_eligibility_proved'] is False
primary=RuntimeError('synthetic failed end attestation')
def failed(c):raise primary
ns['attest']=failed;r2=Receiver();r2._geometry=g.Geometry(8192);r2._geometry.begin(14);r2.active=True
try:ns['end_batch'](r2)
except RuntimeError as e:assert e is primary and r2.poisoned and r2.last_geometry_summary is None and r2._geometry.data is None
else:raise AssertionError('attestation bypass')
z=g.Geometry(1);z.begin(0)
try:z.finish(0,0,0)
except ValueError:pass
else:raise AssertionError('bytecap bypass')
z.poison();assert z.data is None
(R/'RESULT01.json').write_text(json.dumps({'fixed_histograms_counts_range':True,'end_batch_order':events,'end_attestation_failure_primary_preserved_and_summary_cleared':True,'serialized_cap_refused':True,'summary_bytes':len(r.last_geometry_summary),'summary':d,'qualification':'Actual helper and extracted end_batch method, metadata-only synthetic receiver; no fabricated Owner or admission.'},indent=2)+'\n')
