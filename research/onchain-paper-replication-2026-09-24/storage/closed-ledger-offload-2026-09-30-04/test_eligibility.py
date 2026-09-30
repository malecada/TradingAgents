import importlib.util
from pathlib import Path
import tempfile,json,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate',HERE/'offload.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def fixture(self,root):
  path=Path('research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-graph-resource-20260930-06/aggregation/ledger.sqlite');p=root/path;p.parent.mkdir(parents=True);p.write_bytes(b'closed synthetic ledger');st=p.stat()
  row={'path':str(path),'bytes':st.st_size,'sha256':m.old.sha(p),'stat_identity':m.old.identity(st)}
  c={'files':[row],'total_bytes':st.st_size,'closure':{}}
  owner={'experiment':'old','monitor_pid':2147483646};objects={'owner':owner,'guard':{'phase':'complete','cleanup_verified':True,'cgroup':str(root/'absent-cgroup'),'owner_identity':owner},'claim':{'experiment_id':'old'},'artifact_index':{str(path):{'bytes':row['bytes'],'sha256':row['sha256']}}}
  for name,obj in objects.items():
   f=root/(name+'.json');f.write_text(json.dumps(obj));c['closure'][name]={'path':f.name,'sha256':m.old.sha(f)}
  f=root/'terminal.json';f.write_text(json.dumps({'status':'complete','experiment_id':'old','claim_sha256':c['closure']['claim']['sha256'],'output_sha256':{'artifact-index.json':c['closure']['artifact_index']['sha256']}}));c['closure']['terminal']={'path':f.name,'sha256':m.old.sha(f)}
  return c,p
 def test_closed_exact_ledger_admitted(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'check_output',return_value=b''):
   c,p=self.fixture(Path(d));self.assertEqual(m.eligibility(Path(d),c),c['files'][0]);self.assertTrue(p.exists())
 def test_scope_journal_sidecar_tracked_and_drift_refused(self):
  for fault in ('path','journal','sidecar','tracked','drift'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'check_output',return_value=b'tracked' if fault=='tracked' else b''):
    root=Path(d);c,p=self.fixture(root)
    if fault=='path':c['files'][0]['path']='unrelated'
    if fault=='journal':p.with_name(p.name+'-journal').touch()
    if fault=='sidecar':p.with_name(p.name+'.remote.json').touch()
    if fault=='drift':p.write_bytes(b'changed')
    with self.assertRaises(ValueError):m.eligibility(root,c)
    self.assertTrue(p.exists())
 def test_active_guard_or_claim_refused(self):
  for fault in ('guard','claim'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'check_output',return_value=b''):
    root=Path(d);c,p=self.fixture(root)
    if fault=='guard':(root/'absent-cgroup').mkdir()
    else:
     active=root/'research_runs/new/claim.json';active.parent.mkdir(parents=True);active.write_text(json.dumps({'experiment':{'inputs':{'ledger':{'path':c['files'][0]['path']}}}}))
    with self.assertRaises(ValueError):m.eligibility(root,c)
 def test_changed_closure_refused_before_body(self):
  with tempfile.TemporaryDirectory() as d,patch.object(m.subprocess,'check_output',return_value=b''):
   root=Path(d);c,p=self.fixture(root);(root/'terminal.json').write_text('{}')
   with self.assertRaises(ValueError):m.eligibility(root,c)
if __name__=='__main__':unittest.main(verbosity=2)
