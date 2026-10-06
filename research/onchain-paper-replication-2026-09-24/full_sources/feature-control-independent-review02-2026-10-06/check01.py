"""Independent bounded arithmetic/source checks, no empirical module imports."""
import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;M=H.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=F/'real-data-pilot-feature-control-inventory01-2026-10-06'
R=F/'real-data-pilot-feature-residual-controls01-2026-10-06'
P=F/'real-data-pilot-feature-control-residual-review01-2026-10-06'
pins={};members=0
for d in [C,R,P]:
    manifest=json.loads((d/'MANIFEST01.json').read_bytes())
    pins[str((d/'MANIFEST01.json').relative_to(M))]=sha(d/'MANIFEST01.json')
    for rel,v in manifest['files'].items():
        p=d/rel;pin=v['sha256'] if isinstance(v,dict) else v
        assert not p.is_symlink() and sha(p)==pin
        members+=1
def load(path,pin):
    assert sha(path)==pin;pins[str(path.relative_to(M))]=pin
    s={'__name__':'independent_offline_arithmetic','__file__':str(path)}
    exec(compile(path.read_bytes(),str(path),'exec'),s);return s
c=load(C/'controls01.py','d6b3bac4b71fc7cd6d2dfaf63d8aa395fb87e47eef5dbc2b7bd501fd385e59f3')
r=load(R/'residuals01.py','54e83b083b8ff83c288c17d6be8b4ebeb1528cf79fc96775c7085f22bbaa5c4c')
b=load(F/'real-data-pilot-resource-input-builder03-2026-10-06/build_inputs03.py','e100a1fa2f8caaa6baf6cde85d5f50aa667ed6e04b6470d9c8368d5424748a2d')
p=load(P/'prepare_builder03_input01.py','37447ae7126049ffe1de5bf94baf41b1606504618d8935cdfd88704bbd3d35f4')
known=json.loads((P/'KNOWN_COUNTS01.json').read_bytes());assert len(known['known'])==4
for week,g in known['known'].items():
    for role in ['manifest','node_count']:
        ref=g[role];path=M/ref['path'];assert path.stat().st_size==ref['bytes'] and sha(path)==ref['sha256']
    assert json.loads((M/g['node_count']['path']).read_bytes())['rows']==g['rows']
draft=json.loads((P/'INPUT_DRAFT01.json').read_bytes());assert sum(v is not None for v in draft['graphs'].values())==4
refusals=[]
def refusal(name,fn):
    try:fn()
    except (ValueError,TypeError) as e:refusals.append({'case':name,'exception':type(e).__name__,'message':str(e)})
    else:raise AssertionError(name)
refusal('four-real-countrefs-cannot-complete-handoff',lambda:p['prepare'](M,draft))
refusal('real-builder-four-week-map',lambda:b['graphs'](M,{w:v for w,v in draft['graphs'].items() if v is not None}))
# Independently varied synthetic integer declarations. No resource grant is selected.
s=json.loads((C/'SYNTHETIC_INPUT01.json').read_bytes())
stage={'pair':{'max_checkpoint_bytes':1024**2},'schedule':{'max_total_checkpoints':5},'restart_retention':{'schema_version':1,'format':'archived-restart-retention-v1','max_stores':3,'max_generations':5,'max_control_bytes':4*1024**2,'max_cumulative_bytes':64*1024**2,'max_live_bytes':10*1024**2,'max_replay_bytes':2*1024**2,'max_input_bytes':2*1024**2,'max_replays':2}}
res=r['resolve'](stage,native_file_bytes=8*1024**2,training_checkpoint_bytes=4*1024**2,runtime_reservation={'logical_bytes':16*1024**2,'regular_files':128,'directories':13,'max_file_bytes':1024**2})
s['residual_domains']=res['residual_domains']
calc=c['allocation']()
rowcounts=[3,2049,17,9,41,100,2]
for w,n in zip(c['WEEKS'],rowcounts):
    g=s['graphs'][w];g['rows']=n
    g['allowances']=calc['graph'](n,s['chunk_cells'],g['tail_part_bytes'],g['output_part_bytes'],s['stage']['chunk_events']*168)['required_typed_allowances']
out=c['calculate'](s)
assert out['status']=='DRAFT_DECLARATIONS_NOT_ADMITTED' and out['storage_budget_unchanged']==s['storage_budget']
assert res['source_bounds']['matching_stages']==7 and res['source_bounds']['original_import_recomputation'] is False
k=res['residual_domains']['checkpoint_retention'];G=5;S=3;K=1024**2
assert k['regular_files']==7*(10*G+9*S+51) and k['directories']==7*(11+S+4*G)
assert k['logical_bytes']==7*(8*1024**2+32768) and k['additional_scratch_bytes']==2*K
assert res['residual_domains']['import_owner_stage_journal']['logical_bytes']==23*65536
assert res['residual_domains']['training_and_lifecycle']['logical_bytes']==64*8*1024**2+4*1024**2+4096
categories=out['categories'];assert categories['retained_original_matrices']['logical_bytes']==128*sum(rowcounts)
for w,n in zip(c['WEEKS'],rowcounts):
    need=out['by_week'][w]['required_typed_allowances']['score-tail-f64']
    assert need['max_recovered_bytes']==80*32*n and need['max_chunks']==2*out['by_week'][w]['tail_preserve_parts']
logical=sum(v['logical_bytes'] for v in categories.values())
fragment=out['builder03_physical_fragment']
independent=sum(fragment[n] for n in ['reserved_growth_bytes','reserved_control_bytes','retained_diagnostic_bytes','caller_scratch_bytes','typed_attempt_metadata_bytes'])+sum(fragment['remaining_control_inventory'].values())
assert independent==logical==out['new_logical_bytes']
fs=s['filesystem'];files=sum(v['regular_files'] for v in categories.values());dirs=sum(v['directories'] for v in categories.values())
overhead=files*(fs['allocation_unit_bytes']-1+fs['per_regular_inode_overhead_bytes'])+dirs*fs['per_directory_allocated_bytes']+fs['extra_allocated_bytes']
assert overhead==out['allocation_overhead_bytes']
assert out['total_with_declared_baseline']=={'logical_bytes':logical+s['baseline']['logical_bytes'],'allocated_bytes':logical+overhead+s['baseline']['allocated_bytes'],'entries':files+dirs+fs['extra_entries']+s['baseline']['entries']}
short=copy.deepcopy(s);short['storage_budget']['limits']['max_allocated_bytes']=out['total_with_declared_baseline']['allocated_bytes']-1
refusal('one-byte-physical-shortfall',lambda:c['calculate'](short))
four=copy.deepcopy(s);four['graphs']={w:four['graphs'][w] for w in known['known']}
refusal('inventory-four-count-map',lambda:c['calculate'](four))
# Actual source AST only: the forwarded path set and RLIMIT call chain.
src=M/'tradingagents/research/onchain_replication'
envtree=ast.parse((src/'real_pilot_storage.py').read_text());fn=next(n for n in envtree.body if isinstance(n,ast.FunctionDef) and n.name=='environment')
routes=next(ast.literal_eval(n.value) for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='routes' for t in n.targets))
assert set(routes.values())==set(r['RUNTIME_PATHS']) and len(set(routes.values()))==12
job=ast.parse((src/'job.py').read_text());funcs={n.name:ast.unparse(n) for n in job.body if isinstance(n,ast.FunctionDef)}
assert "_resource_limit_receipt(args, job, 'monitor')" in funcs['monitor']
assert '_resource_worker_limits(job)' in funcs['_resource_limit_receipt']
assert 'real_pilot_import_caller.worker_limits(job)' in funcs['_resource_worker_limits']
caller=ast.parse((src/'real_pilot_import_caller.py').read_text());worker=next(ast.unparse(n) for n in caller.body if isinstance(n,ast.FunctionDef) and n.name=='worker_limits')
assert 'resource.setrlimit(resource.RLIMIT_FSIZE, (expected, expected))' in worker and 'resource.getrlimit(resource.RLIMIT_FSIZE) == (expected, expected)' in worker
for n in ['job.py','real_pilot_import_caller.py','real_pilot_storage.py','stage_retention.py','restart_retention.py','archive_owner_policy.py']:
    pins[str((src/n).relative_to(M))]=sha(src/n)
result={'decision':'accepted-source-arithmetic-only','authenticated_manifest_members':members,'source_pins':pins,'four_current_count_refs_authenticated':4,'missing_weeks':known['missing_weeks'],'refusals':refusals,'synthetic_new_logical_bytes':logical,'synthetic_allocation_overhead_bytes':overhead,'physical_fragment_exactly_reconciled':True,'native_monitor_worker_selected_RLIMIT_chain':True,'runtime_paths_exact':sorted(set(routes.values())),'source_matching_stages':7,'archive_reservation_stages':8,'capacity_admission_or_grants':False,'scientific_or_numerical_imports':False,'payload_reads':0}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_pins'}))
