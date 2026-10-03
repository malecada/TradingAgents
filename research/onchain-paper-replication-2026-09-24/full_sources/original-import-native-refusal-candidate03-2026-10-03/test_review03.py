"""Identical actual-parser RED/GREEN corpus, realistic fabricated metadata only."""
import importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent/'original-import-fixture-native-preparation03-2026-10-03'));sys.path.insert(0,str(D))
S=Path(os.environ.get('REFUSAL_PARSER_DIR',D.parent/'original-import-native-refusal-candidate02-2026-10-03'))
spec=importlib.util.spec_from_file_location('refusal_evidence',S/'refusal_evidence.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from evidence_fixture03 import fixture,caller
from stage_fixture03 import populate
class Reviewed(unittest.TestCase):
 def test_each_empty_real_format_stage_refused(self):
  for variant in ('wrong-purpose','wrong-ack','wrong-matrix','wrong-count'):
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);fixture(root,variant)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant=variant)
 def test_each_registered_original_semantic_field_refused(self):
  for field,value in [('ordered_motifs',['9'*64]*32),('representative_sample_indices',[999999]*32),('bundle_sha256','8'*64),('numeric_bytes',-1),('extra',False)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'lease-terminal');p=j/'compact/dictionary-import/import-complete.json';v=json.loads(p.read_bytes());v['numeric'][field]=value;w(p,v)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='lease-terminal')
 def test_valid_format_remains_accepted(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);j,w=fixture(root,'wrong-count');populate(root,j,'wrong-count',w);self.assertTrue(caller.terminal(root=root,variant='wrong-count')['observed'])
if __name__=='__main__':unittest.main()
