"""Actual fresh35 public binding only; private references never opened or stat'ed."""
import copy,hashlib,json,os,resource,signal,stat
from pathlib import Path,PurePosixPath
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];T=F/'real-data-pilot-full35-binding-preparation01-2026-10-11';NAME='eth-paper-real-data-end-to-end-resource-20261011-35';refs={};counts={}
def ck(v,n):assert v,n;counts[n]=counts.get(n,0)+1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);relative=str(p.relative_to(R));assert not relative.startswith(('research_artifacts/','research_runs/')) and p.name not in ('connection.json','.env','hf_token.txt') and not {'.git','.venv','keys','apis'}&set(p.parts)
 before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<4*1024**2
 b=p.read_bytes();after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
 refs[relative]={'bytes':len(b),'sha256':sha(b)};return b
def obj(p):return json.loads(read(p))
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def pin(p):b=read(p);return {'path':str(p.relative_to(R)),'bytes':len(b),'sha256':sha(b)}
G=F/'pilot35-generated-public-review01-2026-10-11/REVIEW01.json';generated=obj(G)
ck(sha(read(G))=='5d6a18d3cb1b1fc28d7875a596bf08d062314dd1092cd41f1952ff8466977cd6' and generated['decision']=='accepted','accepted generated-public review')
bound=obj(T/'BOUND01.json');check=obj(T/'BINDING_CHECK01.json');request=obj(T/'REQUEST01.json');prepared=obj(T/'PREPARED01.json');draft=obj(T/'PUBLIC_INPUT_REFS_DRAFT01.json');actual=obj(T/'ALL_INPUT_REFS01.json')
ck(len(actual)==72 and len(draft)==71 and set(actual)==set(draft)|{'archive_transport'},'complete72 reference denominator')
for role,value in actual.items():
 q=PurePosixPath(value['path']);ck(set(value)=={'path','sha256','dataset'} and value['dataset']=='eth' and not q.is_absolute() and '..' not in q.parts and str(q)==value['path'] and len(value['sha256'])==64 and all(c in '0123456789abcdef' for c in value['sha256']),'strict canonical input references')
ck(check['status']==bound['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and bound['independent_approval'] is False and check['experiment']==NAME and check['all_input_roles']==72 and all(check[k] is False for k in ('claim','launch','network')),'actual nonadmitted binding status')
ck(bound['source_request']==request and check['actual_opaque_input']==bound['private_input'],'request and opaque metadata joins')
for field,name in [('bound','BOUND01.json'),('prepared','PREPARED01.json'),('request','REQUEST01.json')]:ck(check[field]==pin(T/name),'actual check body joins')
binder=R/check['binder']['path'];ck(pin(binder)==check['binder'] and check['binder']['sha256']=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb','unchanged accepted binder body')
ck(request['prepared']==pin(T/'PREPARED01.json') and request['archive_policy']==pin(T/'public01/archive_policy.json'),'actual public request pins')
for name in ('PREPARED01.json','REQUEST01.json','PUBLIC_INPUT_REFS_DRAFT01.json','MANIFEST01.json'):
 relative=str((T/name).relative_to(R));r=pin(T/name);accepted=generated['references'][relative];ck(r['sha256']==accepted['sha256'] and r['bytes']==accepted['bytes'],'accepted generated input unchanged')
private=bound['private_input'];ck(set(private)=={'archive_transport'},'exact one opaque role')
opaque=private['archive_transport'];ck(set(opaque)=={'path','sha256','bytes'} and opaque['path']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-35-01/archive_transport01.json' and type(opaque['bytes']) is int and 0<opaque['bytes']<=4*1024**2 and all(actual['archive_transport'][k]==opaque[k] for k in ('path','sha256')),'opaque canonical metadata only')
ck(request['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-35-01' and request['private_leaf']=='archive_transport01.json','fresh35 private reference namespace')
docs=bound['inputs'];ck(len(docs)==11 and set(docs)<=set(draft),'eleven public bound documents')
ck({p.name for p in (T/'inputs01').iterdir()}=={role+'.json' for role in docs},'exact bound public file roster')
for role,doc in docs.items():
 path=T/'inputs01'/(role+'.json');b=read(path);ck(b==raw(doc) and actual[role]=={'path':str(path.relative_to(R)),'sha256':sha(b),'dataset':'eth'},'canonical published bound documents')
unchanged=set(draft)-set(docs)
ck(len(unchanged)==60 and all(actual[k]==draft[k] for k in unchanged),'sixty unchanged public reference rows reused without historical reads')
bridge=bound['binding'];archive=docs['archive_policy'];unbound=obj(T/'public01/archive_policy.json')
ck(archive['remote_namespace']=='ethpilot-20261011-35' and sha(raw(archive))==bridge['archive_policy_sha256']==actual['archive_policy']['sha256'] and archive['transport_identity']==bridge['transport_identity'],'actual bound archive identity hash')
inverted=copy.deepcopy(docs);arch=inverted.pop('archive_policy');arch['transport_identity']=None;ck(arch==unbound,'archive literal inverse')
selected=next(iter(inverted['execution_job']['payload']['representation_jobs'].values()));producer=inverted['producer_plan']['producers'][selected['producer']]
for item in (selected,producer):
 ck(item['compact_archive_transport_input']=='archive_transport' and item['descriptor']['compact_archive_execution']=={'backend':archive['backend'],'policy_sha256':bridge['archive_policy_sha256']},'both actual archive descriptor joins')
 ck(item['descriptor']['pair_execution']['policy_sha256']==actual['pair_policy']['sha256'],'both actual pair descriptor joins')
 item['descriptor']['compact_archive_execution']['policy_sha256']=bridge['prior_descriptor_policy_sha256']
expected=prepared['builder03_result']['inputs'];ck(expected['archive_transport']['connection'] is None,'prepared opaque body placeholder remains unbound')
inverted['archive_transport']=expected['archive_transport'];ck(inverted==expected,'complete binder three-change inverse; no science or budget changes')
edge=docs['mcm_policy']['batched']['execution'];policy=edge['compiled_edge_policy'];roles=edge['compiled_edge_inputs'];ck(roles=={kind:'compiled_edge_'+kind for kind in ('source','adapter','library','runtime','abi')},'exact five backend roles')
for kind,role in roles.items():
 value=actual[role];ck(str(R/value['path'])==policy[kind+'_path'] and value['sha256']==policy[kind+'_sha256'],'backend role policy join')
 b=read(R/value['path']);ck(sha(b)==value['sha256'],'actual public backend opaque bytes')
 if kind in ('runtime','abi'):ck(len(b)==policy[kind+'_bytes'],'backend metadata exact extents')
numerical=docs['pair_policy']['numerical_source'];ck(numerical['commit']=='53b8890630765d06f8a44e3e8fbaee1f4b00bdfb' and len(numerical['files'])==200,'current200 numerical source metadata')
for name,h in numerical['files'].items():
 ck(name.startswith('tradingagents/') and sha(read(R/name))==h,'actual current source bodies')
# Current bodies are authenticated here; recorded committed Git joins are reused
# from the accepted generated-public review, with no new Git operation.
result={'decision':'ACCEPT_ACTUAL_PUBLIC_BINDING_ONLY_PENDING_FINAL_ENTRY','identity':NAME,'counts':{'all_roles':72,'opaque_reference_only':1,'bound_public_documents':11,'unchanged_public_reference_rows':60,'backend_roles':5,'current_source_bodies':200},'check_category_counts':counts,'references':refs,'input_refs':{k:{f:v[f] for f in ('path','sha256')} for k,v in actual.items()},'opaque_reference_metadata':opaque,'actual_tool_observation':{'chunk_id':'686c44','exit_code':0,'status':'BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED','all_roles':72,'claim':False,'network':False,'basis':'Original trusted Root tool observation supplied in task; output/body joins checked separately. File presence alone is not execution attestation.'},'next_entry_preparation':'Public binding joins permit reviewed Root source/registration preparation; final fresh scratch, gate, source/evidence closure and release remain absent from this preliminary decision.','limits':['No private dispatch or connection/key/credential path was opened, hashed, stat-ed or resolved. Opaque bytes/mode/existence/identity proof reused only as published metadata and accepted binder execution context.','No old graph/dictionary/sample/price/claim bodies reopened; their exact unchanged reference rows inherit accepted generated-public review.','No Git, binder, native, scientific, Admission, genuine Owner or claim execution. Current200 source hashes verified; committed joins reuse accepted generated-public evidence.','No final gate/full entry approval, current resource capacity, numerical outcome or empirical authority.']}
with (P/'BINDING_CHECK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':result['decision'],'counts':result['counts'],'checks':sum(counts.values())},sort_keys=True))
