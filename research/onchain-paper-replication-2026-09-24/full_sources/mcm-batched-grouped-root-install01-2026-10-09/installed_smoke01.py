"""Installed schema6 metadata/preload check, no scientific arrays or authority."""
import ast,hashlib,json,os,resource,signal,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
signal.alarm(60);os.nice(10)
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent
sys.path.insert(0,str(R))
install=json.loads((H/'INSTALL01.json').read_bytes())
for row in install['files'].values():
    assert hashlib.sha256((R/row['destination']).read_bytes()).hexdigest()==row['sha256']
from tradingagents.research.onchain_replication import real_pilot_import_caller as caller
from tradingagents.research.onchain_replication import real_pilot_reservations as reservations
from tradingagents.research.onchain_replication import typed_payload_operations as typed
caller._prepare_lease_modules(batched=True,grouped=True)
assert callable(typed._Operation.retire_batched_group)
roles=('compact_mcm_batched','matching_immutable_session','batched_driver','batched_journal',
       'batched_pair_executor','batched_numeric_execution','batched_numeric_reuse',
       'registered_offload','batched_offload_semantics','batched_pilot_reservations',
       'grouped_offload','grouped_offload_semantics','typed_payload_operations')
for name in roles:
    module=sys.modules['tradingagents.research.onchain_replication.'+name]
    assert Path(module.__file__).resolve()==R/'tradingagents/research/onchain_replication'/f'{name}.py'
# Reuse only fixture-construction statements from the previous focused check.
# No old matrix or RED test is rerun, and no fake Run/Owner is instantiated.
source=F/'mcm-batched-pilot-entry-integration01-2026-10-09/check01.py'
tree=ast.parse(source.read_bytes());start=next(i for i,n in enumerate(tree.body)
    if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='gate' for x in n.targets))
stop=next(i for i,n in enumerate(tree.body)
    if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='original' for x in n.targets))
ns={'ROOT':R,'HERE':source.parent,'hashlib':hashlib,'read':lambda p:json.loads(p.read_bytes())}
exec(compile(ast.Module(body=tree.body[start:stop],type_ignores=[]),str(source),'exec'),ns)
args=ns['args'];keys=ns['keys'];legacy=reservations.validate(*args)
start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
    and any(isinstance(x,ast.Name) and x.id=='n' for x in n.targets))
stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign)
    and any(isinstance(x,ast.Name) and x.id=='value' for x in n.targets))
import copy
ns.update(legacy=legacy,copy=copy)
exec(compile(ast.Module(body=tree.body[start:stop],type_ignores=[]),str(source),'exec'),ns)
selected=ns['selected'];selected[2]['schema_version']=6
selected[2]['batched'].update(group_batches=16,retention='typed-grouped-recover-before-retire-v1')
groups=0
for g in selected[5]['graphs'].values():
    batches=(g['rows']*32+4095)//4096;count=(batches+15)//16;groups+=count
    g['kinds']['mcm-batched-bundle-v3'].update(max_operations=2*count,max_chunks=3*count,
      max_preserved_bytes=count*4*1024**2,max_recovered_bytes=2*count*4*1024**2)
value=reservations.validate(*selected)
assert groups==6352 and value['batched_schema']==6 and value['physical_capacity_admitted'] is False
assert value['pair_occurrences']==legacy['pair_occurrences']
result={'decision':'PASS','installed_files':len(install['files']),
 'preloaded_roles':len(roles),'metadata_graphs':len(keys),'groups':groups,
 'original_cells':sum(value['pair_occurrences'].values()),
 'source_check_max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
 'scientific_arrays':False,'authority_instances':False,'claim':False,'whole_capacity_admitted':False}
(H/'INSTALLED_SMOKE01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':'PASS','roles':len(roles),'groups':groups,'claim':False}))
