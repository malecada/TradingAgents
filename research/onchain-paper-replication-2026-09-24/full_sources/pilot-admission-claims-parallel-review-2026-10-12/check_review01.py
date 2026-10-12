"""Adversarial synthetic scheduling controls; no genuine claims/Git/project import."""
import ast,copy,concurrent.futures,json,runpy,tempfile,threading,unittest
from unittest.mock import patch
from pathlib import Path
P=Path(__file__).resolve().parent;C=P.parent/'pilot-admission-claims-parallel-candidate-2026-10-12';M=runpy.run_path(str(C/'check_candidate01.py'))
class Review(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=P);self.root=Path(self.temp.name);folder=self.root/'research_runs';folder.mkdir()
  for n in ('a','b','c'):(folder/n).mkdir();(folder/n/'claim.json').write_text('{}')
 def tearDown(self):self.temp.cleanup()
 def test_main_interrupt_drains_pending_and_notes_later_failure(self):
  started=threading.Barrier(3);release=threading.Event();done=[];calls=[];fatal=KeyboardInterrupt('caller interrupt')
  def verify(p):
   calls.append(p.name);started.wait(3);release.wait(3);done.append(p.name)
   if p.name=='b':raise ValueError('later b failed')
   return {'experiment_id':p.name}
  def interrupted_wait(*a,**k):started.wait(3);release.set();raise fatal
  env=M['load'](C/'admission.py',verify)
  with patch.object(concurrent.futures,'wait',interrupted_wait):
   with self.assertRaises(KeyboardInterrupt) as caught:env['claims'](self.root,workers=2)
  self.assertIs(caught.exception,fatal);self.assertEqual(set(calls),{'a','b'});self.assertEqual(set(done),set(calls));self.assertTrue(any('later b failed' in n for n in fatal.__notes__))
  self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_shutdown_failure_after_all_finished_refuses(self):
  original=concurrent.futures.ThreadPoolExecutor;attempts=[]
  class FailedShutdown(original):
   def shutdown(self,**kw):
    super().shutdown(**kw);attempts.append(1);raise RuntimeError('post-drain cleanup failed')
  env=M['load'](C/'admission.py',lambda p:{'experiment_id':p.name})
  with patch.object(concurrent.futures,'ThreadPoolExecutor',FailedShutdown):
   with self.assertRaisesRegex(RuntimeError,'post-drain'):env['claims'](self.root,workers=2)
  self.assertEqual(len(attempts),2);self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_observed_later_failure_blocks_refill_even_if_earlier_succeeds(self):
  release=threading.Event();calls=[];actual_wait=concurrent.futures.wait
  def verify(p):
   calls.append(p.name)
   if p.name=='a':release.wait(3);return {'experiment_id':p.name}
   raise ValueError('later failed')
  def observed(*a,**k):
   result=actual_wait(*a,**k);release.set();return result
  env=M['load'](C/'admission.py',verify)
  with patch.object(concurrent.futures,'wait',observed):
   with self.assertRaisesRegex(ValueError,'later failed'):env['claims'](self.root,workers=2)
  self.assertEqual(set(calls),{'a','b'});self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_committed_selector_corruption_before_proofs(self):
  tree=ast.parse((C/'admission.py').read_text());f=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admit'));f.returns=None
  stop=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='claim_workers' for t in n.targets));f.body=f.body[:stop+1]+[ast.Return(ast.Name('claim_workers',ast.Load()))]
  spec={'schema_version':1};events=[]
  env=M['load'](C/'admission.py',lambda p:events.append('proof'));env.update(_git=lambda root,*a:(b'source' if a[0]=='rev-parse' else json.dumps(spec).encode() if a[0]=='show' else b''),_committed=lambda *a:json.dumps(spec).encode())
  exec(compile(ast.fix_missing_locations(ast.Module([f],[])),'synthetic-admit-prefix','exec'),env)
  for bad in (None,{'format':'bounded-claims-v1','workers':True},{'format':'bounded-claims-v1','workers':2,'cache':True},{'format':'bounded-claims-v1','workers':'2'}):
   spec['historical_claim_verification']=bad
   with self.assertRaises(ValueError):env['admit'](root=self.root,registration='gate',experiment='e',source='source')
  self.assertEqual(events,[])
 def test_secondary_drain_probe_failure_preserves_caller_fatal(self):
  original=concurrent.futures.ThreadPoolExecutor;release=threading.Event();started=threading.Barrier(3);fatal=KeyboardInterrupt('first caller interrupt');probefail=SystemExit('second drain interruption');draining=[False]
  class Executor(original):
   def submit(self,*a,**k):
    future=super().submit(*a,**k);actual=future.done
    def done():
     if draining[0]:raise probefail
     return actual()
    future.done=done;return future
   def shutdown(self,**kw):super().shutdown(**kw);draining[0]=True
  def verify(p):started.wait(3);release.wait(3);return {'experiment_id':p.name}
  def interrupted_wait(*a,**k):started.wait(3);release.set();raise fatal
  env=M['load'](C/'admission.py',verify)
  with patch.object(concurrent.futures,'ThreadPoolExecutor',Executor),patch.object(concurrent.futures,'wait',interrupted_wait):
   try:env['claims'](self.root,workers=2)
   except BaseException as caught:self.assertIs(caught,fatal)
   else:self.fail('interruption must refuse')
  self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
if __name__=='__main__':unittest.main()
