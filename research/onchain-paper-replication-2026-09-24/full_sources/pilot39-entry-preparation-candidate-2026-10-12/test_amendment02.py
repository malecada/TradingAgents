import ast,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('entry39amendment',P/'prepare_entry01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Amendment(unittest.TestCase):
 def test_existing_observation_refuses_before_import_or_scan(self):
  with tempfile.TemporaryDirectory(dir=P) as directory:
   here=Path(directory);body=b'original observation';(here/'BASELINE_STORAGE_OBSERVATION01.json').write_bytes(body)
   with patch.object(m,'HERE',here),patch('builtins.__import__',side_effect=AssertionError('unexpected import before refusal')):
    with self.assertRaisesRegex(AssertionError,'Root39 observation already used'):m.observe('a'*40)
   self.assertEqual((here/'BASELINE_STORAGE_OBSERVATION01.json').read_bytes(),body)
 def test_actual_bound_transport_full_reference_preserved(self):
  public=P.parent/'real-data-pilot-full39-binding-preparation01-2026-10-12'
  bound=json.loads((public/'BOUND01.json').read_bytes());inputs=json.loads((public/'ALL_INPUT_REFS01.json').read_bytes())
  tree=ast.parse((P/'prepare_entry01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
  start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='transport' for t in n.targets))
  nodes=fn.body[start:start+4];scope={'bound':bound,'inputs':inputs,'binding':{}}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-source-amendment>','exec'),scope)
  self.assertEqual(scope['binding']['transport'],bound['private_input']['archive_transport']);self.assertEqual(scope['binding']['transport']['bytes'],930)
if __name__=='__main__':unittest.main()
