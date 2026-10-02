"""Pure source/stdlib checks. No genuine admission or numerical proof."""
import ast,importlib.util,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('cases',ROOT/'refusal_cases.py');cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
def extracted(path,names,ns):
 tree=ast.parse(path.read_text());chosen=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names];exec(compile(ast.Module(body=chosen,type_ignores=[]),str(path),'exec'),ns);return ns
class Source(unittest.TestCase):
 def test_class_variant_claim_owner_denominators(self):
  self.assertEqual(len(cases.GROUPS),16);self.assertEqual(len(cases.NAMES),27);self.assertEqual(len(set(map(cases.identity,cases.NAMES))),27)
  self.assertEqual(sum(cases.policy(n)['claim_cardinality_max'] for n in cases.NAMES),23);self.assertEqual(sum(cases.policy(n)['owner_cardinality_max'] for n in cases.NAMES),17)
 def test_real_selection_accepts_all_finite_refusal_cases(self):
  path=Path(os.environ.get('REFUSAL_FIXTURE_SOURCE',ROOT/'resource_fixture.py'));tree=ast.parse(path.read_text());keys=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='KEYS' for t in n.targets));ns={'cases':cases,'KEYS':ast.literal_eval(keys.value)}
  ns=extracted(path,{'require','selection'},ns)
  for variant in cases.NAMES:
   selected={k:k for k in ns['KEYS']};selected['operation']='produce';selected['descriptor']={'arm':'proposed','dictionary_origin':'imported-original-v1','required_graphs':['a'*64,'b'*64],'resource_graph_inputs':{'a'*64:'a','b'*64:'b'},'resource_fixture':{'schema_version':1,'case':'refusal-'+variant,'data_kind':'synthetic-targets-original-dictionary','target_nodes':{'a'*64:2,'b'*64:3},'target_provenance_input':'p'}}
   ns['selection']({'payload':{'representation_jobs':{'r':selected}}})
 def test_exact_observer_no_wrong_failure_or_success(self):
  ns=extracted(ROOT/'resource_refusal.py',{'require','observe'},{});observe=ns['observe']
  def expected():raise ValueError('exact intended refusal')
  self.assertTrue(observe(expected,'intended')['observed'])
  with self.assertRaises(AssertionError):observe(lambda:None,'intended')
  with self.assertRaises(ValueError):observe(expected,'wrong')
  fatal=MemoryError('first')
  def fails():raise fatal
  with self.assertRaises(MemoryError) as caught:observe(fails,'intended')
  self.assertIs(caught.exception,fatal)
 def test_actual_hooks_delegate_once_and_only_selected_mutation(self):
  ns=extracted(ROOT/'resource_refusal.py',{'require','score_callback','compute_callback','returned'},{'active_case':lambda _: 'wrong-ack'})
  calls=[]
  def matcher(p,a,b):calls.append(p);return {'purpose_sha256':'a'*64,'score':.5}
  cb=ns['compute_callback'](None,matcher);result=cb({'real':True},None,None);self.assertEqual(calls,[{'real':True}]);self.assertEqual(result,{'purpose_sha256':'0'*64,'score':.5})
  with self.assertRaises(ValueError):cb({},None,None)
  ns['active_case']=lambda _:'wrong-count';original={'completed_cells':64};self.assertEqual(ns['returned'](None,original),{'completed_cells':65});self.assertEqual(original,{'completed_cells':64})
if __name__=='__main__':unittest.main()
