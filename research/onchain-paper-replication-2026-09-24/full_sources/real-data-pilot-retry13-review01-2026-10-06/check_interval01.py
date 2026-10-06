import hashlib,importlib.util,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry13-review01-2026-10-06';src=R/'tradingagents/research/onchain_replication/imported_authority_interval.py';spec=importlib.util.spec_from_file_location('review_interval_stdlib',src);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
g=json.loads((F/'real-data-pilot-final12-2026-10-06/gate01.json').read_text());ref=next(iter(g['experiments'].values()))['inputs']['imported_authority_lease'];old=json.loads((R/ref['path']).read_text());new=dict(old,max_stale_ms=60000);rows=[]
for limit,elapsed,fatal in [(30000,30.05162506600027,False),(60000,30.05162506600027,False),(60000,60.,False),(60000,60.001,False),(60000,0.,True)]:
 t=[0.];s=m.Interval(dict(old,max_stale_ms=limit),clock=lambda:t[0]);callbacks=[]
 def full():
  callbacks.append('full');t[0]=elapsed
  if fatal:raise RuntimeError('independent-sentinel')
 def finger():callbacks.append('finger')
 def live():callbacks.append('live')
 error=None
 try:s.validate(full,finger,live,boundary=True)
 except Exception as e:error=(type(e).__name__,str(e))
 expected_error=fatal or elapsed*1000>limit
 assert (error is not None)==expected_error and s.closed==expected_error and s.full==(None if expected_error else elapsed)
 if fatal:assert error==('RuntimeError','independent-sentinel')
 if expected_error:
  try:s.validate(lambda:None,lambda:None,lambda:None)
  except ValueError as e:assert str(e)=='import lease: poisoned/closed interval'
  else:raise AssertionError('poison lost')
 rows.append({'max_stale_ms':limit,'synthetic_callback_seconds':elapsed,'fatal':fatal,'callbacks':callbacks,'closed':s.closed,'full_timestamp':s.full,'error':error})
assert m.policy(new)==new
out={'schema_version':1,'status':'PASS','interval_source':{'path':str(src.relative_to(R)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()},'original_policy':ref,'selected_policy':new,'rows':rows,'qualification':'Real unchanged stdlib Interval class, explicit synthetic clock/callbacks only. No actual authority or measured full60s callback; replayed total12 interval age as one synthetic callback does not decompose or reconstruct actual12 trace. All ordinary callback/final freshness and poisoned-refusal checks remain.'};p=H/'INTERVAL_CHECK01.json';p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
