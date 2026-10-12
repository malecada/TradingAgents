"""AST and tiny flock engineering only; no genuine authority constructed."""
from pathlib import Path
import ast,types,unittest,contextlib,tempfile,fcntl,json
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
N=types.SimpleNamespace
I={};exec(compile((S/'imported_authority_interval.py').read_text(),str(S/'imported_authority_interval.py'),'exec'),I)
def require(ok,why):
 if not ok:raise ValueError(why)
def load(path,names,ns):
 t=ast.parse(path.read_text());t.body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names]
 for n in ast.walk(t):
  if isinstance(n,ast.FunctionDef):n.body=[s for s in n.body if not isinstance(s,ast.ImportFrom)]
 exec(compile(t,str(path),'exec'),ns);return ns
class Fixture:
 def __init__(self,selected=True,cost=9):
  self.time=0;self.cost=cost;self.events=[];self.hook=None;self.polls=0;self.active_lock=False;self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.lockpath=self.root/'lock'
  f=self
  @contextlib.contextmanager
  def lock(root):
   with f.lockpath.open('a') as stream:
    fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);f.active_lock=True
    try:yield
    finally:f.active_lock=False
  self.lock=lock
  class ResearchRun:
   def _active(self):f.events.append('active')
   def _check_source(self):f.events.append('source');f.time+=f.cost
   def read_inputs(self,names,**kw):
    with lock(f.root):
     self._active();self._check_source();values={n:f.body(n) for n in names};self._active();self._check_source()
     for n in names:require(f.body(n)==values[n],'original read rejoin')
     self._active();return values
  class Target:
   def lease(self):
    # A second independently opened descriptor is precisely the production
    # non-reentrant flock hazard; LOCK_NB turns a deadlock into a test failure.
    with f.lockpath.open('a') as probe:
     fcntl.flock(probe.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not f.active_lock,'poll under lifecycle lock');f.polls+=1;f.events.append('poll')
    f.interval.validate(lambda:None,lambda:None,lambda:None)
    if f.hook:f.hook(self)
  self.run=ResearchRun();self.run.admission=N(root=self.root,inputs={'x':{'path':'x','sha256':'hash'},'y':{'path':'y','sha256':'other'}})
  self.owner=N(bound=N(_run=self.run));self.target=Target();self.target.owner=self.owner;self.target.execution=N(_owner=self.owner,_bound=self.owner.bound);self.values={'x':b'x','y':b'y'}
  cfg=dict(schema_version=1,kind=I['KIND'],live_interval_ms=1000,fingerprint_interval_ms=2000,full_interval_ms=10000,max_stale_ms=60000,max_calls_between_full=1000,assumption=I['ASSUMPTION'])
  self.interval=I['Interval'](cfg,clock=lambda:self.time);self.interval.validate(lambda:None,lambda:None,lambda:None)
  ns=dict(require=require,ResearchRun=ResearchRun,Target=Target,_lock=lock,MAX_MANIFEST_BYTES=32*1024**2,_registered_body=lambda run,name,limit:f.body(name),_read_registered=lambda run,name,**kw:f.body(name))
  name='batched_continuation.py' if selected else 'BASELINE_batched_continuation.py'
  load(P/name,{'_target_identity','_poll_target','_reader_target','_bounded_input','_polled_batch_inputs','_load_batch'},ns);self.ns=ns
 def body(self,name):self.events.append('read:'+name);return self.values[name]
 def close(self):self.temp.cleanup()
class Checks(unittest.TestCase):
 def test_original_twelve_checks_red_selected_green(self):
  a=Fixture(False);b=Fixture()
  try:
   for _ in range(6):a.ns['_bounded_input'](a.run,'x',max_bytes=100)
   with self.assertRaisesRegex(ValueError,'stale interval'):a.target.lease()
   for _ in range(6):self.assertEqual(b.ns['_bounded_input'](b.run,'x',max_bytes=100,target=b.target),b'x')
   self.assertEqual(a.time,b.time);self.assertEqual(b.time,108);self.assertEqual(b.polls,12)
  finally:a.close();b.close()
 def test_bundle_outside_real_nonreentrant_lock(self):
  f=Fixture()
  try:
   for _ in range(6):self.assertEqual(f.ns['_polled_batch_inputs'](f.run,('x','y'),f.target),{'x':b'x','y':b'y'})
   self.assertEqual(f.time,108)
   with f.lock(f.root):
    with self.assertRaises(BlockingIOError):f.target.lease()
  finally:f.close()
 def test_default_order_literal(self):
  a=Fixture(False);b=Fixture()
  try:self.assertEqual(a.ns['_bounded_input'](a.run,'x',max_bytes=100),b.ns['_bounded_input'](b.run,'x',max_bytes=100));self.assertEqual(a.events,b.events)
  finally:a.close();b.close()
 def test_indivisible_transaction_still_refuses(self):
  for bundle in (False,True):
   f=Fixture(cost=31)
   try:
    with self.assertRaisesRegex(ValueError,'stale interval'):
     if bundle:f.ns['_polled_batch_inputs'](f.run,('x','y'),f.target)
     else:f.ns['_bounded_input'](f.run,'x',max_bytes=100,target=f.target)
   finally:f.close()
 def test_post_callback_rejoin_mutation(self):
  for bundle in (False,True):
   for contract in (False,True):
    f=Fixture()
    def mutate(t):
     if f.polls==2:
      if contract:f.run.admission.inputs['x']['sha256']='changed'
      else:f.values['x']=b'changed'
    f.hook=mutate
    try:
     with self.assertRaisesRegex(ValueError,'changed after target poll'):
      if bundle:f.ns['_polled_batch_inputs'](f.run,('x','y'),f.target)
      else:f.ns['_bounded_input'](f.run,'x',max_bytes=100,target=f.target)
    finally:f.close()
 def test_run_owner_execution_and_callback_fatal(self):
  f=Fixture()
  try:
   for target in (object(),N(owner=f.owner,execution=f.target.execution)):
    with self.assertRaises(ValueError):f.ns['_poll_target'](f.run,target)
   original=f.owner.bound._run;f.owner.bound._run=object()
   with self.assertRaises(ValueError):f.ns['_poll_target'](f.run,f.target)
   f.owner.bound._run=original;f.hook=lambda t:setattr(t,'execution',N(_owner=f.owner,_bound=f.owner.bound))
   with self.assertRaisesRegex(ValueError,'changed during poll'):f.ns['_poll_target'](f.run,f.target)
   fatal=KeyboardInterrupt('original');f.hook=lambda t:(_ for _ in ()).throw(fatal)
   with self.assertRaises(KeyboardInterrupt) as e:f.ns['_bounded_input'](f.run,'x',max_bytes=100,target=f.target)
   self.assertIs(e.exception,fatal)
  finally:f.close()
 def test_retained_reader_target_and_legacy(self):
  f=Fixture()
  try:
   reader=(f.run,b'{}',False,'manifest');self.assertIsNone(f.ns['_reader_target'](f.run,reader));pin=f.ns['_target_identity'](f.run,f.target);reader=(*reader,pin);self.assertIs(f.ns['_reader_target'](f.run,reader),f.target)
   f.target.owner=N(bound=f.owner.bound)
   with self.assertRaises(ValueError):f.ns['_reader_target'](f.run,reader)
  finally:f.close()
 def test_restoration_and_reload_forwarding_static(self):
  t=ast.parse((P/'batched_continuation.py').read_text())
  funcs={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
  for name in ('verify_prefix','restore_prefix','_load_batch'):
   for call in (n for n in ast.walk(funcs[name]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('_bounded_input','_authority','_registered_batch')):
    self.assertTrue(any(k.arg is None and "'target'" in ast.unparse(k.value) for k in call.keywords),(name,ast.unparse(call)))
  original=ast.parse((P/'BASELINE_batched_continuation.py').read_text());old=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='_bounded_input');new=funcs['_bounded_input'];new.args.kwonlyargs.pop();new.args.kw_defaults.pop();new.body=[n for n in new.body if not (isinstance(n,ast.If) and ast.unparse(n.test)=='target is not None')];self.assertEqual(ast.dump(old),ast.dump(new))
if __name__=='__main__':unittest.main(verbosity=2)
