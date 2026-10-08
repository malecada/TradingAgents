import sys, importlib.util, copy, json, time, hashlib, difflib
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.matching_reference import match_reference

def module(file, name):
    name='tradingagents.research.onchain_replication.'+name
    spec=importlib.util.spec_from_file_location(name,P/file);obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj
B=module('baseline.py','annealing_baseline_exact01');C=module('matching_annealing.py','annealing_candidate_exact01')
config=dict(beta0=.2,beta_final=.5,beta_rate=.5,max_iterations=3,alpha=.7,max_pair_entries=100000,normalization_iterations=1,solver='algorithm1_literal')
def graph(n,edges,tie=False,dtype=np.float64):
    idx=np.asarray(edges,dtype=np.int64).reshape(-1,2).T
    return GraphSnapshot('ETH','2020-01-01T00:00:00Z','2020-01-02T00:00:00Z','2020-01-02T00:00:00Z',('a'*64,),'b'*64,tuple(str(x) for x in range(n)),np.asarray([[0.,0.] if tie else [x/7,x*x/11] for x in range(n)],dtype=dtype),idx,np.asarray([[0.,0.] if tie else [x/9,(x%5)/3] for x in range(len(edges))],dtype=dtype).reshape(-1,2),len(edges),len(edges),{})
checks=0

def equal(x,y):
    global checks
    assert set(x)==set(y)
    for k in x:
        if isinstance(x[k],np.ndarray):assert x[k].dtype==y[k].dtype and x[k].tobytes()==y[k].tobytes(),k
        else:assert x[k]==y[k],(k,x[k],y[k])
    checks+=1
fixtures=[('asymmetric',graph(3,[(0,1),(0,2),(2,1),(1,0)]),graph(4,[(0,1),(0,2),(1,2),(2,3),(3,0)])),('tie',graph(3,[(0,1),(0,2),(1,2)],True),graph(3,[(0,1),(0,2),(2,1)],True)),('empty',graph(2,[]),graph(3,[(0,1)])),('float32fallback',graph(3,[(0,1),(0,2),(1,2)],dtype=np.float32),graph(4,[(0,1),(0,2),(1,2),(2,3)],dtype=np.float32)),('chunkboundary',graph(12,[(u,v) for u in range(12) for v in range(12) if u!=v]),graph(8,[(u,v) for u in range(8) for v in range(8) if u!=v]))]
for name,a,b in fixtures:
    for schedule in ([1],[7,8,9,15,16,17],[1023,1024,1025],[100000]):
        x=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32);y=C.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32)
        steps=0
        while x['phase']!='done':
            budget=schedule[steps%len(schedule)]
            assert B.advance(x,a,b,config,max_operations=budget)==C.advance(y,a,b,config,max_operations=budget)
            equal(x,y);steps+=1
            if steps==2:
                directory=P/('checkpoint-'+name+'-'+str(schedule[0]))
                digest=C.save(y,directory,a,b,config,max_checkpoint_bytes=1000000)
                y=B.load(directory,a,b,config,expected_sha256=digest,max_state_bytes=1000000,max_chunk_entries=32)
                equal(x,y)
        rx=B.result(x,a,b,config);ry=C.result(y,a,b,config)
        assert rx.assignment.tobytes()==ry.assignment.tobytes() and rx.score.hex()==ry.score.hex() and rx.soft_assignment.tobytes()==ry.soft_assignment.tobytes() and rx.convergence==ry.convergence and rx.iterations==ry.iterations
# Throughput uses only synthetic repeated destinations with unique graph edges.
a,b=fixtures[-1][1:];x=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32)
B.advance(x,a,b,config,max_operations=len(a.node_ids)*len(b.node_ids)+1)
times={}
for label,mod in [('baseline',B),('candidate',C)]:
    samples=[]
    for _ in range(5):
        state=copy.deepcopy(x);t=time.perf_counter();mod._advance_checked(state,a,b,config,max_operations=7392);samples.append(time.perf_counter()-t)
    times[label]=samples
# Exception-prefix preservation: agreement overflow before end of a batched chunk.
x=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32);B.advance(x,a,b,config,max_operations=97)
a_bad=graph(12,[(u,v) for u in range(12) for v in range(12) if u!=v]);object.__setattr__(a_bad,'edge_features',a_bad.edge_features.copy());a_bad.edge_features[1,0]=1e308
y=copy.deepcopy(x)
errors=[]
for mod,state in [(B,x),(C,y)]:
    try:mod._advance_checked(state,a_bad,b,config,max_operations=1024)
    except BaseException as error:errors.append(type(error).__name__)
assert errors==['OverflowError','OverflowError'];equal(x,y)
receipt={'status':'PASS','state_boundary_checks':checks,'fixture_names':[v[0] for v in fixtures],'timing_seconds':times,'median_speedup':float(np.median(times['baseline'])/np.median(times['candidate'])),'numpy':np.__version__,'python':sys.version,'limitations':'Synthetic only. No empirical admission or capacity proof.'}
(P/'RESULT01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
