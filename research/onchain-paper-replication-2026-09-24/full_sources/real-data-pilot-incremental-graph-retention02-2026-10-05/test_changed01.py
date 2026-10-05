"""Reviewer's source-metadata witness, no scientific objects or live mutation."""
import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).resolve().parent;A=D.parent/'real-data-pilot-incremental-graph-retention01-2026-10-05'
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=load('original_synthetic_fixture',A/'test_select01.py');new=load('new_selector',D/'select01.py')
class Changed(unittest.TestCase):
 def test_reviewer_result_reference_red_green(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp,patch.object(new.subprocess,'check_output',return_value=b''):
   root=Path(tmp);put,run,base=f.fixture(root)
   put('research_runs/active/claim.json',{'experiment':{'inputs':{'graph_result':{'path':base+'result.json','sha256':new.sha((root/base/'result.json').read_bytes())}}}})
   self.assertEqual(f.m.select(root,f.ID)['status'],'DRAFT')
   with self.assertRaisesRegex(ValueError,'active consumer'):new.select(root,f.ID)
 def test_metadata_ancestor_and_unrelated_controls(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp,patch.object(new.subprocess,'check_output',return_value=b''):
   root=Path(tmp);put,run,base=f.fixture(root)
   for target in (base+'graph-2022-05-02/manifest.json',base+'source-coverage.json',base,base+'aggregation',str(Path(base).parent)):
    put('research_runs/active/claim.json',{'experiment':{'inputs':{'input':{'path':target}}}})
    with self.subTest(target=target),self.assertRaisesRegex(ValueError,'active consumer'):new.select(root,f.ID)
   put('research_runs/active/claim.json',{'experiment':{'inputs':{'input':{'path':base.rstrip('/')+'-other/result.json'}}}})
   self.assertEqual(new.select(root,f.ID)['status'],'DRAFT')
 def test_literal_inverse(self):
  s=(D/'select01.py').read_text().replace('def active_reference(root,rows,inputs,producer):','def active_reference(root,rows,inputs):').replace('require(not q.is_relative_to(producer) and not any(','require(not any(').replace("active_reference(root,[p.resolve()],a['experiment']['inputs'],(root/base).resolve())","active_reference(root,[p.resolve()],a['experiment']['inputs'])")
  self.assertEqual(s,(A/'select01.py').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
