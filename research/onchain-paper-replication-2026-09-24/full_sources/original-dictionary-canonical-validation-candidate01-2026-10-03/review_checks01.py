"""Independent exact-byte semantics and provenance readback; synthetic JSON only."""
import ast,copy,dataclasses,hashlib,importlib.util,json,pathlib,sys,unittest
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D));import test_validate03 as fixtures
old=fixtures.load(D/'baseline.py','review_baseline');new=fixtures.load(D/'candidate01.py','review_candidate')
class Checks(unittest.TestCase):
 def test_all_frozen_pins_and_baseline_selected_origin(self):
  m=json.loads((D/'MANIFEST01.json').read_text());self.assertEqual(len(m['files']),13)
  for row in m['files']:
   b=(D/row['path']).read_bytes();self.assertEqual(len(b),row['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
  origin=json.loads((D/'origins01.json').read_text())
  for row in origin['references']:
   b=(ROOT/row['path']).read_bytes();self.assertEqual(len(b),row['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
  inv=json.loads((ROOT/origin['references'][1]['path']).read_bytes());row=next(r for r in inv['source_inventory'] if r['target']==origin['target']);self.assertEqual(row['sha256'],origin['selected_baseline_sha256'])
 def test_independent_whole_module_inverse_slice_and_pure_serializer(self):
  a=ast.parse((D/'baseline.py').read_bytes());b=ast.parse((D/'candidate01.py').read_bytes());fa=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='validate');fb=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
  ia=next(i for i,n in enumerate(fa.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='(g, group)');ib=next(i for i,n in enumerate(fb.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='(g, group)')
  self.assertEqual(ast.unparse(fb.body[ib-1]),"sample_bytes = [None] * len(s['graphs'])")
  fb.body[ib-1:ib+1]=[fa.body[ia]];self.assertEqual(ast.dump(a),ast.dump(b))
  canonical=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='canonical');self.assertEqual(len(canonical.body),1);self.assertIsInstance(canonical.body[0],ast.Return);self.assertIn('json.dumps',ast.unparse(canonical));self.assertIn('.encode()',ast.unparse(canonical))
 def test_full_scan_comparisons_are16384_in_both(self):
  p,blobs=fixtures.fixture(512,32);results=[]
  for module in (old,new):
   base=module.canonical;counts={'canonical':0,'comparisons':0}
   class ObservedBytes(bytes):
    def __eq__(self,other):counts['comparisons']+=1;return bytes.__eq__(self,other)
   def observe(v):
    result=base(v)
    if type(v) is dict and set(v)==fixtures.GRAPH_KEYS:counts['canonical']+=1;return ObservedBytes(result)
    return result
   module.canonical=observe
   try:evidence=module.validate(p,blobs)
   finally:module.canonical=base
   results.append((counts,dataclasses.asdict(evidence)))
  self.assertEqual(results[0][0],{'canonical':32768,'comparisons':16384});self.assertEqual(results[1][0],{'canonical':544,'comparisons':16384});self.assertEqual(results[0][1],results[1][1]);print('independent full-scan',results[0][0],results[1][0])
 def test_unicode_float_types_and_order_exact_bytes(self):
  def mutate(gs,rs,groups):
   for seq in (gs,rs):
    for g in seq:
     index=int(g['center_id'][1:]);name='節點😀'+str(index);g['node_ids']=[name];g['center_id']=name;g['node_features']=[[index, -0.0, 1e-120, 2.0]];g['edge_index']=[[0],[0]];g['edge_features']=[[0.0,3]]
  for n,m in ((6,2),(32,8)):
   p,b=fixtures.fixture(n,m,mutate);self.assertEqual(dataclasses.asdict(old.validate(p,b)),dataclasses.asdict(new.validate(p,b)))
 def test_private_fresh_parses_and_no_retained_cache_on_evidence(self):
  p,b=fixtures.fixture();original_parse=new.parse;parsed_graph_ids=[];held=[]
  def parse(raw):
   v=original_parse(raw)
   if type(v) is dict and 'graphs' in v and 'records' in v:parsed_graph_ids.append(id(v));held.append(v)
   return v
  new.parse=parse
  try:
   e1=new.validate(p,b);held[0]['graphs'][0]['node_features'][0][0]=999;e2=new.validate(p,b)
  finally:new.parse=original_parse
  self.assertEqual(dataclasses.asdict(e1),dataclasses.asdict(e2));self.assertEqual(len(set(parsed_graph_ids)),2);self.assertNotIn('sample_bytes',new.OriginalEvidence.__slots__)
 def test_rehashed_semantic_corruption_still_refuses_each_call(self):
  p,b=fixtures.fixture();new.validate(p,b)
  changed_p,changed_b=fixtures.fixture(mutation=lambda gs,rs,gp:rs[0]['node_features'][0].__setitem__(0,444))
  for module in (old,new):
   with self.assertRaisesRegex(ValueError,'representative is not unique original sample member'):module.validate(changed_p,changed_b)
  self.assertEqual(dataclasses.asdict(new.validate(p,b)),dataclasses.asdict(old.validate(p,b)))
 def test_no_numerical_or_package_imports(self):self.assertFalse({'numpy','torch','scipy','pandas','pyarrow','tradingagents'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
