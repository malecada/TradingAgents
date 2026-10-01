"""Fresh tiny constant-score orchestration investigation; no empirical inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication.provenance import thaw
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.compact_policy import dictionary_capacity
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication.dictionary import cluster_medoids
from tradingagents.research.onchain_replication.matching_pair import BACKEND
from tradingagents.research.onchain_replication.neighborhoods import SampleManifest

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
paths = [BASE / 'pair-workload-2026-09-30/workload.py',
         ROOT / 'tradingagents/research/onchain_replication/compact_policy.py',
         ROOT / 'tradingagents/research/onchain_replication/dictionary.py']
pins = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def reconstruction(n, k, threshold, partsize, seed):
    rng = np.random.Generator(np.random.PCG64(seed))
    seen = set(); visits = []; actual = 0; indices = list(range(n))
    while True:
        final = len(indices) <= threshold
        shuffled = indices if final else list(map(int, rng.permutation(indices)))
        parts = [indices] if final else [sorted(shuffled[i:i+partsize]) for i in range(0,len(shuffled),partsize)]
        representatives = []
        for part in parts:
            key = tuple(part); reused = key in seen
            visits.append({'indices': part, 'reused': reused, 'final': final})
            if not reused: actual += len(part)*(len(part)-1); seen.add(key)
            matrix = np.full((len(part),len(part)), .5); np.fill_diagonal(matrix, 0.)
            centers, _ = cluster_medoids(matrix, min(k,len(part)))
            representatives.extend(part[i] for i in centers)
        if final: return actual, visits
        indices = sorted(representatives)

attempts = 0; found = None
for n in range(3,11):
    for k in range(2,n):
        for threshold in range(k,n):
            for partsize in range(k+1,n+1):
                for seed in range(16):
                    attempts += 1
                    capacity = dictionary_capacity(sample_count=n,size=k,partition_threshold=threshold,partition_size=partsize)
                    actual, visits = reconstruction(n,k,threshold,partsize,seed)
                    if actual < capacity['max_pairs']:
                        found = (n,k,threshold,partsize,seed,capacity,actual,visits); break
                if found: break
            if found: break
        if found: break
    if found: break
assert found is not None
n,k,threshold,partsize,seed,capacity,count,visits = found
settings = dict(sample_count=n,size=k,partition_threshold=threshold,partition_size=partsize)
graphs = tuple(AttributedGraph((str(i),),np.array([[float(i)]]),np.array([[0],[0]],dtype=np.int64),
    np.array([[1.]]),'a'*64,str(i)) for i in range(n))
records = tuple(dict(graph_hash='a'*64,center_id=str(i),center_index=i,probability=1/n,node_count=1,edge_count=1) for i in range(n))
rng_state = np.random.PCG64(seed).state
identity = cache_key({'training_graphs':('a'*64,), 'config':settings,'seed':seed,'records':records,'rng_state':rng_state})
samples = SampleManifest(graphs, records, ('a'*64,), rng_state, seed, identity)
spec = importlib.util.spec_from_file_location('fresh_dictionary_count',paths[0]); module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
asked = []
def score(purpose, left, right):
    asked.append(purpose)
    return {'purpose_sha256':cache_key(purpose),'score':.5}
result = module.fit(samples, {}, settings, workflow='b'*64,backend=BACKEND,max_entries=10000,score_pair=score)
assert len(asked) == count < capacity['max_pairs']
assert all(asked[i]['sample_indices'] == asked[i+1]['sample_indices'][::-1] for i in range(0,len(asked),2))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in pins.items())
out = dict(identity='compact-dictionary-count-investigation-02', synthetic_only=True,
    numeric_oracle=False, sample_draw_provenance=False, constant_score=.5, settings=settings,seed=seed,
    search_candidates=attempts, conservative_capacity=capacity,actual_directional_comparisons=len(asked),
    actual_unique_matrix_entries=sum(x['matrix'].size for x in result['matrices']),
    reconstructed_visits=visits, actual_matrix_subsets=[x['indices'] for x in result['matrices']],
    actual_directional_indices=[p['sample_indices'] for p in asked],
    hierarchy=result['dictionary'].hierarchy,memberships=result['dictionary'].memberships,
    sample_manifest_sha256=identity,source_sha256=pins)
target=Path(__file__).with_name('investigation-02.json')
with target.open('x') as file: json.dump(thaw(out),file,sort_keys=True,indent=2);file.write('\n')
print(json.dumps({'settings':settings,'seed':seed,'capacity':capacity,'actual':len(asked),'visits':visits}))
