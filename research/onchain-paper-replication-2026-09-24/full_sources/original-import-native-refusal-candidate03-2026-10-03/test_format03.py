"""Exact original source functions, stdlib buffer stand-ins; not array/Owner proof."""
import ast,array,hashlib,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent;F=D.parent;ROOT=D.parents[3]
sys.path.insert(0,str(D))
import original_semantics as selected
class Formats(unittest.TestCase):
 def test_metadata_validator_prefix_is_byte_exact_accepted_source(self):
  original=(F/'original-import-fixture-io-candidate02-2026-10-02/original_dictionary.py').read_text().split('\nclass ImportedOriginal:')[0]
  self.assertTrue((D/'original_semantics.py').read_text().startswith(original))
 def test_motif_hash_matches_actual_identity_function_without_numerical_library(self):
  path=ROOT/'tradingagents/research/onchain_replication/matching_identity.py';tree=ast.parse(path.read_text());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('canonical','graph_identity')]
  class Local:pass
  class Weekly:pass
  env={'hashlib':hashlib,'json':json,'AttributedGraph':Local,'GraphSnapshot':Weekly,'validate_attributed':lambda x:None};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
  class Buffer(array.array):pass
  for edges in (0,1):
   record={'node_ids':['nü','β'],'parent_hash':'b'*64,'center_id':'β','node_features':[[1.,-0.,2.,3.],[0.,0.,0.,0.]],'edge_index':[[0],[1]] if edges else [[],[]],'edge_features':[[.5,.25]] if edges else [],'edge_width':2};g=Local()
   for n in ('node_ids','parent_hash','center_id'):setattr(g,n,record[n])
   for n,code,shape in [('node_features','d',(2,4)),('edge_index','q',(2,edges)),('edge_features','d',(edges,2))]:
    b=Buffer(code,[v for row in record[n] for v in row]);b.dtype=SimpleNamespace(kind='f' if code=='d' else 'i',str='<f8' if code=='d' else '<i8');b.shape=shape;b.nbytes=len(b)*8;b.size=len(b);b.flags=SimpleNamespace(c_contiguous=True);setattr(g,n,b)
   expected=env['graph_identity'](g);actual,extent=selected.motif_record_identity(record);self.assertEqual(actual,expected);self.assertEqual(extent,64+32*edges)
 def test_destination_json_encoding_matches_actual_writer(self):
  from refusal_stage import io_json
  p=F/'original-import-fixture-io-candidate02-2026-10-02/score_batches.py';node=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_json');env={'json':json,'META_LIMIT':8192,'_require':lambda v,m:None};exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),env)
  value={'directory':'/test/β','start_sha256':'a'*64,'index':0,'start_cell':0,'cells':64};self.assertEqual(io_json(value),env['_json'](value))
 def test_numeric_count_bool_and_reordered_original_indices_rejected_by_full_record(self):
  from synthetic_original import fixture
  p,b=fixture();v=selected.expected_numeric(p,b)
  self.assertEqual(v['representative_sample_indices'],list(range(32)));self.assertEqual(v['numeric_bytes'],1024);self.assertEqual(len(set(v['ordered_motifs'])),32)
  for field in ('sample_identity','dictionary_identity'):
   changed=dict(p);changed[field]='f'*64
   with self.assertRaises(ValueError):selected.expected_numeric(changed,b)
if __name__=='__main__':unittest.main()
