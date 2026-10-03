"""Actual source, tiny metadata/file refusal checks; no authority fabrication."""
import ast,hashlib,importlib.util,json,os,pathlib,sys,tempfile,time,types,unittest
from unittest.mock import patch
SOURCE=pathlib.Path(sys.argv[1]).resolve();del sys.argv[1]
sys.path.insert(0,str(SOURCE))
import archive01 as a
import collector01 as c
class Cases(unittest.TestCase):
 def test_large_row_after_flush_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'pages'
   with self.assertRaises(ValueError):a.pages(p,[{'path':'small'},{'path':'x'*8200}])
   self.assertTrue(all(x.stat().st_size<=8192 for x in p.iterdir()))
 def test_exact_page_boundary_newline_and_all_rows(self):
  with tempfile.TemporaryDirectory() as d:
   rows=[{'path':str(i),'data':'x'*1000} for i in range(18)];p=pathlib.Path(d)/'pages';refs=a.pages(p,rows)
   self.assertEqual([v for ref in refs for v in json.loads(a.read(p/ref['path'],8192))],rows)
   self.assertTrue(all(ref['bytes']<=8192 for ref in refs))
 def test_credential_name_rejected_before_open(self):
  for name in ('keys/key.pub','apis/public.json','.env','hf_token.txt','.env.local'):
   with self.subTest(name=name),patch.object(a.io,'_opened',side_effect=AssertionError('IO reached')) as opened:
    with self.assertRaises(ValueError):c.reference({'path':'/never-read/'+name,'sha256':'1'*64})
    opened.assert_not_called()
 def test_external_reference_recursive_secret_refuses_without_touch(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'refs'
   with patch.object(a.io,'_opened',side_effect=AssertionError('IO reached')) as opened:
    with self.assertRaises(ValueError):c.capture_external({'reference':{'path':'/never-read/keys/test','sha256':'1'*64}},p)
    opened.assert_not_called()
 def test_all_capsule_namespaces_count_as_born(self):
  for ns in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
   with self.subTest(ns=ns),tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d);(root/ns/c.IDS['materialize']).mkdir(parents=True)
    v=c.observed_phase(root,'materialize',None)
    self.assertNotEqual(v['original_lifecycle_observation'],'not_observed')
 def test_actual_disposition_assignment_refuses_born_namespace(self):
  # Extract exactly the actual collect assignment, not a mirrored classifier.
  tree=ast.parse((SOURCE/'collector01.py').read_text());assign=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Subscript) and isinstance(n.targets[0].slice,ast.Constant) and n.targets[0].slice.value=='strict_scientific_disposition');code=compile(ast.fix_missing_locations(ast.Module(body=[assign],type_ignores=[])),str(SOURCE/'collector01.py'),'exec')
  for role in ('wrapper','parent'):
   with self.subTest(role=role),tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d)/'capsule';root.mkdir();outside=pathlib.Path(d)/'outside';outside.mkdir();paths={'wrapper':str(outside/'wrapper'),'parent':str(outside/'parent')};pathlib.Path(paths[role]).mkdir();q={'reservation_roots':{'materialize':paths}}
    v={'original_lifecycle_observation':'not_observed','scientific_authentication':{},'wrapper_authentication':{},'cleanup':{},'lifecycle_authentication':{}}
    env=dict(vars(c),value=v,phase='materialize',wrapper=None,root=root,q=q);exec(code,env)
    self.assertNotEqual(v['strict_scientific_disposition'],'NOT_ATTEMPTED_OBSERVED')
 def test_actual_disposition_requires_explicit_absent_roots(self):
  self.assertTrue(hasattr(c,'unattempted_observation'),'explicit planned roots absent')
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'capsule';root.mkdir();q={'reservation_roots':{'materialize':{'wrapper':str(pathlib.Path(d)/'w'),'parent':str(pathlib.Path(d)/'p')}}}
   self.assertTrue(c.unattempted_observation(q,root,'materialize')['all_absent'])
   with self.assertRaises((ValueError,KeyError)):c.unattempted_observation({},root,'materialize')
   pathlib.Path(q['reservation_roots']['materialize']['parent']).symlink_to('/absent')
   with self.assertRaises(ValueError):c.unattempted_observation(q,root,'materialize')
if __name__=='__main__':unittest.main(verbosity=2)
