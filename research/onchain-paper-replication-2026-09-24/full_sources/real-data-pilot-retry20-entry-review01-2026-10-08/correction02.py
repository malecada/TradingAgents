import json,hashlib,copy
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent;NAME='eth-paper-real-data-end-to-end-resource-20261008-20'
base=json.loads((H/'SOURCE_CLOSURE01.json').read_text());evidence=dict(base['evidence']);checks=[]
def read(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
def check(n,v):
 assert v,n
 checks.append(n)
a=load(N/'gate01.json');b=load(N/'gate02.json');old=a['experiments'][NAME];new=b['experiments'][NAME]
check('only_two_input_refs_changed',{k for k in old['inputs'] if old['inputs'][k]!=new['inputs'][k]}=={'compact_policy','mcm_policy'})
draft=load(N/'INPUT_DRAFT02.json');roles=set(load(N/'INPUT_REFS05.json'))
for role,v in draft['protocol']['references'].items():
 if role in new['inputs'] and role not in roles:check('unbound_reference_join_'+role,all(new['inputs'][role][k]==v[k] for k in ('path','sha256')))
check('all_refs06_exact',load(N/'ALL_INPUT_REFS06.json')==new['inputs'])
for role in ('compact_policy','mcm_policy'):
 v=new['inputs'][role];read(R/v['path']);check('corrected_hash_'+role,evidence[v['path']]==v['sha256'])
pair=load(R/new['inputs']['pair_policy']['path']);compact=load(R/new['inputs']['compact_policy']['path'])
check('runtime_pair_compact_limits_join',pair['limits']==compact['stage_policy']['pair'])
check('actual_runtime_sharded',compact['stage_policy']['pair']['checkpoint_layout']=={'format':'sharded-npy-v1','chunk_entries':262144})
check('actual_runtime_selected64MiB',compact['stage_policy']['restart_retention']['max_selected_input_json_bytes']==67108864)
check('actual_runtime_extraction_limit',load(R/new['inputs']['mcm_policy']['path'])['numeric']['extraction_limit']==350110)
expected=copy.deepcopy(a);e=expected['experiments'][NAME];e['inputs']=new['inputs'];e['source_files']=new['source_files'];check('gate_no_other_mutations',expected==b)
pre=read(N/'preflight02.py').decode();check('preflight02_exact_inverse',pre.replace("HERE/'gate02.json'","HERE/'gate01.json'")==read(N/'preflight01.py').decode())
check('rootio02_exact_inverse',read(N/'root_io02.py').decode().replace('from preflight02 import check','from preflight01 import check')==read(N/'root_io.py').decode())
expected=dict(old['source_files'])
for before,after in [('preflight01.py','preflight02.py'),('root_io.py','root_io02.py')]:
 del expected[str((N/before).relative_to(R))];expected[str((N/after).relative_to(R))]=hashlib.sha256((N/after).read_bytes()).hexdigest()
p=N/'correct_input_refs20.py';expected[str(p.relative_to(R))]=hashlib.sha256(read(p)).hexdigest()
check('exact_source_delta',expected==new['source_files'])
for path,h in new['source_files'].items():check('source_pin_'+path,hashlib.sha256((R/path).read_bytes()).hexdigest()==h);evidence[path]=h
x=load(N/'BINDING_DRAFT01.json');y=load(N/'BINDING_DRAFT02.json');x['gate']=y['gate'];check('binding_only_gate_changed',x==y)
for role in ('gate','draft','preparation','baseline','transport','transport_binding'):
 v=y[role];check('required_join_'+role,hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']);evidence[v['path']]=v['sha256']
# Keep actual fresh absence narrow and do not execute admission.
for p in load(N/'INITIAL_NAMESPACE_OBSERVATION01.json')['paths_absent']:check('still_absent_'+p,not (R/p).exists() and not (R/p).is_symlink())
load(N/'INPUT_REFERENCE_CORRECTION01.json')
v={'schema_version':1,'decision':'accepted','identity':NAME,'evidence':evidence,'accepted_gate':y['gate'],'checks':checks,'prior_checks':{'metadata_and_entry_checks':138,'inherited_changed_main_source_closure':21},'preserved_refusal':'BINDING_REFUSAL01.json','scope':'Exact corrected gate02 and binding draft02 diagnostic entry joins only. Ready for Root binding and final release sealing; no empirical admission, current committed-source proof, resource observation, native launch or financial conclusion. Full seven-stage capacity and MCM/update/fit remain incomplete. Existing sampled live-history and storage enforcement limitations remain unchanged.'}
(H/'BINDING_REVIEW01.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'ACCEPTED_CORRECTED_ENTRY_JOINS','checks':len(checks),'binding_review_sha256':hashlib.sha256((H/'BINDING_REVIEW01.json').read_bytes()).hexdigest()}))
