"""Concrete May30 metadata draft only: no gate write, admission or launch."""
from pathlib import Path
import argparse,copy,datetime,hashlib,importlib.metadata,json,os,platform,stat
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
FULL=HERE.parent
OLD=FULL/'real-data-pilot-third-graph01-2026-10-06'
NAME='eth-paper-real-pilot-graph-20220530-20261005-01'
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24'
def digest(path):
    if path.stat().st_size>4*1024**2:raise ValueError('compact metadata/source limit: '+str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':str(path.relative_to(ROOT)),'sha256':digest(path),'dataset':'eth'}
def validate_week(weekly, case):
    start=datetime.datetime.fromisoformat(case['week'].replace('Z','+00:00'))
    end=start+datetime.timedelta(days=7)
    stamp=lambda d:d.isoformat().replace('+00:00','Z')
    if (weekly['start_utc']!=stamp(start) or weekly['end_utc']!=stamp(end)
            or weekly['expected_members']!=7 or len(weekly['members'])!=7
            or weekly['expected_rows']!=case['expected_rows']):raise ValueError('complete fixed week required')
    for i,(member,day) in enumerate(zip(weekly['members'],case['daily_members'])):
        if (member['start_utc']!=stamp(start+datetime.timedelta(days=i))
                or member['end_utc']!=stamp(start+datetime.timedelta(days=i+1))
                or member['path']!=str(ROOT/day['mapping_path']) or member['sha256']!=day['mapping_sha256']
                or member['expected_rows']!=day['expected_rows']):raise ValueError('missing/late/reordered original daily member')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);a=parser.parse_args();out=Path(a.output).resolve()
    if out.parent!=HERE or out.exists():raise ValueError('fresh directory directly inside assigned preparation required')
    namespace=[ROOT/'research_runs'/NAME,ROOT/PREFIX/'runs'/NAME,ROOT/PREFIX/'sources'/NAME,HERE/'launch-attempt01.json',HERE/'outer-exit01.json']
    if any(x.exists() or x.is_symlink() for x in namespace):raise ValueError('fixed namespace already used')
    census=FULL/'real-data-pilot-remaining-graph-inputs01-2026-10-06/RAW_EXTENTS01.json'
    case=next(x for x in json.loads(census.read_bytes())['cases'] if x['identity']==NAME)
    if case['parent'] is not None or case['run_started'] is not False or case['week']!='2022-05-30T00:00:00Z' or case['expected_rows']!=7507236:raise ValueError('fixed independent May30 case differs')
    if len(case['daily_members'])!=7 or sum(d['expected_rows'] for d in case['daily_members'])!=case['expected_rows']:raise ValueError('complete original daily denominator differs')
    for d in case['daily_members']:
        if digest(ROOT/d['mapping_path'])!=d['mapping_sha256']:raise ValueError('original daily map changed')
        for segment in d['segments']:
            path=Path(segment['path']);s=path.lstat()
            if path.is_symlink() or not stat.S_ISREG(s.st_mode) or (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)!=tuple(segment[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns')):raise ValueError('raw extent changed: '+str(path))
    for r in case['inputs'].values():
        if digest(ROOT/r['path'])!=r['sha256']:raise ValueError('original graph input changed')
    validate_week(json.loads((ROOT/case['inputs']['weekly_source']['path']).read_bytes()),case)
    plan=json.loads((ROOT/case['inputs']['graph_plan']['path']).read_bytes())
    if plan['coverage']!=[[case['week'],'2022-06-06T00:00:00Z']] or plan['expected_weeks']!=[case['week']] or plan['source_inputs']!=['weekly_source']:raise ValueError('full original coverage differs')
    gate=json.loads((OLD/'gate01.json').read_bytes());prior=next(iter(gate['experiments'].values()));job=json.loads((OLD/'execution-job01.json').read_bytes())
    required={str(f.relative_to(ROOT)) for folder in (ROOT/'tradingagents/research/onchain_replication',ROOT/'tradingagents/research') for f in folder.glob('*.py')}|{'tradingagents/__init__.py'}
    pins={name:digest(ROOT/name) for name in sorted(required)}
    extras=[HERE/'prepare_draft01.py',HERE/'preflight_DRAFT01.py',HERE/'launch_DRAFT01.py',HERE/'CHARTER_DRAFT01.md',FULL/'real-data-end-to-end-pilot-preparation01-2026-10-05/CUMULATIVE_ALLOCATION_PROPOSED71_01.json',ROOT/prior['cumulative_budget_extension']['extension']['path'],ROOT/prior['cumulative_budget_extension']['review']['path']]
    pins.update({str(f.relative_to(ROOT)):digest(f) for f in extras})
    if len(pins)!=178:raise ValueError('expected current178 source/entry closure differs')
    old_sources=prior['source_files'];changed={name:{'before':old_sources[name],'after':pins[name]} for name in required&set(old_sources) if pins[name]!=old_sources[name]};added=sorted(required-set(old_sources))
    if changed or added:raise ValueError('current package differs from frozen May16 source')
    runtime={f.name:digest(f) for f in sorted((ROOT/'tradingagents/research').glob('*.py'))}
    environment={'python':platform.python_version(),'cpu_count':os.cpu_count(),'lock_sha256':digest(ROOT/'uv.lock'),'packages':{k:importlib.metadata.version(k) for k in ('numpy','scipy','pyarrow','torch','scikit-learn')}}
    environment_ref=prior['inputs']['environment']
    if digest(ROOT/environment_ref['path'])!=environment_ref['sha256'] or environment!=json.loads((ROOT/environment_ref['path']).read_bytes()):raise ValueError('original installed runtime environment differs')
    inherited={k:v for k,v in prior['inputs'].items() if k.startswith('storage_') or k in ('source_integration','execution_workspace','environment','input_selection')}
    for value in inherited.values():
        if digest(ROOT/value['path'])!=value['sha256']:raise ValueError('required inherited actual input changed')
    inputs=copy.deepcopy(case['inputs'])
    for i,d in enumerate(case['daily_members']):inputs[f'daily_map_{i:02d}']=ref(ROOT/d['mapping_path'])
    projection=json.loads((OLD/'STORAGE_PROJECTION01.json').read_bytes());rows=case['expected_rows'];reference_rows=projection['retained_graph_reference']['declared_raw_rows'];ledger=(rows*projection['closed_ledger_reference']['bytes']+reference_rows-1)//reference_rows;arrays=(rows*projection['retained_graph_reference']['saved_array_bytes']+reference_rows-1)//reference_rows;growth=2*ledger+arrays+case['largest_projected_parquet_bytes']+projection['scratch_margin_bytes']
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    extent={'at':at,'week':case['week'],'days':7,'declared_rows':rows,'daily_members':case['daily_members'],'segments':sum(len(d['segments']) for d in case['daily_members']),'stored_bytes':sum(s['bytes'] for d in case['daily_members'] for s in d['segments']),'largest_projected_object_logical_bytes':case['largest_projected_parquet_bytes'],'raw_bodies_read':False,'census':ref(census),'status':'DRAFT_NOT_RELEASED'}
    draft={'status':'DRAFT_NOT_RELEASED','identity':NAME,'parent':None,'effective_budget_unchanged':71,'cells':case['cells'],'outputs':case['outputs'],'windows':[{'dataset':'eth','start':case['week'],'end':'2022-06-06T00:00:00Z','availability':'existing'}],'raw_input_refs':inputs,'inherited_actual_inputs_required':inherited,'execution_job_exact_May16':job,'prospective_source_files':dict(sorted(pins.items())),'runtime_hashes':runtime,'environment':environment,'fresh_root_inputs_required':['actual May23 outcome/preservation/recovery acceptance and any retirement receipts','fresh storage policy/baseline and startup/free-space admission','current source-integration receipt, committed gate and independent source/entry release review'],'no_registration_or_claim_created':True}
    delta={'status':'DRAFT_NOT_RELEASED','old_gate':ref(OLD/'gate01.json'),'old_source_count':len(old_sources),'prospective_source_count':len(pins),'added_package_source':added,'changed_package_sources':changed,'unchanged_package_bodies':len(required)-len(added)-len(changed),'same_method':True,'execution_job_byte_semantics_unchanged':True,'old_week':'2022-05-16T00:00:00Z','new_week':case['week'],'old_graph_inputs':{k:v for k,v in prior['inputs'].items() if k.startswith('daily_map_') or k in case['inputs']},'new_graph_inputs':inputs,'raw_extent_stat_joins':extent['segments'],'namespace_absent':[str(x.relative_to(ROOT)) for x in namespace]}
    estimate={'status':'DRAFT_NOT_RELEASED_ESTIMATE_NOT_CAPACITY','basis':ref(OLD/'STORAGE_PROJECTION01.json'),'declared_rows':rows,'density_projected_ledger_bytes':ledger,'density_projected_arrays_bytes':arrays,'largest_projected_parquet_logical_bytes':case['largest_projected_parquet_bytes'],'scratch_margin_bytes':projection['scratch_margin_bytes'],'prospective_growth_estimate_bytes':growth,'prospective_startup_free_bytes':job['resources']['disk_floor_bytes']+growth,'fresh_baseline_not_observed':True}
    out.mkdir()
    for name,value in [('MAY30_DRAFT01.json',draft),('RAW_EXTENT_DRAFT01.json',extent),('STORAGE_PROJECTION_DRAFT01.json',estimate),('SOURCE_INPUT_DELTA01.json',delta)]:
        with (out/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({'identity':NAME,'rows':rows,'segments':extent['segments'],'source_pins':len(pins),'raw_input_pins':len(inputs),'status':'DRAFT_NOT_RELEASED','output':str(out)},sort_keys=True))
if __name__=='__main__':main()
