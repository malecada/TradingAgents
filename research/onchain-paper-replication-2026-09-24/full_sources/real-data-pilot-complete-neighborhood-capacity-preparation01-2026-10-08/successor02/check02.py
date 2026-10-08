"""Focused metadata-only regression for three persistent binary file extents."""
import ast
import json
from pathlib import Path
import struct
import sys
from capacity import prepare,digest
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[4]/'tradingagents/research/onchain_replication'
# Exact one-insertion successor; no unrelated source change.
assert (HERE/'capacity.py').read_text().replace((HERE/'ADDITION.txt').read_text(),'')==(HERE.parent/'capacity.py').read_text()
# Read/execute only the original scalar record-format declarations.
for name,names,expected in [('score_tail.py',{'RECORD_BYTES','FRAME'},80),('compact_pair_log.py',{'FRAME','RECORD_BYTES'},168)]:
    nodes=[n for n in ast.parse((SOURCE/name).read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
    env={'struct':struct};exec(compile(ast.Module(body=nodes,type_ignores=[]),name,'exec'),env)
    assert env['RECORD_BYTES']==expected and env['FRAME'].size+32==expected

def graph(i,n,e):return dict(graph_sha256=f'{i:064x}',nodes=n,edges=e,node_features=2,edge_features=1,node_itemsize=8,edge_itemsize=8)
topology=dict(hop_depth=1,direction='weak',includes_center=True,graphs=[graph(1,100000,100000)|dict(maximum_cardinality=3,maximum_center_index=0)])
motifs=dict(dictionary_sha256='a'*64,dictionary_config_sha256='b'*64,representatives=[graph(2,2,1)|dict(motif_index=0)])
limits=dict(extraction_limit=10000,max_pair_entries=4_000_000,max_state_bytes=1024**2,normalization_chunk_entries=65536,
            hardening_buffer_bytes=80*1024**2,max_score_buffer_bytes=1024**2,max_checkpoint_bytes=256*1024,max_file_bytes=4194304,
            max_buffer_bytes=439582708,max_output_bytes=289981568,max_numeric_bytes=729564276,max_entries=100_000_000,
            edge_chunk=65536,score_chunk_edges=65536,score_chunk_cells=65536,log_chunk_events=49152,max_total_checkpoints=160)
def run(cap):return prepare(topology,motifs,expected_topology_sha256=digest(topology),expected_motifs_sha256=digest(motifs),limits=limits|{'max_file_bytes':cap})
expected={'score_tail_records_single_file_bytes':5242880,'float64_score_data_single_file_bytes':524288,'pair_event_chunk_single_file_bytes':8257536}
result=run(4194304)
for name,size in expected.items():
    assert result['universal_component_envelopes'][name]['required']==size
    assert any(x['requirement']==name for x in result['refusals'])==(size>4194304)
    assert not any(x['requirement']==name for x in run(size)['refusals'])
    assert any(x['requirement']==name for x in run(size-1)['refusals'])
assert result['universal_component_envelopes']['persistence_json_single_file_allowance_bytes']['required']==8192
# Final partial chunks use actual possible records, no fictional full payload.
topology['graphs'][0].update(nodes=3,edges=2)
partial=run(4194304)['universal_component_envelopes']
assert partial['score_tail_records_single_file_bytes']['required']==3*80
assert partial['float64_score_data_single_file_bytes']['required']==3*8
assert partial['pair_event_chunk_single_file_bytes']['required']==(2*3+160)*168
assert not result['execution_admitted'] and not result['complete_resource_envelope_proven']
for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
print(json.dumps({'status':'PASS','source_record_widths_verified':True,'source_inverse_byte_identical':True,
                  'physical_file_cap':4194304,'full_chunk_bytes':expected,
                  'new_refusals_at_cap':['score_tail_records_single_file_bytes','pair_event_chunk_single_file_bytes'],
                  'exact_and_one_byte_below_thresholds':'PASS','partial_chunks':'PASS','numerical_imports':False},indent=2))
