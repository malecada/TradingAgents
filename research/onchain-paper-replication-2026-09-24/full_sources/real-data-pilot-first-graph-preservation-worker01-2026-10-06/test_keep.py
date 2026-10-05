"""Tiny synthetic bytes and fake transport only; no authority/native/network execution."""
import hashlib,importlib.util,json,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
spec=importlib.util.spec_from_file_location('candidate_keep',D/'keep.py');k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
base=k.bind_primitives(ROOT)
class Transport:
 def __init__(self,bad=None):self.bodies={};self.events=[];self.bad=bad;self.remaining=8*k.GIB
 def put(self,p,key):self.events.append(('put',key));self.bodies[key]=p.read_bytes()
 def get(self,key,p):
  self.events.append(('get',key));raw=self.bodies[key]
  if self.bad and key.endswith(self.bad):raw+=b'corrupt'
  with p.open('xb') as f:f.write(raw)
 def available(self):return 100*k.GIB
 def mkdir(self,key):self.events.append(('mkdir',key))
def row(root,p):return {'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'stat_identity':base.identity(p.stat()),'mode':p.stat().st_mode,'nlink':p.stat().st_nlink}
class Checks(unittest.TestCase):
 def fixture(self):
  ctx=tempfile.TemporaryDirectory(dir=D);self.addCleanup(ctx.cleanup);root=Path(ctx.name);here=root/'preserve';here.mkdir();p=root/'original';p.write_bytes(b'original tiny bytes');return root,here,p,row(root,p)
 def test_keep_exact_body_metadata_and_no_sidecar(self):
  root,here,p,r=self.fixture();before=p.stat();t=Transport();out=k.keep_one(root,here,r,0,'fresh',t,primitives=base)
  self.assertEqual(base.identity(p.stat()),base.identity(before));self.assertEqual(p.read_bytes(),(here/'00-recovered.bin').read_bytes());self.assertFalse(p.with_name('original.remote.json').exists());self.assertEqual((here/'00-restore.json').read_bytes(),(here/'00-recovered-restore.json').read_bytes());self.assertTrue(out['original_retained']);self.assertEqual([x[0] for x in t.events],['put','get','put','get'])
  with self.assertRaises(FileExistsError):k.keep_one(root,here,r,0,'fresh',t,primitives=base)
 def test_roundtrip_mismatches_retain_everything(self):
  for bad in ('.bin','-restore.json'):
   root,here,p,r=self.fixture();t=Transport(bad)
   with self.assertRaises(ValueError):k.keep_one(root,here,r,0,'fresh',t,primitives=base)
   self.assertTrue(p.exists());self.assertTrue((here/'00-recovered.bin').exists());self.assertFalse((here/'00-verified.json').exists());self.assertEqual(list(root.glob('*.remote.json')),[])
 def test_source_stat_mismatch_before_transport(self):
  root,here,p,r=self.fixture();r['stat_identity'][1]+=1;t=Transport()
  with self.assertRaises(ValueError):k.keep_one(root,here,r,0,'fresh',t,primitives=base)
  self.assertEqual(t.events,[]);self.assertTrue(p.exists())
 def test_loop_failed_and_skipped_receipts(self):
  root,here,p,r=self.fixture();p2=root/'second';p2.write_bytes(b'second');rows=[r,row(root,p2)];c={'identity':k.ID,'schema_version':1,'files':rows,'count':2,'total_bytes':sum(x['bytes'] for x in rows),'max_body_bytes':max(x['bytes'] for x in rows),'disk_floor_bytes':10*k.GIB,'transport_payload_budget_bytes':8*k.GIB,'owned_tree_limit_bytes':5*k.GIB,'remote':'fresh'}
  with patch.object(k,'bind_primitives',return_value=base),patch.object(k.shutil,'disk_usage',return_value=types.SimpleNamespace(free=100*k.GIB)):
   with self.assertRaises(ValueError):k.preserve_selected(root,here,c,Transport('.bin'),lambda:None)
  failed=json.loads((here/'failed.json').read_text());self.assertEqual(failed['attempted'],[0]);self.assertEqual(failed['skipped'],[1]);self.assertEqual(failed['failed_row'],0);self.assertTrue(p.exists() and p2.exists())
 def test_literal_derivative(self):
  inv=json.loads((D/'INVERSE01.json').read_text());old=Path(inv['baseline']).read_text();new=(D/'keep.py').read_text();self.assertIn(inv['original_function'],old);self.assertIn(inv['candidate_function'],new);self.assertNotIn('.unlink(',new);self.assertNotIn('publish(sidecar',new);self.assertEqual(hashlib.sha256(Path(inv['baseline']).read_bytes()).hexdigest(),inv['baseline_sha256'])
if __name__=='__main__':unittest.main(verbosity=2)
