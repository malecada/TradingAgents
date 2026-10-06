"""One fixed metadata-only entry preparation; actual recovery/baseline required."""
import copy,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
NAME='eth-paper-real-pilot-may30-ledger-continuation-20261006-01'
BASE=F/'real-data-pilot-fifth-graph01-2026-10-06'
HANDOFF=F/'real-data-pilot-may30-ledger-continuation-handoff01-2026-10-06'
GIB=1024**3

def need(ok,message):
    if not ok:raise ValueError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(ref):
    need(type(ref) is dict and set(ref)=={'path','sha256'},'exact real reference required')
    rel=Path(ref['path']);p=ROOT/rel
    need(not rel.is_absolute() and '..' not in rel.parts and p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2,'bounded canonical metadata required')
    need(digest(p)==ref['sha256'],'metadata hash differs')
    return json.loads(p.read_bytes())
def control():
    p=ROOT/'tradingagents/research/onchain_replication/graph_ledger_continuation.py'
    need(digest(p)=='c204412df8e0733e932feef171431ec50487181bb012c771a783ac63b807c2d8','reviewed continuation helper differs')
    sp=importlib.util.spec_from_file_location('continuation_metadata',p);m=importlib.util.module_from_spec(sp);m.__package__='tradingagents.research.onchain_replication';sp.loader.exec_module(m);return m

BASE_PINS={'execution-job01.json': 'f4602068cbe1aae6d6553212b06e8313ae03302cd18752060a65a41ecaf2cbb2', 'gate01.json': 'b0c58b8a610a102ec11d943c9c869ef9162da5a80edac3c8edda3c57135195c3'}
def baseline(name):
    p=BASE/name
    need(digest(p)==BASE_PINS[name],'frozen predecessor metadata changed')
    return json.loads(p.read_bytes())

def validate_binding(b):
    fields={'identity','plan','recovery','storage_policy','environment','extension','extension_review','charter','source_files','runtime_hashes','relocation_receipt','relocation_review'}
    need(type(b) is dict and set(b)==fields and all(v is not None for v in b.values()),'actual recovery/source/storage bindings unavailable')
    need(b['identity']==NAME,'fixed fresh continuation identity required')
    m=control();p=m.plan_check(read(b['plan']));need(p['new_experiment_id']==NAME,'plan identity differs')
    need(p['schema_version']==2,'explicit fixed cross-volume plan required')
    def relocation_read(role):
        key={p['relocation_receipt_input']:'relocation_receipt',p['relocation_review_input']:'relocation_review'}[role]
        read(b[key]);return (ROOT/b[key]['path']).read_bytes()
    m.relocated_path(ROOT,p,relocation_read)
    r=read(b['recovery']);need(r.get('decision')=='accepted' and r.get('predecessor')==m.OLD and r.get('parent_status')=='failed' and r.get('ledger_byte_recovery') is True and r.get('ledger')==p['ledger'] and r.get('committed_source_rows')==7507236 and r.get('source_boundary_count')==7,'actual independently accepted ledger recovery required')
    s=read(b['storage_policy']);need(set(s)=={'schema_version','identity','baseline','baseline_evidence','output_bytes','sqlite_scratch_bytes','control_and_overhead_bytes','growth_estimate_bytes','startup_free_requirement_bytes','scratch_scope','storage_budget','data_store'},'explicit complete storage declaration required')
    need(s['schema_version']==2 and s['identity']==NAME,'storage identity differs')
    observed=read(s['baseline_evidence']);need(s['baseline']==observed,'actual measured baseline differs')
    for key in ('output_bytes','sqlite_scratch_bytes','control_and_overhead_bytes'):need(type(s[key]) is int and s[key]>0,'finite positive storage component required')
    # Conservative reservations, not certified node/edge counts or guaranteed peaks.
    need(s['output_bytes']>=2*GIB and s['sqlite_scratch_bytes']>=p['ledger']['bytes'] and s['control_and_overhead_bytes']>=64*1024**2,'minimum continuation reservation unavailable')
    growth=sum(s[k] for k in ('output_bytes','sqlite_scratch_bytes','control_and_overhead_bytes'))
    need(s['growth_estimate_bytes']==growth and s['startup_free_requirement_bytes']==10*GIB+growth,'physical growth/floor sum differs')
    old=baseline('execution-job01.json')['resources']['storage_budget'];budget=s['storage_budget']
    need(budget['root']==old['root'] and set(budget)==set(old),'original watched source root required')
    for k in ('max_depth','max_entries','max_scan_seconds'):need(budget['limits'][k]==old['limits'][k],'unchanged scan controls required')
    for k in ('max_logical_bytes','max_allocated_bytes'):need(budget['limits'][k]==old['limits'][k],'no storage ceiling change authorized')
    need(observed['logical_file_bytes']+growth<=budget['limits']['max_logical_bytes'] and observed['allocated_bytes']+growth<=budget['limits']['max_allocated_bytes'],'unchanged storage ceiling cannot fit declared continuation')
    need(type(s['scratch_scope']) is dict and set(s['scratch_scope'])=={'sqlite_temp_candidates'} and bool(s['scratch_scope']['sqlite_temp_candidates']),'actual SQLite scratch paths required')
    need(s['data_store']=={'storage_budget':m.data_budget(p),'device':m.DATA_DEVICE,'disk_floor_bytes':10*GIB,'free_reserve_bytes':m.DATA_RESERVE},'exact separately retained Data accounting required')
    import shutil
    need(shutil.disk_usage(m.DATA_ROOT).free>=10*GIB+m.DATA_RESERVE,'Data floor plus retained-store headroom unavailable')
    e=read(b['extension']);review=read(b['extension_review'])
    need(e['initial_experiment']==NAME and e['cumulative_ceiling']==72 and review['decision']=='accepted' and review['extension_sha256']==b['extension']['sha256'],'exact reviewed prospective72 required')
    need(type(b['source_files']) is dict and bool(b['source_files']) and type(b['runtime_hashes']) is dict and bool(b['runtime_hashes']),'current source/runtime closure required')
    required={'tradingagents/research/onchain_replication/'+n for n in ('graph_production.py','graph_ledger_continuation.py','weekly_retained_ledger.py','resources.py','job.py')}
    need(required<=set(b['source_files']),'continuation/guard source closure incomplete')
    return p,s,m

def prepare(binding,out):
    p,s,m=validate_binding(binding);out=Path(out).resolve()
    need(out.is_relative_to(F) and out.is_dir() and {x.name for x in out.iterdir()}=={'prepare01.py','preflight01.py','launch01.py'},'fresh Root-installed three-source entry directory required')
    for name in ('prepare01.py','preflight01.py','launch01.py'):
        need(digest(out/name)==digest(HERE/name) and binding['source_files'].get(str((out/name).relative_to(ROOT)))==digest(out/name),'exact entry source closure required')
    need(not (ROOT/'research_runs'/NAME).exists(),'fresh namespace already consumed')
    for rel,h in binding['source_files'].items():
        q=ROOT/rel;need(q.resolve(strict=True)==q and digest(q)==h,'current source body differs')
    gate=baseline('gate01.json');e=copy.deepcopy(next(iter(gate['experiments'].values())))
    job=baseline('execution-job01.json');job['payload']={'plan_input':'continuation_plan'};job['resources']['storage_budget']=s['storage_budget'];job['resources']['disk_paths']=[str(ROOT),str(m.DATA_ROOT)]
    e.update(cells=['graph-2022-05-30'],parent=None,question='Fresh graph-only retained-ledger continuation; old May30 FAILED remains spent; no source reingestion.',charter=binding['charter'],source_files=binding['source_files'],runtime_hashes=binding['runtime_hashes'],cumulative_budget_extension={'extension':binding['extension'],'review':binding['extension_review']})
    e['inputs']=copy.deepcopy(m.FIXED)
    for role,ref in [('continuation_plan',binding['plan']),(p['recovery_review_input'],binding['recovery']),('environment',binding['environment']),('storage_policy',binding['storage_policy']),(p['relocation_receipt_input'],binding['relocation_receipt']),(p['relocation_review_input'],binding['relocation_review'])]:
        need(role not in e['inputs'],'input role collision');e['inputs'][role]={'dataset':'eth',**ref}
    # Output names stay genuine existing graph dispatcher names; no source cell.
    jobpath=out/'execution-job01.json';jobpath.write_text(json.dumps(job,sort_keys=True,indent=2)+'\n')
    e['inputs']['execution_job']={'dataset':'eth','path':str(jobpath.relative_to(ROOT)),'sha256':digest(jobpath)}
    binding_path=out/'BINDINGS01.json'
    binding_path.write_text(json.dumps(binding,sort_keys=True,indent=2)+'\n')
    e['inputs']['continuation_entry_bindings']={'dataset':'eth','path':str(binding_path.relative_to(ROOT)),'sha256':digest(binding_path)}
    gate['experiments']={NAME:e}
    for name,value in [('gate01.json',gate),('STORAGE_POLICY01.json',s)]:
        with (out/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    return {'status':'PREPARED_NOT_ADMITTED','identity':NAME,'gate_sha256':digest(out/'gate01.json'),'growth_estimate_bytes':s['growth_estimate_bytes'],'startup_free_requirement_bytes':s['startup_free_requirement_bytes']}
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--binding',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();print(json.dumps(prepare(json.loads(v.binding.read_text()),v.output),sort_keys=True))
