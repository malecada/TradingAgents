"""Finite synthetic component profile; incomplete hardening is intentional."""
from pathlib import Path
import gc
import hashlib
import importlib.util
import json
import os
import time
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.resources import assert_guarded_worker,GIB
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
N=2000

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()

def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
    assert_guarded_worker(HERE/'guard01',__import__('sys').orig_argv,required_paths=[ROOT],wall_seconds=180,memory_max_bytes=GIB,memory_high_bytes=3*GIB//4,disk_floor_bytes=10*GIB)
    for name,h in json.loads((HERE/'bindings.json').read_bytes()).items():assert sha(ROOT/name)==h,name
    write(HERE/'started.json',{'pid':os.getpid(),'at_unix':time.time(),'qualification':'Synthetic 2000-square directed-chain constant-feature graph only; not a research claim or whole-match completion.'})
    graph=GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z','2024-01-09T00:00:00Z',('a'*64,),'b'*64,tuple(map(str,range(N))),np.zeros((N,1)),np.stack((np.arange(N-1,dtype=np.int64),np.arange(1,N,dtype=np.int64))),np.ones((N-1,1)),N-1,N-1,{})
    config=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes())
    assert config['max_pair_entries']==4000000
    config['max_iterations']=2 # Explicit synthetic prefix, never a scientific config edit.
    spec=importlib.util.spec_from_file_location('probe_composite',HERE.with_name('matching-composite-checkpoints-2026-09-30')/'combined.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    policy=dict(max_state_bytes=128*1024**2,normalization_chunk_entries=65536,hardening_chunk_entries=65536,hardening_buffer_bytes=8*1024**2)
    timings={};start=time.monotonic();s=m.create(graph,graph,config,**policy);timings['create_seconds']=time.monotonic()-start
    start=time.monotonic();operations=0;calls=0
    while s['phase']=='annealing':
        operations+=m.advance(s,graph,graph,config,max_operations=4000000);calls+=1
        assert calls<=8
    timings['annealing_seconds']=time.monotonic()-start
    assert s['phase']=='hardening' and s['annealing']['iterations']==2
    error=float(np.max(np.abs(s['annealing']['M'].sum(axis=0)-1)));assert error<1e-12
    start=time.monotonic();used=m.advance(s,graph,graph,config,max_operations=256);timings['hardening_prefix_seconds']=time.monotonic()-start
    assert used==256 and s['phase']=='hardening'
    pairs=s['hardening']['pairs'];assert len(pairs)==3 and len({u for u,i in pairs})==3 and len({i for u,i in pairs})==3
    before={k:s['hardening'][k] for k in ('phase','cursor','pairs','best_index','best_value')}
    soft=hashlib.sha256(memoryview(s['annealing']['M']).cast('B')).hexdigest()
    start=time.monotonic();digest=m.save(s,HERE/'checkpoint01',graph,graph,config,max_checkpoint_bytes=128*1024**2);timings['save_seconds']=time.monotonic()-start
    del s;gc.collect()
    start=time.monotonic();restored=m.load(HERE/'checkpoint01',graph,graph,config,expected_sha256=digest,**policy);timings['load_seconds']=time.monotonic()-start
    assert {k:restored['hardening'][k] for k in before}==before
    assert hashlib.sha256(memoryview(restored['annealing']['M']).cast('B')).hexdigest()==soft
    logical=sum(f.stat().st_size for f in (HERE/'checkpoint01').rglob('*') if f.is_file())
    result={'status':'complete_synthetic_component_probe','nodes_each':N,'pair_entries':N*N,'edges_each':N-1,'edge_pair_updates':2*(N-1)**2,'matching_iterations':2,'annealing_calls':calls,'annealing_operations':operations,'hardening_chunks':used,'selected_pairs':len(pairs),'hardening_cursor':before['cursor'],'retained_numeric_state_bytes':sum(restored['annealing'][n].nbytes for n in ('V','M','Q')),'checkpoint_logical_bytes':logical,'checkpoint_manifest_sha256':digest,'soft_matrix_sha256':soft,'column_normalization_max_absolute_error':error,'timings':timings,'matching_complete':False,'qualification':'Single synthetic component profile including atomic validation/hash/native temporaries under outer guard. Full hardening/scoring, full annealing schedule, real neighborhoods, dictionaries, MCM/neural work and financial fits are not measured. Only synthetic directed-chain edge cross-products are profiled. Retained checkpoint is synthetic; no scientific capacity or production backend changed.'}
    write(HERE/'result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
