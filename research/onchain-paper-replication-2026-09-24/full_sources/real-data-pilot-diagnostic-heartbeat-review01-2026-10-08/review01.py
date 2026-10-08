import ast,hashlib,json,tempfile,types
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'real-data-pilot-diagnostic-heartbeat01-2026-10-08';checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
p=C/'real_pilot_partial_progress.py';s=p.read_text();ck('source_hash',hashlib.sha256(p.read_bytes()).hexdigest()=='1161ebde4d2ec281c29065fbd0c10bac39a9f0e2dbe3796d11acfb5b428c190a');ck('manifest_hash',hashlib.sha256((C/'MANIFEST.json').read_bytes()).hexdigest()=='39577047f0777ae2f52598fb60486d4b3bb86d6374421c83055092bfbcf1ad2f')
a=s.replace('\n        self._refresh_at=None;self._refresh_count=0','',1).replace('        try:\n            self._write();self._refresh_at=self.began','        try:self._write()',1).replace("now=_time(self.clock());elapsed=now-began;require(elapsed>=0,'diagnostic clock reversed')","elapsed=_time(self.clock())-began;require(elapsed>=0,'diagnostic clock reversed')",1).replace('\n        if self._refresh_count<480 and now-self._refresh_at>=60:\n            self._write()\n            self._refresh_at=now;self._refresh_count+=1','',1).replace(' Automatic refresh is sampled after timing callbacks, at most once per60seconds and480times; blocked calls have no guaranteed refresh.','',1)
ck('full_inverse',a==(C/'baseline_real_pilot_partial_progress.py').read_text());ck('baseline_pin',hashlib.sha256(a.encode()).hexdigest()=='488b713a6bee7aff1a44089ad61a25f582af357641020969a0914aabd42d4b33')
ns={};exec(compile(s,str(p),'exec'),ns);policy={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'}
with tempfile.TemporaryDirectory(dir=H) as tmp:
 now=[0.];d=ns['ScoringDiagnostic'](policy,Path(tmp),claim_sha256='a'*64,source='b'*64,clock=lambda:now[0]);real=d._write
 try:
  sentinel=object();now[0]=59.999;ck('return_unchanged',d.measure('event_publication',lambda:sentinel) is sentinel);ck('no_early_refresh',d._refresh_count==0)
  def outer():now[0]=60.;return d.measure('lease',lambda:sentinel)
  ck('nested_return',d.measure('event_publication',outer) is sentinel);ck('nested_single_refresh',d._refresh_count==1 and d.writes==2)
  d.measure('lease',lambda:None);ck('same_sample_no_refresh',d._refresh_count==1)
  now[0]=120.;before=(d._refresh_at,d._refresh_count,d.writes)
  def badwrite():raise OSError('synthetic write failure')
  d._write=badwrite
  try:d.measure('lease',lambda:None)
  except OSError:checks.append('write_failure_propagates')
  else:raise AssertionError('write swallowed')
  ck('failed_write_does_not_advance',before==(d._refresh_at,d._refresh_count,d.writes))
  original=ValueError('synthetic callback failure')
  def fail():raise original
  try:d.measure('lease',fail)
  except ValueError as got:ck('callback_primary_retained',got is original and 'synthetic write failure' in got.__notes__[0])
  else:raise AssertionError('callback swallowed')
  d._write=real;d.measure('lease',lambda:None);ck('retry_success_updates_after_write',d._refresh_at==120. and d._refresh_count==2)
  # Isolated metadata publication recorder exercises finite cap without480fsyncs.
  published=[];d._write=lambda:published.append(now[0])
  for i in range(3,483):now[0]=float(i*60);d.measure('lease',lambda:None)
  ck('exact480_automatic_cap',d._refresh_count==480 and len(published)==478)
  d._write=real;before=d.writes;d.begin('c'*64,types.SimpleNamespace(state={'completed_pairs':0}));ck('mandatory_begin_after_cap',d.writes==before+1)
  # Original mandatory stop path, no scalar numerical operation.
  d.completed=d.graph_completed=1023
  try:d.completed_pair(types.SimpleNamespace(state={'completed_pairs':1024,'pending':None}))
  except ns['PlannedScoringStop']:checks.append('original1024_stop')
  else:raise AssertionError('stop lost')
  ck('original_pair_counter',d.completed==1024 and d.graph_completed==1024 and d.stopped)
  # Backwards sample within a timing call still refuses before aggregate update.
  calls=d.timings['lease']['calls']
  def reverse():now[0]-=1
  try:d.measure('lease',reverse)
  except ValueError:checks.append('backward_elapsed_refuses')
  else:raise AssertionError('negative elapsed accepted')
  ck('negative_elapsed_no_counter',d.timings['lease']['calls']==calls)
  now[0]=1.2345678901234567e240
  for phase in ns['STARTUP_ONCE']:d.startup_enter(phase);d.startup_complete()
  for i in range(7):
   for phase in ns['STARTUP_GRAPHS']:d.startup_enter(phase,i);d.startup_complete()
  for item in d.startup:item.update(entered_seconds=1.2345678901234567e240,elapsed_seconds=1.2345678901234567e240)
  d.startup[-1].update(state='failed',failure_type='F'*64)
  for item in d.timings.values():item.update(seconds=1.2345678901234567e240,calls=2**63-1)
  d.writes=2**63-1;d.tail={'acknowledged_tail_cells':1024,'durable_tail_cells':1024,'completed_batch_cells':1024,'durability_poisoned':False};d._write();size=(d.directory/'progress.json').stat().st_size;ck('28phase_longfloat_size',size<=8192 and len(d.startup)==28)
 finally:d.close()
result={'decision':'accepted-source-only','candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(a.encode()).hexdigest(),'manifest_sha256':hashlib.sha256((C/'MANIFEST.json').read_bytes()).hexdigest(),'checks':checks,'stress_checkpoint_bytes':size,'reused_event_review':'855d52c5ee905b31c95cefe9440eaadcba189e789e8f1bc1faf7d205d30b349a','limitations':['Automatic refresh sampled after timing callback completion; blocking calls have no refresh guarantee. No runtime savings claim.','Uses existing monotonic clock contract; elapsed negative within a call refuses. This change does not add cross-call global clock monotonicity enforcement.','Counter/last sample advance only after successful _write. Existing phase timing aggregates advance before publication and failed publication does not roll those back.','Synthetic hashes/metadata only. No scientific imports, data, claim, Owner, process, Main/Git/live changes.','Finite480 automatic-write cap does not limit unchanged mandatory writes. Source acceptance is not fresh entry release.']}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'bytes':size,'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
