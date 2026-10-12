"""Finite public/binder reconstruction. No binder/Git/runtime/data execution."""
import ast,copy,hashlib,json,os,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
B=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
OLD=F/'real-data-pilot-full36-binding-preparation01-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261012-38';OLDNAME='eth-paper-real-data-end-to-end-resource-20261011-36'
ANCHOR='1394d8b03163233df2fcefe658378e0f7b13424d'
pins={}
def raw(p):
 assert p.resolve()==p and not p.is_symlink()
 a=p.stat();assert stat.S_ISREG(a.st_mode)
 b=p.read_bytes();z=p.stat()
 assert (a.st_dev,a.st_ino,a.st_mode,a.st_nlink,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_mode,z.st_nlink,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 pins[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def load(p):return json.loads(raw(p))
def ref(p):raw(p);return {'path':str(p.relative_to(R)),**pins[str(p.relative_to(R))]}
def encode(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=load(B/'MANIFEST01.json')
for name,pin in manifest['files'].items():assert ref(B/name)==pin
joins=load(B/'CURRENT_NUMERICAL_GIT_JOIN01.json')
assert joins['source']==ANCHOR and joins['count']==len(joins['files'])==205 and joins['actual_git_batch_exit']==0 and joins['claim'] is False
reconstructed=hashlib.sha256();source_pins={}
for row in joins['files']:
 path=row['path'];b=raw(R/path);assert len(b)==row['bytes'] and sha(b)==row['sha256']
 oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert oid==row['git_oid']
 reconstructed.update((oid+' blob '+str(len(b))+'\n').encode()+b+b'\n');source_pins[path]=row['sha256']
assert len(source_pins)==205 and reconstructed.hexdigest()==joins['actual_git_batch_stdout_sha256']
job=R/'tradingagents/research/onchain_replication/job.py'
fn=next(n for n in ast.parse(raw(job)).body if isinstance(n,ast.FunctionDef) and n.name=='required_sources')
env={'Path':Path,'__file__':str(job)};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(job),'exec'),env)
assert set(env['required_sources']())==set(source_pins)
docs={p.stem:load(p) for p in (B/'public01').glob('*.json')}
old={p.stem:load(p) for p in (OLD/'public01').glob('*.json')}
assert set(docs)==set(old) and len(docs)==12
expected=copy.deepcopy(old)
expected['mcm_policy']['entry_qualification']['experiment_id']=NAME
expected['pair_policy']['numerical_source']={'commit':ANCHOR,'files':source_pins}
expected['archive_policy']['remote_namespace']='ethpilot-20261012-38'
expected['archive_transport']['namespace']='ethpilot-20261012-38'
for resources in (expected['pilot']['resource_policy'],expected['execution_job']['resources']):
 resources['storage_budget']['experiment']=NAME;resources['storage_budget']['roots'][1]=str(R/'research_runs'/NAME)
expected['pilot']['cell_id']='real-eth-first-graph-entry-preparation-resource38'
for descriptor in (expected['producer_plan']['producers']['original32']['descriptor'],expected['execution_job']['payload']['representation_jobs']['original32']['descriptor']):
 for role,key in (('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')):
  descriptor[key]['policy_sha256']=sha(encode(expected[role]))
assert docs==expected,'unlisted public semantic change'
accepted=load(F/'pilot-efficiency-integration-2026-10-12/SOURCE02.json')
changed={k:v for k,v in source_pins.items() if v!=old['pair_policy']['numerical_source']['files'].get(k)}
assert changed=={x['path']:x['after_sha256'] for x in accepted['changes']}
assert set(source_pins)==set(old['pair_policy']['numerical_source']['files'])
cores=['compact_policy','original_import','resource_population_plan','mcm_output_policy']
assert all(raw(B/'public01'/(x+'.json'))==raw(OLD/'public01'/(x+'.json')) for x in cores)
for k in ('decisions','graph_inputs','graph_sequences','batch_size','seed','lookback_days','model_execution','model_input','training_input','indices'):
 assert docs['pilot'][k]==old['pilot'][k]
assert len(docs['typed_payload']['graphs'])==7 and sum(v['rows']*32 for v in docs['typed_payload']['graphs'].values())==415968128
before=raw(OLD/'bind_actual01.py');after=raw(B/'bind_actual01.py')
assert after==before.replace(b'20261011-36',b'20261012-38')
assert ast.dump(ast.parse(after.replace(b'20261012-38',b'20261011-36')))==ast.dump(ast.parse(before))
binder=F/'real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py'
assert sha(raw(binder))=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
prepared=load(B/'PREPARED01.json');ep=load(OLD/'PREPARED01.json')
ep['builder03_result']['inputs']={k:v for k,v in docs.items() if k!='archive_policy'}
ep['builder03_spec']['references']['archive_policy']=ref(B/'public01/archive_policy.json');assert ep==prepared
request=load(B/'REQUEST01.json');er=load(OLD/'REQUEST01.json')
er.update(prepared=ref(B/'PREPARED01.json'),archive_policy=ref(B/'public01/archive_policy.json'),private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01');assert er==request
# Never open request.connection or any path named inside its target.
bound=load(B/'BOUND01.json');check=load(B/'BINDING_CHECK01.json')
assert bound['status']==check['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED'
assert bound['independent_approval'] is False and bound['source_request']==request
assert check['experiment']==NAME and not any(check[k] for k in ('claim','network','launch'))
for key in ('prepared','request','bound','binder'):
 assert ref(R/check[key]['path'])==check[key]
assert check['actual_opaque_input']==bound['private_input'] and check['all_input_roles']==73
eb={k:copy.deepcopy(v) for k,v in docs.items() if k!='archive_transport'}
bridge=bound['binding'];oldbound=load(OLD/'BOUND01.json')
assert bridge['transport_identity']==oldbound['binding']['transport_identity']
eb['archive_policy']['transport_identity']=bridge['transport_identity']
archive_sha=sha(encode(eb['archive_policy']))
assert bridge=={'archive_policy_sha256':archive_sha,'archive_role':'archive_policy','prior_descriptor_policy_sha256':sha(encode(docs['archive_policy'])),'transport_identity':bridge['transport_identity'],'transport_role':'archive_transport'}
for descriptor in (eb['producer_plan']['producers']['original32']['descriptor'],eb['execution_job']['payload']['representation_jobs']['original32']['descriptor']):
 descriptor['compact_archive_execution']['policy_sha256']=archive_sha
assert eb==bound['inputs']
assert set(p.stem for p in (B/'inputs01').glob('*.json'))==set(eb)
for role,value in eb.items():assert raw(B/'inputs01'/(role+'.json'))==encode(value)
public_refs=load(B/'PUBLIC_INPUT_REFS_DRAFT01.json');old_refs=load(OLD/'PUBLIC_INPUT_REFS_DRAFT01.json');all_refs=load(B/'ALL_INPUT_REFS01.json')
assert len(public_refs)==72 and len(all_refs)==73 and set(all_refs)==set(public_refs)|{'archive_transport'}
for role,pin in public_refs.items():
 if role in docs:assert pin=={'path':str((B/'public01'/(role+'.json')).relative_to(R)),'sha256':sha(encode(docs[role])),'dataset':'eth'}
 elif role=='expected_code_cache':assert pin=={'path':str((B/'EXPECTED_CODE_POLICY01.json').relative_to(R)),'sha256':sha(raw(B/'EXPECTED_CODE_POLICY01.json')),'dataset':'eth'}
 else:assert pin==old_refs[role]
expected_refs=copy.deepcopy(public_refs)
for role in eb:expected_refs[role]={'path':str((B/'inputs01'/(role+'.json')).relative_to(R)),'sha256':sha(encode(eb[role])),'dataset':'eth'}
opaque=bound['private_input']['archive_transport'];assert set(bound['private_input'])=={'archive_transport'}
assert opaque['path']==request['private_parent']+'/'+request['private_leaf']
expected_refs['archive_transport']={'path':opaque['path'],'sha256':opaque['sha256'],'dataset':'eth'};assert all_refs==expected_refs
for role,pin in all_refs.items():
 p=R/pin['path'];assert sha(raw(p))==pin['sha256']
 if role=='archive_transport':
  assert p.stat().st_size==opaque['bytes'] and stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_nlink==1
  assert stat.S_IMODE(p.parent.stat().st_mode)==0o700 and p.parent.stat().st_uid==os.getuid()
lease=ast.parse(raw(R/'tradingagents/research/onchain_replication/imported_authority_lease.py'))
policy=next(n.value for n in lease.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_POLICY' for t in n.targets))
assert load(B/'EXPECTED_CODE_POLICY01.json')==ast.literal_eval(policy)==load(OLD/'EXPECTED_CODE_POLICY01.json')
assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
assert not os.path.lexists(R/'research_runs'/NAME) and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261012-38')
result={'status':'ACCEPTED_PUBLIC_AND_BOUND_METADATA_ONLY','source_anchor':ANCHOR,'source_bodies':205,'public_documents':12,'all_roles':73,'changed_source_pins':changed,'whole_graph_cells':415968128,'scientific_cores_unchanged':cores,'binder_exact_namespace_only_inverse':True,'binder_source_sha256':'bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb','git_join_qualification':'Current source bytes independently match every retained SHA256/Git blob OID and reconstructed exact batch stdout digest. Commit/path lookup itself is inherited from authenticated Root receipt; no Git command was rerun.','opaque_qualification':'Only exact envelope raw digest/extent, path, stable identity and600/700 modes checked; never decoded. Original connection target and credential/key paths not opened.','not_admitted':['ResearchRun','native launch','entry timing qualification','whole-pilot capacity','increment recovery','empirical or financial fit'],'evidence':pins}
(P/'PUBLIC_BINDING_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','source_anchor','source_bodies','public_documents','all_roles','whole_graph_cells')}))
