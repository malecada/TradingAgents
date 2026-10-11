"""Fixed finite synthetic full-solver corpus; no lifecycle claim or raw inputs."""
import json,time,statistics,resource,hashlib
from pathlib import Path
import numpy as np
import scipy
from tradingagents.research.onchain_replication import compiled_edge_owner as edge
from tradingagents.research.onchain_replication import compiled_normalization_policy as norm
from tradingagents.research.onchain_replication import matching_checkpoint as engine, matching_annealing as ann
from tradingagents.research.onchain_replication import matching_numeric_policy as numeric, phase_timing
from tradingagents.research.onchain_replication.matching_immutable_session import ImmutablePairSession
from tests.research.onchain_replication.test_matching_numeric_policy import graph,config
ROOT=Path.cwd();DEST=Path(__file__).parent
refs=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full35-entry-preparation01-2026-10-11/BINDING01.json').read_bytes())['input_refs']
def make_policy(prefix,format,roles):
    p={'format':format}
    for role in roles:
        ref=refs[prefix+'_'+role];path=ROOT/ref['path']
        p[role+'_path']=str(path);p[role+'_sha256']=ref['sha256']
        if role in ('runtime','abi'):p[role+'_bytes']=path.stat().st_size
    return p
EP=make_policy('compiled_edge',edge.FORMAT,('source','adapter','library','runtime','abi'))
NP=make_policy('compiled_normalization',norm.FORMAT,('source','library','runtime'))
CP=dict(format='adaptive-lazy-edge-cache-v1',max_edge_products=16384,chunk_entries=256,max_scratch_bytes=262144)
def one(n,e,width,selected):
    # Timed graph extraction + immutable copy + policy/backend joins + complete
    # solver/state checks/hardening/final score + close; no real Owner/offload.
    start=time.perf_counter();cpu=time.process_time();totals=phase_timing.PhaseTotals()
    a=graph(n,e,width=width);b=graph(n,e,.03,width=width);c=config()
    owner=edge.EdgeOwner(EP,numpy=np,scipy=scipy,agreement=ann.agreement)
    session=None;state=None
    try:
        with phase_timing.activate(totals):
            state=engine.create(a,b,c,max_state_bytes=4*1024**2)
            session=ImmutablePairSession(a,b,c,engine=engine,annealing=ann,edge_cache_policy=CP,
                compiled_normalization_policy_value=NP,edge_chunk_owner=owner,
                numeric_kernel_policy=dict(numeric.POLICY) if selected else None)
            cursor=[]
            while state['phase']!='done':
                used=session.advance(state,max_operations=1000000)
                cursor.append((used,state['phase'],state['annealing']['cursor'],state['annealing']['iterations']))
            result=engine.result(state,a,b,c)
            counts={} if session._numeric_adapter is None else session._numeric_adapter.snapshot()
    finally:
        if session is not None:session.close()
        if state is not None:engine.close(state)
        owner.close()
    return result,dict(wall=time.perf_counter()-start,cpu=time.process_time()-cpu,cursor=cursor,adapter=counts,telemetry=totals.snapshot())
rows=[]
for n,e,width in ((3,7,2),(9,81,2),(12,144,2),(16,256,2),(12,144,4)):
    row=dict(n=n,edges=e,width=width,runs=[])
    for repeat in range(3):
        old,ot=one(n,e,width,False);new,nt=one(n,e,width,True)
        np.testing.assert_allclose(old.soft_assignment,new.soft_assignment,atol=1e-8,rtol=1e-6)
        assert abs(old.score-new.score)<=1e-8+1e-6*abs(old.score)
        assert ot['cursor']==nt['cursor']
        assert (new.assignment.sum(0)<=1).all() and (new.assignment.sum(1)<=1).all()
        row['runs'].append(dict(current=ot,selected=nt))
    row['speedup']=statistics.median(x['current']['wall'] for x in row['runs'])/statistics.median(x['selected']['wall'] for x in row['runs'])
    row['selected_cells_per_second']=1/statistics.median(x['selected']['wall'] for x in row['runs'])
    rows.append(row)
report=dict(format='finite-full-solver-c05-v1',rows=rows,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    native_policy=EP,normalization_policy=NP,numeric_policy=dict(numeric.POLICY),
    authority=False,offload_measured=False,node_agreement='unchanged scalar',
    source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(ann.__file__),Path(numeric.__file__),Path(__file__))})
(DEST/'RESULTS01.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps([{'n':r['n'],'edges':r['edges'],'width':r['width'],'speedup':r['speedup'],'cells_per_second':r['selected_cells_per_second']} for r in rows],indent=2))
