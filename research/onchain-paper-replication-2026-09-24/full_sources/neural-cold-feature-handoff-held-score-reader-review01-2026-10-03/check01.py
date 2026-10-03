"""Actual-source extracted weakref/failure seams, expressly synthetic objects."""
import ast,gc,sys,types,unittest,weakref
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;P=BASE/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03';sys.path.insert(0,str(P))
from test_completion01 import load
class Marker:pass
class Checks(unittest.TestCase):
 def test_completion_weak_key_releases_known_lease_graph(self):
  s,ns=load();target=Marker();target.graph=Marker();target.owner=Marker();s._imported=s._imported_pin=target
  # Extract the actual nonarchive producer lease body. Its free variables bind
  # stage/dictionary/root/fd/start/io, not the stream local captured by compute.
  source=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source-bodies/tradingagents/research/onchain_replication/compact_mcm.py'
  outer=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked');lease=next(n for n in ast.walk(outer) if isinstance(n,ast.FunctionDef) and n.name=='lease')
  wrapper=ast.parse('def make(stage,dictionary,root,fd,start,io,require):\n pass').body[0];wrapper.body=[lease,ast.Return(ast.Name('lease',ast.Load()))];env={};exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),str(source),'exec'),env)
  stage=Marker();stage.owner=target.owner;s.batches.lease=env['make'](stage,target,Path('/synthetic'),-1,{},None,None)
  self.assertNotIn('stream',s.batches.lease.__code__.co_freevars);self.assertNotIn('compute',s.batches.lease.__code__.co_freevars)
  s.finish();sw=weakref.ref(s);tw=weakref.ref(target);gw=weakref.ref(target.graph);bw=weakref.ref(s.batches) if hasattr(s.batches,'__weakref__') else None
  del s,target,stage;gc.collect();self.assertIsNone(sw());self.assertIsNone(tw());self.assertIsNone(gw());self.assertEqual(len(ns['_COMPLETED']),0)
 def test_weak_key_not_general_no_callback_retention_guarantee(self):
  s,ns=load();s.batches.lease=lambda stream=s:None;s.finish();w=weakref.ref(s);del s;gc.collect();self.assertIsNotNone(w());self.assertEqual(len(ns['_COMPLETED']),1)
  # This explicit synthetic back-reference is not evidence of an actual caller.
  ns['_COMPLETED'].clear();gc.collect();self.assertIsNone(w())
 def test_registry_publication_failure_remains_failure_after_close(self):
  s,ns=load();fatal=MemoryError('synthetic registry allocation')
  class Fail(dict):
   def __setitem__(self,*a):raise fatal
  ns['_COMPLETED']=Fail()
  with self.assertRaises(MemoryError) as got:s.finish()
  self.assertIs(got.exception,fatal);self.assertTrue(s.closed);self.assertEqual(ns['_COMPLETED'],{})
 def test_directory_rejoin_failure_never_publishes_success(self):
  s,ns=load();error=ValueError('synthetic replaced directory');ns['_directory_rejoin']=lambda *_:(_ for _ in ()).throw(error)
  with self.assertRaises(ValueError) as got:s.finish()
  self.assertIs(got.exception,error);self.assertNotIn(s,ns['_COMPLETED']);self.assertTrue(s.closed)
 def test_success_identity_mutations_refuse(self):
  for field,value in [('batches',None),('_imported',object()),('head','e'*64),('n',True)]:
   with self.subTest(field=field):
    s,ns=load();s.finish();setattr(s,field,value)
    with self.assertRaises((ValueError,AttributeError)):ns['completed_evidence'](s)
 def test_archive_lease_closure_excludes_produce_and_stream(self):
  p=Path('tradingagents/research/onchain_replication/archive_owner_writer.py');tree=ast.parse(p.read_text());outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_run_locked');lease=next(n for n in ast.walk(outer) if isinstance(n,ast.FunctionDef) and n.name=='lease');names={n.id for n in ast.walk(lease) if isinstance(n,ast.Name)};self.assertNotIn('produce',names);self.assertNotIn('stream',names);self.assertIn('science_lease',names)
if __name__=='__main__':unittest.main(verbosity=2)
