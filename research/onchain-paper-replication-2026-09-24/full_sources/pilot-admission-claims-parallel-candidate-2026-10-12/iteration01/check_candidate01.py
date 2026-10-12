"""Synthetic AST engineering controls; no project modules, Git or real claims."""
import ast,copy,hashlib,json,tempfile,threading,time,types,unittest
import concurrent.futures
from unittest.mock import patch
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];LIVE=R/'tradingagents/research/admission.py'
def load(path,verify):
 tree=ast.parse(path.read_text());env={'Path':Path,'verify_claim':verify,'json':json}
 class LocalImports(ast.NodeTransformer):
  def visit_ImportFrom(self,n):return ast.Pass() if n.level else n
 names={'claims','_parallel_claims','_verify_claim_child','_claim_workers','_claim_failure_note'}
 nodes=[LocalImports().visit(copy.deepcopy(n)) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 exec(compile(ast.fix_missing_locations(ast.Module(nodes,[])),str(path),'exec'),env);return env
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);folder=self.root/'research_runs';folder.mkdir()
  for name in ('a','b','c','d'):(folder/name).mkdir();(folder/name/'claim.json').write_text('{}')
  (folder/'.hidden').mkdir()
 def tearDown(self):self.tmp.cleanup()
 def test_default_parity_and_worker1(self):
  observed=[]
  for path,kw in ((LIVE,{}),(P/'admission.py',{}),(P/'admission.py',{'workers':1})):
   calls=[];env=load(path,lambda p:calls.append(p.name) or {'experiment_id':p.name});value=env['claims'](self.root,**kw);observed.append((value,calls))
  self.assertEqual(observed[0],observed[1]);self.assertEqual(observed[0],observed[2])
 def test_overlap_cap_order_and_freshness(self):
  lock=threading.Lock();barrier=threading.Barrier(2);active=0;peak=0;calls=[]
  def verify(p):
   nonlocal active,peak
   with lock:active+=1;peak=max(peak,active);calls.append(p.name)
   barrier.wait(timeout=3)
   if p.name in ('a','c'):time.sleep(.01)
   with lock:active-=1
   return {'experiment_id':p.name}
  env=load(P/'admission.py',verify)
  for _ in range(2):self.assertEqual([x['experiment_id'] for x in env['claims'](self.root,workers=2)],list('abcd'))
  self.assertEqual((peak,active,len(calls)),(2,0,8));self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_earliest_failure_drain_no_later_submission(self):
  started=threading.Barrier(2);later_finished=threading.Event();calls=[];early=ValueError('a first');late=RuntimeError('b later')
  def verify(p):
   calls.append(p.name);started.wait(timeout=3)
   if p.name=='a':later_finished.wait(3);raise early
   later_finished.set();raise late
  env=load(P/'admission.py',verify)
  with self.assertRaises(ValueError) as got:env['claims'](self.root,workers=2)
  self.assertIs(got.exception,early);self.assertEqual(set(calls),{'a','b'});self.assertTrue(any('b later' in n for n in early.__notes__));self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_later_speculative_fatal_recorded(self):
  barrier=threading.Barrier(2);first=ValueError('first');later=KeyboardInterrupt('speculative fatal')
  def verify(p):barrier.wait(3);raise first if p.name=='a' else later
  env=load(P/'admission.py',verify)
  with self.assertRaises(ValueError) as got:env['claims'](self.root,workers=2)
  self.assertIs(got.exception,first);self.assertTrue(any('KeyboardInterrupt' in n for n in first.__notes__))
 def test_fatal_and_note_failure(self):
  class Fatal(BaseException):
   def add_note(self,text):raise RuntimeError('override')
  barrier=threading.Barrier(2);first=Fatal('first')
  def verify(p):barrier.wait(3);raise first if p.name=='a' else ValueError('later')
  env=load(P/'admission.py',verify)
  with self.assertRaises(Fatal) as got:env['claims'](self.root,workers=2)
  self.assertIs(got.exception,first)
 def test_child_checks_and_hidden(self):
  for workers in (1,2):
   env=load(P/'admission.py',lambda p:{'experiment_id':'wrong'})
   with self.assertRaisesRegex(ValueError,'identity differs'):env['claims'](self.root,workers=workers)
   env=load(P/'admission.py',lambda p:{'experiment_id':p.name});a=self.root/'research_runs/a';(a/'complete.json').touch();(a/'failed.json').touch()
   with self.assertRaisesRegex(ValueError,'contradictory'):env['claims'](self.root,workers=workers)
   (a/'complete.json').unlink();(a/'failed.json').unlink();(a/'claim.json').unlink()
   with self.assertRaisesRegex(ValueError,'partial run'):env['claims'](self.root,workers=workers)
   (a/'claim.json').write_text('{}')
 def test_unprintable_later_failure_recorded(self):
  class Unprintable(BaseException):
   def __str__(self):raise RuntimeError('bad str')
  env=load(P/'admission.py',lambda p:None);first=ValueError('first')
  env['_claim_failure_note'](first,'later speculative',Unprintable())
  self.assertEqual(first.__notes__,['later speculative: Unprintable'])
 def test_policy(self):
  env=load(P/'admission.py',lambda p:None);f=env['_claim_workers']
  for workers in (1,2):self.assertEqual(f({'format':'bounded-claims-v1','workers':workers}),workers)
  for bad in (None,{},[],{'format':'bad','workers':2},{'format':'bounded-claims-v1','workers':True},{'format':'bounded-claims-v1','workers':3},{'format':'bounded-claims-v1','workers':2,'cache':True}):
   with self.assertRaises(ValueError):f(bad)
 def test_committed_admit_selection(self):
  tree=ast.parse((P/'admission.py').read_text());f=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admit'));f.returns=None
  stop=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prior' for t in n.targets));f.body=f.body[:stop+1]+[ast.Return(ast.Name('prior',ast.Load()))]
  spec={'schema_version':1,'program_id':'p','families':{'f':{'mechanism_id':'m','attempt_budget':1,'prior_attempts':0,'history_reference':'synthetic'}},'datasets':{},'experiments':{'e':{'charter':{'path':'charter','sha256':'hash'},'family':'f','parent':None,'question':'synthetic','stage':'development','reuse':'exploratory','source_files':{'x':'hash'},'runtime_hashes':{},'cells':['c'],'outputs':['a.json'],'windows':[{}],'inputs':{'x':{}}}}};calls=[]
  env=load(P/'admission.py',lambda p:None);env.update(identity=lambda *a:None,digest=lambda b:'hash',runtime_hashes=lambda:{},_source_files=lambda *a:None,claims=lambda root,**kw:calls.append(kw) or ['synthetic'],_committed=lambda *a:json.dumps(spec).encode() if a[2]=='gate' else b'charter',_git=lambda root,*a:b'source' if a[0]=='rev-parse' else (json.dumps(spec).encode() if a[-1]=='source:gate' else b'charter'))
  exec(compile(ast.fix_missing_locations(ast.Module([f],[])),'admit-prefix','exec'),env)
  for option,expected in ((None,{}),(1,{}),(2,{'workers':2})):
   if option is None:spec.pop('historical_claim_verification',None)
   else:spec['historical_claim_verification']={'format':'bounded-claims-v1','workers':option}
   self.assertEqual(env['admit'](root=self.root,registration='gate',experiment='e',source='source'),['synthetic']);self.assertEqual(calls[-1],expected)
  before=len(calls);spec['historical_claim_verification']={'format':'bounded-claims-v1','workers':True}
  with self.assertRaises(ValueError):env['admit'](root=self.root,registration='gate',experiment='e',source='source')
  self.assertEqual(len(calls),before)
 def test_shutdown_failure_never_accepts(self):
  original=concurrent.futures.ThreadPoolExecutor
  class Interrupted(original):
   tries=0
   def shutdown(self,**kw):
    self.tries+=1
    if self.tries==1:raise RuntimeError('shutdown interruption')
    return super().shutdown(**kw)
  env=load(P/'admission.py',lambda p:{'experiment_id':p.name})
  with patch.object(concurrent.futures,'ThreadPoolExecutor',Interrupted):
   with self.assertRaisesRegex(RuntimeError,'shutdown interruption'):env['claims'](self.root,workers=2)
  self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_fatal_survives_shutdown_error(self):
  original=concurrent.futures.ThreadPoolExecutor
  class Fatal(BaseException):
   def add_note(self,text):raise RuntimeError('override')
  class Cleanup(original):
   def shutdown(self,**kw):
    super().shutdown(**kw);raise RuntimeError('cleanup uncertain')
  fatal=Fatal('primary');env=load(P/'admission.py',lambda p:(_ for _ in ()).throw(fatal))
  with patch.object(concurrent.futures,'ThreadPoolExecutor',Cleanup):
   with self.assertRaises(Fatal) as got:env['claims'](self.root,workers=2)
  self.assertIs(got.exception,fatal);self.assertTrue(any('cleanup uncertain' in n for n in fatal.__notes__))
  self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_scheduler_fatal_drains_launched_work(self):
  original=concurrent.futures.wait;fatal=KeyboardInterrupt('scheduler');calls=[];done=[]
  def verify(p):calls.append(p.name);time.sleep(.025);done.append(p.name);return {'experiment_id':p.name}
  def fail_wait(*a,**kw):raise fatal
  env=load(P/'admission.py',verify)
  with patch.object(concurrent.futures,'wait',fail_wait):
   with self.assertRaises(KeyboardInterrupt) as got:env['claims'](self.root,workers=2)
  self.assertIs(got.exception,fatal);self.assertEqual(set(calls),{'a','b'});self.assertEqual(set(done),set(calls));self.assertFalse(any(t.name.startswith('claim-proof') for t in threading.enumerate()))
 def test_unmodified_transport_and_body(self):
  a=ast.parse(LIVE.read_text());b=ast.parse((P/'admission.py').read_text());original={n.name:ast.dump(n) for n in a.body if isinstance(n,ast.FunctionDef)};updated={n.name:ast.dump(n) for n in b.body if isinstance(n,ast.FunctionDef)}
  for name in original:
   if name not in ('admit','claims'):self.assertEqual(original[name],updated[name],name)
  old=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='claims');new=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='claims')
  self.assertEqual(ast.dump(old.body[-2]),ast.dump(new.body[-2])) # complete sequential for loop
if __name__=='__main__':unittest.main()
