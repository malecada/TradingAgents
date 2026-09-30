"""Full-schedule zero-edge synthetic matching, hardening and score profile."""
from pathlib import Path
import gc
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.resources import assert_guarded_worker, GIB

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
N = 2000


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def main():
    assert_guarded_worker(HERE/'guard01', sys.orig_argv, required_paths=[ROOT],
        wall_seconds=1800, memory_max_bytes=GIB, memory_high_bytes=3*GIB//4,
        disk_floor_bytes=10*GIB)
    for name, digest in json.loads((HERE/'bindings.json').read_bytes()).items():
        assert sha(ROOT/name) == digest, name
    write(HERE/'started.json', {'pid':os.getpid(), 'at_unix':time.time(),
        'qualification':'Fresh synthetic fixture; no empirical body or claim.'})
    graph = GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z',
        '2024-01-09T00:00:00Z',('a'*64,),'b'*64,tuple(map(str,range(N))),
        np.zeros((N,1)),np.empty((2,0),dtype=np.int64),np.empty((0,1)),0,0,{})
    config = json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes())
    assert config['max_pair_entries'] == N*N
    beta = config['beta0']
    expected_iterations = 0
    while beta <= config['beta_final'] and expected_iterations < config['max_iterations']:
        expected_iterations += 1
        beta *= 1 + config['beta_rate']
    assert expected_iterations == 48 and beta > config['beta_final']
    path = HERE.with_name('matching-score-only-checkpoints-2026-09-30')/'result_only.py'
    spec = importlib.util.spec_from_file_location('complete_probe_score', path)
    score_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(score_module)
    combined = score_module.combined
    policy = dict(max_state_bytes=128*1024**2, normalization_chunk_entries=65536,
        hardening_chunk_entries=65536, hardening_buffer_bytes=8*1024**2)
    timings = {}
    start = time.monotonic()
    state = combined.create(graph,graph,config,**policy)
    timings['create_seconds'] = time.monotonic()-start
    operations = calls = 0
    start = time.monotonic()
    while state['phase'] == 'annealing':
        operations += combined.advance(state,graph,graph,config,max_operations=4000000)
        calls += 1
        assert calls <= 100
    timings['annealing_seconds'] = time.monotonic()-start
    assert state['annealing']['iterations'] == expected_iterations
    error = float(np.max(np.abs(state['annealing']['M']-1/N)))
    assert error < 1e-14
    start = time.monotonic()
    chunks = combined.advance(state,graph,graph,config,max_operations=256)
    timings['hardening_prefix_seconds'] = time.monotonic()-start
    assert chunks == 256 and state['phase'] == 'hardening'
    assert state['hardening']['pairs'] == [[i,i] for i in range(3)]
    before = {k:state['hardening'][k] for k in ('phase','cursor','pairs','best_index','best_value')}
    soft = hashlib.sha256(memoryview(state['annealing']['M']).cast('B')).hexdigest()
    start = time.monotonic()
    prefix_sha = combined.save(state,HERE/'checkpoint01',graph,graph,config,
        max_checkpoint_bytes=128*1024**2)
    timings['prefix_save_seconds'] = time.monotonic()-start
    del state
    gc.collect()
    start = time.monotonic()
    state = combined.load(HERE/'checkpoint01',graph,graph,config,
        expected_sha256=prefix_sha,**policy)
    timings['prefix_load_seconds'] = time.monotonic()-start
    assert {k:state['hardening'][k] for k in before} == before
    assert hashlib.sha256(memoryview(state['annealing']['M']).cast('B')).hexdigest() == soft
    expected_chunks = math.ceil(N*N/65536)*(N+1)
    start = time.monotonic()
    while state['phase'] != 'done':
        used = combined.advance(state,graph,graph,config,max_operations=256)
        assert used > 0
        chunks += used
        assert chunks <= expected_chunks
    timings['hardening_remainder_seconds'] = time.monotonic()-start
    assert chunks == expected_chunks
    assert state['hardening']['pairs'] == [[i,i] for i in range(N)]
    start = time.monotonic()
    result = score_module.score_only(state,graph,graph,config,max_buffer_bytes=8*1024**2)
    timings['score_seconds'] = time.monotonic()-start
    assert result.score == 0.5 and result.iterations == 48 and result.convergence == 'temperature_complete'
    start = time.monotonic()
    final_sha = combined.save(state,HERE/'checkpoint02',graph,graph,config,
        max_checkpoint_bytes=128*1024**2)
    timings['final_save_seconds'] = time.monotonic()-start
    del state
    gc.collect()
    start = time.monotonic()
    state = combined.load(HERE/'checkpoint02',graph,graph,config,
        expected_sha256=final_sha,**policy)
    timings['final_load_seconds'] = time.monotonic()-start
    assert state['phase'] == 'done' and state['hardening']['pairs'] == [[i,i] for i in range(N)]
    assert hashlib.sha256(memoryview(state['annealing']['M']).cast('B')).hexdigest() == soft
    start = time.monotonic()
    restored = score_module.score_only(state,graph,graph,config,max_buffer_bytes=8*1024**2)
    timings['restored_score_seconds'] = time.monotonic()-start
    assert restored == result
    record = {'status':'complete_synthetic_full_match_probe','nodes_each':N,
        'pair_entries':N*N,'edges_each':0,'matching_iterations':result.iterations,
        'convergence':result.convergence,'score':result.score,'annealing_calls':calls,
        'annealing_operations':operations,'hardening_chunks':chunks,'selected_pairs':N,
        'retained_numeric_state_bytes':sum(state['annealing'][n].nbytes for n in ('V','M','Q')),
        'checkpoint_manifest_sha256':{'checkpoint01':prefix_sha,'checkpoint02':final_sha},
        'checkpoint_logical_bytes':{name:sum(p.stat().st_size for p in (HERE/name).rglob('*') if p.is_file())
            for name in ('checkpoint01','checkpoint02')},
        'soft_matrix_sha256':soft,'uniform_matrix_max_absolute_error':error,
        'timings':timings,'matching_complete':True,
        'qualification':'Fresh zero-edge synthetic graph only. Full schedule/hardening and scalar score completed; no nonzero edge, real-hub, dictionary, MCM, neural, GPU or financial feasibility inference. Production backend and scientific capacity unchanged.'}
    write(HERE/'result.json',record)
    print(json.dumps(record),flush=True)


if __name__ == '__main__':
    main()
