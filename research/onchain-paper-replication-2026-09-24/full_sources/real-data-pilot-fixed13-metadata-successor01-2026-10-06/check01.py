"""Actual Interval with finite synthetic clock; no claim/arrays/numerical imports."""
from pathlib import Path
import json,re,types,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
interval=ROOT/'tradingagents/research/onchain_replication/imported_authority_interval.py';m=types.ModuleType('fixture_interval');exec(compile(interval.read_bytes(),str(interval),'exec'),vars(m))
old=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/imported_authority_lease.json';new=HERE/'candidate/imported_authority_lease.json';before=json.loads(old.read_text());after=json.loads(new.read_text());assert after==before|{'max_stale_ms':60000}
log=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261006-12/guard/child.log';raw=log.read_text();match=re.search(r'full_callback_seconds=([0-9.]+); pre_callback_age_seconds=([0-9.]+); total_age_seconds=([0-9.]+)',raw);assert match;duration,age,total=map(float,match.groups());assert abs(age+duration-total)<1e-9

def run(p,age,duration):
    clock=[0.];calls=[]
    scheduler=m.Interval(p,clock=lambda:clock[0]);scheduler.validate(lambda:None,lambda:None,lambda:None,boundary=True);clock[0]=age
    def full():calls.append('full');clock[0]+=duration
    try:scheduler.validate(full,lambda:calls.append('finger'),lambda:calls.append('live'),boundary=True);status='pass';reason=None
    except ValueError as error:status='refuse';reason=str(error)
    return {'status':status,'closed':scheduler.closed,'reason':reason,'full_timestamp':scheduler.full,'end_clock':clock[0],'calls':calls}
rows=[]
a=run(before,age,duration);b=run(after,age,duration);assert a['status']=='refuse' and a['closed'] and b['status']=='pass' and not b['closed'];rows.append({'case':'actual12 aggregated age/callback supplied to synthetic clock','original30':a,'authorized60':b})
a=run(after,55.,6.);assert a['status']=='refuse' and a['closed'] and a['full_timestamp']==0.;rows.append({'case':'61second aggregate refuses and poisons without refresh','result':a})
a=run(after,61.,0.);assert a['status']=='refuse' and a['closed'] and not a['calls'];rows.append({'case':'already stale61second entry refuses before callbacks','result':a})
for key,value in [('full_interval_ms',60000),('fingerprint_interval_ms',99),('live_interval_ms',10001),('max_stale_ms',0)]:
    bad=after|{key:value}
    try:m.policy(bad)
    except ValueError:rows.append({'case':'original ordered positive policy check','field':key,'value':value,'status':'refuse'})
    else:raise AssertionError('invalid ordered policy accepted')
assert new.read_text().replace('"max_stale_ms": 60000','"max_stale_ms": 30000')==old.read_text()
result={'status':'PASS','checks':rows,'policy_literal_inverse_exact':True,'interval_source_sha256':hashlib.sha256(interval.read_bytes()).hexdigest(),'actual12_log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'actual12_aggregate_seconds':{'prior_age':age,'full_callback':duration,'total':total},'qualification':'Actual recorded aggregate durations drive fake clock in unchanged real Interval code. No replay, scientific authority, empirical capacity or next-run success claim. Only max_stale_ms is explicitly changed; live/fingerprint/full intervals, callcount and all other policies retain original values.'}
(HERE/'CHECK_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':len(rows),'actual12_total_seconds':total}))
