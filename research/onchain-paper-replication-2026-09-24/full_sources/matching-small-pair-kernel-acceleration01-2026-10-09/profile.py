import sys,json,time,importlib.util,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as old
from tradingagents.research.onchain_replication.contracts import AttributedGraph
config=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes())
def graph(n):
 edges=np.array([(i,j) for i in range(n) for j in range(n) if i!=j and (i+j)%3],dtype=np.int64).T.copy()
 return AttributedGraph(tuple('n'+str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.01,edges,np.arange(edges.shape[1]*2,dtype=np.float64).reshape(-1,2)*.02,'a'*64,'n0')
a,b=graph(4),graph(5)
source=Path(old.__file__).read_text();probe=source.replace('        used=0\n','        used=0\n        _phase=None;_tick=None\n').replace("            phase=state['phase']","            if _tick is not None: _timings[_phase]=_timings.get(_phase,0.)+_clock()-_tick\n            phase=state['phase'];_phase=phase;_tick=_clock()").replace("        state['safe']=True\n","        if _tick is not None: _timings[_phase]=_timings.get(_phase,0.)+_clock()-_tick\n        state['safe']=True\n")
ns={'__name__':'tradingagents.research.onchain_replication._phase_probe','__package__':'tradingagents.research.onchain_replication','_clock':time.perf_counter,'_timings':{}};exec(compile(probe,'phase-probe','exec'),ns)
results={}
for name,module in [('baseline',old),('phase_probe',ns)]:
 timings=[]
 for i in range(20):
  state=old.create(a,b,config,max_state_bytes=1000000);fn=module['_advance_checked'] if isinstance(module,dict) else module._advance_checked;t=time.perf_counter();used=fn(state,a,b,config,max_operations=1000000);timings.append(time.perf_counter()-t);assert state['phase']=='done'
 results[name]={'seconds':timings,'used':used,'iterations':state['iterations'],'hash':hashlib.sha256(b''.join(state[k].tobytes() for k in ('V','M','Q'))).hexdigest()}
assert results['baseline']['hash']==results['phase_probe']['hash'];results.update({'phase_seconds':ns['_timings'],'shape':[4,5],'edges':[a.edge_index.shape[1],b.edge_index.shape[1]],'profile_method':'Phase wall clock insertion in isolated source copy, no sys.setprofile; runtime agreement reuse remains enabled. Observational overhead included.','affinity':sorted(os.sched_getaffinity(0)),'baseline_sha256':hashlib.sha256(source.encode()).hexdigest()});(D/'PROFILE01.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results['phase_seconds']))
