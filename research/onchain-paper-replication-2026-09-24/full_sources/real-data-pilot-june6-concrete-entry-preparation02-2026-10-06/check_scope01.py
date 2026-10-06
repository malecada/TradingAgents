from pathlib import Path
import ast,copy,hashlib,importlib.util,json
H=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('scoped_boundary',H/'boundary01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
D=m.ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-sixth-graph-input-preparation01-2026-10-06/draft01'
p=json.loads((D/'STORAGE_PROJECTION_DRAFT01.json').read_bytes());got=m.storage_scopes(p)
assert got['physical_root_growth_bytes']==7155620336 and got['named_sources_growth_bytes']==6744020747 and got['unnamed_projected_parquet_bytes']==411599589 and got['physical_startup_free_bytes']==17893038576 and got['named_rollback_journal_allowance_bytes']==3099885508
bad=copy.deepcopy(p);bad['prospective_growth_estimate_bytes']-=p['largest_projected_parquet_logical_bytes']
try:m.storage_scopes(bad)
except ValueError:pass
else:raise AssertionError('whole physical reservation was silently reduced')
basis=m.temporary_file_basis()
draft=json.loads((D/'JUNE6_DRAFT01.json').read_bytes());weekly=m.read(draft['raw_input_refs']['weekly_source']);assert len(weekly['members'])==7 and all(x['format']=='projected_zstd' for x in weekly['members'])
for name in ('boundary01.py','prepare01.py','preflight01.py','launch01.py'):compile((H/name).read_bytes(),str(H/name),'exec')
# Reconstruct unchanged original entry check after removing only the declared new scope checks.
text=(H/'preflight01.py').read_text()
block1="""    from boundary01 import storage_scopes,temporary_file_basis
    temporary_file_basis()
    scopes=storage_scopes(json.loads((HERE/'STORAGE_PROJECTION01.json').read_bytes()))
    if policy.get('scope_reservations')!=scopes:raise ValueError('declared physical/named-tree reservation differs')
"""
block2="""    limits=job['resources']['storage_budget']['limits']
    if storage['logical_file_bytes']+scopes['named_sources_growth_bytes']>limits['max_logical_bytes'] or storage['allocated_bytes']+scopes['named_sources_growth_bytes']>limits['max_allocated_bytes']:
        raise ValueError('fresh named-tree projection exceeds unchanged source-store ceilings')
"""
for block in (block1,block2):assert text.count(block)==1;text=text.replace(block,'')
text=text.replace('admission.effective_attempt_budget!=72','admission.effective_attempt_budget!=71').replace("'effective_attempt_budget':72","'effective_attempt_budget':71").replace("policy.get('preceding_continuation_boundary')","policy.get('failed_predecessor_retained')").replace('fresh storage policy must bind actual continuation closure, preserved failure and separate Data retention','fresh storage policy must explicitly retain failed originals and recoveries; no retirement credit')
f=lambda s:next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='check')
old=m.ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-sixth-graph-failed-predecessor-entry01-2026-10-06/preflight01.py';assert ast.dump(f(text))==ast.dump(f(old.read_text()))
sources={}
for name in ('graph_production.py','aggregation.py','weekly.py','eth_source.py','graph_store.py','workflow_storage.py'):
 q=m.ROOT/'tradingagents/research/onchain_replication'/name;sources[str(q.relative_to(m.ROOT))]=hashlib.sha256(q.read_bytes()).hexdigest()
result={'decision':'pass','scope_reservations':got,'stdlib_basis':basis,'source_pins':sources,'physical_shrink_refused':True,'rollback_reserve_retained':True,'original_preflight_check_AST_reconstructed':True,'payload_reads':0,'active_continuation_outputs_read':False,'live_baseline_not_sampled':True,'no_capacity_claim':True}
(H/'CHECK_SCOPE01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('source_pins','stdlib_basis')}))
