"""Bounded synthetic metadata and real engine-I/O boundary checks; no arrays."""
import runpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent
mode,case=sys.argv[1:3];sys.argv=[str(H/'probe01.py'),mode]
runpy.run_path(sys.argv[0],run_name='__main__')
import copy,hashlib,importlib.util,json,tempfile
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication import compact_policy
package='tradingagents.research.onchain_replication'
assert package+'.matching_checkpoint' not in sys.modules
assert pair.LIMIT==65536
assert pair.POLICY_FIELDS=={'max_state_bytes','normalization_chunk_entries','hardening_chunk_entries','hardening_buffer_bytes','max_score_buffer_bytes','chunk_edges','max_checkpoint_bytes','max_publications','total_checkpoint_bytes'}
assert pair.BACKEND==dict(name='scalar_ranked_typed_graph',version=2,device='cpu',affinity='scalar_float64',normalization='scipy_float64',hardening='stable_descending_row_major',objective='sparse_scalar_float64',output='float64_score',checkpoint_schema=3)
p=dict(schema_version=1,backend='resident-native-compact-current-owner-v1',pair={'max_state_bytes':100000,'normalization_chunk_entries':4,'hardening_chunk_entries':2,'hardening_buffer_bytes':4096,'max_score_buffer_bytes':4096,'chunk_edges':2,'max_checkpoint_bytes':400000,'max_publications':10,'total_checkpoint_bytes':5000000},schedule={'operations_per_call':10000,'calls_per_checkpoint':64,'max_checkpoints':4,'max_total_checkpoints':10,'max_total_checkpoint_bytes':6000000},log={'chunk_events':16,'max_events':200,'max_pairs':64,'max_logical_bytes':60000},score_chunk_cells=4,max_retained_logical_bytes=10000000)
if case=='metadata':
 assert compact_policy.validate(p,kind='dictionary',pairs=30)['logical_reservation_bytes']==6060000
 for mutation in ('missing','boolean','edge_chunk','reservation'):
  q=copy.deepcopy(p)
  if mutation=='missing':del q['pair']['chunk_edges']
  elif mutation=='boolean':q['pair']['chunk_edges']=True
  elif mutation=='edge_chunk':q['pair']['chunk_edges']=65537
  else:q['pair']['total_checkpoint_bytes']=1
  try:compact_policy.validate(q,kind='dictionary',pairs=30)
  except ValueError:pass
  else:raise AssertionError('mutation accepted: '+mutation)
 assert package+'.matching_checkpoint' not in sys.modules
elif case=='write_boundary':
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'metadata.json';value={'synthetic':True}
  result=pair.write(path,value)
  assert json.loads(path.read_text())==value and result==hashlib.sha256(path.read_bytes()).hexdigest()
  try:pair.write(path,value)
  except FileExistsError:pass
  else:raise AssertionError('exclusive write overwritten')
 assert package+'.matching_checkpoint' in sys.modules and 'scipy.special' in sys.modules
elif case=='compact_matcher_boundary':
 full=package+'.compact_matcher';p=H/'compact_matcher.py'
 spec=importlib.util.spec_from_file_location(full,p);m=importlib.util.module_from_spec(spec);sys.modules[full]=m;spec.loader.exec_module(m)
 assert m.engine is sys.modules[package+'.matching_checkpoint']
 assert m.engine.__file__.endswith('/tradingagents/research/onchain_replication/matching_checkpoint.py')
else:raise AssertionError('unknown case')
assert 'torch' not in sys.modules
print(json.dumps({'case':case,'status':'passed','numerical_arrays_evaluated':False}),flush=True)
