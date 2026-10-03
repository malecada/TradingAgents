"""Independent pure synthetic metadata checks; no genuine admission or arrays."""
import ast,copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;P=HERE.parent/'neural-cold-feature-handoff-population-batch-projection-preparation01-2026-10-03';sys.path.insert(0,str(P))
from test_projection01 import load,fixture,canonical,sha
m=load()
def rebind(p,b):
 e=p['examples'];e['train_hash']=sha(canonical(e['train']));e['test_mask_hash']=sha(canonical([x['decision_at'] for x in e['test']]));p['scaler']['train_hash']=e['train_hash'];b.update(train_hash=e['train_hash'],test_mask_hash=e['test_mask_hash'],test_examples_hash=sha(canonical(e['test'])))
class Checks(unittest.TestCase):
 def test_partition_boundary_gap_firstuse_allpositions(self):
  p,b,a=fixture();e=p['examples'];e['test']=e['train'][16:];e['train']=e['train'][:16];e['train'][0]['graph_hashes'][0]='a'*64;e['train'][0]['graph_hashes'][27]='b'*64;rebind(p,b)
  v=m.project(p,b,a,{})
  self.assertEqual([(x['partition'],len(x['ordinals'])) for x in v['batches']],[('train',16),('test',1)])
  self.assertEqual(v['batches'][0]['graph_hashes'],['a'*64,'2'*64,'1'*64,'b'*64]);self.assertEqual(sum(v['batches'][0]['multiplicity']),448);self.assertEqual(v['batches'][0]['multiplicity'],[1,223,223,1]);self.assertEqual(v['batches'][1]['ordinals'],[0]);self.assertEqual(sum(v['batches'][1]['multiplicity']),28)
 def test_semantic_corruptions_after_coherent_hash_rebinding(self):
  for kind in ('duplicate','position','late','unknownfield'):
   with self.subTest(kind=kind):
    p,b,a=fixture();row=p['examples']['train'][0]
    if kind=='duplicate':p['examples']['train'][1]=copy.deepcopy(row)
    if kind=='position':row['input_dates'][0],row['input_dates'][1]=row['input_dates'][1],row['input_dates'][0]
    if kind=='late':row['graph_available_at'][27]='2024-02-02T00:00:00Z'
    if kind=='unknownfield':row['diagnostic_target']=1
    rebind(p,b)
    with self.assertRaises(ValueError):m.project(p,b,a,{})
 def test_metadata_declared_not_owner_or_body_proof(self):
  h='1'*64;s=lambda v:{'kind':'scalar','value':v};tree={'kind':'dict','items':[[s('feature'),{'kind':'dict','items':[[s('mcm'),{'kind':'array','member':'array-000000.npy'}],[s('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[s('aligned_vectors'),s(None)]]}
  value={'schema_version':1,'context':{'graph_hash':h},'tree':tree,'arrays':{'array-000000.npy':{'shape':[1,32],'dtype':'float32','bytes':129,'sha256':'2'*64},'array-000001.npy':{'shape':[2,0],'dtype':'int64','bytes':1,'sha256':'3'*64}}}
  result=m.component(value,h);self.assertEqual(result['status'],'declared_metadata_only');self.assertFalse(result['body_header_owner_terminal_verified']);self.assertEqual(result['fixed_tensor_bytes'],128)
  for mutate in (lambda x:x['arrays']['array-000000.npy'].__setitem__('shape',[True,32]),lambda x:x['arrays']['array-000001.npy'].__setitem__('bytes',False),lambda x:x['tree']['items'].reverse()):
   bad=copy.deepcopy(value);mutate(bad)
   with self.assertRaises(ValueError):m.component(bad,h)
 def test_missing_unavailable_and_exclusions_not_upgraded(self):
  p,b,a=fixture();e={'status':'unavailable','reason':'synthetic retained failure','evidence_hashes':['f'*64]};v=m.project(p,b,a,{'1'*64:e});self.assertEqual(v['components']['1'*64],e);self.assertEqual(v['components']['2'*64],{'status':'missing_registered_component'});self.assertEqual(v['exclusions'],p['examples']['exclusions']);self.assertFalse(v['scientific_feature_admission'])
 def test_total_and_serialized_output_caps(self):
  p,b,a=fixture();old=m.OUTPUT_LIMIT
  try:
   m.OUTPUT_LIMIT=1
   with self.assertRaises(ValueError):m.project(p,b,a,{})
  finally:m.OUTPUT_LIMIT=old
  with self.assertRaises(ValueError):m.parse(b'{"n":NaN}')
  with self.assertRaises(ValueError):m.parse(b'{"n":1,"n":2}')
 def test_module_source_imports_and_genuine_type_guard(self):
  tree=ast.parse((P/'population_batch_projection.py').read_text());imports=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):imports.update(x.name for x in n.names)
  self.assertFalse(imports&{'numpy','torch','pandas','pyarrow'});context=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_context');self.assertIn('type(run) is _run_class()',ast.unparse(context));self.assertIn('run._check_source()',ast.unparse(context));self.assertIn('run._check_inputs()',ast.unparse(context))
if __name__=='__main__':unittest.main(verbosity=2)
