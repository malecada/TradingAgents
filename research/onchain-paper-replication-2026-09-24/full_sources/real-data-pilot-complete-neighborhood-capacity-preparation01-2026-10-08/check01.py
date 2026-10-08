"""Small deterministic metadata tests only; zero numerical imports or real data."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from capacity import prepare, digest, MetadataUnavailable

HERE=Path(__file__).resolve().parent
SRC=HERE.parents[3]/'tradingagents/research/onchain_replication'

def graph(i,n,e):
    return dict(graph_sha256=f'{i:064x}',nodes=n,edges=e,node_features=2,edge_features=1,node_itemsize=8,edge_itemsize=8)

T=dict(hop_depth=1,direction='weak',includes_center=True,graphs=[graph(1,10,20)|dict(maximum_cardinality=3,maximum_center_index=0)])
M=dict(dictionary_sha256='a'*64,dictionary_config_sha256='b'*64,representatives=[graph(2,2,1)|dict(motif_index=0)])
L=dict(extraction_limit=10000,max_pair_entries=4_000_000,max_state_bytes=1024**2,normalization_chunk_entries=65536,
       hardening_buffer_bytes=80*1024**2,max_score_buffer_bytes=1024**2,max_checkpoint_bytes=256*1024,max_file_bytes=4*1024**2,
       max_buffer_bytes=128*1024**2,max_output_bytes=128*1024**2,max_numeric_bytes=256*1024**2,max_entries=100_000_000,
       edge_chunk=2,score_chunk_edges=2,score_chunk_cells=100,log_chunk_events=100,max_total_checkpoints=10)

def run(t=T,m=M,l=L):return prepare(t,m,expected_topology_sha256=digest(t),expected_motifs_sha256=digest(m),limits=l)
def reject(call,text):
    try:call()
    except ValueError as error:assert text in str(error),(text,str(error))
    else:raise AssertionError('missing refusal '+text)

before=copy.deepcopy((T,M,L));small=run();assert (T,M,L)==before
assert small['reported_limits_satisfied'] and not small['execution_admitted']
w=small['universal_component_envelopes']
assert w['pair_entries']['required']==6 and w['retained_pair_state_bytes']['required']==192
assert w['normalization_axis_entries']['required']==6
assert w['logical_checkpoint_bytes']['required']==192+512+3*65536
assert w['checkpoint_single_array_file_bytes']['required']==176
assert w['index_and_complete_output_upper_bytes']['required']==(16*(20+10+1)+16*20+40*11+4*10+2*(64+32+16))+2*(3*16+20*24)
assert small['storage_components']['all_target_pair_occurrences']==10
# Seven wholly synthetic targets; every target x every motif is represented.
seven=copy.deepcopy(T);seven['graphs']=[graph(i+10,100+i,200+i)|dict(maximum_cardinality=i+2,maximum_center_index=i) for i in range(7)]
two=copy.deepcopy(M);two['representatives'].append(graph(30,3,4)|dict(motif_index=1))
r=run(seven,two);assert len(r['pairs'])==14
assert r['universal_component_envelopes']['pair_entries']['required']==8*3
# Synthetic hub-sized dimensions. Motif32 is invented for a test, NOT preserved motif metadata.
hub=copy.deepcopy(T);hub['graphs']=[graph(40,350110,1_000_000)|dict(maximum_cardinality=350110,maximum_center_index=5)]
fake_motif=copy.deepcopy(M);fake_motif['representatives']=[graph(41,32,64)|dict(motif_index=0)]
r=run(hub,fake_motif)
refused={v['limit_field'] for v in r['refusals']}
assert {'extraction_limit','max_pair_entries','max_state_bytes','normalization_chunk_entries','max_checkpoint_bytes','max_file_bytes'} <= refused
assert r['universal_component_envelopes']['normalization_axis_entries']['required']==700220
# Metadata-only upper bound detects the fixed hardening manifest seam too.
large=copy.deepcopy(T);large['graphs']=[graph(50,10000,20000)|dict(maximum_cardinality=10000,maximum_center_index=0)]
wide=copy.deepcopy(M);wide['representatives']=[graph(51,10000,20000)|dict(motif_index=0)]
assert any(x['limit_field']=='fixed_hardening_manifest_limit' for x in run(large,wide)['refusals'])
# Exact requirement boundary passes; one-byte/entry deficit reports refusal.
for field,entry in [('max_state_bytes','retained_pair_state_bytes'),('max_pair_entries','pair_entries'),
                    ('normalization_chunk_entries','normalization_axis_entries'),('max_checkpoint_bytes','logical_checkpoint_bytes')]:
    limits=copy.deepcopy(L);need=small['universal_component_envelopes'][entry]['required'];limits[field]=need
    assert not any(v['limit_field']==field for v in run(l=limits)['refusals'])
    limits[field]-=1;assert any(v['limit_field']==field for v in run(l=limits)['refusals'])
reject(lambda:prepare(T,None,expected_topology_sha256=digest(T),expected_motifs_sha256=None,limits=L),'required')
reject(lambda:prepare(T,M,expected_topology_sha256='0'*64,expected_motifs_sha256=digest(M),limits=L),'digest differs')
for mutate,text in [(lambda x:x.update(hop_depth=2),'weak-one-hop'),
                    (lambda x:x['graphs'][0].update(nodes=True),'integer'),
                    (lambda x:x['graphs'][0].update(maximum_cardinality=11),'outside'),
                    (lambda x:x['graphs'].append(copy.deepcopy(x['graphs'][0])),'duplicate')]:
    bad=copy.deepcopy(T);mutate(bad);reject(lambda:run(bad),text)
bad=copy.deepcopy(M);bad['representatives']=[];reject(lambda:run(m=bad),'unavailable')
bad=copy.deepcopy(M);bad['representatives'][0]['motif_index']=2;reject(lambda:run(m=bad),'ordered')
bad=copy.deepcopy(M);bad['representatives'][0]['node_features']=3;reject(lambda:run(m=bad),'dimensions')
bad=copy.deepcopy(T);bad['graphs'][0]['edges']=2**63-1;reject(lambda:run(bad),'derived capacity')
# Source policy formulas: execute only scalar functions extracted by AST.
def scalar(file,name,env):
    node=next(n for n in ast.parse((SRC/file).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),env);return env[name]
normal=scalar('matching_annealing.py','normalization_policy',{})
for n,m in ((3,2),(350110,32),(350110,1),(1,100)):
    needed=max(m,n if m==1 else 2*n);normal(n,m,needed);reject(lambda:normal(n,m,needed-1),'axis')
hard=scalar('matching_hardening.py','explicit_bytes',{})
assert hard(3,2)==small['universal_component_envelopes']['hardening_explicit_bytes']['required']
# Optional extraction policy: execute only validator and local config-selection AST.
kernel=ast.parse((HERE/'imported_kernel.py').read_text())
def need(ok,message):
    if not ok:raise ValueError(message)
env={'require':need}
validator=next(n for n in kernel.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy')
exec(compile(ast.Module(body=[validator],type_ignores=[]),'kernel-validator','exec'),env)
policy=dict(schema_version=1,max_buffer_bytes=100,edge_chunk=2,max_output_bytes=100,max_numeric_bytes=200)
assert env['validate_policy'](policy,2)==policy
for value in (0,True,-1,2**63):reject(lambda:env['validate_policy'](policy|{'extraction_limit':value},2),'extraction')
function=next(n for n in kernel.body if isinstance(n,ast.FunctionDef) and n.name=='mcm')
start=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='extraction_config' for t in n.targets))
selection=ast.Module(body=function.body[start:start+2],type_ignores=[])
original=dict(hop_depth=1,maximum_neighborhood_nodes=10000,sample_count=32)
for requested in (None,350110):
    local=dict(require=need,dictionary=SimpleNamespace(config=original),policy={} if requested is None else {'extraction_limit':requested})
    exec(compile(selection,'selection','exec'),local)
    assert original==dict(hop_depth=1,maximum_neighborhood_nodes=10000,sample_count=32)
    assert local['extraction_config']['hop_depth']==1 and local['extraction_config']['sample_count']==32
    assert local['extraction_config']['maximum_neighborhood_nodes']==(10000 if requested is None else requested)
    assert (local['extraction_config'] is original)==(requested is None)
for requested in (9999,):
    local=dict(require=need,dictionary=SimpleNamespace(config=original),policy={'extraction_limit':requested})
    reject(lambda:exec(compile(selection,'selection','exec'),local),'reduce')
for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
assert 'numpy' not in __import__('sys').modules and 'torch' not in __import__('sys').modules
print(json.dumps({'status':'PASS','scope':'synthetic metadata only; preserved motif dimensions not supplied or inferred',
                  'all_seven_synthetic_pairs_checked':14,'synthetic_hub_refused_limits':sorted(refused),
                  'optional_extraction_default_preserved':True,'numerical_imports':False},indent=2))
