"""Tiny offline serialization tests; no real data, Owner, admission or claim."""
import ast, hashlib, importlib, json, shutil, sys, tempfile, types
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
MAIN=Path.cwd()/'tradingagents/research/onchain_replication'
pkg=types.ModuleType('checkpoint_candidate');pkg.__path__=[str(HERE),str(MAIN)];sys.modules[pkg.__name__]=pkg
sys.modules['checkpoint_candidate.contracts']=importlib.import_module('tradingagents.research.onchain_replication.contracts')
engine=importlib.import_module('checkpoint_candidate.matching_checkpoint')
matcher=importlib.import_module('checkpoint_candidate.compact_matcher')
retention=importlib.import_module('checkpoint_candidate.restart_retention')
legacy=importlib.import_module('tradingagents.research.onchain_replication.matching_checkpoint')
from tradingagents.research.onchain_replication.contracts import AttributedGraph

def graph(n):
    return AttributedGraph(tuple(map(str,range(n))),np.arange(n*2,dtype=np.float64).reshape(n,2)/7,
        np.array([range(n-1),range(1,n)],dtype=np.int64),np.ones((n-1,1),dtype=np.float64),'a'*64,'0')
a,b=graph(3),graph(2)
c=dict(max_pair_entries=100,beta0=1.,beta_final=1.,beta_rate=.5,alpha=1.,normalization_iterations=1,solver='algorithm1_literal',max_iterations=2)
p=dict(max_state_bytes=262144,normalization_chunk_entries=16,hardening_chunk_entries=2,hardening_buffer_bytes=4096)
layout=dict(format='sharded-npy-v1',chunk_entries=2)
checks=[]
def check(name,value):
    if not value:raise AssertionError(name)
    checks.append(name)
def same(x,y):
    if isinstance(x,np.ndarray):return x.dtype==y.dtype and x.shape==y.shape and x.tobytes()==y.tobytes()
    if isinstance(x,dict):return x.keys()==y.keys() and all(same(x[k],y[k]) for k in x)
    return x==y

def hashes(path):return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}
def refuse(name,action):
    try:action()
    except (ValueError,OSError,TypeError,KeyError):checks.append(name);return
    raise AssertionError(name+' accepted')

with tempfile.TemporaryDirectory(prefix='checkpoint-synthetic-') as tmp:
    root=Path(tmp)
    state=engine.create(a,b,c,**p)
    for phase in ('annealing','hardening','done'):
        while state['phase']!=phase:engine.advance(state,a,b,c,max_operations=1)
        target=root/phase
        sha=engine.save(state,target,a,b,c,max_checkpoint_bytes=1048576,checkpoint_layout=layout)
        restored=engine.load(target,a,b,c,expected_sha256=sha,checkpoint_layout=layout,**p)
        check(phase+' bitwise roundtrip',same(state,restored))
        policy=p|{'max_checkpoint_bytes':1048576}
        actual=matcher._snapshot(target,sha,{'ordered_pair':engine.ann.identity(a,b,c)},policy,checkpoint_layout=layout)
        check(phase+' snapshot bytes',actual==sum(f.stat().st_size for f in target.rglob('*') if f.is_file()))
        check(phase+' retention tree',retention._tree(target,1048576,checkpoint_layout=layout)['logical_bytes']==actual)
        check(phase+' physical chunk size',all(f.stat().st_size<=2*1024**2+128 for f in target.rglob('*') if f.is_file()))
        old=root/(phase+'-old');new=root/(phase+'-default')
        legacy.save(state,old,a,b,c,max_checkpoint_bytes=1048576)
        engine.save(state,new,a,b,c,max_checkpoint_bytes=1048576)
        check(phase+' exact legacy file bytes',hashes(old)==hashes(new))
        while restored['phase']!='done':engine.advance(restored,a,b,c,max_operations=1)
        reference=legacy.create(a,b,c,**p)
        while reference['phase']!='done':legacy.advance(reference,a,b,c,max_operations=1)
        check(phase+' resumed final state bitwise',same(restored,reference))
        engine.close(restored);legacy.close(reference)
    selected=root/'done'
    sha=hashlib.sha256((selected/'manifest.json').read_bytes()).hexdigest()
    load=lambda:engine.load(selected,a,b,c,expected_sha256=sha,checkpoint_layout=layout,**p)
    file=next((selected/'annealing').glob('*.npy'));raw=file.read_bytes();file.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    refuse('corrupt numeric chunk',load);file.write_bytes(raw)
    extra=selected/'annealing/foreign';extra.write_bytes(b'x');refuse('extra member',load);extra.unlink()
    refuse('layout mismatch',lambda:engine.load(selected,a,b,c,expected_sha256=sha,checkpoint_layout=layout|{'chunk_entries':3},**p))
    file.unlink();file.symlink_to(root/'annealing/annealing/M-00000000.npy');refuse('redirected member',load);file.unlink();file.write_bytes(raw)
    # Ordered extent validator must reject even self-consistent rehashed metadata.
    meta=json.loads((selected/'annealing/manifest.json').read_bytes());desc=meta['files']['M'];desc['chunks'].reverse()
    refuse('chunk permutation',lambda:engine.chunks.validate_descriptor(desc,[3,2],'<f8',layout,'M'))
    check('maximum chunk bytes',engine.chunks.describe([262145],'<f8',dict(format='sharded-npy-v1',chunk_entries=262144),'M')['chunks'][0]['bytes']==2097280)
    # Candidate never substitutes a different arithmetic routine.
    for module,names in [('matching_checkpoint',['create','advance','score_only','result','check']),('matching_annealing',['create','advance','check']),('matching_hardening',['create','advance','check'])]:
        def defs(path):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef)}
        before,after=defs(MAIN/(module+'.py')),defs(HERE/(module+'.py'))
        check(module+' numerical AST unchanged',all(before[n]==after[n] for n in names))
pair=importlib.import_module('checkpoint_candidate.matching_pair')
cp=importlib.import_module('checkpoint_candidate.compact_policy')
policy=p|dict(max_checkpoint_bytes=1048576,max_score_buffer_bytes=4096,chunk_edges=16,max_publications=1,total_checkpoint_bytes=2097152)
sharded=policy|{'checkpoint_layout':layout}
check('compact pair admission accepts explicit layout',pair.policy_check(a,b,c,sharded,allow_checkpoint_layout=True)==sharded)
refuse('legacy pair route refuses layout',lambda:pair.policy_check(a,b,c,sharded))
refuse('invalid layout refuses',lambda:pair.policy_check(a,b,c,policy|{'checkpoint_layout':layout|{'chunk_entries':262145}},allow_checkpoint_layout=True))
schedule=dict(operations_per_call=1,calls_per_checkpoint=1,max_checkpoints=1,max_total_checkpoints=1,max_total_checkpoint_bytes=4194304)
stage=dict(schema_version=1,backend=cp.BACKEND,pair=sharded,schedule=schedule,log=dict(chunk_events=4,max_pairs=1,max_events=4,max_logical_bytes=1048576),score_chunk_cells=1,max_retained_logical_bytes=16777216)
check('compact stage schema accepts layout',cp.validate(stage,kind='mcm',pairs=1)['execution_admitted'] is False)
context={'namespace':'a'*64,'source_commit':'a'*40,'runtime_hash':'b'*64}
check('scope binds embedded layout',matcher.scope(c,context,sharded,'c'*64,schedule)['policy']==matcher.cache_key({'pair':sharded,'schedule':schedule}))
check('new chunk module source pinned',any(name.startswith('checkpoint_chunks.py:') for name in matcher._components()))
# Metadata-only largest observed pair: no large numeric allocation.
large_layout=dict(format='sharded-npy-v1',chunk_entries=262144)
large_policy=policy|{'checkpoint_layout':large_layout}
check('legacy control default unchanged',retention.control_limit(policy)==16384 and retention.generation_control(policy)==retention.GENERATION_CONTROL)
check('explicit bounded control cap',retention.control_limit(large_policy)==65536)
files={}
for directory,names in [('annealing',['M','Q','V']),('hardening',['order'])]:
    for name in names:
        for i in range(33):files[f'{directory}/{name}-{i:08d}.npy']={'bytes':2097280,'sha256':'a'*64,'inode':[2**63-1,2**63-1]}
for name in ('manifest.json','annealing/manifest.json','hardening/manifest.json'):
    files[name]={'bytes':65536,'sha256':'b'*64,'inode':[2**63-1,2**63-1]}
tree={'directories':{name:[2**63-1,2**63-1] for name in ('.','annealing','hardening')},'files':files,'logical_bytes':269100000}
proof={'schema_version':1,'claim_sha256':'c'*64,'generation':2**63-1,'generation_inode':[2**63-1,2**63-1],
    'state_sha256':'d'*64,'tree':tree,'event':{'sha256':'e'*64,'event':{'pair':{'numeric_identity':{'left':'f'*64,'right':'a'*64,'configuration':'b'*64}}}},
    'predecessor':'a'*64,'body_available':True,'restart_eligible':True,'execution_admitted':False}
proof['event']['event'].update(schema_version=1,kind='progress',event_ordinal=2**63-1,generation=2**63-1,state_sha256='a'*64,state={'phase':'hardening','annealing_phase':'done','cursor':2**63-1,'iterations':2**63-1})
proof['event']['event']['pair'].update(ordinal=2**63-1,purpose_sha256='b'*64)
raw=retention._raw(proof,limit=retention.control_limit(large_policy))
large_proof_bytes=len(raw)
check('132-shard proof fits selected control',16384<len(raw)<=65536 and json.loads(raw)==proof)
refuse('132-shard proof legacy control refusal',lambda:retention._raw(proof))
refuse('over64KiB metadata refusal',lambda:retention._raw({'data':'x'*65536},limit=65536))
check('selected generation reservation',retention.generation_control(large_policy)==8*65536+3*65536)
check('scratch body reserve',engine.chunks.io_scratch_bytes(large_layout)==6357376)
refuse('missing sharded I/O scratch reserve',lambda:pair.policy_check(a,b,c,sharded|{'max_state_bytes':192},allow_checkpoint_layout=True))
# Actual isolated retention utility on tiny synthetic data. These fixture hashes
# are not ResearchRun/Owner/Binding objects or scientific authorization.
for selected in (None,layout):
    with tempfile.TemporaryDirectory(prefix='retention-synthetic-') as tmp:
        root=Path(tmp);record_pair=dict(ordinal=0,purpose_sha256='a'*64,numeric_identity=engine.ann.identity(a,b,c))
        rp=p|{'max_checkpoint_bytes':1048576}
        if selected is not None:rp['checkpoint_layout']=selected
        limits=dict(max_generations=2,max_generation_bytes=1048576,max_control_bytes=4194304,max_cumulative_bytes=16777216,max_replay_bytes=1048576,max_replays=1)
        store=retention.Store(root/'store',bindings={k:'a'*64 for k in ('owner','stage','source','runtime','policy')},pair=record_pair,policy=rp,limits=limits,replay_first=True,lease=lambda:None)
        def publish(value):
            event=root/f'event-{value["event_ordinal"]}.json';raw=retention._raw(value);event.write_bytes(raw)
            return retention.EventRef(event,hashlib.sha256(raw).hexdigest())
        state=engine.create(a,b,c,**p)
        store.checkpoint(state,a,b,c,publish_progress=publish)
        engine.advance(state,a,b,c,max_operations=1)
        store.checkpoint(state,a,b,c,publish_progress=publish)
        expected=dict(schema_version=1,kind='complete',pair=record_pair,event_ordinal=3,score=0.,iterations=0,convergence='iteration_cap')
        terminal=store.finish(publish(expected),expected=expected)
        verified=retention.verify(store.root,expected_claim=store.claim_sha256,expected_terminal=terminal)
        check(('legacy' if selected is None else 'sharded')+' actual utility retirement/replay/terminal accounting',verified['generations']==2 and list(verified['retired'])==[0,1] and list(verified['replays'])==[0])
        engine.close(state)
print(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'largest_fixture_proof_bytes':large_proof_bytes,'selected_io_scratch_bytes':engine.chunks.io_scratch_bytes(large_layout),'scope':'tiny synthetic serialization and actual helper inventory; no genuine Owner/admission or full resource measurement'},indent=2))
