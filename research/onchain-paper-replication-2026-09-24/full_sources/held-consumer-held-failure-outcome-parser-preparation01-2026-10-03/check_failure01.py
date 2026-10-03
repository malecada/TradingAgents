"""Qualified synthetic metadata only; no real/fake Owner, Run or Binding."""
import ast,copy,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('failure',P/'held_failure01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
REASON='FixturePublicationFailure: registered second-target publication boundary; retain first output; no retry'
def witness():
 cells=[dict(id='import-target-01',status='complete',resource_only=True),dict(id='import-target-02',status='failed',resource_only=True,reason=REASON)]
 resource=dict(schema_version=2,kind='original-import-resource-terminal',status='failed',resource_only=True,financial_representation_admitted=False,reason=REASON)
 journal=dict(schema_version=1,status='failed',reason=REASON,workflow_identity='a'*64,required_graphs=list(m.TARGETS))
 return cells,resource,journal,'a'*64
class Checks(unittest.TestCase):
 def test_pure_shape(self):self.assertEqual(m.failure_shape(*witness()),REASON)
 def test_unknown_early_partial_refused(self):
  for key,value in [('status','unavailable'),('status','complete'),('reason','MemoryError'),('resource_only',False)]:
   args=witness();args[0][1][key]=value
   with self.assertRaises(ValueError):m.failure_shape(*args)
  for index in (0,1):
   args=witness();args[0].pop(index)
   with self.assertRaises(ValueError):m.failure_shape(*args)
 def test_mutated_journals(self):
  for idx,key,value in [(1,'financial_representation_admitted',True),(1,'schema_version',True),(1,'reason','other'),(2,'schema_version',True),(2,'status','complete'),(2,'workflow_identity','b'*64),(2,'required_graphs',[])]:
   args=witness();args[idx][key]=value
   with self.assertRaises(ValueError):m.failure_shape(*args)
 def test_workflow_namespace(self):
  root=Path('/synthetic/only');g=next(iter(m.TARGETS));cells=witness()[0];cells[0]['target']={'output':{'directory':str(root/'research_artifacts/onchain_compact_outputs'/('a'*64)/m.IDENTITY/('mcm-'+g))}}
  self.assertEqual(m.workflow_from_first(root,cells,g),'a'*64)
  for bad in ['/elsewhere','/synthetic/only/research_artifacts/onchain_compact_outputs/../other']:
   cells[0]['target']['output']['directory']=bad
   with self.assertRaises(ValueError):m.workflow_from_first(root,cells,g)
 def test_real_absence_and_born_marker(self):
  root=P/'owned-absence01';root.mkdir();root=root.resolve();r=m.Reader(root);m.absent(r,'missing')
  (root/'missing').write_bytes(b'kept')
  with self.assertRaises(ValueError):m.absent(r,'missing')
  (root/'dangling').symlink_to('nonexistent')
  with self.assertRaises(ValueError):m.absent(r,'dangling')
 def test_fatal_independent_cleanup(self):
  first=MemoryError('earliest');calls=[]
  def close():calls.append(1);raise OSError('late')
  with self.assertRaises(MemoryError) as got:m.cleanup([close,close],first)
  self.assertIs(got.exception,first);self.assertEqual(len(calls),2)
 def test_inherited_helpers_ast(self):
  old=ast.parse((P/'held_outcome.baseline01.py').read_bytes());new=ast.parse((P/'held_failure01.py').read_bytes())
  newer={n.name:n for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  for n in old.body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='authenticate':self.assertEqual(ast.dump(n),ast.dump(newer[n.name]),n.name)
 def test_unreleased_real_template(self):
  p=P.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json';raw=p.read_bytes();root=json.loads(raw)['capsule_root']
  with self.assertRaisesRegex(ValueError,'unreleased'):m.authenticate(root,p.resolve(),m.sha(raw))
if __name__=='__main__':unittest.main()
