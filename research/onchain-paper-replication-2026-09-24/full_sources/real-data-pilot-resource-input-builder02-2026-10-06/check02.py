"""One dimensional regression; no numerical, network or authority execution."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OLD=HERE.parent/'real-data-pilot-resource-input-builder01-2026-10-06'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
before=load('builder01',OLD/'build_inputs01.py');after=load('builder02',HERE/'build_inputs02.py')
spec=json.loads((OLD/'SYNTHETIC_SPEC01.json').read_bytes());root=OLD/'synthetic02';base=before.build(root,spec)
# Small artificial original graphs, very large allowed cumulative traffic.
# No new allowance is selected for an actual job; both versions see the same caps.
large=copy.deepcopy(spec);network=1024**4
large['transport_limits']['max_payload_bytes']=network
large['transport_limits']['max_diagnostic_bytes']=network+after.TRANSPORT_META*large['transport_limits']['max_commands']
try:before.build(root,large)
except ValueError as error:
    assert str(error)=='all selected control reservations must share physical budget';red=str(error)
else:raise AssertionError('original cumulative/local conflation not reproduced')
fixed=copy.deepcopy(large);store=fixed['physical_store'];store.update(retained_diagnostic_bytes=after.TRANSPORT_META*large['transport_limits']['max_commands']+after.ARCHIVE_MAX_BYTES,caller_scratch_bytes=3*after.ARCHIVE_MAX_BYTES,allocation_overhead_bytes=64*1024**2)
result=after.build(root,fixed)
assert result['inputs']['transport']['max_payload_bytes']==large['transport_limits']['max_payload_bytes']
assert result['inputs']['transport']['max_diagnostic_bytes']==large['transport_limits']['max_diagnostic_bytes']
assert all(result['inputs'][k]==v for k,v in base['inputs'].items() if k!='transport')
refusals=[]
for field in ('retained_diagnostic_bytes','caller_scratch_bytes','reserved_control_bytes'):
    bad=copy.deepcopy(fixed);bad['physical_store'][field]=result['capacity_lower_bounds']['retained_local_lower_bounds'][field]-1
    try:after.build(root,bad)
    except ValueError as error:
        assert str(error)=='retained local component underfunded: '+field;refusals.append(field)
    else:raise AssertionError('underfunded '+field)
bad=copy.deepcopy(fixed);bad['physical_store']['allocation_overhead_bytes']=64*1024**3
try:after.build(root,bad)
except ValueError as error:assert str(error)=='common store allocation exceeded';refusals.append('allocation overhead exceeds unchanged root budget')
else:raise AssertionError('allocation budget bypass')
change=json.loads((HERE/'CHANGE02.json').read_bytes());body=(HERE/'build_inputs02.py').read_text()
for e in reversed(change['literal_edits']):assert body.count(e['after'])==1;body=body.replace(e['after'],e['before'])
assert hashlib.sha256(body.encode()).hexdigest()==change['before_sha256']
# Read constant assignments only; never import scientific/transport modules.
def constant(path,name):
    t=ast.parse(path.read_text());node=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
    return eval(compile(ast.Expression(node.value),str(path),'eval'),{'__builtins__':{}})
assert after.ARCHIVE_MAX_BYTES==constant(ROOT/'tradingagents/research/onchain_replication/score_batches.py','MAX_CHUNK_BYTES')==8*1024**2
assert after.TRANSPORT_META==constant(ROOT/'tradingagents/research/onchain_replication/archive_dispatch.py','META')
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
record={'red01':red,'green02':'passed','network_allowance_unchanged':network,'transport_diagnostic_cap_unchanged':large['transport_limits']['max_diagnostic_bytes'],'retained_local_lower_bounds':result['capacity_lower_bounds']['retained_local_lower_bounds'],'declared_logical_growth_bytes':result['capacity_lower_bounds']['declared_logical_growth_bytes'],'declared_allocated_growth_bytes':result['capacity_lower_bounds']['declared_allocated_growth_bytes'],'all_other_generated_inputs_equal_to_original_fixture':True,'refusals':refusals,'exact_inverse':True,'scope':'synthetic declared allowances only; not measured capacity or executed traffic'}
(HERE/'CHECK02.json').write_bytes(after.raw(record));(HERE/'SYNTHETIC_SPEC02.json').write_bytes(after.raw(fixed));(HERE/'SYNTHETIC_DRAFT02.json').write_bytes(after.raw(result));print(json.dumps(record,indent=2))
