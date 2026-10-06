import ast,hashlib,importlib.util,io,json,math,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;M=H.parents[3];P=Path('tradingagents/research/onchain_replication');D=H/'candidate'/P
spec=importlib.util.spec_from_file_location('partial',D/'real_pilot_partial_progress.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
NODES={format(i,'064x'):2 for i in range(7)};KEY=next(iter(NODES))
class Clock:
 def __init__(self):self.now=0
 def __call__(self):return self.now
class Tests(unittest.TestCase):
 def make(self,output=None,max_records=8):
  clock=Clock();output=io.StringIO() if output is None else output
  report=p.MCMProgress({'schema_version':1,'interval_seconds':10,'max_records':max_records},NODES,claim_sha256='a'*64,source='b'*40,output=output,clock=clock)
  report.begin(KEY,2,32);return report,clock,output
 def test_genuine_scalar_event_transition_and_batch_lag(self):
  # Real pure PairLog transition function; synthetic scalar frames, no PairLog/Owner created.
  source=M/P/'compact_pair_log.py';tree=ast.parse(source.read_text());names={'_advance','_empty'}
  ns=dict(FRAME=struct.Struct('<QB7xQdQ32s32s32s'),ZERO='0'*64,math=math,require=p.require)
  exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(source),'exec'),ns)
  state=ns['_empty']();frame=ns['FRAME'];limits={'max_events':100,'max_pairs':64}
  def advance(kind):
   nonlocal state
   state=ns['_advance'](state,frame.pack(state['events'],kind,0,.5 if kind else 0.,2 if kind else 0,b'a'*32,b'b'*32,bytes(32)),limits,100)
  advance(0);log=SimpleNamespace(state=state);report,clock,out=self.make();report.poll(log,None)
  first=json.loads(out.getvalue());self.assertEqual(first['acknowledged_computed_matching_pairs'],0);self.assertTrue(first['pending_pair']);self.assertIsNone(first['acknowledged_pairs_per_second'])
  advance(1);log.state=state;clock.now=10;report.poll(log,None)
  row=report.last;self.assertEqual(row['acknowledged_computed_matching_pairs'],1);self.assertEqual(row['durable_tail_cells'],0);self.assertEqual(row['durable_score_batches'],0)
  stream=SimpleNamespace(cells=1,batches=SimpleNamespace(cells=0,chunks=0));clock.now=20;report.poll(log,stream)
  self.assertEqual(report.last['durable_tail_cells'],1);self.assertEqual(report.last['durable_score_batch_cells'],0)
  stream.batches.cells=1;stream.batches.chunks=1;clock.now=30;report.poll(log,stream)
  self.assertEqual(report.last['durable_score_batches'],1);self.assertEqual(report.last['representation_credit'],0);self.assertFalse(report.last['full_mcm_completion_verified_here']);self.assertFalse(report.last['joint_update_verified_here'])
 def test_finite_budget_throttle_clock_and_invalid_policy(self):
  report,c,out=self.make(max_records=2);log=SimpleNamespace(state={'started_pairs':0,'completed_pairs':0,'pending':None});report.poll(log,None)
  c.now=9;report.poll(log,None);self.assertEqual(report.records,1)
  c.now=10;report.poll(log,None);self.assertTrue(report.last['last_budget_slot']);c.now=100;report.poll(log,None);self.assertEqual(report.records,2);self.assertLessEqual(len(out.getvalue().encode()),2*p.MAX_LINE_BYTES)
  other,c,_=self.make();other.poll(log,None);c.now=-1
  with self.assertRaises(ValueError):other.poll(log,None)
  self.assertIsNotNone(other.error)
  for policy in ({'schema_version':1,'interval_seconds':0,'max_records':1},{'schema_version':1,'interval_seconds':True,'max_records':1},{'schema_version':1,'interval_seconds':10,'max_records':1025}):
   with self.assertRaises(ValueError):p.policy(policy)
 def test_observation_failure_propagates_and_does_not_block_cleanup_poll(self):
  class Fatal(BaseException):pass
  failure=Fatal('original diagnostic failure')
  class Sink:
   def write(self,text):raise failure
   def flush(self):raise AssertionError('not reached')
  report,c,_=self.make(Sink());log=SimpleNamespace(state={'started_pairs':1,'completed_pairs':0,'pending':{'ordinal':0}})
  with self.assertRaises(Fatal) as seen:report.poll(log,None)
  self.assertIs(seen.exception,failure);self.assertEqual(report.records,0);self.assertIsNone(report.last)
  report.poll(log,None);self.assertEqual(report.summary()['telemetry_error'],'Fatal');self.assertEqual(report.summary()['representation_credit'],0)
 def test_exact_inverses_and_only_existing_genuine_lease_hook(self):
  changes=json.loads((H/'SOURCE_DELTA01.json').read_bytes())
  for name,record in changes.items():
   body=(D/name).read_text();self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),record['after_sha256'])
   ast.parse(body)
   for edit in reversed(record['literal_edits']):self.assertEqual(body.count(edit['after']),1);body=body.replace(edit['after'],edit['before'])
   self.assertEqual(body,(H/'baseline'/name).read_text());self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),record['before_sha256'])
  source=(D/'compact_mcm.py').read_text();tree=ast.parse(source)
  locked=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
  lease=next(n for n in ast.walk(locked) if isinstance(n,ast.FunctionDef) and n.name=='lease')
  self.assertEqual(ast.unparse(lease.body[-1]),'if progress is not None:\n    progress.poll(log, stream)')
  self.assertIn('MCM producer start changed',ast.unparse(lease.body[-2]))
  caller=(D/'real_pilot_import_caller.py').read_text();self.assertIn("require(full, 'partial progress requires explicit schema2 plan')",caller)
  self.assertIn("if progress is not None:summary['partial_mcm_progress'] = progress.summary()",caller)

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 assert not {'numpy','torch','networkx','scipy'} & sys.modules.keys()
 (H/'CHECK01.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'Synthetic scalar metadata and exact source inverses; no genuine Authority, numeric arrays or empirical work.'},indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
