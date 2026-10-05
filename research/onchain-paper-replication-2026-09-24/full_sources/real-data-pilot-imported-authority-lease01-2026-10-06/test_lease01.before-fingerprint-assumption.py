"""Mechanical offline controls only: no Run/Owner/Binding or scientific objects."""
import ast,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
pkg=types.ModuleType('lease_test');pkg.__path__=[str(T)];sys.modules['lease_test']=pkg
import lease_test.imported_authority_interval as m
import lease_test.imported_authority_lease as helper
POLICY={'schema_version':1,'kind':m.KIND,'live_interval_ms':10,'fingerprint_interval_ms':20,'full_interval_ms':100,'max_stale_ms':500,'max_calls_between_full':1000,'assumption':m.ASSUMPTION}
class Checks(unittest.TestCase):
 def test_finite_intervals_and_forced_boundary(self):
  now=[10.];v=m.Interval(POLICY,clock=lambda:now[0]);calls=[]
  full=lambda:calls.append('full');finger=lambda:calls.append('finger');live=lambda:calls.append('live')
  v.validate(full,finger,live);self.assertEqual(calls,['live','full','finger'])
  calls.clear()
  for _ in range(20):v.validate(full,finger,live)
  self.assertEqual(calls,[])
  now[0]+=.011;v.validate(full,finger,live);self.assertEqual(calls,['live'])
  now[0]+=.011;v.validate(full,finger,live);self.assertEqual(calls,['live','live','finger'])
  calls.clear();v.validate(full,finger,live,boundary=True);self.assertEqual(calls,['live','full','finger'])
 def test_stale_backward_and_fatal_poison(self):
  for delta in (1.,-1.):
   now=[10.];v=m.Interval(POLICY,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None);now[0]+=delta
   with self.assertRaises(ValueError):v.validate(lambda:self.fail('no stale refresh'),lambda:None,lambda:None)
   self.assertTrue(v.closed)
  original=MemoryError('synthetic fatal');v=m.Interval(POLICY)
  def fail():raise original
  with self.assertRaises(MemoryError) as e:v.validate(fail,lambda:None,lambda:None)
  self.assertIs(e.exception,original);self.assertIsNone(v.full);self.assertTrue(v.closed)
 def test_file_fingerprint_and_loaded_code_mutations(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp:
   root=Path(tmp);p=root/'tiny.py';p.write_text('def value():\n    return 1\n');pin=m.fingerprint(p);st=p.stat();p.write_text('def value():\n    return 2\n');os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns));self.assertNotEqual(pin,m.fingerprint(p))
   raw=p.read_bytes();sources={'tiny.py':hashlib.sha256(raw).hexdigest()};mod=types.ModuleType('lease_tiny_source');mod.__file__=str(p);exec(compile(raw,str(p),'exec'),vars(mod));sys.modules[mod.__name__]=mod
   try:
    loaded=helper._loaded(root,sources);helper._authenticate_loaded(loaded,sources,root)
    exec(compile('def value():\n    return 3\n',str(p),'exec'),vars(mod));changed=helper._loaded(root,sources);self.assertNotEqual(loaded,changed)
    with self.assertRaisesRegex(ValueError,'loaded code'):helper._authenticate_loaded(changed,sources,root)
   finally:del sys.modules[mod.__name__]
 def test_call_bound_and_live_crossing_deadline(self):
  selected=dict(POLICY,max_calls_between_full=2);now=[10.];v=m.Interval(selected,clock=lambda:now[0]);calls=[]
  for _ in range(3):v.validate(lambda:calls.append('full'),lambda:None,lambda:None)
  self.assertEqual(calls,['full','full'])
  v=m.Interval(POLICY,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None);now[0]+=.02
  def long_live():now[0]+=1.
  with self.assertRaisesRegex(ValueError,'stale during live'):v.validate(lambda:self.fail('expired interval refreshed'),lambda:None,long_live)
  self.assertTrue(v.closed)
 def test_exact_inverse_and_registered_wiring(self):
  for name,row in json.loads((D/'SOURCE_DELTA01.json').read_text()).items():
   s=(T/name).read_text();ast.parse(s)
   for edit in reversed(row['edits']):self.assertEqual(s.count(edit['new']),1);s=s.replace(edit['new'],edit['old'])
   self.assertEqual(s,Path(row['baseline']).read_text())
  for name in ('imported_authority_lease.py','imported_authority_interval.py'):ast.parse((T/name).read_text())
  self.assertFalse({'torch','numpy','networkx','scipy'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
