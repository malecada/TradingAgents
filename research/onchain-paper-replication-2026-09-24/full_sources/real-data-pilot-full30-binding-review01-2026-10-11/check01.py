"""Public source/reference checks only. No binding/private metadata operations."""
import ast,copy,datetime,difflib,hashlib,json,os,resource,signal,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];C=F/'real-data-pilot-full30-binding-preparation01-2026-10-11';B=F/'real-data-pilot-full29-transport-binding01-2026-10-09'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(20,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(25)
checks=[];refs={};total=0
def ck(v,n):
    assert v,n
    checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    global total
    p=Path(p);assert not {'keys','apis','.git','.venv','real_pilot_runtime'}&set(p.parts) and p.name not in {'connection.json','.env','hf_token.txt'}
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=2*1024**2
    b=p.read_bytes();total+=len(b);assert total<12*1024**2
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
mb=read(C/'MANIFEST01.json');ck(sha(mb)=='fc60e0198aea3e77e9cea5419d448a25882b66ca83b81461d23c2621ff2af9e8','external frozen preparation manifest');m=json.loads(mb)
for name,pin in m['files'].items():
    b=read(C/name);ck({'bytes':len(b),'sha256':sha(b)}==pin,'frozen candidate '+name)
binder=read(R/m['binder']['path']);ck(sha(binder)==m['binder']['sha256']=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb','accepted unchanged binder body')
reviewb=read(F/'real-data-pilot-full29-final-entry-review01-2026-10-09/BINDING_REVIEW02.json');ck(sha(reviewb)=='28bfc0b4f80f4d8a063f0f9008259b32c125a1ad78a1a14579ec98142e90beda','accepted29 binding review anchor');review=json.loads(reviewb)
ck(review['decision']=='accepted' and review['evidence'][m['binder']['path']]==sha(binder),'accepted binder reuse join')
correction=js(B/'BINDER_DEPENDENCY_CORRECTION01.json');ck(sha(read(B/'BINDER_DEPENDENCY_CORRECTION01.json'))=='6a4e6816e0df9709b2359d0cdcb1c36d3e07547334f136ad35cc8bf9b0edd297','accepted binder dependency correction')
dependencies=js(B/'binder02/DEPENDENCIES01.json');ck(dependencies==correction['current_dependencies'],'exact accepted dependency map')
for name,pin in dependencies.items():ck(sha(read(R/pin['path']))==pin['sha256'],'current public binder dependency '+name)
origins=js(C/'ORIGINS01.json');old={};docs={}
for role,pin in origins['public_templates'].items():
    b=read(R/pin['path']);ck({'bytes':len(b),'sha256':sha(b),'path':pin['path']}==pin,'public origin '+role);old[role]=json.loads(b);docs[role]=js(C/'public01'/(role+'.json'))
for role in ('root_job','root_mcm','root_gate','scratch','connection_metadata_only'):
    pin=origins[role];b=read(R/pin['path']);ck({'bytes':len(b),'sha256':sha(b),'path':pin['path']}==pin,'public origin '+role)
request=js(C/'REQUEST01.json');oldrequest=js(R/origins['connection_metadata_only']['path'])
ck(request['connection']==oldrequest['connection'] and request['connection']['bytes']==485,'connection PUBLIC metadata copied only')
ck(request['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-30-01' and request['private_leaf']=='archive_transport01.json','exact new opaque output route names')
prepared=js(C/'PREPARED01.json');ck(prepared['status']==prepared['builder03_result']['status']=='DRAFT_NOT_REGISTERED_NOT_ADMITTED' and prepared['independent_approval'] is False,'unadmitted draft status')
ck(prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'},'all exact prepared public bodies')
ck(prepared['builder03_spec']['template_roles']=={'archive':'archive_policy','job':'execution_job','producer_plan':'producer_plan'},'exact binder role map')
for role in ('prepared','archive_policy'):
    pin=request[role];b=read(R/pin['path']);ck(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'actual request reference '+role)
ck(prepared['builder03_spec']['references']['archive_policy']==request['archive_policy'],'prepared archive request pin join')
ck(docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None,'public draft remains unbound')
for role,key in [('archive_transport','namespace'),('archive_policy','remote_namespace')]:
    restored=copy.deepcopy(docs[role]);ck(restored[key]=='ethpilot-20261011-30','fresh30 namespace '+role);restored[key]=old[role][key];ck(restored==old[role],'only namespace changes '+role)
job=docs['execution_job'];selected=job['payload']['representation_jobs']['original32'];producer=docs['producer_plan']['producers']['original32']
ck(set(job['payload']['representation_jobs'])=={'original32'} and selected['descriptor']==producer['descriptor'],'single original32 actual job/producer join')
ck(selected['plan_input']=='producer_plan' and selected['compact_archive_input']==producer['compact_archive_input']=='archive_policy' and selected['compact_archive_transport_input']==producer['compact_archive_transport_input']=='archive_transport','binder selected roles compatible')
for key,role in [('compact_archive_execution','archive_policy'),('compact_execution','compact_policy'),('pair_execution','pair_policy')]:ck(selected['descriptor'][key]['policy_sha256']==sha(raw(docs[role])),'canonical descriptor policy join '+role)
ck(docs['pilot']['resource_policy']==job['resources'],'pilot agrees with actual fresh job resource policy')
restored=copy.deepcopy(docs['pilot']);restored['resource_policy']=old['pilot']['resource_policy'];ck(restored==old['pilot'],'pilot science unchanged')
restored=copy.deepcopy(job);restored['payload']['representation_jobs']['original32']['descriptor']=old['execution_job']['payload']['representation_jobs']['original32']['descriptor'];restored['resources']['storage_budget']['experiment']=old['execution_job']['resources']['storage_budget']['experiment'];restored['resources']['storage_budget']['roots']=old['execution_job']['resources']['storage_budget']['roots'];ck(restored==old['execution_job'],'job limits/science unchanged outside declared identity/policy join')
ck(job['resources']['storage_budget']['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-30','fresh job storage experiment')
ck([p.replace('20261009-29','20261011-30') for p in old['execution_job']['resources']['storage_budget']['roots']]==job['resources']['storage_budget']['roots'],'only29-to30 storage root change')
for role in ('compact_policy','pair_policy','original_import','resource_population_plan','typed_payload','mcm_output_policy'):ck(docs[role]==old[role],'unchanged science/policy '+role)
restored=copy.deepcopy(docs['producer_plan']);restored['producers']['original32']['descriptor']=old['producer_plan']['producers']['original32']['descriptor'];ck(restored==old['producer_plan'],'producer only declared descriptor join')
restored=copy.deepcopy(docs['mcm_policy']);execution=restored['batched']['execution'];compiled=execution.pop('compiled_normalization_policy');compiledroles=execution.pop('compiled_normalization_inputs');ck(restored==old['mcm_policy'],'MCM science/caps unchanged except explicit compiled selection')
ck(docs['mcm_policy']==js(R/origins['root_mcm']['path']),'Root selected MCM policy retained')
publicrefs=js(C/'PUBLIC_INPUT_REFS_DRAFT01.json');gate=js(R/origins['root_gate']['path']);NAME='eth-paper-real-data-end-to-end-resource-20261011-30';oldrefs=gate['experiments'][NAME]['inputs']
ck(len(publicrefs)==66 and len(oldrefs)==67 and set(publicrefs)==set(oldrefs)-{'archive_transport'},'exact66 public plus opaque67th role denominator')
changed=set(docs)-{'archive_transport'}|{'matching_ordered_edge_scratch'}
for role,pin in publicrefs.items():
    if role not in changed:ck(pin==oldrefs[role],'unchanged inherited PUBLIC reference '+role)
    else:
        expected=C/'public01'/(role+'.json') if role!='matching_ordered_edge_scratch' else C/'MATCHING_SCRATCH_RESERVATION01.json';ck(pin=={'path':str(expected.relative_to(R)),'sha256':sha(read(expected)),'dataset':'eth'},'fresh concrete PUBLIC reference '+role)
ck(set(compiledroles)=={'source','library','runtime'},'three exact compiled roles')
for kind,role in compiledroles.items():ck(str(R/publicrefs[role]['path'])==compiled[kind+'_path'] and publicrefs[role]['sha256']==compiled[kind+'_sha256'],'compiled role policy join '+kind)
returned_public=set(prepared['builder03_result']['inputs'])-{'archive_transport'}|{'archive_policy'}
ck(returned_public<=set(publicrefs) and len(set(publicrefs)|{'archive_transport'})==67,'actual binder output role compatibility')
scratch=js(C/'MATCHING_SCRATCH_RESERVATION01.json');oldscratch=js(R/origins['scratch']['path']);restored=copy.deepcopy(scratch)
for k in ('experiment','installed_source','qualification'):restored[k]=oldscratch[k]
restored['current_integration_review']=restored.pop('historical_integration_review');ck(restored==oldscratch,'scratch inverse keeps every actual cap')
ck(scratch['experiment']==NAME and scratch['installed_source']['sha256']=='eb509ecf5c9ed7d28783b1a4230013ddcba8036a0fb5174d3aaa60307fc63b43' and sha(read(R/scratch['installed_source']['path']))==scratch['installed_source']['sha256'],'scratch exact fresh identity/current source')
# Independent reconstruction of the declared unified patch, without patch execution.
diff=[]
for role,pin in sorted(origins['public_templates'].items()):
    a=R/pin['path'];b=C/'public01'/(role+'.json');diff.extend(difflib.unified_diff(read(a).decode().splitlines(True),read(b).decode().splitlines(True),fromfile=str(a.relative_to(R)),tofile=str(b.relative_to(R))))
a=R/origins['scratch']['path'];b=C/'MATCHING_SCRATCH_RESERVATION01.json';diff.extend(difflib.unified_diff(read(a).decode().splitlines(True),read(b).decode().splitlines(True),fromfile=str(a.relative_to(R)),tofile=str(b.relative_to(R))))
ck(''.join(diff).encode()==read(C/'PUBLIC_LITERAL_PATCH01.diff'),'exact public diff reencoding/inverse evidence')
wrapper=read(C/'bind_actual01.py').decode();tree=ast.parse(wrapper);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');lines=ast.unparse(main)
for token in ["load(HERE / 'REQUEST01.json')","HERE / 'BOUND01.json'","HERE / 'inputs01'","HERE / 'ALL_INPUT_REFS01.json'","HERE / 'BINDING_CHECK01.json'",'not os.path.lexists(p)','parent.mkdir(mode=448, exist_ok=False)','module.bind(ROOT, request)',"ref(HERE / 'REQUEST01.json')","ref(HERE / 'BOUND01.json')","len(refs) == 67"]:ck(token in lines,'wrapper one-use/caller seam '+token)
ck(lines.index('not os.path.lexists(p)')<lines.index('parent.mkdir(')<lines.index('module.bind(ROOT, request)')<lines.index("save(HERE / 'BOUND01.json'"),'all freshness guards before atomic parent creation/bind/public output')
ck('REQUEST02' not in wrapper and 'BOUND02' not in wrapper and '.unlink' not in wrapper and 'rmtree' not in wrapper,'consistent01 names; no cleanup/deletion/retry')
ck("with p.open('xb')" in wrapper and 'types.ModuleType' in wrapper and "module.__file__=str(BINDER)" in wrapper,'exclusive reports and correct pinned binder module location')
for p in [R/'research_runs'/NAME,R/'research_artifacts/archive-dispatch-ethpilot-20261011-30',C/'BOUND01.json',C/'inputs01',C/'ALL_INPUT_REFS01.json',C/'BINDING_CHECK01.json']:
    ck(not os.path.lexists(p),'fresh public/claim namespace absent '+str(p.relative_to(R)))
# Only the NEW parent is checked for absence. No historical/private/connection target is statted.
ck(not os.path.lexists(R/request['private_parent']),'new declared private parent absent only')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_FROZEN_PUBLIC_SOURCE_AND_EXACT_ENTRY','checks':checks,'references':refs,'read_bytes':total,'public_roles':66,'required_bound_roles':67,'binder_imported_or_executed':False,'original_private_connection_key_metadata_or_bodies_touched':False,'new_private_parent_absence_only':True,'limits':{'cpu_seconds':20,'address_space_bytes':512*1024**2,'alarm_seconds':25,'per_output_bytes':4*1024**2}}
with (P/'CHECKS01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references')}));print('checks',len(checks))
