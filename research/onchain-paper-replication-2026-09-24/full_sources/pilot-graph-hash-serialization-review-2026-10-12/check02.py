import os,resource
os.sched_setaffinity(0,{2,3})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,json,hashlib,difflib,statistics,runpy
from pathlib import Path
import numpy as np
F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
C=F/'pilot-graph-hash-serialization-candidate-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST01.json').read_text())
assert h(C/'SOURCE_MANIFEST01.json')=='de2eaeb94787c7621fa67412fe8138a6c778f5dd95f42a693b4744b83ef63b12'
for row in [m['baseline'],*m['unchanged_dependencies'],*m['files'],*m['preserved_iteration01']]:
 p=Path(row['path']);assert len(p.read_bytes())==row['bytes'] and h(p)==row['sha256'],p
old=(C/'BASELINE_neighborhoods.py').read_text();new=(C/'neighborhoods.py').read_text()
for name,a,b,pa,pb in [('LITERAL_PATCH01.diff',old,new,m['baseline']['path'],str(C/'neighborhoods.py')),('LITERAL_INVERSE01.diff',new,old,str(C/'neighborhoods.py'),m['baseline']['path'])]:
 assert ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=pa,tofile=pb))==(C/name).read_text(),name
oldast=ast.parse(old);newast=ast.parse(new)
oldnodes={x.name:ast.dump(x,include_attributes=False) for x in oldast.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
newnodes={x.name:ast.dump(x,include_attributes=False) for x in newast.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
assert set(newnodes)==set(oldnodes)|{'_graph_chunk_bytes'}
assert all(v==newnodes[k] for k,v in oldnodes.items() if k!='graph_hash')
# Restore exactly the two authored graph_hash substitutions and remove helper.
helper=next(x for x in newast.body if isinstance(x,ast.FunctionDef) and x.name=='_graph_chunk_bytes')
restored=''.join(new.splitlines(True)[:helper.lineno-1]+new.splitlines(True)[helper.end_lineno+2:])
restored=restored.replace('h.update(_graph_chunk_bytes(value[start:start+rows])[1:-1])','h.update(canonical_bytes(value[start:start+rows].tolist())[1:-1])').replace("encoded=(_graph_chunk_bytes(chunk) if isinstance(chunk,np.ndarray)\n                         else canonical_bytes(chunk))\n                h.update(encoded[1:-1])","if isinstance(chunk,np.ndarray):chunk=chunk.tolist()\n                h.update(canonical_bytes(chunk)[1:-1])")
assert ast.dump(ast.parse(restored))==ast.dump(oldast)
canon=runpy.run_path('tradingagents/research/onchain_replication/provenance.py')['current_canonical_bytes']
# Execute only the exact helper AST; replace its relative import with supplied genuine serializer.
helper.body=[n for n in helper.body if not isinstance(n,ast.ImportFrom)]
env={'np':np,'current_canonical_bytes':canon}
exec(compile(ast.fix_missing_locations(ast.Module([helper],[])),str(C/'neighborhoods.py'),'exec'),env)
fn=env['_graph_chunk_bytes'];calls=[]
def spy(v):calls.append(v);return canon(v)
env['current_canonical_bytes']=spy
controls=[]
class Trap(np.ndarray):
 @property
 def dtype(self):raise AssertionError('subclass dtype touched')
 def tolist(self):return ['雪',-0.0]
a=np.zeros(1).view(Trap);assert fn(a)==canon(a.tolist()) and len(calls)==1;controls.append('subclass dtype trap fallback')
for a in [np.arange(1025),np.ones((2,2,2)),np.array([1],dtype=np.dtype('i4',metadata={'x':1}))]:
 calls.clear();assert fn(a)==canon(a.tolist()) and len(calls)==1
controls.append('oversize dimension metadata fallback')
a=np.arange(2048,dtype='>f8')[::-2];calls.clear();assert fn(a)==canon(a.tolist()) and not calls
controls.append('negative stride endian exact1024 direct')
for a in [np.array([0.,np.nan]),np.array([np.inf,-0.])]:
 def error(f):
  try:f()
  except Exception as e:return type(e).__name__,str(e)
 assert error(lambda:fn(a))==error(lambda:canon(a.tolist()))
 assert error(lambda:fn(a))[0]=='ValueError'
controls.append('nonfinite exact exception parity')
a=np.array([np.iinfo('u8').max],dtype='u8');before=fn(a);a[0]=0;assert fn(a)==canon(a.tolist())!=before
controls.append('uint64 extreme fresh mutation')
b=json.loads((C/'BENCHMARK02.json').read_text());assert b['candidate_sha256']==h(C/'neighborhoods.py')
assert b['affinity']==[2,3] and b['address_limit_bytes']==1024**3 and b['cpu_limit_seconds']==60
metrics={}
for label,row in b['results'].items():
 vals=row['runs'];assert all(len(v)==7 for v in vals.values());assert len({x['result'] for v in vals.values() for x in v})==1
 med={k:statistics.median(x['wall'] for x in v) for k,v in vals.items()};assert med==row['median_wall_seconds']
 assert med['baseline']/med['candidate']==row['baseline_over_candidate']
 assert 1-med['candidate']/med['baseline']==row['wall_reduction_fraction']
 metrics[label]={'medians':med,'wall_reduction_percent':100*row['wall_reduction_fraction'],'raw_result':vals['baseline'][0]['result']}
assert (C/'BASELINE_RESULTS01.json').read_bytes()==(C/'COMPATIBILITY_RESULTS02.json').read_bytes()
print(json.dumps({'status':'PASS','controls':controls,'manifest_and_literal_inverse':True,'unchanged_other_ast_and_restored_graph_ast':True,'benchmark':metrics,'affinity':sorted(os.sched_getaffinity(0)),'numpy':np.__version__},indent=2))
