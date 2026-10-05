from pathlib import Path
import ast,copy,hashlib,json,sys
D=Path(__file__).resolve().parent;M=D.parents[3];F=D.parent;E=F/'real-data-pilot-first-graph01-2026-10-05';P=Path('tradingagents/research/onchain_replication')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
a=read(E/'gate01.json');b=read(E/'gate02.json');name='eth-paper-real-pilot-graph-20220502-20261005-01'
assert h(E/'gate02.json')=='56b420d1df16f2406f4147a9b81a810e090db14ab25a4397839df3f9ad964a1b'
old=a['experiments'][name]['source_files'];new=b['experiments'][name]['source_files'];normalized=copy.deepcopy(b);normalized['experiments'][name]['source_files']=old;assert normalized==a
r=read(E/'SOURCE_REBIND02.json');assert sorted(set(new)-set(old))==r['added_source_pins'];assert not set(old)-set(new)
changes={p:{'before':old[p],'after':new[p]} for p in old if old[p]!=new[p]};assert changes==r['changed_source_pins'];assert len(old)==150 and len(new)==167 and len(changes)==9
for p,pin in new.items():assert h(M/p)==pin,p
A=F/'real-data-pilot-main-import-authority-port01-2026-10-05';delta=read(A/'SOURCE_DELTA01.json')
for item in delta['changed']+delta['reused']:
 p=Path(item['path']);assert (M/p).read_bytes()==(A/'candidate'/p).read_bytes()
for p,pin in delta['main_unchanged_package'].items():assert h(M/p)==pin
oldpre=(E/'preflight01.py').read_text();newpre=(E/'preflight02.py').read_text();assert newpre.replace('gate02.json','gate01.json').replace('RELEASE_REVIEW02.json','RELEASE_REVIEW01.json')==oldpre
assert (E/'launch02.py').read_text().replace('from preflight02 import','from preflight01 import')==(E/'launch01.py').read_text()
# Execute only actual pure source-enumeration function; no package imports/admission.
jobpath=M/P/'job.py';t=ast.parse(jobpath.read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');env={'Path':Path,'__file__':str(jobpath)};exec(compile(ast.Module(body=[f],type_ignores=[]),str(jobpath),'exec'),env);required=env['required_sources']();assert required<=set(new)
namespace=[M/'research_runs'/name,M/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name,M/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/name,E/'launch-attempt01.json',E/'outer-exit01.json']
for p in namespace:assert not p.exists() and not p.is_symlink(),str(p)
prior=read(E/'RELEASE_REVIEW01.json');expected_drift={str(P/'job.py'),str(P/'resources.py')}
actual_drift={p for p,pin in prior['evidence'].items() if h(M/p)!=pin};assert actual_drift==expected_drift,actual_drift
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
print(json.dumps({'decision':'pass','gate_sha256':h(E/'gate02.json'),'unchanged_non_source_registration':True,'prior_source_pins':150,'current_source_pins':167,'new_pins':17,'changed_pins':9,'complete_current_required_sources':len(required),'exact_adopted_candidate_bodies':24,'unchanged_Main_bodies':126,'preflight_literal_inverse':True,'launch_literal_inverse':True,'prior_72_evidence_drift_only':sorted(actual_drift),'unused_namespace_paths':[str(p.relative_to(M)) for p in namespace],'numerical_imports':False,'admission_or_native_execution':False,'resource_eligibility_tested':False},sort_keys=True,indent=2))
