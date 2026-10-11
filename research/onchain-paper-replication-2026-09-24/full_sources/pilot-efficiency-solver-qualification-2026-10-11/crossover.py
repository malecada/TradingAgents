"""Fixed crossover diagnostic, including immutable index construction per call."""
import importlib.util,json,time,statistics
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication import matching_numeric_kernel as kernel
from tradingagents.research.onchain_replication import matching_numeric_policy as policy
from tradingagents.research.onchain_replication.edge_chunk_adapter import make_filler
from tradingagents.research.onchain_replication.matching_reference import agreement
from tests.research.onchain_replication.test_matching_numeric_policy import frozen
root=Path.cwd();dest=Path(__file__).parent
path=root/'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-two-attribute-agreement01-2026-10-11/_edge_chunk.cpython-313-x86_64-linux-gnu.so'
import hashlib
assert hashlib.sha256(path.read_bytes()).hexdigest()=='adead75d8f74f77b7d70164dab5465fef8a0e7ec06255b3dcd599f721745df97'
spec=importlib.util.spec_from_file_location('_crossover._edge_chunk',path);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
fill=make_filler(native,np,agreement)
a=frozen(np.arange(128*2).reshape(128,2)*.001);b=frozen(a+.03)
rows=[]
for count in (8,32,64,128,256,512,1024):
    li=np.arange(count,dtype=np.int64)%128;ri=(li+3)%128;out=np.empty(count)
    def candidate():
        il=np.frombuffer(li.tobytes(),dtype=np.int64);ir=np.frombuffer(ri.tobytes(),dtype=np.int64)
        assert kernel.fill_agreement(a,b,il,ir,out,0,count)
        out[:]*=.5
    def current():assert fill(out,a,b,li,ri,count,agreement,[0])
    row={'count':count,'selected':count>=256,'times':{}}
    for name,fn in (('native_current',current),('numpy_with_index_copy',candidate)):
        times=[]
        for _ in range(5):
            start=time.perf_counter()
            for _ in range(200):fn()
            times.append((time.perf_counter()-start)/200)
        row['times'][name]=times
    row['ratio']=statistics.median(row['times']['native_current'])/statistics.median(row['times']['numpy_with_index_copy'])
    rows.append(row)
(dest/'CROSSOVER01.json').write_text(json.dumps({'policy_unchanged':dict(policy.POLICY),'rows':rows},indent=2)+'\n')
print([(r['count'],round(r['ratio'],3)) for r in rows])
