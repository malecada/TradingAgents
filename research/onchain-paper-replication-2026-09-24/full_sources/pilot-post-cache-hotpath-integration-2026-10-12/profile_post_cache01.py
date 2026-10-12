"""Root-only finite synthetic attribution; no profiler, empirical data or authority.

Instrument an AST copy of the exact current annealing body before any session
captures helper identities. Timers alter observation overhead, not arithmetic.
Keep runtime primitives intact: tracing/profiling would disable fast paths.
"""
from pathlib import Path
from contextlib import contextmanager
import ast,hashlib,json,math,os,resource,sys,time

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
sys.path.insert(0,str(ROOT))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as ann
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_numeric_policy as policy
from tradingagents.research.onchain_replication import matching_numeric_kernel as kernel
from tradingagents.research.onchain_replication.matching_immutable_session import ImmutablePairSession
from tradingagents.research.onchain_replication.contracts import AttributedGraph

counts={};stack=[]
@contextmanager
def measured(name):
    entry=[time.perf_counter(),0.];stack.append(entry)
    try:yield
    finally:
        elapsed=time.perf_counter()-entry[0];stack.pop()
        if stack:stack[-1][1]+=elapsed
        row=counts.setdefault(name,{'calls':0,'inclusive_seconds':0.,'exclusive_seconds':0.})
        row['calls']+=1;row['inclusive_seconds']+=elapsed
        row['exclusive_seconds']+=elapsed-entry[1]

original_source=Path(ann.__file__).read_text()
tree=ast.parse(original_source)
original_function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
source='\n'.join(original_source.splitlines()[original_function.lineno-1:original_function.end_lineno])+'\n'
changes=[]
def wrap(old,name):
    global source
    assert source.count(old)==1,name
    indent=len(old)-len(old.lstrip(' '));prefix=' '*indent
    new=prefix+"with _post_cache_measure('"+name+"'):\n"+''.join('    '+line for line in old.splitlines(True))
    source=source.replace(old,new);changes.append({'name':name,'old':old,'new':new})

wrap('''                    positions=np.arange(start,start+count,dtype=np.int64)
                    left,right=np.divmod(positions,right_edges)
                    u,v=a.edge_index[:,left];i,j=b.edge_index[:,right]
                    old_values=state['M'][v,j]
''','geometry')
old="                    if np.all(np.abs(old_values)<=1.) and np.all(np.abs(state['Q'][u,i])<=1e100):\n"
new="                    with _post_cache_measure('finite_accumulation_domain'):\n                        eligible_chunk=np.all(np.abs(old_values)<=1.) and np.all(np.abs(state['Q'][u,i])<=1e100)\n                    if eligible_chunk:\n"
assert source.count(old)==1;source=source.replace(old,new);changes.append({'name':'finite_accumulation_domain','old':old,'new':new})
start=source.index('                        weights=np.empty(count,dtype=np.float64)\n')
end=source.index('                        np.multiply(weights,old_values,out=weights)\n',start)
wrap(source[start:end],'weight_dispatch')
wrap('                        np.multiply(weights,old_values,out=weights)\n','multiply')
wrap("                        np.add.at(state['Q'],(u,i),weights)\n",'ordered_scatter')
Path(P/'INSTRUMENTED_advance01.py').write_text(source)
Path(P/'INSTRUMENTATION01.json').write_text(json.dumps({'original_sha256':hashlib.sha256(original_source.encode()).hexdigest(),'literal_changes':changes,'exclusions':['empirical authority','native owners','production wall distribution'],'runtime_primitives_changed':False},indent=2)+'\n')
ann._post_cache_measure=measured
exec(compile(source,str(P/'INSTRUMENTED_advance01.py'),'exec'),ann.__dict__)

def wrapper(function,name):
    def timed(*args,**kwargs):
        with measured(name):return function(*args,**kwargs)
    return timed
for name in ('_cache_current','_feature_current','_cache_domain','_cache_fill'):
    setattr(policy,name,wrapper(getattr(policy,name),name))
kernel.fill_agreement=wrapper(kernel.fill_agreement,'original_miss_kernel')

def frozen(a,dtype):
    a=np.asarray(a,dtype=dtype)
    return np.frombuffer(a.tobytes(),dtype=dtype).reshape(a.shape)
def graph(edges,offset):
    n=max(2,math.ceil(math.sqrt(edges)));position=np.arange(edges,dtype=np.int64)
    index=np.asarray((position//n,position%n),dtype=np.int64).reshape(2,edges)
    node=(np.arange(n*4,dtype=np.float64).reshape(n,4)%29)*.017+offset
    features=(np.arange(edges*2,dtype=np.float64).reshape(edges,2)%97)*.013+offset
    return AttributedGraph(tuple(map(str,range(n))),frozen(node,np.float64),
        frozen(index,np.int64),frozen(features,np.float64),'a'*64,'0')

config_path=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-connected-qualification03-2026-10-11/matching-config.json'
raw=config_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b3b8d88424a56a6009a4baa447e00b971d769930299c769414f6d33d9a4e873e'
c=json.loads(raw);rows=[]
baseline_path=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/pilot-matching-weight-cache-integration-2026-10-12/MATCHING_BENCHMARK01.json'
baseline_raw=baseline_path.read_bytes()
assert hashlib.sha256(baseline_raw).hexdigest()=='ade28d799c9f7896c655d66917069209f46b0a39c54ad774e261d9b4c06e8932'
expected={row['edge_products']:row['v2_soft_sha256'] for row in json.loads(baseline_raw)['cases']}
for left,right in ((128,128),(256,512),(1024,1024)):
    counts.clear();a,b=graph(left,0.),graph(right,.031)
    state=engine.create(a,b,c,max_state_bytes=16*1024**2,hardening_buffer_bytes=4*1024**2)
    session=ImmutablePairSession(a,b,c,engine=engine,annealing=ann,
        numeric_kernel_policy=dict(policy.CACHE_POLICY),edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY))
    start=time.perf_counter();operations=0
    try:
        while state['phase']!='done':operations+=session.advance(state,max_operations=1000000)
        wall=time.perf_counter()-start
        assert state['annealing']['iterations']==48
        soft_sha=hashlib.sha256(state['annealing']['M'].tobytes()).hexdigest()
        assert soft_sha==expected[left*right], 'instrumented result differs from prior selected solver'
        rows.append({'products':left*right,'advance_wall_seconds':wall,'operations':operations,
            'timings':json.loads(json.dumps(counts)),'cache_counts':session._numeric_adapter.snapshot(),
            'soft_sha256':soft_sha,'matches_prior_selected_digest':True})
    finally:session.close();engine.close(state)
out={'kind':'instrumented-selected-v2-synthetic-attribution','cases':rows,
    'timing_interval':'session advances/hardening, excludes cold create, score, cleanup and authority',
    'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'qualification':'one observation per fixture; timers add overhead; not production throughput or full capacity',
    'native_caps_changed':False,'empirical_claim':None}
with (P/'POST_CACHE_PROFILE01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(out,indent=2,sort_keys=True))
