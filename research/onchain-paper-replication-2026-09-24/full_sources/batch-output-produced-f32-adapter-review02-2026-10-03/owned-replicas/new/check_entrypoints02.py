"""Actual extracted entrypoints/classes, owned FD; authority bypass is test-only.

No real Context/Owner/Operation capability or remote session is constructed.
Actual Session constructor is entered only up to its original current-authority
check, which is replaced by a rejecting boundary sentinel in this source test.
"""
import ast,os,sys,types,unittest
from pathlib import Path
P=Path(__file__).parent
class BoundaryReached(Exception):pass
def extract(path,names,ns):
 tree=ast.parse(path.read_text());exec(compile(ast.Module([n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],[]),str(path),'exec'),ns);return ns
class Checks(unittest.TestCase):
 def setup_engine(self,schema):
  io=extract(P.parent/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/owned_io.py',{'CleanupFailure','_fatal','_flatten','_cleanup'},dict(sys=sys,_UNSET=object()))
  durable=extract(P/'archive_non_tail.py',{'require','fatal','select','Context','Operation'},dict(CleanupFailure=io['CleanupFailure']))
  calls=[]
  def close(fd):calls.append(('close',fd));os.close(fd)
  def boundary(c):calls.append('actual Session authority boundary');raise BoundaryReached()
  engine=extract(P/'selected_non_tail_transport.py',{'require','dispatch','close_context','Session'},dict(durable=types.SimpleNamespace(**durable),owned_io=types.SimpleNamespace(**io),os=types.SimpleNamespace(close=close),check_context=boundary,_late_failure=lambda c,e:calls.append(('failure',e))))
  c=object.__new__(durable['Context']);c.policy={'schema_version':schema,'terminal_output':'terminal.json'};c.failed=False;c.closed=False;c.active=None;c._transfer_active=None;c._transfer_spent={};c._transfer_observed={};c.operations={}
  def current():
   if c.closed:raise ValueError('qualified test Context closed')
  c.check=current;c.publish=lambda *args:calls.append(('publish',args));c.run=types.SimpleNamespace(write_json=lambda *args:calls.append(('output',args)))
  op=object.__new__(durable['Operation']);op.ledger=types.SimpleNamespace(context=c);op.check=lambda:calls.append('qualified operation check')
  def failed(error):c.failed=True;calls.append(('operation failed',error));raise error
  op.fail=failed
  return engine,c,op,calls
 def test_raw_dispatch_actual_session_boundary(self):
  e,c,op,calls=self.setup_engine(3)
  with self.assertRaises(BoundaryReached):e['dispatch'](op)
  self.assertIn('actual Session authority boundary',calls);self.assertTrue(c.failed)
 def test_f64_dispatch_unchanged(self):
  e,c,op,calls=self.setup_engine(2)
  with self.assertRaises(BoundaryReached):e['dispatch'](op)
  self.assertIn('actual Session authority boundary',calls)
 def close_case(self,schema,primary=None,publish_error=None):
  e,c,op,calls=self.setup_engine(schema);c.fd=os.open(P,os.O_RDONLY|os.O_DIRECTORY)
  if publish_error:
   def publish(*a):raise publish_error
   c.publish=publish
  try:
   if primary is None and publish_error is None:
    result=e['close_context'](c);self.assertEqual(result['status'],'complete-selected-pipe-controls-only')
   else:
    expected=primary if isinstance(primary,MemoryError) else publish_error or primary
    with self.assertRaises(type(expected)) as raised:e['close_context'](c,primary)
    self.assertIs(raised.exception,expected)
   with self.assertRaises(OSError):os.fstat(c.fd)
   self.assertTrue(c.closed);self.assertEqual(len([x for x in calls if isinstance(x,tuple) and x[0]=='close']),1)
   with self.assertRaises(BaseException):e['close_context'](c)
   self.assertEqual(len([x for x in calls if isinstance(x,tuple) and x[0]=='close']),1)
  finally:
   try:os.fstat(c.fd)
   except OSError:pass
   else:os.close(c.fd) # RED harness retains ownership after old early refusal.
 def test_raw_owned_fd_close_once(self):self.close_case(3)
 def test_f64_owned_fd_unchanged(self):self.close_case(2)
 def test_raw_firstfatal_body(self):self.close_case(3,MemoryError('first'),OSError('later'))
 def test_raw_later_firstfatal(self):self.close_case(3,ValueError('body'),MemoryError('cleanup'))
 def test_unselected_and_float_schema_refused(self):
  for schema in (1,4,True,3.0,'3'):
   e,c,op,calls=self.setup_engine(schema)
   with self.assertRaises((ValueError,NotImplementedError)):e['dispatch'](op)
   with self.assertRaises(ValueError):e['close_context'](c)
   self.assertNotIn('actual Session authority boundary',calls)
 def test_wrong_types_refused(self):
  e,c,op,calls=self.setup_engine(3)
  with self.assertRaises(ValueError):e['dispatch'](types.SimpleNamespace(ledger=op.ledger))
  with self.assertRaises(ValueError):e['close_context'](types.SimpleNamespace(policy=c.policy))
if __name__=='__main__':unittest.main()
