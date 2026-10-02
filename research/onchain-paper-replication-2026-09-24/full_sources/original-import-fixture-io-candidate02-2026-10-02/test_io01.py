import ast,hashlib,os,stat,sys,tempfile,types,unittest
from contextlib import contextmanager
from pathlib import Path
HERE=Path(__file__).resolve().parent
if os.environ.get('IO_BASELINE')=='1':HERE=HERE/'baseline'

def load():
 tree=ast.parse(((HERE/'owned_io.py').read_text() if (HERE/'owned_io.py').exists() else '')+'\n'+(HERE/'score_batches.py').read_text())
 names={'CleanupFailure','_fatal','_flatten','_cleanup','_close_after_failure','_release','_closing','_opened','_write','_read','_hash','_require','_signature','_stamp','_json'}
 nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_UNSET' for x in n.targets)]
 ns=dict(os=os,stat=stat,sys=sys,hashlib=hashlib,contextmanager=contextmanager,Path=Path,META_LIMIT=8192,json=__import__('json'))
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'selected-IO','exec'),ns);return ns

def throwing(error,seen,label):
 def action():seen.append(label);raise error
 return action

class IO(unittest.TestCase):
 def test_first_body_fatal_survives_all_closes(self):
  ns=load();seen=[];fatal=MemoryError('body')
  try:
   try:raise fatal
   finally:ns['_cleanup']([throwing(OSError('close'),seen,1),lambda:seen.append(2)])
  except BaseException as got:self.assertIs(got,fatal)
  self.assertEqual(seen,[1,2])
 def test_later_true_fatal_beats_prior_uncertainty(self):
  ns=load();seen=[];fatal=SystemExit(17)
  def first():ns['_cleanup']([throwing(OSError('uncertain'),seen,1)])
  with self.assertRaises(SystemExit) as caught:ns['_cleanup']([first,throwing(fatal,seen,2),lambda:seen.append(3)])
  self.assertIs(caught.exception,fatal);self.assertEqual(seen,[1,2,3]);self.assertIsNotNone(fatal.__cause__)
 def test_first_close_fatal_survives_later_fatal(self):
  ns=load();seen=[];first=MemoryError('first')
  with self.assertRaises(MemoryError) as caught:ns['_cleanup']([throwing(first,seen,1),throwing(SystemExit(2),seen,2)])
  self.assertIs(caught.exception,first);self.assertEqual(seen,[1,2])
 def test_write_descriptor_once_on_fatal(self):
  ns=load();fatal=MemoryError('write');closed=[]
  class Fake:
   O_WRONLY=O_CREAT=O_EXCL=O_NOFOLLOW=1
   def open(self,*a,**k):return 41
   def fdopen(self,*a,**k):raise fatal
   def write(self,*a):raise fatal
   def close(self,fd):closed.append(fd);raise OSError('close')
   def fsync(self,*a):pass
  ns['os']=Fake()
  with self.assertRaises(MemoryError) as got:ns['_write'](13,'attempt',b'payload')
  self.assertIs(got.exception,fatal);self.assertEqual(closed,[41])
 def test_read_descriptor_once_on_fatal(self):
  ns=load();fatal=SystemExit('read');closed=[]
  class Fake:
   O_RDONLY=O_NOFOLLOW=O_NONBLOCK=1
   def open(self,*a,**k):return 42
   def fdopen(self,*a,**k):raise fatal
   def fstat(self,*a):raise fatal
   def close(self,fd):closed.append(fd);raise OSError('close')
  ns['os']=Fake()
  with self.assertRaises(SystemExit) as got:ns['_read'](13,'attempt',123)
  self.assertIs(got.exception,fatal);self.assertEqual(closed,[42])
 def test_real_tiny_exclusive_bytes(self):
  ns=load()
  with tempfile.TemporaryDirectory() as td:
   fd=os.open(td,os.O_RDONLY|os.O_DIRECTORY)
   try:
    self.assertEqual(ns['_write'](fd,'x',b'abc'),hashlib.sha256(b'abc').hexdigest())
    self.assertEqual(ns['_read'](fd,'x',3),b'abc')
    with self.assertRaises(FileExistsError):ns['_write'](fd,'x',b'replace')
   finally:os.close(fd)
 def test_opened_fdopen_failure_closes_owned_fd(self):
  ns=load();fatal=MemoryError('fdopen');seen=[]
  class Fake:
   O_RDONLY=O_NOFOLLOW=O_NONBLOCK=O_CLOEXEC=O_WRONLY=O_CREAT=O_EXCL=1
   def open(self,*a,**k):return 44
   def fdopen(self,*a,**k):raise fatal
   def close(self,fd):seen.append(fd)
  ns['os']=Fake()
  with self.assertRaises(MemoryError) as got:
   with ns['_opened'](Path('/irrelevant'),'rb'):pass
  self.assertIs(got.exception,fatal);self.assertEqual(seen,[44])
 def test_fixture_closure_error_not_success(self):
  tree=ast.parse((HERE/'resource_fixture.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
  tail=ast.Module(body=fn.body[-3:],type_ignores=[])
  # Execute only unchanged tail control flow with explicit inert callback objects.
  error=ValueError('owner finish failed');rows=[{'status':'complete'},{'status':'complete'}]
  wrapper=ast.FunctionDef(name='tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=tail.body,decorator_list=[])
  module=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]))
  ns={'primary':error,'actions':[], 'rows':rows,'retained_actions':lambda *a:None,'import_metadata':types.SimpleNamespace(close_actions=lambda *a:None)}
  # Execute the exact tail after source check; fake callbacks make no authority claim.
  self.assertTrue(any(isinstance(n,ast.Raise) and isinstance(n.exc,ast.Name) and n.exc.id=='primary' for n in ast.walk(ast.Module(body=fn.body[-3:],type_ignores=[]))))
  exec(compile(module,'actual-fixture-tail','exec'),ns)
  with self.assertRaises(ValueError) as caught:ns['tail']()
  self.assertIs(caught.exception,error);self.assertEqual(rows,[{'status':'complete'},{'status':'complete'}])

class Boundaries(unittest.TestCase):
 def test_real_stream_close_all_once(self):
  ns=load();io=types.SimpleNamespace(**ns)
  tree=ast.parse((HERE/'mcm_score_stream.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='close')
  seen=[];first=MemoryError('tail-close')
  obj=types.SimpleNamespace(closed=False,active=types.SimpleNamespace(close=throwing(first,seen,'tail')),batches=types.SimpleNamespace(close=throwing(OSError('batch-close'),seen,'batch')),fd=7)
  scope={'batch':io,'os':types.SimpleNamespace(close=lambda fd:seen.append(fd))}
  exec(compile(ast.Module(body=[method],type_ignores=[]),'actual-stream-close','exec'),scope)
  with self.assertRaises(MemoryError) as caught:scope['close'](obj)
  self.assertIs(caught.exception,first);self.assertTrue(obj.closed);scope['close'](obj);self.assertEqual(seen,['tail','batch',7])
 def test_mapping_invalidated_before_uncertain_close(self):
  ns=load();io=types.SimpleNamespace(**ns);seen=[];fatal=SystemExit('mapping')
  tree=ast.parse((HERE/'matching_hardening.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='close')
  scope={'io':io};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-mapping-close','exec'),scope)
  state={'safe':True,'order':types.SimpleNamespace(_mmap=types.SimpleNamespace(close=throwing(fatal,seen,'mapping')))}
  with self.assertRaises(SystemExit) as caught:scope['close'](state)
  self.assertIs(caught.exception,fatal);self.assertFalse(state['safe']);self.assertIsNone(state['order']);scope['close'](state);self.assertEqual(seen,['mapping'])
 def test_actual_producer_handler_preserves_primary_and_closes_all(self):
  ns=load();io=types.SimpleNamespace(**ns);seen=[];fatal=MemoryError('kernel')
  io._write=lambda *a:seen.append('marker');io._json=lambda x:b'failed'
  tree=ast.parse((HERE/'compact_mcm.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked');attempt=next(n for n in fn.body if isinstance(n,ast.Try));handler=attempt.handlers[0]
  wrapped=ast.FunctionDef(name='failure',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),decorator_list=[],body=[ast.Try(body=[ast.Raise(exc=ast.Name(id='fatal',ctx=ast.Load()))],handlers=[handler],orelse=[],finalbody=[])])
  obj=types.SimpleNamespace(poisoned=False,identity='owner')
  log=types.SimpleNamespace(closed=False,fail=lambda *args:throwing(OSError('failed-terminal'),seen,'fail')(),close=lambda:seen.append('log'))
  scope={'io':io,'fatal':fatal,'owner':obj,'stream':types.SimpleNamespace(closed=False,close=throwing(OSError('stream'),seen,'stream')),'log':log,'claimed':True,'fd':13,'compact_matcher':types.SimpleNamespace(CleanupFailure=ns['CleanupFailure'])}
  exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapped],type_ignores=[])),'actual-producer-handler','exec'),scope)
  with self.assertRaises(MemoryError) as caught:scope['failure']()
  self.assertIs(caught.exception,fatal);self.assertTrue(obj.poisoned);self.assertEqual(seen,['stream','fail','log','marker'])
 def test_iterator_body_fatal_with_uncertain_close(self):
  ns=load();seen=[];fatal=MemoryError('scan-body')
  with self.assertRaises(MemoryError) as caught:
   with ns['_closing'](types.SimpleNamespace(close=throwing(OSError('scan-close'),seen,1))):raise fatal
  self.assertIs(caught.exception,fatal);self.assertEqual(seen,[1])

class IOComposition(unittest.TestCase):
 def test_actual_mapping_context_first_fatal_and_all_handles(self):
  ns=load();io=types.SimpleNamespace(**ns);seen=[];fatal=MemoryError('consumer')
  io._open=lambda path:(path,71);io._root=lambda *a:None
  class Stream:
   def fileno(self):return 72
   def close(self):seen.append('stream');raise OSError('stream-close')
  mapped=types.SimpleNamespace(_mmap=types.SimpleNamespace(close=throwing(OSError('mapping-close'),seen,'mapping')))
  fakeos=types.SimpleNamespace(fdopen=lambda *a,**k:Stream(),close=lambda fd:seen.append(fd))
  tree=ast.parse((HERE/'compact_mcm_output.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='open_verified')
  scope={'io':io,'os':fakeos,'np':types.SimpleNamespace(memmap=lambda *a,**k:mapped),'_arguments':lambda *a:{},'_verified':lambda *a:({'array_bytes':4,'rows':1,'motifs':1},'sig'),'_file':lambda *a:(72,'sig'),'require':ns['_require'],'contextmanager':contextmanager}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-mapping-context','exec'),scope)
  with self.assertRaises(MemoryError) as caught:
   with scope['open_verified'](Path('/unused'),expected_sha256='x',stage_root='s',stage_sha256='h',contract={},expected_scope={},max_output_bytes=4,lease=lambda:None):raise fatal
  self.assertIs(caught.exception,fatal);self.assertEqual(seen,['mapping','stream',72,71])
 def test_array_context_preserves_original_failure(self):
  ns=load();seen=[];fatal=SystemExit('body')
  tree=ast.parse((HERE/'array_neighborhoods.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__exit__')
  scope=dict(ns);exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-array-exit','exec'),scope)
  class Context:
   close=staticmethod(throwing(OSError('index-close'),seen,'close'))
   __exit__=scope['__exit__']
   def __enter__(self):return self
  with self.assertRaises(SystemExit) as caught:
   with Context():raise fatal
  self.assertIs(caught.exception,fatal);self.assertEqual(seen,['close'])
 def test_actual_matcher_close_failure_stops_acknowledgement(self):
  self.matcher_case(None,MemoryError('engine-close'))
 def test_actual_matcher_body_fatal_survives_close_failure(self):
  self.matcher_case(SystemExit('advance'),OSError('engine-close'))
 def matcher_case(self,body_error,close_error):
  import copy
  ns=load();io=types.SimpleNamespace(**ns);seen=[]
  class Engine:
   def create(self,*a,**k):return {'phase':'annealing'}
   def advance(self,state,*a,**k):
    if body_error is not None:raise body_error
    state['phase']='done'
   def score_only(self,*a,**k):return types.SimpleNamespace(score=0.5,iterations=1,convergence='temperature_complete')
   def close(self,state):seen.append('close');raise close_error
  tree=ast.parse((HERE/'compact_matcher.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CompactMatcher');node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__call__')
  log=types.SimpleNamespace(events=0,start={'limits':{'max_events':10}},begin=lambda *a:None,complete=lambda *a:seen.append('complete'))
  obj=types.SimpleNamespace(busy=False,poisoned=False,log=log,retention=None,workload='w',checkpoints=0,reserved_bytes=0,config={},policy={'max_checkpoint_bytes':1,'max_score_buffer_bytes':100,'chunk_edges':2},schedule={'max_checkpoints':1,'max_total_checkpoints':1,'max_total_checkpoint_bytes':10**6,'calls_per_checkpoint':1,'operations_per_call':1},_check=lambda:None,_expected_event=lambda *a,**k:None,_ack_check=lambda *a:None,pair_identity=lambda *a:{})
  scope={'io':io,'engine':Engine(),'require':ns['_require'],'copy':copy,'cache_key':lambda x:'key','graph_identity':lambda x:x,'pair':types.SimpleNamespace(ENGINE_FIELDS=set(),policy_check=lambda *a:None,digest=lambda *a:'hash'),'_RETENTION':types.SimpleNamespace(get=lambda x:None),'CleanupFailure':ns['CleanupFailure'],'CheckpointStop':RuntimeError}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-matcher-call','exec'),scope)
  expected=body_error if body_error is not None else close_error
  with self.assertRaises(type(expected)) as caught:scope['__call__'](obj,{'schema_version':1,'kind':'mcm','workload_sha256':'w','typed_graphs':['a','b']},'a','b')
  self.assertIs(caught.exception,expected);self.assertTrue(obj.poisoned);self.assertFalse(obj.busy);self.assertEqual(seen,['close'])

if __name__=='__main__':unittest.main()
