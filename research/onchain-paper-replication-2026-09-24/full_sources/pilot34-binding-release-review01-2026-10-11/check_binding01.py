"""Changed33 source/capacity/gate/public binding joins. No real preflight/admission."""
import ast,copy,hashlib,json,resource,signal
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));signal.alarm(40)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full34-entry-preparation01-2026-10-11';O=F/'real-data-pilot-full33-entry-preparation01-2026-10-11';T=F/'real-data-pilot-full34-binding-preparation01-2026-10-11';N='eth-paper-real-data-end-to-end-resource-20261011-34';checks={};evidence={};read_bytes=0
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
 expected_inputs=j(P/'EXPECTED_INPUTS01.json')
 previous=j(F/'pilot33-final-entry-review01-2026-10-11/RELEASE_REVIEW01.json');ck(sha((F/'pilot33-final-entry-review01-2026-10-11/RELEASE_REVIEW01.json').read_bytes())=='c611ec6ac8b7828f2de1dbc832b1cdf544666b01e8e79452f702840bce2ec203','accepted exact33 release')
 binding=j(D/'BINDING_DRAFT01.json');ck(set(binding['budget_review'])=={'path','sha256'},'strict budget review reference')
 gate=j(D/'gate01.json');exp=gate['experiments'][N];oldgate=j(O/'gate01.json');oldexp=oldgate['experiments'][N.replace('-34','-33')]
 ck({k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in oldgate.items() if k!='experiments'} and {k:v for k,v in gate['experiments'].items() if k!=N}==oldgate['experiments'],'all historical experiments families and datasets unchanged')
 allowed={'charter','cumulative_budget_extension','inputs','parent','question','source_files'};ck(all(v==oldexp[k] for k,v in exp.items() if k not in allowed),'unchanged originalcell method windows runtime and dispositions')
 ck(exp['parent']==N.replace('-34','-33') and exp['cells']==['real-eth-seven-graph-joint-update-resource29'],'exact spent33 parent and original selected cell')
 for v in exp['cumulative_budget_extension'].values():ck(set(v)=={'path','sha256'} and exp['source_files'].get(v['path'])==v['sha256'],'strict105 metadata source-pinned '+v['path'])
 budget=read(binding['budget_review']);ck(set(budget)=={'schema_version','decision','extension_sha256','reviewer','scope'} and budget['decision']=='accepted' and budget['extension_sha256']==exp['cumulative_budget_extension']['extension']['sha256'] and binding['budget_review']==exp['cumulative_budget_extension']['review'],'genuine exact fivefield105 review and strict join')
 extension=read(exp['cumulative_budget_extension']['extension']);charter=rb(R/exp['charter']['path']);ck(sha(charter)==exp['charter']['sha256'],'exact current charter')
 originalcode=rb(O/'preflight33_01.py').decode();code=rb(D/'preflight34_01.py').decode();expected=originalcode
 for a,b in [('20261011-33','20261011-34'),('genuine budget104','genuine budget105'),('exact reviewed full33','exact reviewed full34'),('effective_attempt_budget!=104','effective_attempt_budget!=105'),("'effective_attempt_budget':104","'effective_attempt_budget':105")]:expected=expected.replace(a,b)
 oldline=next(x for x in expected.splitlines() if x.startswith('FROZEN_PREPARATION='));newline=next(x for x in code.splitlines() if x.startswith('FROZEN_PREPARATION='));expected=expected.replace(oldline,newline)
 ck(code==expected and ast.dump(ast.parse(code))==ast.dump(ast.parse(expected)),'whole preflight literal and AST identity/ref/budget-only inverse')
 ck(rb(D/'root_io34_01.py')==rb(O/'root_io33_01.py').replace(b'from preflight33_01 import check',b'from preflight34_01 import check'),'RootIO exact preflight import-only change')
 capacity=j(D/'CAPACITY_DECLARATION_ROOT01.json');oldcap=j(O/'CAPACITY_DECLARATION_ROOT01.json');differences={k for k in capacity if capacity[k]!=oldcap[k]};ck(set(capacity)==set(oldcap) and differences=={'at','identity','owned_paths','qualification','source_anchor','source_body_pins'},'capacity only prospective lineage fields changed')
 ck(capacity['identity']==N and capacity['owned_paths']==[v.replace('20261011-33','20261011-34') for v in oldcap['owned_paths']],'fresh34 capacity owned scopes')
 mapping=j(D/'CAPACITY_SOURCE_MAP01.json');oldmap=j(O/'CAPACITY_SOURCE_MAP01.json');pins=mapping['source_files'];ck(len(pins)==421 and set(pins)==set(oldmap['source_files']) and [p for p in pins if pins[p]!=oldmap['source_files'][p]]==['tradingagents/research/onchain_replication/compact_mcm.py'],'421 source denominator sole reviewedabd86 cadence delta')
 ck(capacity['source_body_pins']==pins and capacity['source_anchor']==mapping['source_anchor']==expected_inputs['source_anchor'],'capacity selected source anchor joins')
 src=exp['source_files'];ck(len(src)==expected_inputs['source_count'] and all(src.get(p)==v for p,v in pins.items()),'declared actual source roster includes exact421 capacity closure')
 reused=[];new=[]
 for p,v in src.items():
  if previous['evidence'].get(p)==v:evidence[p]=v;reused.append(p)
  else:ck(sha(rb(R/p))==v,'new or changed public source '+p);new.append(p)
 ck(pins['tradingagents/research/onchain_replication/real_pilot_import_caller.py']=='f65ff353315bfb9e4db80d326170e02e5b2ebc6da1e5d59e5a8e9243b4afd11a','exact installed preload source')
 sr=j(F/'pilot34-binding-source-review01-2026-10-11/REVIEW01.json');ck(ref(F/'pilot34-binding-source-review01-2026-10-11/REVIEW01.json')['sha256']==expected_inputs['binder_review_sha256'] and sr['decision']=='ACCEPT_EXACT_ACTUAL34_PUBLIC_SOURCE_AND_OFFLINE_BINDER_COMMAND_ONLY','reuse exact accepted34 source caller and independent198Git join')
 for role,v in binding.items():
  if type(v) is dict and {'path','sha256'}<=set(v):
   if role=='transport':evidence[v['path']]=v['sha256']
   else:read(v)
 actual={k:{q:v[q] for q in ('path','sha256')} for k,v in exp['inputs'].items()};ck(len(actual)==67 and actual==binding['input_refs'],'gate and binding exact67refs')
 bound=read(binding['transport_binding']);receipt=read(binding['binding_readback']);allrefs=j(T/'ALL_INPUT_REFS01.json');reduced={k:{q:v[q] for q in ('path','sha256')} for k,v in allrefs.items()};ck(set(actual)==set(reduced) and [k for k in actual if actual[k]!=reduced[k]]==['matching_ordered_edge_scratch'],'actualbinder67 refs only explicit scratch difference')
 ck(receipt['actual_opaque_input']==bound['private_input'] and receipt['all_input_roles']==67 and all(receipt[k] is False for k in ('claim','launch','network')),'actualRoot binder public receipt joins')
 ck(j(R/actual['matching_ordered_edge_scratch']['path'])==json.loads(rb(R/oldexp['inputs']['matching_ordered_edge_scratch']['path']).replace(b'20261011-33',b'20261011-34')),'scratch full JSON inverse changes identity only')
 core=read(binding['core_manifest']);oldcore=j(O/'CORE_MANIFEST01.json');ck(set(core['inputs'])==set(oldcore['inputs']) and core['source']==oldcore['source'],'same core source and scientific roster')
 for role,v in core['inputs'].items():ck(v['sha256']==oldcore['inputs'][role]['sha256'],'unchanged scientific policy '+role)
 ops=j(D/'ROOT_PREPARATION_OPERATIONS01.json');ck(ops['source_anchor']==mapping['source_anchor'] and ops['actual_remote_readback']['head']==mapping['source_anchor'] and ops['actual_remote_readback']['exit_code']==0 and all(v['exit_code']==0 for v in ops['operations']),'Root actual source/public/binder/registration operation receipts')
 source_review=read(binding['integration_review']);ck(binding['integration_review']['sha256']==expected_inputs['source_review_sha256'] and source_review['references'][str((F/'pilot33-preparation-cadence-correction01-2026-10-11/compact_mcm.py').relative_to(R))]['sha256']==pins['tradingagents/research/onchain_replication/compact_mcm.py']==expected_inputs['candidate_sha256'],'exact independently accepted installed cadence correction')
 ck(binding['prior_outcome_review']['sha256']=='5047103b1a6cad4f95767dc504fd5d751f70b791169527d6480608f2d40e5279' and binding['prior_recovery_review']['sha256']==expected_inputs['outcome25_review_sha256'],'actual33 terminal and independent returned25 evidence joins')
 # Reuse unchanged actual pure validator, substitute only Git capacity work with explicit static joins.
 tree=ast.parse(code);scope={'Path':Path,'copy':copy,'json':json,'hashlib':hashlib,'ROOT':R,'NAME':N,'OPAQUE_ROLE':'archive_transport','read':read,'read_path':rb}
 for node in tree.body:
  if isinstance(node,ast.Assign):
   for t in node.targets:
    if isinstance(t,ast.Name) and t.id in {'BINDER','FROZEN_PREPARATION','COMPILED_POLICY','COMPILED_INPUTS'}:scope[t.id]=ast.literal_eval(node.value)
 names={'need','reference','inverse_binding','_encoded','_path_envelope','prepared_inputs'};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'actual34-pure-binding-functions','exec'),scope)
 def capacity_subset(c,p,s,current):ck(c['source_body_pins']==p['source_pins']==pins and all(s.get(k)==v for k,v in pins.items()) and c['source_anchor']==mapping['source_anchor'],'actual pure capacity421 source subset')
 scope['_capacity_source']=capacity_subset
 review={'schema_version':1,'decision':'accepted','identity':N,'input_refs':actual,'evidence':evidence};memory=copy.deepcopy(binding);memory['binding_review']={'path':str((P/'BINDING_REVIEW01.json').relative_to(R)),'sha256':'0'*64};release=dict(evidence);release[memory['binding_review']['path']]='0'*64
 scope['read']=lambda v:review if v is memory['binding_review'] else read(v)
 scope['prepared_inputs'](memory,{'evidence':release},SimpleNamespace(inputs=exp['inputs'],experiment=exp,source=mapping['source_anchor']),read(actual['execution_job']))
 ck(True,'actual entire pure prepared_inputs inverse publicbodies core compiled policies caps passes')
 review.update({'reviewer':'independent outcome16_release_review','evidence':dict(evidence),'checks':checks,'scope':'Actual34 public67 bound-input inverse and strict current gate/source/capacity joins; opaque transport reference only. Accepted33 entry and independently reviewed34 numerical198 Git/current source joins reused.','read_bytes':read_bytes,'source_count':len(src),'reused_source_count':len(reused),'new_source_count':len(new),'draft':ref(D/'BINDING_DRAFT01.json'),'gate':binding['gate'],'conditions':['Root final BINDING01 may change only status and binding_review from exact DRAFT01. Exact final release follows actual final body and genuine metadata admission.','Final committed current entry, whole live preflight, source freeze and independently accepted fresh external current preparation recovery must precede one unused34 launch.'],'limits':['No private/connection/body or empirical arrays read/stat/hash; native library reference reused.','No genuine preflight/admission, numerical module, Owner/native/claim/Git/network action.','Declared source pins reuse identical accepted33 evidence and authenticate new/changed public bodies; Root421 and independent34 binder198 Git/current source metadata joins reused.','No actual capacity/performance/saving/financial validity claim.'],'final_entry_release':False})
 save('BINDING_REVIEW01.json',review);print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':sha((P/'BINDING_REVIEW01.json').read_bytes()),'source_count':len(src),'input_count':len(actual),'reused_sources':len(reused),'new_sources':len(new)},sort_keys=True))
except BaseException as e:save('BINDING_FAILED01.json',{'error':repr(e),'checks':checks,'evidence':evidence,'read_bytes':read_bytes});raise
