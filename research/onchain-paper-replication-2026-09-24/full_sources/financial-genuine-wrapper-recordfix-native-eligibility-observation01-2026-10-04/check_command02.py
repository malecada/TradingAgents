import ast,hashlib,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;INV=BASE/'financial-genuine-wrapper-recordfix-launch-command-investigation01-2026-10-04';cmd=json.loads((INV/'COMMAND01.json').read_bytes());q=json.loads(Path(cmd['argv'][4]).read_bytes());root=Path(q['capsule_root']);parent=Path(q['parent_root']);checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
tree=ast.parse((root/'tradingagents/research/onchain_replication/job.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_command');ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual pure _command>','exec'),ns)
args=types.SimpleNamespace(root=str(root),registration=q['registration'],experiment=q['identity'],source=q['source']);actual=ns['_command'](args,'launch');check(actual==cmd['genuine_nested_job_argv'],'pure genuine command exactly reproduced without job import')
for name,h in q['helper_hashes'].items():check(sha((parent/name).read_bytes())==h,'installed helper '+name)
check(len(q['helper_hashes'])==6,'all six helper hashes')
ob=json.loads((HERE/'OBSERVATION01.json').read_bytes());r=ob['resources'];criteria={'observed_MemTotal_at_most_16GiB':r['MemTotal_bytes']<=16*1024**3,'observed_MemAvailable_at_least_6GiB':r['MemAvailable_bytes']>=6*1024**3,'observed_each_disk_at_least_10GiB':all(d['free']>=10*1024**3 for d in r['disks'].values()),'observed_affinity_has_at_least_two_CPUs':len(r['cpu_affinity'])>=2,'all_five_fixed_namespaces_observed_absent':all(not n['lexically_present'] for n in ob['fixed_namespaces']),'selected_active_units_observed_zero':all(u['active']=='failed' for u in ob['selected_systemd_units']),'selected_process_matches_observed_zero':not ob['proc']['matches']}
# A snapshot of predicates is not eligibility admission.
out={'checks':len(checks),'check_names':checks,'actual_reconstructed_nested_argv':actual,'snapshot_predicates':criteria,'observation_sha256':sha((HERE/'OBSERVATION01.json').read_bytes()),'dispatch_authority':False,'no_runtime_package_import':True,'actual_native_policy_instantiation':None}
with (HERE/'COMMAND_CHECK02.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'criteria':criteria}))
