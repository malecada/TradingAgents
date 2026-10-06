"""Changed scalar domains only; original synthetic metadata remains read-only."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-resource-input-builder02-2026-10-06'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
before=load('before',OLD/'build_inputs02.py');after=load('after',HERE/'build_inputs03.py')
spec=json.loads((OLD/'SYNTHETIC_SPEC02.json').read_bytes());root=F/'real-data-pilot-resource-input-builder01-2026-10-06/synthetic02'
original=before.build(root,spec)
# Exact one-row RED02 witness: original semantic replay needs 2560 B / 2 credits.
g={w:{'rows':1,'hash':str(i)*64} for i,w in enumerate(before.WEEKS,1)}
selection=copy.deepcopy(spec['typed_allocations'])
for kinds in selection['by_week'].values():
 kinds['score-tail-f64'].update(max_preserved_bytes=2560,max_recovered_bytes=1,max_chunks=1,max_operations=1)
before.typed_budget(g,selection)
try:after.typed_budget(g,selection)
except ValueError as e:assert 'typed allocation below' in str(e);red=str(e)
else:raise AssertionError('mandatory semantic replay omission survived')
for kinds in selection['by_week'].values():kinds['score-tail-f64'].update(max_recovered_bytes=2560,max_chunks=2)
_,_,low=after.typed_budget(g,selection)
assert all(v['score-tail-f64']=={'preserved_bytes':2560,'recovered_bytes':2560,'chunks':2,'operations':1} for v in low.values())
fixed=copy.deepcopy(spec);store=fixed['physical_store']
store.update(typed_attempt_metadata_bytes=7*5*4*8192,remaining_control_inventory={'stream_tail_batch_headers_bytes':1000000,'producer_output_controls_bytes':1000000,'other_selected_controls_bytes':1000000},additional_scratch_bytes=0)
result=after.build(root,fixed)
# Existing generous fixture quotas already include actual replay. No transport,
# model, method, membership, prices/scaler inputs or job limits are changed.
assert result['inputs']==original['inputs']
assert result['opaque_references']==original['opaque_references']
assert result['capacity_lower_bounds']['shared']==original['capacity_lower_bounds']['shared']
assert result['capacity_lower_bounds']['retained_local_lower_bounds']['typed_attempt_metadata_bytes']==7*5*4*8192
refusals=[]
def reject(value,message):
 try:after.build(root,value)
 except ValueError as e:assert message in str(e),(message,str(e));refusals.append(str(e))
 else:raise AssertionError(message)
for key in ('typed_attempt_metadata_bytes','caller_scratch_bytes'):
 bad=copy.deepcopy(fixed);bad['physical_store'][key]=result['capacity_lower_bounds']['retained_local_lower_bounds'][key]-1
 reject(bad,'retained local component underfunded: '+key)
bad=copy.deepcopy(fixed);del bad['physical_store']['remaining_control_inventory']['other_selected_controls_bytes'];reject(bad,'complete remaining control declarations required')
bad=copy.deepcopy(fixed);bad['physical_store']['additional_scratch_bytes']=None;reject(bad,'explicit finite additional scratch declaration required')
bad=copy.deepcopy(fixed);bad['physical_store']['remaining_control_inventory']['other_selected_controls_bytes']=64*1024**3;reject(bad,'common store allocation exceeded')
# Non-tiny scalar phase witness: full original 65536-cell batch plus near-8MiB
# pair source/snapshot/readback exceeds the old three-archive-extent floor.
big=copy.deepcopy(result['graphs']);alloc=copy.deepcopy(fixed['typed_allocations'])
for v in big.values():v['rows']=100000
for kinds in alloc['by_week'].values():
 for b in kinds.values():b.update(max_operations=10000,max_preserved_bytes=10**10,max_recovered_bytes=10**10,max_chunks=10000)
pair_chunk=(8*1024**2//168)*168
buffer=after.selected_buffers(big,alloc,pair_chunk);phase=next(iter(buffer.values()))
assert phase['selected_payload_overlap_upper_bytes']==3*pair_chunk+65536*(80+8)>3*after.ARCHIVE_MAX_BYTES
change=json.loads((HERE/'CHANGE03.json').read_bytes());body=(HERE/'build_inputs03.py').read_text()
for e in reversed(change['literal_edits']):assert body.count(e['after'])==1;body=body.replace(e['after'],e['before'])
assert hashlib.sha256(body.encode()).hexdigest()==change['before_sha256']
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
record={'red02':red,'green03_tail_required':next(iter(low.values()))['score-tail-f64'],'all_eight_generated_inputs_and_opaque_references_unchanged':True,'unchanged_shared_transport_allowances':result['capacity_lower_bounds']['shared'],'retained_local_lower_bounds':result['capacity_lower_bounds']['retained_local_lower_bounds'],'non_tiny_selected_overlap_witness_bytes':phase['selected_payload_overlap_upper_bytes'],'old_scratch_floor_bytes':3*after.ARCHIVE_MAX_BYTES,'refusals':refusals,'exact_inverse':True,'scope':'pure synthetic metadata; no capacity or authority claim'}
(HERE/'CHECK03.json').write_bytes(after.raw(record));(HERE/'SYNTHETIC_SPEC03.json').write_bytes(after.raw(fixed));(HERE/'SYNTHETIC_DRAFT03.json').write_bytes(after.raw(result));print(json.dumps(record,indent=2))
