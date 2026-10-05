"""Offline composition interfaces only; no model import or empirical construction."""
import ast,hashlib,importlib,inspect,json,sys,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');C=D/'candidate'/P
pkg=types.ModuleType('composition_probe');pkg.__path__=[str(C),str(ROOT/P)];sys.modules[pkg.__name__]=pkg

def tree(name):return ast.parse((C/name).read_text())
def definition(name,function):return next(x for x in tree(name).body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==function)
def parameters(node):return {a.arg for a in [*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]}
class Checks(unittest.TestCase):
 def test_exact_overlay_and_finite_roster(self):
  source=json.loads((D/'SOURCE_MAP01.json').read_text());self.assertEqual(len(source['files']),15);self.assertFalse(source['typed_tail_activation_included'])
  for rel,row in source['files'].items():
   raw=(D/'candidate'/rel).read_bytes();self.assertEqual(raw,(ROOT/row['source']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256']);ast.parse(raw)
  inverse=json.loads((D/'INVERSE_PROOF01.json').read_text());self.assertEqual(len(inverse['edges']),22);self.assertTrue(all(x['literal_inverse'] for x in inverse['edges']))
 def test_metadata_only_import_and_callable_interfaces(self):
  for name in ['real_pilot_import_caller','real_pilot_population','real_pilot_throughput','real_pilot_storage','imported_authority_interval','imported_authority_lease']:
   m=importlib.import_module('composition_probe.'+name);self.assertEqual(Path(m.__file__).resolve(),C/(name+'.py'))
  caller=sys.modules['composition_probe.real_pilot_import_caller'];self.assertEqual(list(inspect.signature(caller.execute).parameters),['run','payload'])
  storage=sys.modules['composition_probe.real_pilot_storage'];self.assertEqual(list(inspect.signature(storage.WritableUnion).parameters),['budget','root'])
  lease=sys.modules['composition_probe.imported_authority_lease'];self.assertEqual(list(inspect.signature(lease.activate).parameters),['execution','input_name'])
  self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))
 def test_caller_boundary_interfaces_and_unselected_archive(self):
  execute=definition('real_pilot_import_caller.py','execute');calls=[n for n in ast.walk(execute) if isinstance(n,ast.Call)]
  training=next(n for n in calls if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='training_helper' and n.func.attr=='run_one_update')
  self.assertLessEqual({k.arg for k in training.keywords},parameters(definition('real_pilot_training.py','run_one_update')))
  mcm=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='produce_imported');self.assertLessEqual({k.arg for k in mcm.keywords},parameters(definition('compact_mcm.py','produce_imported')))
  text=ast.unparse(execute);self.assertIn("activate(execution, p['imported_authority_lease_input'])",text)
  self.assertNotIn('archive_owner_operations.attach',text);self.assertNotIn('archive_owner_policy.select',text)
  for name in ('imported_mcm_identity.py','mcm_score_stream.py','compact_mcm.py'):
   self.assertIn('boundary=True',(C/name).read_text())
if __name__=='__main__':unittest.main(verbosity=2)
