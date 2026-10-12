"""Finite synthetic serialization measurement; no empirical or numerical engine."""
import os,resource,time,statistics,json,runpy
from pathlib import Path
os.sched_setaffinity(0,{2,3})
assert os.sched_getaffinity(0)=={2,3}
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=Path(__file__).resolve().parent;ns=runpy.run_path(str(P/'check_serialization01.py'));np=ns['np']
count=131072;arrays={'int64':np.arange(count,dtype='i8'),'float64':np.linspace(-.75,.875,count,dtype='f8')};g=ns['graph'](32769)
def chunks(arr,fast):
 total=0
 for start in range(0,len(arr),1024):
  value=arr[start:start+1024]
  raw=ns['candidate']['_graph_chunk_bytes'](value) if fast else ns['canonical'](value.tolist())
  total+=len(raw)
 return total
def measure(fn):
 w=time.perf_counter();c=time.process_time();result=fn();return {'wall':time.perf_counter()-w,'cpu':time.process_time()-c,'result':result}
rows={}
for label in ('int64','float64','validated_graph'):
 values={'baseline':[],'candidate':[]}
 for repeat in range(7):
  for name,fast in (('baseline',False),('candidate',True)):
   fn=(lambda:ns['candidate' if fast else 'base']['graph_hash'](g)) if label=='validated_graph' else (lambda:chunks(arrays[label],fast))
   values[name].append(measure(fn))
 assert len({x['result'] for records in values.values() for x in records})==1
 med={name:statistics.median(x['wall'] for x in records) for name,records in values.items()}
 rows[label]={'runs':values,'median_wall_seconds':med,'baseline_over_candidate':med['baseline']/med['candidate'],'wall_reduction_fraction':1-med['candidate']/med['baseline']}
result={'status':'SYNTHETIC_ONLY','affinity':sorted(os.sched_getaffinity(0)),'address_limit_bytes':1024**3,'cpu_limit_seconds':60,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'numpy':np.__version__,'chunk_cells':1024,'serialization_cells':count,'graph_nodes':32769,'graph_edges':32768,'repetitions':7,'results':rows,'qualification':'Shared host; no real graph, Owner, source admission, lease/boundary, storage or pipeline benchmark. Full graph validation retained in graph case.'}
with (P/'BENCHMARK01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'peak_rss_kib':result['peak_rss_kib'],'results':{k:{x:v[x] for x in ('median_wall_seconds','baseline_over_candidate','wall_reduction_fraction')} for k,v in rows.items()}}))
