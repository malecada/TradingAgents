from pathlib import Path
import json,hashlib,ast,importlib.util,sys,copy
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';T=F/'real-data-pilot-may30-ledger-continuation01-2026-10-06';I=F/'real-data-pilot-may30-ledger-live-integration01-2026-10-06';O=Path(__file__).resolve().parent;NAME='eth-paper-real-pilot-may30-ledger-continuation-20261006-01';E={}
def read(p,pin=None):
 assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if pin:assert h==pin,(str(p),h,pin)
 E[str(p.relative_to(R))]=h;return b
def obj(p,pin=None):return json.loads(read(p,pin))
def bound(ref):return read(R/ref['path'],ref['sha256'])
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
g=obj(T/'gate01.json','f9e203de0fe362c1b6c07e147fe5ea3b709fe976f444aa0b18a7e6b50ca4775c');b=obj(T/'BINDINGS01.json','f5147e56113dc508d8691512a5725e97ade11d67a5387183ff01ae2b5d269a31');cl=obj(I/'SOURCE_RUNTIME_CLOSURE03.json');j=obj(T/'execution-job01.json');s=obj(T/'STORAGE_POLICY01.json')
assert cl['source_pins']==len(b['source_files'])==187 and cl['runtime_pins_verified']==len(b['runtime_hashes'])==7 and cl['bindings']['sha256']==E[str((T/'BINDINGS01.json').relative_to(R))]
assert read(I/'CONTINUATION_BINDINGS03.json')==read(T/'BINDINGS01.json')
assert set(g['experiments'])=={NAME};e=g['experiments'][NAME]
assert e['parent'] is None and e['cells']==['graph-2022-05-30'] and e['family']=='paper' and e['reuse']=='exploratory'
assert e['source_files']==b['source_files'] and e['runtime_hashes']==b['runtime_hashes'] and e['charter']==b['charter']
for p,h in b['source_files'].items():read(R/p,h)
for n,h in b['runtime_hashes'].items():read(R/'tradingagents/research'/n,h)
required={str(p.relative_to(R)) for d in [R/'tradingagents/research/onchain_replication',R/'tradingagents/research'] for p in d.glob('*.py')}|{'tradingagents/__init__.py'}
assert required<=set(b['source_files'])
for r in e['inputs'].values():assert r['dataset']=='eth';bound(r)
for k in ['charter','plan','recovery','storage_policy','environment','extension','extension_review','relocation_receipt','relocation_review']:bound(b[k])
assert s==json.loads(bound(b['storage_policy']))
base=obj(F/'real-data-pilot-fifth-graph01-2026-10-06/gate01.json');basejob=obj(F/'real-data-pilot-fifth-graph01-2026-10-06/execution-job01.json','f4602068cbe1aae6d6553212b06e8313ae03302cd18752060a65a41ecaf2cbb2')
assert {k:v for k,v in g.items() if k!='experiments'}=={k:v for k,v in base.items() if k!='experiments'}
oldres=copy.deepcopy(basejob['resources']);oldres['disk_paths']=[str(R),'/home/malecada/Data'];assert j['resources']==oldres
assert j['kind']=='graphs' and j['payload']=={'plan_input':'continuation_plan'}
assert oldres['memory_high_bytes']==5*1024**3 and oldres['memory_max_bytes']==int(5.5*1024**3) and oldres['reserve_bytes']==3*1024**3 and oldres['start_reserve_bytes']==int(8.5*1024**3) and oldres['wall_seconds']==28800 and oldres['disk_floor_bytes']==10*1024**3
assert s['baseline']==json.loads(bound(s['baseline_evidence'])) and s['growth_estimate_bytes']==sum(s[k] for k in ['output_bytes','sqlite_scratch_bytes','control_and_overhead_bytes'])==5403824128 and s['startup_free_requirement_bytes']==10*1024**3+s['growth_estimate_bytes']
for k,obs in [('max_logical_bytes','logical_file_bytes'),('max_allocated_bytes','allocated_bytes')]:assert s['baseline'][obs]+s['growth_estimate_bytes']<=oldres['storage_budget']['limits'][k]
from tradingagents.research.onchain_replication.environment import inventory
assert inventory(R)==json.loads(bound(b['environment']))
# Only genuine metadata APIs, never admission/check/start/producer.
sp=importlib.util.spec_from_file_location('exact_continuation_prepare',T/'prepare01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
p,policy,control=m.validate_binding(b);assert policy==s and p==json.loads(bound(b['plan']))
assert control.FIXED.items()<=e['inputs'].items()
for role,key in [('continuation_plan','plan'),(p['recovery_review_input'],'recovery'),('storage_policy','storage_policy'),(p['relocation_receipt_input'],'relocation_receipt'),(p['relocation_review_input'],'relocation_review')]:assert {k:e['inputs'][role][k] for k in ['path','sha256']}==b[key]
assert e['inputs']['continuation_entry_bindings']['sha256']==E[str((T/'BINDINGS01.json').relative_to(R))] and e['inputs']['execution_job']['sha256']==E[str((T/'execution-job01.json').relative_to(R))]
ext=json.loads(bound(b['extension']));allocation=json.loads(bound(ext['allocation']));review=json.loads(bound(b['extension_review']));assert ext['base_family']==g['families']['paper'] and ext['consumed_before']==41 and allocation['identities']==[NAME] and allocation['refunds']==allocation['category_transfers']==0
relevant=[]
for cp in (R/'research_runs').glob('*/claim.json'):
 c=json.loads(cp.read_bytes())
 if c.get('program_id')==g['program_id'] and c.get('experiment',{}).get('family')=='paper':relevant.append(c)
from tradingagents.research.budget_extensions import effective_budget
assert len(relevant)==24 and effective_budget(R,g['program_id'],NAME,e,g['families']['paper'],relevant,bound)==72
assert sum(c.get('effective_attempt_budget',51)==72 for c in relevant)==0
assert any(c['experiment_id']==p['predecessor'] for c in relevant)
for q in [R/'research_runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,T/'launch-attempt01.json',T/'outer-exit01.json']:assert not q.exists() and not q.is_symlink()
# Existing immutable source reviews are source-only ancestry, not substitute grants.
for q in [F/'real-data-pilot-may30-ledger-relocation-review01-2026-10-06/cross-volume-source01/REVIEW01.json',F/'real-data-pilot-may30-ledger-relocation-review01-2026-10-06/relocation-final-outcome01/RELOCATION_REVIEW01.json',I/'INTEGRATION_CROSS_VOLUME02.json',I/'CROSS_VOLUME_SOURCE_HANDOFF01.json']:obj(q)
launch=read(T/'launch01.py').decode();assert "subprocess.call(_command(args,'launch'),cwd=ROOT)" in launch and 'code=None' in launch
assert not any(n in sys.modules for n in ['numpy','torch','sqlite3'])
check={'decision':'pass','source_pins':187,'runtime_pins':7,'compact_input_pins':len(e['inputs']),'required_source_closure_members':len(required),'effective_budget_if_genuine_admission_passes':72,'existing_claims':24,'prior_attempts':17,'spent_before':41,'highest_already_adopted':max(c.get('effective_attempt_budget',51) for c in relevant),'new_claim_created':False,'original_failed_preserved':True,'parent':None,'cells':e['cells'],'growth_estimate_bytes':5403824128,'actual_preflight_or_admission_executed':False,'payload_SQL_reads':0,'scientific_imports':False}
put('CHECK01.json',check);E[str((O/'CHECK01.json').relative_to(R))]=hashlib.sha256((O/'CHECK01.json').read_bytes()).hexdigest()
put('RELEASE_REVIEW01.json',{'decision':'accepted','identity':NAME,'gate_sha256':E[str((T/'gate01.json').relative_to(R))],'scope':'Exact current source/registration/entry release only for one fresh graph-only retained-ledger continuation. Root must commit exact evidence/release and pass genuine preflight/native admission immediately before one use. No rerun or original failed-claim replacement.','evidence':E,'accounting':{'spent_before':41,'highest_adopted_before':71,'prospective_effective_budget':72,'unchanged_unused':30,'fresh_continuation_slots':1},'qualifications':['Actual native RAM/process/storage eligibility remains mandatory at preflight.','Storage growth is a finite reservation estimate, not capacity proof or hard filesystem quota.','Data bytes/ancestry inherit genuine copy/recovery/retirement; no reviewer payload or SQL access.','Guarded worker must rehash retained ledger and perform registered SQL consistency and scientific checks.','No MCM, model update, fit, source reingestion, partial-array reuse or paper-credit inference.']})
print(json.dumps(check));print(hashlib.sha256((O/'RELEASE_REVIEW01.json').read_bytes()).hexdigest())
