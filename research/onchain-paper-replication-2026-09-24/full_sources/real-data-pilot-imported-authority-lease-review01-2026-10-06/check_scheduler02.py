from pathlib import Path
import importlib.util,json,hashlib
D=Path(__file__).resolve().parent
P=D.parent/'real-data-pilot-imported-authority-lease01-2026-10-06/candidate/tradingagents/research/onchain_replication/imported_authority_interval.py'
spec=importlib.util.spec_from_file_location('interval_witness',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p={'schema_version':1,'kind':m.KIND,'live_interval_ms':10,'fingerprint_interval_ms':20,'full_interval_ms':100,'max_stale_ms':500,'max_calls_between_full':1000,'assumption':m.ASSUMPTION}
now=[10.];v=m.Interval(p,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None)
previous=v.full;now[0]=10.11
v.validate(lambda:now.__setitem__(0,10.55),lambda:None,lambda:None)
assert not v.closed and (now[0]-previous)*1000>p['max_stale_ms']
first={'previous_full':previous,'new_full':v.full,'elapsed_from_old_full_ms':(now[0]-previous)*1000,'accepted':True}
now=[10.];v=m.Interval(p,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None)
now[0]=10.11;live=[]
v.validate(lambda:now.__setitem__(0,10.115),lambda:None,lambda:live.append(now[0]))
assert live==[10.11] and v.live==10.115
record={'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'full_crosses_old_stale_then_refreshes':first,'live_timestamp_moved_without_live_check':{'actual_live_check':live[0],'recorded_live':v.live},'scope':'pure scheduler synthetic callbacks only; no genuine authority/numerical imports'}
(D/'CHECK_SCHEDULER02.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps(record))
