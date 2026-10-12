"""Finite synthetic baseline, without tracing (tracing disables fast paths).

Only the agreement helper is wrapped before session identity capture. Original
agreement arithmetic/runtime, annealing, normalization and operation budgets
are unchanged. No Run, Owner, data input, fitting or network access occurs.
"""
from pathlib import Path
import hashlib,json,os,resource,sys,time

P=Path(__file__).resolve().parent
R=P.parents[3]
sys.path.insert(0,str(R))
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
import numpy as np
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_annealing as ann
from tradingagents.research.onchain_replication import matching_numeric_kernel as kernel
from tradingagents.research.onchain_replication import matching_numeric_policy as numeric
from tradingagents.research.onchain_replication.matching_immutable_session import ImmutablePairSession
from tradingagents.research.onchain_replication.contracts import AttributedGraph

C=dict(alpha=1.,beta0=1.,beta_final=30.,beta_rate=.075,max_iterations=50,
       normalization_iterations=1,solver='algorithm1_literal',max_pair_entries=65536)

def frozen(a,dtype):
    a=np.asarray(a,dtype=dtype)
    return np.frombuffer(a.tobytes(),dtype=dtype).reshape(a.shape)

def graph(n,edges,offset):
    node=np.arange(n*4,dtype=np.float64).reshape(n,4)/(n*4)+offset
    positions=np.arange(edges,dtype=np.int64)
    idx=np.stack((positions//n,positions%n))
    features=np.arange(edges*2,dtype=np.float64).reshape(edges,2)/max(1,edges*2)+offset
    return AttributedGraph(tuple(map(str,range(n))),frozen(node,np.float64),
        frozen(idx,np.int64),frozen(features,np.float64),'a'*64,'0')

original=kernel.fill_agreement
timing={'calls':0,'accepted':0,'wall_seconds':0.}
def measured(*args,**kwargs):
    started=time.perf_counter()
    try:
        result=original(*args,**kwargs)
        timing['accepted']+=int(result is True)
        return result
    finally:
        timing['calls']+=1;timing['wall_seconds']+=time.perf_counter()-started
kernel.fill_agreement=measured
rows=[]
try:
    for n,e,m,f in ((4,6,4,6),(32,512,8,32),(32,1024,16,128)):
        a,b=graph(n,e,0.),graph(m,f,.03)
        timing.update(calls=0,accepted=0,wall_seconds=0.)
        state=engine.create(a,b,C,max_state_bytes=4*1024**2)
        session=ImmutablePairSession(a,b,C,engine=engine,annealing=ann,
            edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY),numeric_kernel_policy=dict(numeric.POLICY))
        started=time.perf_counter();operations=0
        try:
            while state['phase']!='done':operations+=session.advance(state,max_operations=262144)
            elapsed=time.perf_counter()-started
            rows.append(dict(nodes=[n,m],edges=[e,f],products=e*f,
                wall_seconds=elapsed,agreement_helper=dict(timing),
                helper_fraction=timing['wall_seconds']/elapsed,
                iterations=state['annealing']['iterations'],operations=operations,
                adapter_counts=session._numeric_adapter.snapshot()))
        finally:session.close();engine.close(state)
finally:kernel.fill_agreement=original
record=dict(kind='synthetic-instrumented-baseline-only',cases=rows,
    config=C,affinity=sorted(os.sched_getaffinity(0)),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (R/'tradingagents/research/onchain_replication/matching_annealing.py',
                  R/'tradingagents/research/onchain_replication/matching_numeric_policy.py',
                  R/'tradingagents/research/onchain_replication/matching_numeric_kernel.py')},
    exclusions=['native backend owners','scientific authority','whole pilot','production throughput'],
    qualification='One helper wrapper adds timing overhead; no profiler/runtime primitive patch; no empirical execution.')
with (P/'BASELINE_PROFILE01.json').open('x') as out:json.dump(record,out,indent=2,sort_keys=True);out.write('\n')
print(json.dumps({'cases':len(rows),'iterations':[r['iterations'] for r in rows],
    'helper_fractions':[r['helper_fraction'] for r in rows]}))
