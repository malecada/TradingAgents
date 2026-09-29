"""Synthetic ring stress fixture, larger than retained graph metadata counts.

No empirical file is opened. Every node has exactly two distinct neighbors;
duplicate directed edges and shuffled storage order preserve that oracle.
"""
from pathlib import Path
import json
import time
import numpy as np
from census_engine import census

HERE=Path(__file__).resolve().parent
output=HERE/'synthetic01'
output.mkdir(exist_ok=False)
n=3_000_000;e=4_000_000
started=time.monotonic()
ends=np.arange(e,dtype=np.int64)%n
edges=np.vstack((ends,(ends+1)%n));del ends
np.random.default_rng(417).shuffle(edges,axis=1)
result=census(edges,n,output/'census',identity={'fixture':'shuffled-directed-ring-with-duplicates-v1','nodes':n,'edges':e},edge_chunk=65536,max_output_bytes=512*1024**2)
assert result['nodes']==n and result['minimum']==3 and result['maximum']==3
assert result['unique_nonself_pairs']==n and result['above_10000']==0
counts=np.load(output/'census/cardinalities.npy',mmap_mode='r')
maxima=np.load(output/'census/maxima_indices.npy',mmap_mode='r')
try:
    for start in range(0,n,65536):
        assert np.all(counts[start:start+65536]==3)
        assert np.array_equal(maxima[start:start+65536],np.arange(start,min(n,start+65536)))
finally:
    counts._mmap.close();maxima._mmap.close()
assert np.array_equal(np.load(output/'census/histogram.npy'),np.array([[3,n]]))
files=[p for p in output.rglob('*') if p.is_file()]
value={'status':'complete','fixture':'synthetic-only ring; no empirical feasibility claim',
       'nodes':n,'edges':e,'elapsed_seconds':time.monotonic()-started,'census_elapsed_seconds':result['elapsed_seconds'],
       'logical_bytes':sum(p.stat().st_size for p in files),'allocated_bytes':sum(p.stat().st_blocks*512 for p in files),
       'all_cardinalities_and_maxima_checked':True,'registered_empirical_execution':False}
with (output/'verification.json').open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
print(json.dumps(value),flush=True)
