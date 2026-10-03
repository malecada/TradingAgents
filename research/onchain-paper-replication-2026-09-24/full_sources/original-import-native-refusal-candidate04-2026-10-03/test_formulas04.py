"""Selected pure source formulas executed with identity-only stand-ins, no authority."""
import ast,hashlib,json,sys,tempfile,unittest,copy
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));sys.path.insert(1,str(D.parent/'original-import-fixture-native-preparation03-2026-10-03'))
import refusal_pair_identity as selected
from synthetic_targets04 import graphs
from evidence_fixture03 import fixture,caller
from stage_fixture03 import populate
ROOT=D.parents[3];F=D.parent
class Formulas(unittest.TestCase):
 def test_selected_source_pair_encodings_are_exact(self):
  def extract(path,names,env):
   nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env);return env
  ann=extract(ROOT/'tradingagents/research/onchain_replication/matching_annealing.py',{'body','identity'},{'hashlib':hashlib,'json':json,'graph_hash':lambda g:g})
  pair=extract(ROOT/'tradingagents/research/onchain_replication/matching_pair.py',{'body','digest'},{'hashlib':hashlib,'json':json})
  config={'max_iterations':100,'α':.5};self.assertEqual(ann['body'](config),selected.pair_body(config));self.assertEqual(pair['body'](config),selected.pair_body(config))
  ordered=ann['identity']('a'*64,'b'*64,config);expected={'left':'a'*64,'right':'b'*64,'configuration':hashlib.sha256(selected.pair_body(config)).hexdigest()};self.assertEqual(ordered,expected)
  tree=ast.parse((F/'original-import-fixture-io-candidate02-2026-10-02/compact_matcher.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CompactMatcher');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='pair_identity');env={'engine':SimpleNamespace(ann=SimpleNamespace(identity=ann['identity'])),'pair':SimpleNamespace(BACKEND={'fixed':True})};exec(compile(ast.Module(body=[method],type_ignores=[]),'actual_pair_identity','exec'),env)
  result=env['pair_identity'](SimpleNamespace(config=config,context={'x':1},components={'module':'c'*64}),'a'*64,'b'*64)
  self.assertEqual(result,{'ordered_pair':ordered,'context':{'x':1},'backend':{'fixed':True},'numerical_components':{'module':'c'*64}});self.assertEqual(pair['digest'](result),hashlib.sha256(selected.pair_body(result)).hexdigest())
 def test_neighborhood_order_direction_and_hop_capacity(self):
  graph={'node_ids':['a','b'],'node_features':[[1.,0.,0.,0.],[0.,1.,0.,0.]],'edge_index':[[1,0],[0,1]],'edge_features':[[.1,.2],[.3,.4]]};parent='a'*64
  isolated=selected.local_record(graph,1,{'hop_depth':0,'maximum_neighborhood_nodes':1},parent);self.assertEqual(isolated['node_ids'],['b']);self.assertEqual(isolated['edge_index'],[[],[]])
  expanded=selected.local_record(graph,1,{'hop_depth':3,'maximum_neighborhood_nodes':2},parent);self.assertEqual(expanded['node_ids'],['a','b']);self.assertEqual(expanded['edge_index'],[[1,0],[0,1]]);self.assertEqual(expanded['edge_features'],graph['edge_features']);self.assertEqual(expanded['center_id'],'b')
  with self.assertRaises(ValueError):selected.local_record(graph,0,{'hop_depth':1,'maximum_neighborhood_nodes':1},parent)
 def test_all_four_actual_parser_format_controls(self):
  for variant in ('wrong-purpose','wrong-ack','wrong-matrix','wrong-count'):
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,variant);populate(root,j,variant,w);self.assertTrue(caller.terminal(root=root,variant=variant)['observed'])
 def test_wrong_source_and_registered_array_refuse(self):
  for change in ('source','array'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'wrong-ack');populate(root,j,'wrong-ack',w)
    p=root/('tradingagents/research/onchain_replication/matching_pair.py' if change=='source' else 'fixture_inputs/target-01/node_features.npy');p.write_bytes(p.read_bytes()+b' ')
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='wrong-ack')
 def test_guarded_seam_has_no_module_import_or_executable_entry(self):
  tree=ast.parse((D/'guarded_formula_oracle04.py').read_text());self.assertTrue(all(isinstance(n,(ast.Expr,ast.FunctionDef)) for n in tree.body));self.assertEqual([n.name for n in tree.body if isinstance(n,ast.FunctionDef)],['verify'])
if __name__=='__main__':unittest.main()
