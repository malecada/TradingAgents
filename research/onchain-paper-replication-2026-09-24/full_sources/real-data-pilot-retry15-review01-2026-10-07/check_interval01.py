"""Independent synthetic timing tests against actual candidate Interval."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry15-review01-2026-10-07';C=F/'real-data-pilot-archive-idle-fix01-2026-10-07/candidate/archive_control_history.py';O=R/'tradingagents/research/onchain_replication/archive_control_history.py'
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=load(O,'review_old');new=load(C,'review_candidate')
p={'schema_version':1,'format':new.FORMAT,'assumption':new.ASSUMPTION,'success_control_bytes':512,'success_diagnostic_bytes':512,'shard_bytes':4096,'full_interval_ms':10000,'max_stale_ms':60000,'max_callbacks_between_full':100}
results=[]
def scenario(name,module,idle,duration,force,expect,mutate=None):
 t=[0.0];called=[];clock=lambda:t[0];i=module.Interval(p,clock);i.check(lambda:called.append('initial'),force=True);last=i.last;t[0]=idle
 if mutate:mutate(i)
 def audit():called.append('new');t[0]+=duration
 try:i.check(audit,force=force)
 except ValueError as e:
  assert expect in str(e),(name,str(e));assert i.failed and i.last==last
  try:i.check(audit,force=True)
  except ValueError as later:assert str(later)=='history audit poisoned'
  else:raise AssertionError('failure revived')
  result=str(e)
 else:assert expect=='pass' and i.last==idle+duration and not i.failed;result='passed'
 results.append({'case':name,'result':result,'audit_called':'new' in called,'old_last':last,'final_last':i.last})
scenario('old forced idle refuses before audit',old,300,1,True,'history audit stale')
scenario('new forced idle completes full audit',new,300,1,True,'pass')
scenario('new sampled idle still refuses before audit',new,300,1,False,'history audit stale')
scenario('new forced exact60 duration refuses',new,300,60,True,'expired during check')
scenario('new forced just below60 completes',new,300,59.999,True,'pass')
scenario('sampled due audit includes previous age',new,30,31,False,'expired during check')
scenario('forced due audit uses current audit duration',new,30,31,True,'pass')
scenario('backward entry refuses before audit',new,-1,0,True,'clock moved backward')
scenario('backward audit completion refuses',new,300,-1,True,'clock moved backward')
scenario('policy mutation refuses before audit',new,300,0,True,'policy/clock replaced',lambda i:i.p.update(max_stale_ms=60001))
scenario('clock replacement refuses before audit',new,300,0,True,'policy/clock replaced',lambda i:setattr(i,'clock',lambda:300))
assert not results[0]['audit_called'] and not results[2]['audit_called']
t=[0.];i=new.Interval(p,lambda:t[0]);i.check(lambda:None,force=True);t[0]=300
try:i.check(lambda:(_ for _ in ()).throw(ValueError('independent corrupt history')),force=True)
except ValueError as e:assert str(e)=='independent corrupt history' and i.failed and i.last==0
else:raise AssertionError('corruption ignored')
results.append({'case':'failed full audit cannot renew','result':'corruption raised, last unchanged, poisoned'})
out={'schema_version':1,'decision':'passed','candidate':ref(C),'original':ref(O),'policy':p,'cases':results,'scope':'Synthetic Interval timing and callback rejection only; no real clock latency, archive writer, network, scientific arrays or run authority.'};q=H/'INTERVAL_CHECK01.json';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(ref(q)))
