"""Changed32 source/capacity/gate/public binding joins. No real preflight/admission."""
import ast,copy,hashlib,json,resource,signal
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));signal.alarm(40)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full32-entry-preparation01-2026-10-11';O=F/'real-data-pilot-full31-entry-preparation02-2026-10-11';T=F/'real-data-pilot-full32-binding-preparation01-2026-10-11';N='eth-paper-real-data-end-to-end-resource-20261011-32';checks={};evidence={};read_bytes=0
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def rb(p):
 global read_bytes
 p=Path(p);assert not ({'.git','.venv','keys','apis','research_artifacts','research_runs'}&set(p.parts));assert p.name not in {'connection.json','archive_transport01.json'} and p.suffix!='.so'
 b=p.read_bytes();assert len(b)<4*1024**2;read_bytes+=len(b);assert read_bytes<32*1024**2;evidence[str(p.relative_to(R))]=sha(b);return b
def j(p):return json.loads(rb(p))
def ref(p):
 b=rb(p);return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
def read(v):
 b=rb(R/v['path']);ck(sha(b)==v['sha256'] and ('bytes' not in v or len(b)==v['bytes']),'public ref '+v['path']);return json.loads(b)
def save(name,v):
 with (P/name).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
try:
 previous=j(F/'pilot31-final-entry-review01-2026-10-11/RELEASE_REVIEW01.json');ck(sha((F/'pilot31-final-entry-review01-2026-10-11/RELEASE_REVIEW01.json').read_bytes())=='df6c18d04a91cd8013eb7b141d1731dcccd0afb06d56f4a497d27ffdb7483847','accepted exact31 release')
 binding=j(D/'BINDING_DRAFT02.json');draft1=j(D/'BINDING_DRAFT01.json');inv=copy.deepcopy(binding);inv['budget_review']['bytes']=draft1['budget_review']['bytes'];ck(inv==draft1 and set(binding['budget_review'])=={'path','sha256'},'sole strict budgetref correction; original draft refusal retained')
 gate=j(D/'gate01.json');exp=gate['experiments'][N];oldgate=j(O/'gate03.json');oldexp=oldgate['experiments'][N.replace('-32','-31')]
 ck({k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in oldgate.items() if k!='experiments'} and {k:v for k,v in gate['experiments'].items() if k!=N}==oldgate['experiments'],'all historical experiments families and datasets unchanged')
 allowed={'charter','cumulative_budget_extension','inputs','parent','question','source_files'};ck(all(v==oldexp[k] for k,v in exp.items() if k not in allowed),'unchanged originalcell method windows runtime and dispositions')
 ck(exp['parent']==N.replace('-32','-31') and exp['cells']==['real-eth-seven-graph-joint-update-resource29'],'exact spent31 parent and original selected cell')
 for v in exp['cumulative_budget_extension'].values():ck(set(v)=={'path','sha256'} and exp['source_files'].get(v['path'])==v['sha256'],'strict103 metadata source-pinned '+v['path'])
 budget=read(binding['budget_review']);ck(set(budget)=={'schema_version','decision','extension_sha256','reviewer','scope'} and budget['decision']=='accepted' and budget['extension_sha256']==exp['cumulative_budget_extension']['extension']['sha256'] and binding['budget_review']==exp['cumulative_budget_extension']['review'],'genuine exact fivefield103 review and strict join')
 extension=read(exp['cumulative_budget_extension']['extension']);charter=rb(R/exp['charter']['path']);ck(sha(charter)==exp['charter']['sha256'],'exact current charter')
 originalcode=rb(O/'preflight31_03.py').decode();code=rb(D/'preflight32_02.py').decode();expected=originalcode
 for a,b in [('20261011-31','20261011-32'),('gate03.json','gate01.json'),('BINDING03.json','BINDING01.json'),('genuine budget102','genuine budget103'),('exact reviewed full31','exact reviewed full32'),('effective_attempt_budget!=102','effective_attempt_budget!=103'),("'effective_attempt_budget':102","'effective_attempt_budget':103")]:expected=expected.replace(a,b)
 oldline=next(x for x in expected.splitlines() if x.startswith('FROZEN_PREPARATION='));newline=next(x for x in code.splitlines() if x.startswith('FROZEN_PREPARATION='));expected=expected.replace(oldline,newline)
 ck(code==expected,'whole preflight source exact identity/ref/budget substitution only')
 ck(rb(D/'root_io32_02.py')==rb(O/'root_io31_03.py').replace(b'from preflight31_03 import check',b'from preflight32_02 import check'),'RootIO exact preflight import-only change')
 capacity=j(D/'CAPACITY_DECLARATION_ROOT01.json');oldcap=j(O/'CAPACITY_DECLARATION_ROOT01.json');differences={k for k in capacity if capacity[k]!=oldcap[k]};ck(set(capacity)==set(oldcap) and differences=={'at','identity','owned_paths','qualification','source_anchor','source_body_pins'},'capacity only prospective lineage fields changed')
 ck(capacity['identity']==N and capacity['owned_paths']==[v.replace('20261011-31','20261011-32') for v in oldcap['owned_paths']],'fresh32 capacity owned scopes')
 mapping=j(D/'CAPACITY_SOURCE_MAP01.json');oldmap=j(O/'CAPACITY_SOURCE_MAP01.json');pins=mapping['source_files'];ck(len(pins)==421 and set(pins)==set(oldmap['source_files']) and [p for p in pins if pins[p]!=oldmap['source_files'][p]]==['tradingagents/research/onchain_replication/real_pilot_import_caller.py'],'421 source denominator sole reviewedf65 caller delta')
 ck(capacity['source_body_pins']==pins and capacity['source_anchor']==mapping['source_anchor']=='3d07e4cc06cd37352ac633d69ab781a7955b656b','capacity selected source anchor joins')
 src=exp['source_files'];ck(len(src)==620 and all(src.get(p)==v for p,v in pins.items()),'620 source roster includes exact421 capacity closure')
 reused=[];new=[]
 for p,v in src.items():
  if previous['evidence'].get(p)==v:evidence[p]=v;reused.append(p)
  else:ck(sha(rb(R/p))==v,'new or changed public source '+p);new.append(p)
 ck(pins['tradingagents/research/onchain_replication/real_pilot_import_caller.py']=='f65ff353315bfb9e4db80d326170e02e5b2ebc6da1e5d59e5a8e9243b4afd11a','exact installed preload source')
 sr=j(F/'pilot32-binding-source-review01-2026-10-11/REVIEW01.json');ck(ref(F/'pilot32-binding-source-review01-2026-10-11/REVIEW01.json')['sha256']=='af2b7c7b66d260ae7c02e6aa6d98614226e07834563d5cfa20170d309eaeb306' and sr['decision']=='RELEASE_EXACT_PILOT32_BINDER01_ONCE','reuse exact accepted32 source caller and independent198Git join')
 for role,v in binding.items():
  if type(v) is dict and {'path','sha256'}<=set(v):
   if role=='transport':evidence[v['path']]=v['sha256']
   else:read(v)
 actual={k:{q:v[q] for q in ('path','sha256')} for k,v in exp['inputs'].items()};ck(len(actual)==67 and actual==binding['input_refs'],'gate and binding exact67refs')
 bound=read(binding['transport_binding']);receipt=read(binding['binding_readback']);allrefs=j(T/'ALL_INPUT_REFS01.json');reduced={k:{q:v[q] for q in ('path','sha256')} for k,v in allrefs.items()};ck(set(actual)==set(reduced) and [k for k in actual if actual[k]!=reduced[k]]==['matching_ordered_edge_scratch'],'actualbinder67 refs only explicit scratch difference')
 ck(receipt['actual_opaque_input']==bound['private_input'] and receipt['all_input_roles']==67 and all(receipt[k] is False for k in ('claim','launch','network')),'actualRoot binder public receipt joins')
 ck(j(R/actual['matching_ordered_edge_scratch']['path'])==json.loads(rb(R/oldexp['inputs']['matching_ordered_edge_scratch']['path']).replace(b'20261011-31',b'20261011-32')),'scratch full JSON inverse changes identity only')
 core=read(binding['core_manifest']);oldcore=j(O/'CORE_MANIFEST01.json');ck(set(core['inputs'])==set(oldcore['inputs']) and core['source']==oldcore['source'],'same core source and scientific roster')
 for role,v in core['inputs'].items():ck(v['sha256']==oldcore['inputs'][role]['sha256'],'unchanged scientific policy '+role)
 # Reuse unchanged actual pure validator, substitute only Git capacity work with explicit static joins.
 tree=ast.parse(code);scope={'Path':Path,'copy':copy,'json':json,'hashlib':hashlib,'ROOT':R,'NAME':N,'OPAQUE_ROLE':'archive_transport','read':read,'read_path':rb}
 for node in tree.body:
  if isinstance(node,ast.Assign):
   for t in node.targets:
    if isinstance(t,ast.Name) and t.id in {'BINDER','FROZEN_PREPARATION','COMPILED_POLICY','COMPILED_INPUTS'}:scope[t.id]=ast.literal_eval(node.value)
 names={'need','reference','inverse_binding','_encoded','_path_envelope','prepared_inputs'};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'actual32-pure-binding-functions','exec'),scope)
 def capacity_subset(c,p,s,current):ck(c['source_body_pins']==p['source_pins']==pins and all(s.get(k)==v for k,v in pins.items()) and c['source_anchor']==mapping['source_anchor'],'actual pure capacity421 source subset')
 scope['_capacity_source']=capacity_subset
 review={'schema_version':1,'decision':'accepted','identity':N,'input_refs':actual,'evidence':evidence};memory=copy.deepcopy(binding);memory['binding_review']={'path':str((P/'BINDING_REVIEW01.json').relative_to(R)),'sha256':'0'*64};release=dict(evidence);release[memory['binding_review']['path']]='0'*64
 scope['read']=lambda v:review if v is memory['binding_review'] else read(v)
 scope['prepared_inputs'](memory,{'evidence':release},SimpleNamespace(inputs=exp['inputs'],experiment=exp,source=mapping['source_anchor']),read(actual['execution_job']))
 ck(True,'actual entire pure prepared_inputs inverse publicbodies core compiled policies caps passes')
 review.update({'reviewer':'independent outcome16_release_review','evidence':dict(evidence),'checks':checks,'scope':'Actual32 public67 binder inverse and strict current gate/source/capacity joins. Opaque transport reference-only. Original31 source/entry acceptance and32 numerical198Git checks reused.','read_bytes':read_bytes,'reused_source_count':len(reused),'new_source_count':len(new),'draft':ref(D/'BINDING_DRAFT02.json'),'gate':binding['gate'],'conditions':['Root final BINDING01 may change only status and binding_review from exact DRAFT02. Independent exact release follows actual final body and genuine metadata admission.','Root final committed entry live preflight and independently accepted fresh external current preparation recovery must precede one unused32 launch.'],'limits':['No private/connection/body or historical empirical data read/stat/hash; native library reference reused.','No genuine preflight/admission, numerical/scientific module, Owner/native/claim/Git/network execution in this combined review.','620source closure reuses identical accepted31 hashes and authenticates changed/new public bodies;421 Root Git joins are source-preparation evidence, while198changed numerical Git/current joins were independently authenticated in prior32 binder review.','No real capacity/performance/financial validity or future process eligibility claim.'],'final_entry_release':False})
 save('BINDING_REVIEW01.json',review);print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':sha((P/'BINDING_REVIEW01.json').read_bytes()),'source_count':len(src),'input_count':len(actual),'reused_sources':len(reused),'new_sources':len(new)},sort_keys=True))
except BaseException as e:save('BINDING_FAILED01.json',{'error':repr(e),'checks':checks,'evidence':evidence,'read_bytes':read_bytes});raise
