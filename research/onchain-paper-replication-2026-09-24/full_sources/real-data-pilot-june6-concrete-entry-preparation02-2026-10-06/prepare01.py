"""Root-only June6 gate preparation after genuine current continuation closure."""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,stat
from boundary01 import ROOT,NAME,CONT,read,check as boundary_check,storage_scopes,temporary_file_basis
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch
HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-fifth-graph01-2026-10-06'
DRAFT=F/'real-data-pilot-sixth-graph-input-preparation01-2026-10-06/draft01'

def digest(p):
    if p.stat().st_size>4*1024**2:raise ValueError('bounded input/source required')
    return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'dataset':'eth','path':str(p.relative_to(ROOT)),'sha256':digest(p)}
def write(p,v):
    with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
def main():
    # Root binds this exact compact dependency body after the continuation, before any output.
    boundary=load(HERE/'BOUNDARY01.json');prior=boundary_check(boundary)
    for p in (ROOT/'research_runs'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME):
        if p.exists() or p.is_symlink():raise ValueError('original June6 namespace already spent')
    draft=load(DRAFT/'JUNE6_DRAFT01.json');extent=load(DRAFT/'RAW_EXTENT_DRAFT01.json');projection=load(DRAFT/'STORAGE_PROJECTION_DRAFT01.json')
    if draft['identity']!=NAME or draft['parent'] is not None or extent['declared_rows']!=7293215 or extent['days']!=7 or extent['segments']!=223:raise ValueError('fixed June6 membership differs')
    for d in extent['daily_members']:
        if digest(ROOT/d['mapping_path'])!=d['mapping_sha256']:raise ValueError('daily mapping changed')
        for segment in d['segments']:
            p=Path(segment['path']);s=p.lstat()
            if p.is_symlink() or not stat.S_ISREG(s.st_mode) or (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)!=tuple(segment[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns')):raise ValueError('current original raw extent changed')
    for r in draft['raw_input_refs'].values():read(r)
    weekly=read(draft['raw_input_refs']['weekly_source'])
    if len(weekly['members'])!=7 or any(member['format']!='projected_zstd' for member in weekly['members']):raise ValueError('scoped unnamed Parquet declaration requires exact projected_zstd decoder route')
    gate=read(boundary['dependencies']['basis_gate']);current=gate['experiments'][CONT]
    oldgate=load(OLD/'gate01.json');old=next(iter(oldgate['experiments'].values()));job=load(OLD/'execution-job01.json')
    if job!=draft['execution_job_exact_May16']:
        # Only the previously measured shared-tree budget may differ; native/scientific controls must not.
        a=copy.deepcopy(job);b=copy.deepcopy(draft['execution_job_exact_May16']);a['resources'].pop('storage_budget');b['resources'].pop('storage_budget')
        if a!=b:raise ValueError('original job/native controls changed')
    temporary_file_basis();scopes=storage_scopes(projection)
    baseline=StorageWatch(**job['resources']['storage_budget']).check();growth=scopes['physical_root_growth_bytes'];named_growth=scopes['named_sources_growth_bytes']
    # Existing ceilings are retained; this preparer does not enlarge them to force a fit.
    limits=job['resources']['storage_budget']['limits']
    if baseline['logical_file_bytes']+named_growth>limits['max_logical_bytes'] or baseline['allocated_bytes']+named_growth>limits['max_allocated_bytes']:raise ValueError('fresh baseline+original June6 projection exceeds retained source-store ceilings')
    startup=job['resources']['disk_floor_bytes']+growth
    policy=load(OLD/'STORAGE_POLICY01.json');policy.update(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline=baseline,growth_estimate_bytes=growth,startup_free_requirement_bytes=startup,free_disk_observed_bytes=shutil.disk_usage(ROOT).free,storage_budget=job['resources']['storage_budget'],preceding_continuation_boundary=prior,scope_reservations=scopes)
    if policy['free_disk_observed_bytes']<startup:raise ValueError('fresh full projected storage plus10GiB floor unavailable')
    # Retained Data ledger is a separate unchanged read-only store; June6 writes remain under original ROOT watch.
    e=copy.deepcopy(old);e.update(cells=draft['cells'],outputs=draft['outputs'],windows=draft['windows'],parent=None,question='Build the complete preserved ETH June6–13,2022 graph under the original unused pilot allowance.',charter={k:v for k,v in ref(HERE/'CHARTER01.md').items() if k!='dataset'},cumulative_budget_extension=current['cumulative_budget_extension'])
    keep={k:v for k,v in current['inputs'].items() if k in ('environment','execution_workspace','source_integration','input_selection')}
    for r in keep.values():read(r)
    e['inputs']={**keep,**draft['raw_input_refs'],'continuation_boundary':ref(HERE/'BOUNDARY01.json')}
    required={str(p.relative_to(ROOT)) for folder in (ROOT/'tradingagents/research/onchain_replication',ROOT/'tradingagents/research') for p in folder.glob('*.py')}|{'tradingagents/__init__.py'}
    pins=copy.deepcopy(current['source_files'])
    for p in required:
        if pins.get(p)!=digest(ROOT/p):raise ValueError('current integrated source closure differs from accepted continuation basis: '+p)
    for p in (HERE/'prepare01.py',HERE/'boundary01.py',HERE/'preflight01.py',HERE/'launch01.py',HERE/'CHARTER01.md'):pins[str(p.relative_to(ROOT))]=digest(p)
    e['source_files']=pins;e['runtime_hashes']=copy.deepcopy(current['runtime_hashes'])
    # All checks above precede the first write; Root invokes only in the fresh installed directory.
    write(HERE/'RAW_EXTENT01.json',extent);write(HERE/'STORAGE_PROJECTION01.json',projection);write(HERE/'STORAGE_POLICY01.json',policy);write(HERE/'execution-job01.json',job)
    for role,name in [('raw_extent','RAW_EXTENT01.json'),('storage_projection','STORAGE_PROJECTION01.json'),('storage_policy','STORAGE_POLICY01.json'),('execution_job','execution-job01.json')]:e['inputs'][role]=ref(HERE/name)
    gate['experiments']={NAME:e};write(HERE/'gate01.json',gate)
    write(HERE/'ROOT_PREPARATION01.json',{'identity':NAME,'parent':None,'status':'FROZEN_REQUIRES_ENTRY_REVIEW_COMMIT_AND_FRESH_ADMISSION','effective_attempt_budget':72,'original_allowance_retained':True,'transfer_or_refund':False,'source_pins':len(pins),'raw_stat_extents':223,'declared_rows':7293215,'predecessor':prior,'startup_free_requirement_bytes':startup,'scope_reservations':scopes,'capacity_or_claim':False})
    print(json.dumps({'gate_sha256':digest(HERE/'gate01.json'),'identity':NAME,'source_pins':len(pins),'effective_attempt_budget':72,'claim_started':False}))
if __name__=='__main__':main()
