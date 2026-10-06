from pathlib import Path
import ast,copy,datetime,hashlib,importlib.metadata,json,os,platform,shutil,stat,subprocess,sys
from types import SimpleNamespace
D=Path(__file__).resolve().parent;F=D.parent.parent;M=F.parents[2];B=F.parent;C=F/'real-data-pilot-fifth-graph01-2026-10-06';OLD=F/'real-data-pilot-fourth-graph01-2026-10-06';PKG=M/'tradingagents/research/onchain_replication';NAME='eth-paper-real-pilot-graph-20220530-20261005-01';evidence={}
def raw(p):
 p=Path(p);s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();assert all(getattr(p.lstat(),k)==getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'));evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
def h(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
gate=read(C/'gate01.json');assert h(C/'gate01.json')=='b0c58b8a610a102ec11d943c9c869ef9162da5a80edac3c8edda3c57135195c3';e=gate['experiments'][NAME];oldgate=read(OLD/'gate01.json');old=next(iter(oldgate['experiments'].values()))
assert set(gate['experiments'])=={NAME} and e['parent'] is None
assert {k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in oldgate.items() if k!='experiments'}
changed={k for k in old if old[k]!=e[k]};assert changed=={'cells','charter','inputs','question','source_files','windows'}
assert e['cells']==['source-000000','graph-2022-05-30'] and e['windows']==[{'availability':'existing','dataset':'eth','start':'2022-05-30T00:00:00Z','end':'2022-06-06T00:00:00Z'}]
for rel,sha in e['source_files'].items():assert h(M/rel)==sha
assert len(e['source_files'])==178 and len(e['inputs'])==32
for ref in e['inputs'].values():assert h(M/ref['path'])==ref['sha256']
required={'tradingagents/research/onchain_replication/'+p.name for p in PKG.glob('*.py')}|{'tradingagents/research/'+p.name for p in PKG.parent.glob('*.py')}|{'tradingagents/__init__.py'}
assert required<=set(e['source_files'])
oldcore={p:v for p,v in old['source_files'].items() if not p.startswith(str(OLD.relative_to(M))+'/')};newcore={p:v for p,v in e['source_files'].items() if not p.startswith(str(C.relative_to(M))+'/')};assert oldcore==newcore
assert h(C/'preflight01.py').startswith('749879')
assert raw(C/'launch01.py')==raw(OLD/'launch01.py')
oldpf=raw(OLD/'preflight01.py');newpf=raw(C/'preflight01.py');restored=newpf.decode()
pf_edits=[('fourth real-data pilot graph','fifth real-data pilot graph'),('20220523','20220530'),('COMPLETE May16','COMPLETE May23'),('real-pilot-third-graph','real-pilot-fourth-graph'),('20220516','20220523'),('3310923776','3218829312'),('6621847552','6437658624'),('third-ledger','fourth-ledger')]
for before,after in reversed(pf_edits):restored=restored.replace(after,before)
assert restored.encode()==oldpf
inv=read(C/'PREPARATION_INVERSE01.json');prepared=raw(C/'prepare01.py').decode();assert h(C/'prepare01.py')==inv['after_sha256']
for change in reversed(inv['changes']):prepared=prepared.replace(change['after'],change['before'])
assert prepared.encode()==raw(OLD/'prepare01.py') and h(OLD/'prepare01.py')==inv['before_sha256']
job=read(C/'execution-job01.json');oldjob=read(OLD/'execution-job01.json');x=copy.deepcopy(job);x['resources']['storage_budget']=oldjob['resources']['storage_budget'];assert x==oldjob
# Execute only exact pure schema/resource functions; no admission or claim.
funcs=[n for n in ast.parse(raw(PKG/'job.py')).body if isinstance(n,ast.FunctionDef) and n.name in ('job_schema','resource_policy')]
g={'Path':Path,'resources':SimpleNamespace(GIB=1024**3),'__package__':'tradingagents.research.onchain_replication'};exec(compile(ast.Module(body=funcs,type_ignores=[]),'actual-job-metadata-functions','exec'),g);g['job_schema'](job);g['resource_policy'](job['resources'],M)
# Actual preceding-storage source function, with bounded metadata hashing.
f=next(n for n in ast.parse(newpf).body if isinstance(n,ast.FunctionDef) and n.name=='preceding_storage');g={'ROOT':M,'Path':Path,'json':json,'file_hash':h};exec(compile(ast.Module(body=[f],type_ignores=[]),'actual-preceding-storage','exec'),g);preceding=g['preceding_storage'](e['inputs'])
# Installed package metadata only, never import numerical packages.
runtime={'python':platform.python_version(),'cpu_count':os.cpu_count(),'lock_sha256':h(M/'uv.lock'),'packages':{p:importlib.metadata.version(p) for p in ('numpy','scipy','pyarrow','torch','scikit-learn')}};assert runtime==read(M/e['inputs']['environment']['path'])
workspace=read(M/e['inputs']['execution_workspace']['path']);assert workspace['root']==str(M) and workspace['ledger']==str(M/'research_runs') and workspace['artifacts']==str(M/'research_artifacts')
# Existing Git marker metadata only; no Git command.
marker=(M/'.git').read_text().strip();assert marker.startswith('gitdir: ');admin=Path(marker[8:]);assert admin.is_absolute() and admin.resolve()==admin
common=(admin/'commondir').read_text().strip();assert (admin/common).resolve()==Path(workspace['git_common']);assert (admin/'gitdir').read_text().strip()==str(M/'.git')
extent=read(C/'RAW_EXTENT01.json');weekly=read(M/e['inputs']['weekly_source']['path']);plan=read(M/e['inputs']['graph_plan']['path']);assert plan['expected_weeks']==['2022-05-30T00:00:00Z'] and plan['coverage']==[['2022-05-30T00:00:00Z','2022-06-06T00:00:00Z']]
assert len(extent['daily_members'])==len(weekly['members'])==7 and weekly['expected_rows']==7507236 and sum(x['expected_rows'] for x in extent['daily_members'])==7507236
count=0
for i,(member,w) in enumerate(zip(extent['daily_members'],weekly['members'])):
 ref=e['inputs'][f'daily_map_{i:02d}'];assert member['mapping_path']==ref['path'] and member['mapping_sha256']==w['sha256']==ref['sha256'] and str(M/ref['path'])==w['path'] and member['expected_rows']==w['expected_rows']
 daily=read(M/ref['path']);spans={x['path']:x for x in daily['spans']};assert len(spans)==len(member['segments'])
 for seg in member['segments']:
  span=spans[seg['path']];assert span['stored_bytes']==seg['bytes'] and span['stored_sha256']==seg['expected_stored_sha256'];p=Path(seg['path']);s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==[seg[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns')];count+=1
assert count==250
projection=read(C/'STORAGE_PROJECTION01.json');policy=read(C/'STORAGE_POLICY01.json');prior=read(M/projection['basis']['path']);assert h(M/projection['basis']['path'])==projection['basis']['sha256'];den=prior['retained_graph_reference']['declared_raw_rows'];rows=weekly['expected_rows'];ceil=lambda a,b:(a+b-1)//b
assert projection['density_projected_ledger_bytes']==ceil(prior['closed_ledger_reference']['bytes']*rows,den) and projection['density_projected_arrays_bytes']==ceil(prior['retained_graph_reference']['saved_array_bytes']*rows,den)
growth=2*projection['density_projected_ledger_bytes']+projection['density_projected_arrays_bytes']+projection['largest_projected_parquet_logical_bytes']+64*1024**2;assert growth==7568955167==policy['growth_estimate_bytes'];assert policy['startup_free_requirement_bytes']==growth+10*1024**3==18306373407
assert job['resources']['storage_budget']==policy['storage_budget'];assert policy['storage_budget']['limits']['max_allocated_bytes']==policy['baseline']['allocated_bytes']+growth and policy['storage_budget']['limits']['max_logical_bytes']==policy['baseline']['logical_file_bytes']+growth
for p in [M/'research_runs'/NAME,M/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,M/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,C/'launch-attempt01.json',C/'outer-exit01.json']:assert not os.path.lexists(p)
units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
active=[]
for p in (M/'research_runs').glob('*/claim.json'):
 if p.with_name('complete.json').exists() or p.with_name('failed.json').exists():continue
 v=json.loads(p.read_bytes());assert v.get('program_id')!=gate['program_id'];active.append(str(p.relative_to(M)))
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch
observation=StorageWatch(**job['resources']['storage_budget']).check();free=shutil.disk_usage(M).free
mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
GET=F/'real-data-pilot-fourth-graph-get-duplicates-retirement01-2026-10-06';gc=read(GET/'complete01.json');gr=read(GET/'ROOT_TERMINAL01.json');gs=read(GET/'selection01.json');assert h(GET/'complete01.json')=='41f6b0698a94d3e3d825fae68c0aa1f6b2d8c047c8f176c5ca99045ec4aea8f2'==gr['complete_sha256'] and gr['actual_root_exit_code']==0 and gr['actual_root_tool_chunk']=='bcaf37';assert gc['payload_bytes_retired']==501845112 and gc['original_arrays_retained'] is True and gc['removed']==[r['recovered']['path'] for r in gs['rows']]
for r in gs['rows']:
 assert not os.path.lexists(M/r['recovered']['path']);s=(M/r['original']['path']).lstat();assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==r['original']['stat_identity']
assert not any(x in sys.modules for x in ('numpy','torch','scipy','pyarrow'))
result={'gate_sha256':h(C/'gate01.json'),'source_pins':178,'compact_inputs':32,'required_package_sources':len(required),'unchanged_core_source_pins':len(newcore),'experiment_fields_changed':sorted(changed),'raw_extents_stat_only':count,'declared_rows':rows,'actual_preceding_storage_result':preceding,'runtime_metadata_matches':True,'preflight_and_preparation_exact_literal_inverses':True,'launcher_exact_unchanged':True,'actual_five_get_complete_sha256':gr['complete_sha256'],'fixed_namespaces_absent':True,'native_units_empty':True,'unrelated_active_claims':active,'sample_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mem_available_bytes':mem,'start_reserve_bytes':job['resources']['start_reserve_bytes'],'free_disk_bytes':free,'startup_free_requirement_bytes':policy['startup_free_requirement_bytes'],'storage_observation':observation,'fresh_ram_observation_meets':mem>=job['resources']['start_reserve_bytes'],'fresh_disk_observation_meets':free>=policy['startup_free_requirement_bytes'],'qualification':'Read-only metadata/source review and point-in-time resource observation; no admission, native worker, arrays/raw-body reads or capacity authority. Root must repeat genuine post-commit admission and fresh preflight.'}
(D/'ENTRY_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');(D/'EVIDENCE01.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['storage_observation','actual_preceding_storage_result']},sort_keys=True))
