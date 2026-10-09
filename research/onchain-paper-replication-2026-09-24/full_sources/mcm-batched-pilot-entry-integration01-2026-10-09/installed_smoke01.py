"""Actual installed source/preload check; no empirical data or authority."""
import hashlib,json,os,resource,signal,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
signal.alarm(60)
os.nice(10);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
R=Path.cwd();H=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
m=json.loads((H/'MANIFEST01.json').read_bytes())
base=R/'tradingagents/research/onchain_replication'
for name,pin in m['files'].items():
    assert hashlib.sha256((base/name).read_bytes()).hexdigest()==pin
from tradingagents.research.onchain_replication import real_pilot_import_caller as caller
caller._prepare_lease_modules(batched=True)
roles=('compact_mcm_batched','matching_immutable_session','batched_driver',
       'batched_journal','batched_pair_executor','batched_numeric_execution',
       'batched_numeric_reuse','registered_offload','batched_offload_semantics',
       'batched_pilot_reservations')
pins={}
for name in roles:
    module=sys.modules['tradingagents.research.onchain_replication.'+name]
    path=base/(name+'.py');assert Path(module.__file__).resolve()==path.resolve()
    pins[name]=hashlib.sha256(path.read_bytes()).hexdigest()
result={'decision':'PASS','actual_installed_preload_roles':pins,
        'source_check_max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'numerical_arrays_opened':False,'authority_instances':False,'claim':False,
        'whole_capacity_admitted':False}
(H/'INSTALLED_SMOKE01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':'PASS','roles':len(pins),'claim':False}))
