"""Synthetic duplicate-check allocation diagnostic; no research inputs."""
import json
from itertools import pairwise
from pathlib import Path
import time
import tracemalloc
import numpy as np
from tradingagents.research.onchain_replication.contracts import _duplicate_edges

n=200000
edges=np.vstack((np.arange(n,dtype=np.int64),np.roll(np.arange(n,dtype=np.int64),1)))
ids=tuple('synthetic-node-'+str(i) for i in range(n))
def measure(call):
    tracemalloc.start();start=time.perf_counter()
    duplicate=bool(call());elapsed=time.perf_counter()-start
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert not duplicate
    return {'duplicate':duplicate,'seconds':elapsed,'peak_traced_bytes':peak}
result={'synthetic_nodes':n,'synthetic_edges':n,
    'edge_set':measure(lambda:len(set(map(tuple,edges.T)))!=n),
    'edge_sorted':measure(lambda:_duplicate_edges(edges)),
    'node_set':measure(lambda:len(set(ids))!=n),
    'node_sorted':measure(lambda:any(a==b for a,b in pairwise(sorted(ids)))),
    'qualification':'tracemalloc allocations inside duplicate check only; excludes input construction and other validator work; not RSS, full pipeline or real-data feasibility'}
output=Path(__file__).with_name('measurement.json')
with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
