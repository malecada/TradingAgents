"""Actual predecessor parser counterexamples, tiny JSON only."""
import sys,unittest,tempfile,json,os
from pathlib import Path
D=Path(__file__).resolve().parent;old=D.parent/'original-import-native-refusal-candidate02-2026-10-03'
sys.path.insert(0,str(old))
import test_evidence02 as fixture
class Counterexamples(unittest.TestCase):
 def test_empty_numerical_stage_refuses(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);fixture.fixture(root,'wrong-count')
   with self.assertRaises((ValueError,FileNotFoundError,KeyError)):fixture.caller.terminal(root=root,variant='wrong-count')
 def test_each_numeric_identity_corruption_refuses(self):
  for field,value in [('ordered_motifs',['9'*64]*32),('representative_sample_indices',[999999]*32),('bundle_sha256','8'*64),('numeric_bytes',-1)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);journal,write=fixture.fixture(root,'lease-terminal');p=journal/'compact/dictionary-import/import-complete.json';v=json.loads(p.read_bytes());v['numeric'][field]=value;write(p,v)
    with self.assertRaises((ValueError,FileNotFoundError,KeyError)):fixture.caller.terminal(root=root,variant='lease-terminal')
if __name__=='__main__':unittest.main()
