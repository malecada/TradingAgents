import copy,datetime,hashlib,json
from pathlib import Path
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
D=F/'real-data-pilot-retry21-registration01-2026-10-08'
N='eth-paper-real-data-end-to-end-resource-20261008-21'
OLD=F/'real-data-pilot-retry20-registration01-2026-10-08'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def save(p,v):
 b=(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as s:s.write(b)
assert not (D/'EXTENSION_PROPOSED92_01.json').exists()
assert not (R/'research_runs'/N).exists()
a=load(OLD/'CUMULATIVE_ALLOCATION_PROPOSED91_01.json')
e=load(OLD/'EXTENSION_PROPOSED91_01.json')
g=load(F/'real-data-pilot-final20-2026-10-08/gate03.json')
assert N not in g['experiments'] and a['closed_claims']==e['claims']
records={v['experiment']:v for v in e['claims']}
actual={};active=[]
for p in sorted((R/'research_runs').glob('*/claim.json')):
 c=load(p)
 if c.get('program_id')!='onchain-paper-replication-2026-09-24' or c['experiment']['family']!='paper':continue
 name=c['experiment_id'];assert p.parent.name==name
 ts=[s for s in ('complete','failed') if (p.parent/(s+'.json')).is_file()]
 if not ts:active.append(name);continue
 assert len(ts)==1
 t=p.parent/(ts[0]+'.json');v=load(t)
 record={'experiment':name,'claim_sha256':sha(p),'terminal_status':ts[0],'terminal_sha256':sha(t)}
 assert v['claim_sha256']==record['claim_sha256'] and v['experiment_id']==name and v['status']==ts[0]
 actual[name]=record
assert not active and len(actual)==43
assert all(actual[n]==v for n,v in records.items())
new=set(actual)-set(records)
assert new=={'eth-paper-real-data-end-to-end-resource-20261008-20'}
closed=e['claims']+[actual[next(iter(new))]]
assert sum(v['terminal_status']=='complete' for v in closed)==20
assert sum(v['terminal_status']=='failed' for v in closed)==23
consumed=e['base_family']['prior_attempts']+len(closed)
assert consumed==60
assert sum(a['unchanged_pending_allocation'].values())==28
assert len(a['preserved_reserved_preclaim_allowances'])==3

a.update(closed_claims=closed,consumed_before=consumed,identities=[N],proposed_cumulative_ceiling=92,prior_adopted_cumulative_ceiling=91,prior_reviewed_reserved_ceiling=91,new_fixed_allocation={'original_order_1024_pair_scoring_diagnostic_claims':1},equation='92 = 60 genuine permanently spent claims + 28 unchanged pending + 3 closed preclaim03/08/18 reserved allowances + 1 fresh fixed21 scoring diagnostic',question='What feature-generation throughput and phase costs does the faithful corrected production MCM path achieve over its first1024 completed pair-log comparisons?',qualification='A bounded diagnostic is an intermediate measurement toward the unchanged seven-full-graph MCM/GAT/attention-LSTM real-data pilot. Intentional stop after1024 completed pair-log comparisons permanently fails the diagnostic claim, leaving full MCM/neural update/checkpoint/financial fits unavailable. Published tail count may lag completed log count and must remain distinct. Original32 motifs/512spent samples/scientific matching/model/training and all original graph inputs remain unchanged. Explicit nondecreasing extraction/matching and persistence capacity selections plus measured-phase diagnostic source require exact independent source/entry acceptance before execution. Native6GiB maximum/5GiB high/2.5GiB startup=runtime reserve/zeroSwap/twoCPU/10GiB floor/8hours/native1GiB file cap retained. This proposal does not admit source/resources or prove whole capacity; no refund, category transfer, resampling, scope reduction or empirical completion claim.')
save(D/'CUMULATIVE_ALLOCATION_PROPOSED92_01.json',a)
e.update(claims=closed,consumed_before=consumed,cumulative_ceiling=92,initial_experiment=N,allocation=ref(D/'CUMULATIVE_ALLOCATION_PROPOSED92_01.json'),reason='One separately named finite original-order1024-comparison real-scoring diagnostic, following immutable failed20 and the resource-only owner policy adapter correction; original scientific method and diagnostic remain unchanged. Preserve60spent+28pending+3closedpreclaim reserves; no financial-fit credit/refund/transfer/cap ladder. Full end-to-end goal remains unchanged.')
save(D/'EXTENSION_PROPOSED92_01.json',e)
save(D/'ACTUAL_ACCOUNTING_SNAPSHOT01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'previous_allocation':ref(OLD/'CUMULATIVE_ALLOCATION_PROPOSED91_01.json'),'previous_extension':ref(OLD/'EXTENSION_PROPOSED91_01.json'),'actual_local_claims':43,'actual_local_complete':20,'actual_local_failed':23,'historical_prior':17,'consumed_before':60,'active_claims':active,'appended':list(new),'prior_records_preserved':42,'claim_snapshot':closed,'identity':N,'proposed_ceiling':92,'proposal':ref(D/'EXTENSION_PROPOSED92_01.json'),'qualification':'Read-only genuine closed-claim body scan plus prospective metadata. No new claim, allowance adoption, native attempt, source release or numerical import.'})
print(json.dumps({'status':'PROPOSED_NOT_REVIEWED_NOT_ADOPTED','identity':N,'extension':ref(D/'EXTENSION_PROPOSED92_01.json'),'actual_closed':43,'consumed':59,'ceiling':92}))
