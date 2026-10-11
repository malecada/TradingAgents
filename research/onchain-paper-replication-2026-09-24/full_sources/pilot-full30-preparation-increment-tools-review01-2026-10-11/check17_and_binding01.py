"""Actual PUBLIC binding and frozen17 source/refusal checks. No private access."""
import ast,copy,datetime,difflib,hashlib,json,os,resource,signal,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];C=F/'real-data-pilot-full30-binding-preparation01-2026-10-11';D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full30increment17'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(20,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(25)
checks=[];refs={};total=0
def ck(v,n):
    assert v,n
    checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    global total
    p=Path(p);assert not {'keys','apis','.git','.venv','real_pilot_runtime'}&set(p.parts) and p.name not in {'connection.json','.env','hf_token.txt'}
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=2*1024**2
    b=p.read_bytes();total+=len(b);assert total<12*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
release=F/'real-data-pilot-full30-binding-review01-2026-10-11/REVIEW01.json';ck(sha(read(release))=='7bd51953fabb0d2484355743b60ec3320644a790392da11b1c5504c57d20f4a9','accepted exact binding source/caller anchor')
ck(sha(read(C/'MANIFEST01.json'))=='fc60e0198aea3e77e9cea5419d448a25882b66ca83b81461d23c2621ff2af9e8','binding source frozen manifest unchanged')
for name,pin in js(C/'MANIFEST01.json')['files'].items():
    b=read(C/name);ck({'bytes':len(b),'sha256':sha(b)}==pin,'unchanged binding source member '+name)
bound=js(C/'BOUND01.json');receipt=js(C/'BINDING_CHECK01.json');request=js(C/'REQUEST01.json');prepared=js(C/'PREPARED01.json');allrefs=js(C/'ALL_INPUT_REFS01.json');draft=js(C/'PUBLIC_INPUT_REFS_DRAFT01.json')
for name in ('binder','prepared','request','bound'):
    pin=receipt[name];b=read(R/pin['path']);ck(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'actual binding receipt join '+name)
ck(bound['status']==receipt['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and bound['independent_approval'] is False and receipt['claim'] is receipt['launch'] is receipt['network'] is False,'actual unadmitted no-launch binding status')
ck(bound['source_request']==request and receipt['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-30','actual Root request and fresh identity')
ck(set(bound['private_input'])=={'archive_transport'} and bound['private_input']==receipt['actual_opaque_input'],'opaque returned-reference only join')
opaque=bound['private_input']['archive_transport'];ck(opaque['path']==request['private_parent']+'/'+request['private_leaf'] and opaque['bytes']==930 and len(opaque['sha256'])==64,'new opaque metadata identity/extent (no target inspection)')
ck(allrefs['archive_transport']=={'path':opaque['path'],'sha256':opaque['sha256'],'dataset':'eth'},'opaque67th reference is exact returned metadata')
ck(len(allrefs)==receipt['all_input_roles']==67 and len(draft)==66 and set(allrefs)==set(draft)|{'archive_transport'},'actual full67 role denominator')
inputs=bound['inputs'];ck(set(inputs)==set(prepared['builder03_result']['inputs'])-{'archive_transport'}|{'archive_policy'},'actual11 public returned roles')
ck({x.name for x in (C/'inputs01').iterdir()}=={role+'.json' for role in inputs},'exact inputs01 file denominator')
for role,doc in inputs.items():
    p=C/'inputs01'/(role+'.json');b=read(p);ck(b==raw(doc) and allrefs[role]=={'path':str(p.relative_to(R)),'sha256':sha(b),'dataset':'eth'},'actual public serialized body/reference '+role)
for role in set(draft)-set(inputs):ck(allrefs[role]==draft[role],'unchanged inherited public reference '+role)
archive=inputs['archive_policy'];bridge=bound['binding'];ck(archive['transport_identity']==bridge['transport_identity'] and len(bridge['transport_identity'])==64 and sha(raw(archive))==bridge['archive_policy_sha256'],'actual archive identity/hash metadata join')
restored=copy.deepcopy(archive);restored['transport_identity']=None;ck(restored==js(C/'public01/archive_policy.json'),'actual archive only identity binding change')
restored=copy.deepcopy(inputs);restored.pop('archive_policy');original=prepared['builder03_result']['inputs'];restored['archive_transport']=original['archive_transport']
for route in (restored['execution_job']['payload']['representation_jobs']['original32'],restored['producer_plan']['producers']['original32']):route['descriptor']['compact_archive_execution']['policy_sha256']=bridge['prior_descriptor_policy_sha256']
ck(restored==original,'complete independent actual public transform inverse')
job=inputs['execution_job'];selected=job['payload']['representation_jobs']['original32'];producer=inputs['producer_plan']['producers']['original32']
ck(selected['descriptor']==producer['descriptor'] and inputs['pilot']['resource_policy']==job['resources'],'actual two descriptors and resource policy agree')
for field,role in [('compact_archive_execution','archive_policy'),('compact_execution','compact_policy'),('pair_execution','pair_policy')]:ck(selected['descriptor'][field]['policy_sha256']==sha(raw(inputs[role])),'actual descriptor body hash '+role)
ck(archive['remote_namespace']=='ethpilot-20261011-30' and job['resources']['storage_budget']['experiment']==receipt['experiment'],'actual public fresh30 namespace')
execution=inputs['mcm_policy']['batched']['execution'];policy=execution['compiled_normalization_policy'];roles=execution['compiled_normalization_inputs']
for kind,role in roles.items():
    pin=allrefs[role];ck(str(R/pin['path'])==policy[kind+'_path'] and pin['sha256']==policy[kind+'_sha256'] and sha(read(R/pin['path']))==pin['sha256'],'current public compiled body/ref '+kind)
scratch=allrefs['matching_ordered_edge_scratch'];ck(sha(read(R/scratch['path']))==scratch['sha256'],'actual scratch reference body')
sc=js(R/scratch['path']);ck(sc['experiment']==receipt['experiment'] and 'historical_integration_review' in sc and 'current_integration_review' not in sc,'scratch fresh identity keeps historical attribution')
baseline_review=F/'pilot29-terminal-outcome-review01-2026-10-11/tools16/returned01/REVIEW01.json';ck(sha(read(baseline_review))=='1d9e3fc85ac365fc91e1f21214cf2d20107bbe530b22a901af2ad3d12df62a1d','accepted actual16 return review anchor')
base=js(D.parent/'outcome16/FRESH_GIT_RECOVERY16.json');cap=js(R/base['capture']['path']);selection=js(D.parent/'outcome16/SELECTION16.json')
ck(base['source']==base['actual_remote_head']==base['actual_fetch_head']=='41b55367bd226c7292c1f4a802c200cc5cd1f841' and sha(read(R/base['capture']['path']))==base['capture']['sha256'] and sha(read(D.parent/'outcome16/SELECTION16.json'))==cap['selection']['sha256'],'accepted16 baseline receipt/source/capture/selection chain')
manifest=js(D/'HELPERS_MANIFEST01.json');ck(sha(read(D/'HELPERS_MANIFEST01.json'))=='361d13039a4a9081ea445960e9c25480cf9c200ebfdc6868595fb353a8535ee1','frozen17 manifest observed pin');sources={};patch=[]
for name,pin in manifest['files'].items():
    b=read(D/name);ck({'bytes':len(b),'sha256':sha(b)}==pin,'frozen17 member '+name)
for kind,pin in manifest['origins'].items():
    old=read(R/pin['path']);ck(sha(old)==pin['sha256'],'accepted14 source origin '+kind);new=read(D/(kind+'17.py'));sources[kind]=new.decode();ast.parse(new)
for kind in ('select','capture','recover'):
    path=R/manifest['origins'][kind]['path'];new=D/(kind+'17.py');patch.extend(difflib.unified_diff(read(path).decode().splitlines(True),read(new).decode().splitlines(True),fromfile=str(path.relative_to(R)),tofile=str(new.relative_to(R))))
ck(''.join(patch).encode()==read(D/'LITERAL_PATCH01.diff'),'exact14-to17 declared patch reencoding')
tree=ast.parse(sources['select']);owned=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owned' for t in n.targets));ck(owned==manifest['owned'] and len(owned)==8,'exact eight owned17 public directories')
explicit=next(ast.literal_eval(n.iter) for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='name' and isinstance(n.iter,ast.Tuple))
missing=[name for name in explicit if not (D/name).exists()];ck(missing==['capture14.py','recover14.py'],'confirmed frozen17 actual missing-member refusal')
ck('LITERAL_PATCH01.diff' not in explicit,'patch depends only on future Git-derived inclusion')
ck("out=D/'fresh-git-recovered-full29increment14.tar'" in sources['recover'],'stale returned basename isolated to17 directory')
for fragment in ['scopes=[]',"'.git', '.venv', 'node_modules', 'keys', 'apis'",'before.st_nlink == 1','before.st_size <= 64*1024**2',"prior.parent/'SELECTION16.json'",'names-excluded-set(reused)']:
    ck(fragment in sources['select'],'retained selector scope/guard '+fragment)
exclusions=[cap['archive']['path'],base['returned_archive']['path'],str((D.parent/'outcome16/actual_external_archive_blob_return.stdout').relative_to(R))]
ck(len(set(exclusions))==3 and base['returned_archive']['sha256']==cap['archive']['sha256']=='aa118384a578c7e66c2080ce8f4ffb823b9db69e75fb309d5b41e64c7bb1e827','exact three accepted16 duplicate archive exclusions')
for name in ['SELECTION17.json','CAPTURE17.json','full30-preparation-increment17.tar','FRESH_GIT_RECOVERY17.json']:
    ck(not (D/name).exists(),'17 actual operation not yet executed '+name)
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binding_decision':'ACCEPT_ACTUAL_PUBLIC_BINDING67_REFERENCE_JOIN_ONLY','tools17_decision':'WITHHOLD_FROZEN17_MISSING_EXPLICIT_HELPERS','checks':checks,'references':refs,'read_bytes':total,'public_refs':66,'total_refs':67,'opaque_input_reference_only':opaque,'opaque_target_read_hash_stat':False,'missing17_paths':[str((D/name).relative_to(R)) for name in missing],'exact_prior16_duplicate_exclusions':exclusions,'selector_capture_recovery_executed':False,'limitations':['Inherited unchanged historical/scientific references were joined to accepted public draft metadata, not all reopened.','Opaque returned transport body/actual endpoint/currentness excluded from read/hash/stat; only public references authenticate.','No final gate/source/native/accounting/admission/financial claim.','Frozen17 cannot execute successfully; preserve it and review a corrected new successor.']}
with (P/'BINDING_AND_TOOLS17_REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','opaque_input_reference_only','exact_prior16_duplicate_exclusions','limitations')}));print('checks',len(checks))
