from pathlib import Path
import copy,hashlib,importlib.util,json,stat
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;D=F/'real-data-pilot-sixth-graph01-2026-10-06';A=F/'real-data-pilot-june6-concrete-entry-preparation02-2026-10-06';NAME='eth-paper-real-pilot-graph-20220606-20261005-01';CONT='eth-paper-real-pilot-may30-ledger-continuation-20261006-01';evidence={}
def raw(p):
    s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def bound(ref):
    b=raw(R/ref['path']);assert hashlib.sha256(b).hexdigest()==ref['sha256'];return json.loads(b)
g=read(D/'gate01.json');assert evidence[str((D/'gate01.json').relative_to(R))]=='d5298108afe1ba384ef75d9607bb5be3b3fafb8ba8ab098dcff3ddb5f5e67f78'
assert set(g['experiments'])=={NAME};e=g['experiments'][NAME]
prior=read(F/'real-data-pilot-may30-ledger-continuation01-2026-10-06/gate01.json');pe=prior['experiments'][CONT]
assert {k:v for k,v in g.items() if k!='experiments'}=={k:v for k,v in prior.items() if k!='experiments'}
source_review=read(F/'real-data-pilot-june6-concrete-entry-source-review01-2026-10-06/SOURCE_REVIEW01.json');assert source_review['decision']=='accepted-source-only'
for n in ('prepare01.py','boundary01.py','preflight01.py','launch01.py','CHARTER01.md'):assert raw(D/n)==raw(A/n)
assert len(e['source_files'])==192 and len(pe['source_files'])==187
expected=dict(pe['source_files'])
for n in ('prepare01.py','boundary01.py','preflight01.py','launch01.py','CHARTER01.md'):expected[str((D/n).relative_to(R))]=evidence[str((D/n).relative_to(R))]
assert e['source_files']==expected
for path,sha in e['source_files'].items():assert hashlib.sha256(raw(R/path)).hexdigest()==sha
required={str(p.relative_to(R)) for folder in (R/'tradingagents/research/onchain_replication',R/'tradingagents/research') for p in folder.glob('*.py')}|{'tradingagents/__init__.py'}
assert required<=set(e['source_files'])
assert e['runtime_hashes']==pe['runtime_hashes'] and len(e['runtime_hashes'])==7
for path,sha in e['runtime_hashes'].items():assert hashlib.sha256(raw(R/'tradingagents/research'/path)).hexdigest()==sha
inputs={k:bound(v) for k,v in e['inputs'].items()};assert len(inputs)==17
rawdraft=read(F/'real-data-pilot-sixth-graph-input-preparation01-2026-10-06/draft01/JUNE6_DRAFT01.json')
assert len(rawdraft['raw_input_refs'])==11
for key,ref in rawdraft['raw_input_refs'].items():assert e['inputs'][key]==ref
assert e['cells']==rawdraft['cells']==['source-000000','graph-2022-06-06'] and e['windows']==rawdraft['windows'] and e['outputs']==rawdraft['outputs'] and e['parent'] is None
assert e['cumulative_budget_extension']==pe['cumulative_budget_extension']
# Apart from exact selected date/inputs/source/charter/extension, original job science and experiment fields remain.
old=read(F/'real-data-pilot-fifth-graph01-2026-10-06/gate01.json');oe=next(iter(old['experiments'].values()))
for k in ('family','reuse','selection','stage'):assert e[k]==oe[k]
job=inputs['execution_job'];assert job==read(F/'real-data-pilot-fifth-graph01-2026-10-06/execution-job01.json')
a=copy.deepcopy(job);b=copy.deepcopy(rawdraft['execution_job_exact_May16']);a['resources'].pop('storage_budget');b['resources'].pop('storage_budget');assert a==b
assert job['kind']=='graphs' and job['resources']['memory_high_bytes']==5368709120 and job['resources']['memory_max_bytes']==5905580032 and job['resources']['wall_seconds']==28800 and job['resources']['start_reserve_bytes']==9126805504
assert job['resources']['disk_floor_bytes']==10737418240 and job['resources']['reserve_bytes']==3221225472
extent=inputs['raw_extent'];assert extent['days']==7 and extent['segments']==223 and extent['declared_rows']==7293215
count=0
for day in extent['daily_members']:
    assert hashlib.sha256(raw(R/day['mapping_path'])).hexdigest()==day['mapping_sha256']
    for s in day['segments']:
        p=Path(s['path']);t=p.lstat();assert not p.is_symlink() and stat.S_ISREG(t.st_mode)
        assert (t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)==tuple(s[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns'));count+=1
assert count==223
boundary=inputs['continuation_boundary'];draft=read(A/'BOUNDARY_CURRENT_TERMINAL_DRAFT01.json')
for k,v in draft['dependencies'].items():
    if v is not None:assert boundary['dependencies'][k]==v
for k in ('continuation_outcome_review','continuation_recovery_review','post_continuation_accounting'):assert draft['dependencies'][k] is None and type(boundary['dependencies'][k]) is dict;bound(boundary['dependencies'][k])
sp=importlib.util.spec_from_file_location('bound_boundary',D/'boundary01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
actual=m.check(boundary);scopes=m.storage_scopes(inputs['storage_projection']);policy=inputs['storage_policy'];prep=read(D/'ROOT_PREPARATION01.json')
assert policy['preceding_continuation_boundary']==prep['predecessor']==actual
assert policy['scope_reservations']==prep['scope_reservations']==scopes
assert scopes['physical_root_growth_bytes']==policy['growth_estimate_bytes']==7155620336 and scopes['physical_startup_free_bytes']==policy['startup_free_requirement_bytes']==17893038576 and scopes['named_sources_growth_bytes']==6744020747
limits=job['resources']['storage_budget']['limits'];baseline=policy['baseline'];assert policy['storage_budget']==job['resources']['storage_budget']
assert baseline['allocated_bytes']+6744020747<=limits['max_allocated_bytes'] and baseline['logical_file_bytes']+6744020747<=limits['max_logical_bytes']
assert policy['free_disk_observed_bytes']>=policy['startup_free_requirement_bytes']
for p in (R/'research_runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,D/'launch-attempt01.json',D/'outer-exit01.json'):assert not p.exists() and not p.is_symlink()
result={'decision':'pass','identity':NAME,'source_pins':192,'runtime_pins':7,'compact_inputs':17,'raw_input_refs':11,'raw_extents_stat_only':223,'days':7,'declared_rows':7293215,'native_job_unchanged':True,'old_failure_retained':True,'original_allowance_retained':True,'effective_budget':72,'scope':scopes,'prepared_baseline':baseline,'fresh_capacity_claim':False,'genuine_admission_or_preflight_executed':False,'payload_reads':0,'evidence':evidence}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','prepared_baseline','scope')}))
