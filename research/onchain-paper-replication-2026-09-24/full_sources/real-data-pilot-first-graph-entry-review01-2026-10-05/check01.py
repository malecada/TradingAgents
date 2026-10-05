"""Compact source/data joins and fake outer entry only; no admission or raw reads."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,math,os,runpy,subprocess,sys,types
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT))
ENTRY=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-first-graph01-2026-10-05'
TEL=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-disk-telemetry01-2026-10-05'
NAME='eth-paper-real-pilot-graph-20220502-20261005-01'
h=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(p.read_bytes())
gate=load(ENTRY/'gate01.json');item=gate['experiments'][NAME]
assert h((ENTRY/'gate01.json').read_bytes())=='5468e412daf9df0e5ae46dcc3b5068525583914e188d2a2f98faa1bab1fd56ef'
assert len(gate['experiments'])==1 and item['family']=='paper' and item['parent'] is None
assert gate['families']['paper']['attempt_budget']==51 and gate['families']['paper']['prior_attempts']==17
assert item['cells']==['source-000000','graph-2022-05-02']
assert item['outputs']==['cell-ledger.json','source-summary.json','artifact-index.json']
assert len(item['source_files'])==150 and len(item['inputs'])==24
for path,sha in item['source_files'].items():assert h((ROOT/path).read_bytes())==sha,path
inputs={}
for role,ref in item['inputs'].items():
    raw=(ROOT/ref['path']).read_bytes();assert len(raw)<=4*1024**2 and h(raw)==ref['sha256'],role
    inputs[role]=json.loads(raw)
from tradingagents.research.onchain_replication.job import required_sources,workspace_binding,job_schema,resource_policy,_command
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.admission import runtime_hashes
assert required_sources()<=set(item['source_files'])
assert item['runtime_hashes']==runtime_hashes()
assert inputs['execution_workspace']==workspace_binding(ROOT)
assert inputs['environment']==inventory(ROOT)
job=inputs['execution_job'];job_schema(job);resource_policy(job['resources'],ROOT)
assert job['kind']=='graphs' and job['payload']=={'plan_input':'graph_plan'}
plan=inputs['graph_plan'];weekly=inputs['weekly_source'];extent=inputs['raw_extent']
assert plan['schema_version']==1 and plan['mode']=='build' and plan['asset']=='ETH'
assert plan['coverage']==[['2022-05-02T00:00:00Z','2022-05-09T00:00:00Z']]
assert plan['source_inputs']==['weekly_source'] and plan['expected_weeks']==['2022-05-02T00:00:00Z']
assert plan['decoder']=={'schema_input':'eth_schema'} and plan['graph_config_input']=='graph_config'
assert weekly['status']=='complete' and weekly['expected_members']==len(weekly['members'])==7
assert len(extent['daily_members'])==extent['days']==7
assert weekly['expected_rows']==extent['declared_rows']==7734878
total=0;stored=0;segment_count=0;paths=[]
for i,(member,observed) in enumerate(zip(weekly['members'],extent['daily_members'],strict=True)):
    day=datetime.datetime(2022,5,2)+datetime.timedelta(days=i)
    assert member['start_utc']==day.isoformat()+'Z' and member['end_utc']==(day+datetime.timedelta(days=1)).isoformat()+'Z'
    role=f'daily_map_{i:02d}';ref=item['inputs'][role];mapping=inputs[role]
    assert Path(member['path'])==ROOT/ref['path'] and member['sha256']==ref['sha256']==observed['mapping_sha256']
    assert observed['mapping_path']==ref['path'] and member['format']=='projected_zstd'
    assert member['expected_rows']==observed['expected_rows']
    total+=member['expected_rows']
    assert mapping['size']==mapping['object']['size']==observed['object_logical_bytes']
    assert len(mapping['spans'])==len(observed['segments'])
    for span,segment in zip(mapping['spans'],observed['segments'],strict=True):
        assert span['path']==segment['path'] and span['stored_sha256']==segment['expected_stored_sha256'] and span['stored_bytes']==segment['bytes']
        path=Path(segment['path']);st=path.lstat()
        assert not path.is_symlink() and path.is_file()
        assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==tuple(segment[k] for k in ['device','inode','bytes','mtime_ns','ctime_ns'])
        paths.append(str(path));stored+=st.st_size;segment_count+=1
assert total==7734878 and segment_count==extent['segments']==223 and stored==extent['stored_bytes']==668886055
assert len(set(paths))==223
projection=inputs['storage_projection'];policy=inputs['storage_policy']
assert projection['density_projected_ledger_bytes']==math.ceil(3662934016*total/8617920)
assert projection['density_projected_arrays_bytes']==math.ceil(563806472*total/8617920)
assert projection['largest_projected_parquet_logical_bytes']==max(d['object_logical_bytes'] for d in extent['daily_members'])==402554503
growth=2*projection['density_projected_ledger_bytes']+projection['density_projected_arrays_bytes']+402554503+64*1024**2
assert growth==projection['prospective_growth_estimate_bytes']==policy['growth_estimate_bytes']==7550916125
assert projection['prospective_startup_free_bytes']==policy['startup_free_requirement_bytes']==10*1024**3+growth
assert job['resources']['storage_budget']==policy['storage_budget']
limits=policy['storage_budget']['limits'];base=policy['baseline']
assert limits['max_allocated_bytes']==base['allocated_bytes']+growth
assert limits['max_logical_bytes']==base['logical_file_bytes']+growth
assert job['resources']['memory_max_bytes']==int(5.5*1024**3) and job['resources']['memory_high_bytes']==5*1024**3
assert job['resources']['start_reserve_bytes']==int(8.5*1024**3) and job['resources']['reserve_bytes']==3*1024**3
assert job['resources']['wall_seconds']==28800 and job['resources']['disk_floor_bytes']==10*1024**3
closure=inputs['storage_closure_review'];assert closure['decision']=='accepted' and len(closure['evidence'])==42
for path,sha in closure['evidence'].items():assert h((ROOT/path).read_bytes())==sha,path
assert inputs['storage_complete']==inputs['storage_recovered_complete']
assert inputs['storage_restore']==inputs['storage_recovered_restore']
extension=item['cumulative_budget_extension']
for ref in extension.values():assert h((ROOT/ref['path']).read_bytes())==ref['sha256']
budget_review=load(ROOT/extension['review']['path'])
assert budget_review['decision']=='accepted' and budget_review['extension_sha256']==extension['extension']['sha256']
for path in [ROOT/'research_runs'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,ENTRY/'launch-attempt01.json',ENTRY/'outer-exit01.json']:
    assert not path.exists() and not path.is_symlink(),str(path)

# Exact inverse of the only live package source change.
resource=ROOT/'tradingagents/research/onchain_replication/resources.py';current=resource.read_text()
assert h(current.encode())=='7735c451511b99f293d658c608afcdb21956d470c117d72104d1f55228041f44'
assert current==(TEL/'resources.py').read_text()
addition="             'elapsed_time_kill': False, 'retry': False,\n             'minimum_sampled_disk_free_bytes': {},\n             'disk_minimum_qualification': 'Sampled whole-volume free-space minimum per guarded path; includes unnamed temporary files and unrelated activity. Not a kernel quota, continuous minimum or per-job attribution.'}"
update="        for path, free in state['disk_free_bytes'].items():\n            previous = state['minimum_sampled_disk_free_bytes'].get(path, free)\n            state['minimum_sampled_disk_free_bytes'][path] = min(previous, free)\n"
assert current.count(addition)==current.count(update)==1
inverse=current.replace(addition,"             'elapsed_time_kill': False, 'retry': False}").replace(update,'')
assert h(inverse.encode())=='f86e272762865b9fd57442d4cf58e2bad5d976b200515a083b81ed8f07fe55af'

# Import the direct entry without invoking check/admission or scientific modules.
spec=importlib.util.spec_from_file_location('first_graph_entry_readonly',ENTRY/'preflight01.py')
preflight=importlib.util.module_from_spec(spec);spec.loader.exec_module(preflight)
assert preflight.ROOT==ROOT and preflight.HERE==ENTRY and preflight.NAME==NAME
assert not ({'numpy','torch','pyarrow','scipy'} & set(sys.modules))
assert Path(sys.executable)==ROOT/'.venv/bin/python'
args=types.SimpleNamespace(root=ROOT,registration=preflight.GATE,experiment=NAME,source='a'*40)
command=_command(args,'launch')
assert command[:5]==[str(ROOT/'.venv/bin/python'),'-B','-m','tradingagents.research.onchain_replication.job','--mode'] and command[5]=='launch'

# Execute the exact tiny launcher with only its check/command/subprocess edges
# faked. Never construct Admission, ResearchRun, Owner or native guard authority.
fake_results=[]
for case in ('exit-zero','exit-nonzero','call-raises','reserved-namespace'):
    path=HERE/('launch-fixture-'+case);path.mkdir()
    if case=='reserved-namespace':(path/'launch-attempt01.json').write_text('reserved\n')
    stub=types.ModuleType('preflight01');stub.ROOT=ROOT;stub.HERE=path;stub.check=lambda:(args,{'scope':'synthetic outer-entry test only'})
    called=[]
    def fake_call(cmd,**kw):
        called.append(cmd);assert cmd==command and kw=={'cwd':ROOT}
        if case=='call-raises':raise OSError('synthetic spawn failure')
        return 0 if case=='exit-zero' else 7
    try:
        with patch.dict(sys.modules,{'preflight01':stub}),patch.object(subprocess,'call',side_effect=fake_call):
            runpy.run_path(str(ENTRY/'launch01.py'),run_name='__main__')
    except SystemExit as error:
        assert error.code==(0 if case=='exit-zero' else 7)
    except OSError as error:
        assert case in ('call-raises','reserved-namespace')
    else:raise AssertionError('launcher unexpectedly fell through')
    if case=='reserved-namespace':assert not called and not (path/'outer-exit01.json').exists()
    else:
        result=load(path/'outer-exit01.json');assert result['exit_code']==({'exit-zero':0,'exit-nonzero':7,'call-raises':None}[case])
        assert len(called)==1 and (path/'launch-attempt01.json').exists()
    fake_results.append({'case':case,'calls':len(called),'status':'expected_behavior'})

out={'status':'PASS_METADATA_SOURCE_AND_FAKE_ENTRY_ONLY','gate_sha256':h((ENTRY/'gate01.json').read_bytes()),'source_pins':150,'compact_inputs':24,'daily_members':7,'raw_extents_stat_only':223,'declared_rows':total,'raw_stored_extent_bytes':stored,'accepted_storage_evidence_joins':42,'resources_sha256':h(current.encode()),'resources_exact_inverse':True,'author_three_telemetry_tests':load(TEL/'CHECKS01.json')['tests'],'fake_launch_checks':fake_results,'runtime_inventory_matches':True,'entry_root_and_interpreter_match':True,'namespaces_absent':True,'effective71_not_claimed_by_review':True,'current_resource_sufficiency_tested':False,'real_admission_or_native_or_numeric_execution':False,'entry_files':{p.name:h(p.read_bytes()) for p in ENTRY.iterdir() if p.is_file()}}
(HERE/'CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
for n in ('launch01.py','preflight01.py','prepare_registration01.py'):(HERE/('source-'+n)).write_bytes((ENTRY/n).read_bytes())
print(json.dumps({k:v for k,v in out.items() if k not in ('entry_files','author_three_telemetry_tests')},indent=2))
