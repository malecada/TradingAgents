import copy,json
from pathlib import Path
from entry_conditions import check
p=Path(__file__).resolve().parent
r=json.loads((p/'CAPACITY01.json').read_text());j=r['joined']
assert r['sidecar_logical_upper']==sum(x['count']*x['max_body_bytes'] for x in r['sidecar_roster'])
assert j['directory_plus_unmodeled_concurrent_writer_remaining_bytes']==min(j['remaining_under_writer_cap'],j['remaining_under_recorded_free_minus_floor'])
a=dict(mcm={'schema_version':6,'batched':dict(retention='typed-grouped-recover-before-retire-v1',group_batches=16,batch_cells=4096,max_body_bytes=1024)},output={'schema_version':1},pilot={'population_scope':'resource_pilot_subset'},storage_limits=dict(max_logical_bytes=16*1024**3,max_allocated_bytes=20*1024**3),paths=['/synthetic/path'],integer_fields=[1],unmodeled_directory_allocated_bytes=0,other_writer_reserved_bytes=0,remaining_bytes=1)
assert check(**a)['capacity_admitted'] is False
cases=[]
for key,value in [('unmodeled_directory_allocated_bytes',None),('other_writer_reserved_bytes',None),('unmodeled_directory_allocated_bytes',2),('paths',['/synthetic/../path']),('integer_fields',[True])]:
 x=copy.deepcopy(a);x[key]=value
 try:check(**x)
 except ValueError:cases.append(key)
 else:raise AssertionError('refusal missing')
print(json.dumps({'status':'PASS_SOURCE_ARITHMETIC_ONLY','refusals':cases,'genuine_entry_executed':False}))
