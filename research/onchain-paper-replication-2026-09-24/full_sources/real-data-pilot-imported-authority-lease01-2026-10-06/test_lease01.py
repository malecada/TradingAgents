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
   root=Path(tmp);p=root/'tiny.py';p.write_text('def value():\n    return 1\n');pin=m.fingerprint(p);initial=p.read_bytes();st=p.stat();p.write_text('def value():\n    return 2\n');os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns));self.assertNotEqual(initial,p.read_bytes())
   def full():m.require(p.read_bytes()==initial,'full byte baseline changed')
   interval=m.Interval(POLICY)
   with self.assertRaisesRegex(ValueError,'full byte baseline'):interval.validate(full,lambda:m.fingerprint(p),lambda:None,boundary=True)
   self.assertTrue(interval.closed)
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
  with self.assertRaisesRegex(ValueError,'stale interval'):v.validate(lambda:self.fail('expired interval refreshed'),lambda:None,long_live)
  self.assertTrue(v.closed)
 def test_review_stale_full_and_actual_live_time(self):
  now=[10.];v=m.Interval(POLICY,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None);now[0]=10.1
  def long_full():now[0]+=.45
  with self.assertRaisesRegex(ValueError,'stale interval'):v.validate(long_full,lambda:None,lambda:None,boundary=True)
  self.assertEqual(v.full,10.);self.assertTrue(v.closed)
  now=[10.];v=m.Interval(POLICY,clock=lambda:now[0]);lives=[]
  def work():now[0]+=.025
  v.validate(work,lambda:None,lambda:lives.append(now[0]))
  self.assertEqual(lives,[10.,10.025]);self.assertEqual(v.live,10.025)
 def test_real_contextmanager_wrapper_join(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp:
   root=Path(tmp);p=root/'tiny.py';raw=b'from contextlib import contextmanager\n@contextmanager\ndef held():\n    yield 1\n';p.write_bytes(raw)
   mod=types.ModuleType('lease_wrapped');mod.__file__=str(p);exec(compile(raw,str(p),'exec'),vars(mod));sys.modules[mod.__name__]=mod
   sources={'tiny.py':hashlib.sha256(raw).hexdigest()}
   try:
    loaded=helper._loaded(root,sources);helper._authenticate_loaded(loaded,sources,root)
    mod.held.__wrapped__=lambda:None
    with self.assertRaises(ValueError):helper._loaded(root,sources)
   finally:del sys.modules[mod.__name__]
 def test_exact_inverse_and_registered_wiring(self):
  for name,row in json.loads((D/'SOURCE_DELTA01.json').read_text()).items():
   s=(T/name).read_text();ast.parse(s)
   for edit in reversed(row['edits']):self.assertEqual(s.count(edit['new']),1);s=s.replace(edit['new'],edit['old'])
   self.assertEqual(s,Path(row['baseline']).read_text())
  for name in ('imported_authority_lease.py','imported_authority_interval.py'):ast.parse((T/name).read_text())
  self.assertFalse({'torch','numpy','networkx','scipy'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
