"""One full synthetic chain matching run with periodic retained checkpoints."""
from pathlib import Path
import gc,hashlib,importlib.util,json,math,os,shutil,sys,time
import numpy as np
from oracle import chain_score
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.resources import assert_guarded_worker,GIB
from tradingagents.research.onchain_replication.environment import inventory
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;N=2000
POLICY=dict(max_state_bytes=128*1024**2,normalization_chunk_entries=65536,hardening_chunk_entries=65536,hardening_buffer_bytes=80*1024**2)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024**2):h.update(chunk)
    return h.hexdigest()
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def checkpoint(m,state,name,graph,config,records):
    if len(records)>=14 or sum(r['logical_bytes'] for r in records.values())+128*1024**2>2*GIB:raise ValueError('total checkpoint allowance exceeded')
    if shutil.disk_usage(ROOT).free<10*GIB+144*1024**2:raise ValueError('checkpoint disk headroom unavailable')
    before={'phase':state['phase'],'annealing':{k:state['annealing'][k] for k in ('phase','cursor','iterations','beta')},'hardening':None}
    if state['hardening'] is not None:before['hardening']={k:state['hardening'][k] for k in ('phase','cursor','pairs')}
    started=time.monotonic();digest=m.save(state,HERE/name,graph,graph,config,max_checkpoint_bytes=128*1024**2);saved=time.monotonic()-started
    mapping=getattr(state['hardening']['order'],'_mmap',None) if state['hardening'] is not None else None
    m.close(state)
    if mapping is not None:assert mapping.closed
    closed=mapping.closed if mapping is not None else None
    del state,mapping;gc.collect()
    started=time.monotonic();restored=m.load(HERE/name,graph,graph,config,expected_sha256=digest,**POLICY);loaded=time.monotonic()-started
    assert restored['phase']==before['phase'] and {k:restored['annealing'][k] for k in before['annealing']}==before['annealing']
    if before['hardening'] is not None:assert {k:restored['hardening'][k] for k in before['hardening']}==before['hardening']
    logical=sum(p.stat().st_size for p in (HERE/name).rglob('*') if p.is_file());assert logical<=128*1024**2
    records[name]={'manifest_sha256':digest,'logical_bytes':logical,'phase':restored['phase'],'annealing_iterations':restored['annealing']['iterations'],'save_seconds':saved,'load_seconds':loaded,'prior_mapping_closed':closed}
    write(HERE/(name+'-receipt.json'),records[name]);print(json.dumps({'checkpoint':name,**records[name]}),flush=True)
    return restored

def main():
    assert_guarded_worker(HERE/'guard01',sys.orig_argv,required_paths=[ROOT],wall_seconds=1800,memory_max_bytes=GIB,memory_high_bytes=3*GIB//4,disk_floor_bytes=10*GIB)
    for name,h in json.loads((HERE/'bindings.json').read_bytes()).items():assert sha(ROOT/name)==h,name
    assert inventory(ROOT)==json.loads((HERE/'environment.json').read_bytes())
    write(HERE/'started.json',{'pid':os.getpid(),'at_unix':time.time(),'qualification':'Fresh full-schedule directed-chain fixture. No empirical claim or historical profile rerun.'})
    graph=GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z','2024-01-09T00:00:00Z',('a'*64,),'b'*64,tuple(map(str,range(N))),np.zeros((N,1)),np.stack((np.arange(N-1,dtype=np.int64),np.arange(1,N,dtype=np.int64))),np.ones((N-1,1)),N-1,N-1,{})
    config=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes());assert config['max_pair_entries']==N*N
    beta=config['beta0'];expected_iterations=0
    while beta<=config['beta_final'] and expected_iterations<config['max_iterations']:expected_iterations+=1;beta*=1+config['beta_rate']
    assert expected_iterations==48 and beta>config['beta_final']
    expected_operations=N*N+48*((N-1)**2+251);assert expected_operations==195820096
    spec=importlib.util.spec_from_file_location('edge_ranked_composite',HERE.with_name('matching-ranked-composite-2026-09-30')/'combined.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    records={};timings={};started=time.monotonic();state=m.create(graph,graph,config,**POLICY);timings['create_seconds']=time.monotonic()-started
    operations=calls=0;started=time.monotonic()
    while state['phase']=='annealing':
        operations+=m.advance(state,graph,graph,config,max_operations=4_000_000);calls+=1;assert calls<=49
        if calls%4==0 and state['phase']=='annealing':state=checkpoint(m,state,f'annealing-{calls:02d}',graph,config,records)
    timings['annealing_rank_and_periodic_checkpoints_seconds']=time.monotonic()-started
    assert operations==expected_operations and calls==49 and state['annealing']['iterations']==48
    error=float(np.max(np.abs(state['annealing']['M'].sum(axis=0)-1)));assert error<1e-12
    soft=hashlib.sha256(memoryview(state['annealing']['M']).cast('B')).hexdigest()
    started=time.monotonic();entries=m.advance(state,graph,graph,config,max_operations=65536);timings['hardening_prefix_seconds']=time.monotonic()-started
    assert 0<entries<=65536
    state=checkpoint(m,state,'checkpoint01',graph,config,records)
    started=time.monotonic()
    while state['phase']!='done':
        used=m.advance(state,graph,graph,config,max_operations=65536);assert used>0;entries+=used;assert entries<=N*N
    timings['hardening_remainder_seconds']=time.monotonic()-started
    conserved,expected_score=chain_score(state['hardening']['pairs'],N,config['alpha'])
    started=time.monotonic();result=m.score_only(state,graph,graph,config,max_buffer_bytes=8*1024**2);timings['score_seconds']=time.monotonic()-started
    assert abs(result.score-expected_score)<=1e-12 and result.iterations==48 and result.convergence=='temperature_complete'
    state=checkpoint(m,state,'checkpoint02',graph,config,records)
    assert state['phase']=='done' and hashlib.sha256(memoryview(state['annealing']['M']).cast('B')).hexdigest()==soft
    assert m.score_only(state,graph,graph,config,max_buffer_bytes=8*1024**2)==result
    record={'status':'complete_synthetic_full_ranked_chain_probe','nodes_each':N,'edges_each':N-1,'pair_entries':N*N,'matching_iterations':48,'annealing_calls':calls,'annealing_operations':operations,'edge_pair_updates':48*(N-1)**2,'hardening_entries_scanned':entries,'selected_pairs':len(state['hardening']['pairs']),'conserved_directed_chain_edges':conserved,'independent_chain_score':expected_score,'score':result.score,'convergence':result.convergence,'retained_numeric_state_bytes':sum(state['annealing'][n].nbytes for n in ('V','M','Q'))+state['hardening']['order'].nbytes,'soft_matrix_sha256':soft,'column_normalization_max_absolute_error':error,'checkpoints':records,'total_checkpoint_logical_bytes':sum(r['logical_bytes'] for r in records.values()),'timings':timings,'qualification':'Fresh full constant-feature directed-chain fixture only; not real-hub/dictionary/MCM/neural/GPU/financial feasibility or a controlled speedup. Atomic sort and stage counters are not uniform wall-time units. Production/scientific capacity unchanged.'}
    mapping=state['hardening']['order']._mmap;m.close(state);assert mapping.closed;record['final_mapping_explicitly_closed']=True
    write(HERE/'result.json',record);print(json.dumps({'result':record}),flush=True)
if __name__=='__main__':main()
