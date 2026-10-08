"""Tiny stdlib fake-clock diagnostic fixtures; no scientific/authority imports."""
import importlib.util,sys,tempfile,unittest,json
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('heartbeat_candidate',HERE/'real_pilot_partial_progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
POLICY={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'}
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=HERE);self.now=0.
  self.d=m.ScoringDiagnostic(POLICY,Path(self.temp.name),claim_sha256='a'*64,source='b'*64,clock=lambda:self.now)
 def tearDown(self):self.d.close();self.temp.cleanup()
 def test_threshold_return_same_clock(self):
  original=self.d.writes;value=object()
  for now in (0.,59.999):self.now=now;self.assertIs(self.d.measure('lease',lambda:value),value)
  self.assertEqual(self.d.writes,original)
  self.now=60.;self.d.measure('lease',lambda:value);self.assertEqual(self.d.writes,original+1)
  self.d.measure('lease',lambda:value);self.assertEqual(self.d.writes,original+1)
  self.assertEqual(self.d._refresh_at,60.);self.assertEqual(self.d._refresh_count,1)
 def test_pair_checkpoints_stop_unchanged(self):
  log=SimpleNamespace(state={'completed_pairs':0,'pending':None});self.d.begin('c'*64,log);writes=self.d.writes
  for i in range(1,1025):
   log.state['completed_pairs']=i
   if i==1024:
    with self.assertRaises(m.PlannedScoringStop):self.d.completed_pair(log)
   else:self.d.completed_pair(log)
  self.assertEqual(self.d.writes,writes+16);self.assertEqual(self.d.completed,1024);self.assertTrue(self.d.stopped)
 def test_callback_exception_primary_even_write_fails(self):
  original=ValueError('callback failed');self.now=60.
  def callback():raise original
  def failed_write():raise OSError('publication failed')
  self.d._write=failed_write
  with self.assertRaises(ValueError) as ctx:self.d.measure('lease',callback)
  self.assertIs(ctx.exception,original);self.assertIn('publication failed',original.__notes__[0])
  self.assertEqual((self.d._refresh_at,self.d._refresh_count),(0.,0))
 def test_failed_write_does_not_advance(self):
  real=self.d._write;writes=self.d.writes;self.now=60.
  def failed_write():raise OSError('publication failed')
  self.d._write=failed_write
  with self.assertRaises(OSError):self.d.measure('lease',lambda:3)
  self.assertEqual((self.d._refresh_at,self.d._refresh_count,self.d.writes),(0.,0,writes))
  self.d._write=real;self.d.measure('lease',lambda:3)
  self.assertEqual((self.d._refresh_at,self.d._refresh_count,self.d.writes),(60.,1,writes+1))
 def test_nested_timers_only_one_refresh_and_bounded_count(self):
  def outer():
   self.now=60.;return self.d.measure('retention_live',lambda:7)
  before=self.d.writes;self.assertEqual(self.d.measure('lease',outer),7)
  self.assertEqual(self.d.writes,before+1)
  self.d._refresh_count=480;self.now=28860.;self.d.measure('lease',lambda:None)
  self.assertEqual(self.d.writes,before+1)
  # Mandatory publication remains enabled after automatic allowance.
  self.d.begin('d'*64,SimpleNamespace(state={'completed_pairs':0}));self.assertEqual(self.d.writes,before+2)
 def test_full_startup_roster_cap(self):
  for phase in m.STARTUP_ONCE:
   self.d.startup_enter(phase);self.now+=1.2345678901234567e240;self.d.startup_complete()
  for phase in m.STARTUP_GRAPHS:
   for i in range(7):
    self.d.startup_enter(phase,i);self.now+=1.2345678901234567e240
    if phase=='production' and i==6:self.d.startup_failed(type('F'*64,(Exception,),{})())
    else:self.d.startup_complete()
  self.d.graph='c'*64;self.d.matching_began=0.;self.d.completed=self.d.graph_completed=1024
  self.d.tail={'acknowledged_tail_cells':1024,'durable_tail_cells':1024,'completed_batch_cells':1024,'durability_poisoned':False}
  for item in self.d.timings.values():item.update(seconds=1.2345678901234567e240,calls=2**63-1)
  self.d._write();raw=(Path(self.temp.name)/'scoring-diagnostic/progress.json').read_bytes();self.assertLessEqual(len(raw),8192);print('FULL_CAP_BYTES',len(raw))
 def test_full_literal_inverse(self):
  s=(HERE/'real_pilot_partial_progress.py').read_text()
  s=s.replace('\n        self._refresh_at=None;self._refresh_count=0','',1).replace('        try:\n            self._write();self._refresh_at=self.began','        try:self._write()',1)
  s=s.replace("now=_time(self.clock());elapsed=now-began;require(elapsed>=0,'diagnostic clock reversed')","elapsed=_time(self.clock())-began;require(elapsed>=0,'diagnostic clock reversed')",1)
  s=s.replace('\n        if self._refresh_count<480 and now-self._refresh_at>=60:\n            self._write()\n            self._refresh_at=now;self._refresh_count+=1','',1)
  s=s.replace(' Automatic refresh is sampled after timing callbacks, at most once per60seconds and480times; blocked calls have no guaranteed refresh.','',1)
  self.assertEqual(s,(HERE/'baseline_real_pilot_partial_progress.py').read_text())
  self.assertFalse({'numpy','torch'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
