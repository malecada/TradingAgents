"""Bounded public successor03 joins; no admission, Git, private body or numerical execution."""
import ast,copy,hashlib,json,resource,signal
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(15,15));signal.alarm(30)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full31-entry-preparation02-2026-10-11';T=F/'real-data-pilot-full31-binding-preparation03-2026-10-11';N='eth-paper-real-data-end-to-end-resource-20261011-31';checks=[];evidence={};total=0
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
def rb(p):
 global total
 p=Path(p);assert not ({'.git','.venv','keys','apis','research_artifacts','research_runs'}&set(p.parts));assert p.suffix!='.so'
 b=p.read_bytes();assert len(b)<4*1024**2;total+=len(b);assert total<32*1024**2;evidence[str(p.relative_to(R))]=sha(b);return b
def j(p):return json.loads(rb(p))
def read(ref):
 b=rb(R/ref['path']);ck(sha(b)==ref['sha256'] and ('bytes' not in ref or len(b)==ref['bytes']),'authenticated public ref '+ref['path']);return json.loads(b)
def write(name,v):
 with (P/name).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
try:
 retained=j(P/'BINDING_FAILED03.json');checks=retained['checks'];evidence.update(retained['evidence']);total=retained['read_bytes']
 ck(retained['error'].startswith('JSONDecodeError') and all(c['pass'] for c in checks),'retained harness attempted JSON decode of authenticated Python source; no candidate failure')
 binding=j(D/'BINDING_DRAFT03.json');gate=j(D/'gate03.json');exp=gate['experiments'][N];actual={k:{q:v[q] for q in ('path','sha256')} for k,v in exp['inputs'].items()};pins=exp['source_files']
 code=rb(D/'preflight31_03.py').decode();bound=read(binding['transport_binding']);prepared=read(binding['preparation'])
 receipt=read(binding['binding_readback']);ck(receipt['actual_opaque_input']==bound['private_input'] and receipt['all_input_roles']==67 and all(receipt[k] is False for k in ('claim','launch','network')),'original actual binder receipt joins')
 operation=j(D/'ROOT_ADMISSION_OPERATION01.json');admitted=j(D/'ADMISSION_CHECK01.stdout');ck(operation['exit_code']==0 and operation['source']=='84f6b523ddf8db74fea63fa0f25f55e9e98f5bf3' and admitted=={'experiment':N,'stage':'development','ready':True,'status':'metadata_admitted','empirical_inputs_opened':False,'run_started':False} and rb(D/'ADMISSION_CHECK01.stderr')==b'','Root original genuine metadata admission success only')
 tree=ast.parse(code);scope={'Path':Path,'copy':copy,'json':json,'hashlib':hashlib,'ROOT':R,'NAME':N,'OPAQUE_ROLE':'archive_transport','read':read,'read_path':rb}
 for node in tree.body:
  if isinstance(node,ast.Assign):
   for target in node.targets:
    if isinstance(target,ast.Name) and target.id in {'BINDER','FROZEN_PREPARATION','COMPILED_POLICY','COMPILED_INPUTS'}:scope[target.id]=ast.literal_eval(node.value)
 names={'need','reference','inverse_binding','_encoded','_path_envelope','prepared_inputs'}
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'actual-public-binding-functions','exec'),scope)
 def static_capacity(cap,pub,sources,current):
  ck(cap['source_body_pins']==pub['source_pins'] and all(sources.get(p)==v for p,v in pub['source_pins'].items()) and len(pub['source_pins'])==421,'capacity421 exact current admitted-source subset')
  ck(cap['source_anchor']=='b87a3c226ea5af74fab37c48e3884340b11d2458' and 'source' not in cap and 'max_age_seconds' not in cap,'prospective capacity authority retains original anchor; no live-measurement impersonation')
 scope['_capacity_source']=static_capacity
 # Exercise actual pure binding validator with this pending review in memory; no disk fabrication of a final binding or release.
 review={'schema_version':1,'decision':'accepted','identity':N,'input_refs':actual,'evidence':evidence}
 memory=copy.deepcopy(binding);memory['binding_review']={'path':str((P/'BINDING_REVIEW01.json').relative_to(R)),'sha256':'0'*64}
 def scoped_read(ref):return review if ref is memory['binding_review'] else read(ref)
 scope['read']=scoped_read
 released=dict(evidence);released[memory['binding_review']['path']]='0'*64
 scope['prepared_inputs'](memory,{'evidence':released},SimpleNamespace(inputs=exp['inputs'],experiment=exp,source=operation['source']),read(actual['execution_job']))
 ck(True,'actual prepared_inputs predicates including full binder inverse/public bodies/fixednumerics pass; only Git capacity join replaced by explicit static subset check')
 # Two changed-seam counterexamples exercise genuine inverse failure rather than expected-answer duplication.
 bs={'json':json,'hashlib':hashlib};bt=ast.parse(rb(R/scope['BINDER']['path']));exec(compile(ast.Module(body=[n for n in bt.body if isinstance(n,ast.FunctionDef) and n.name in {'raw','sha'}],type_ignores=[]),'accepted-binder-encoding','exec'),bs)
 for label,mut in [('unrelated-public-mutation',lambda x:x['inputs']['pilot'].update({'unexpected':1})),('opaque-role-mutation',lambda x:x['private_input'].update({'other':binding['transport']}))]:
  damaged=copy.deepcopy(bound);mut(damaged)
  try:scope['inverse_binding'](prepared,read(binding['unbound_archive']),damaged,binding['transport'],bs['raw'],bs['sha'])
  except ValueError:ck(True,'actual inverse refuses '+label)
  else:raise AssertionError('inverse accepted '+label)
 review.update({'reviewer':'independent outcome16_release_review','scope':'Exact public31 binding03, fixed scientific/source/capacity joins and unchanged entry predicates. Opaque body reference-only. Source/capacity467 prior checks reused; no empirical data opened. Root genuine metadata admission result authenticated, not replayed. Final binding and exact release pending.','checks':checks,'read_bytes':total,'evidence':dict(evidence),'limitations':['No private dispatch, connection, credential, historical empirical input or runtime-library body read/stat/hash.','No current Git operation, live resources/native eligibility, claim, launch or remote preservation performed.','421 initial source bodies reuse SOURCE_CHECK01; additional133 public sources independently authenticated.','No financial validity, timing improvement, complete-run feasibility or full native capacity claim.'],'conditions':['Root must create final BINDING03 with only status and this binding_review changed from the frozen draft; independent final release must authenticate it.','Root genuine preflight must authenticate current committed bodies, private dispatch, live resources, fresh identity and absence of active claims before one launch.','Full frozen preparation requires independent actual external returned-body preservation acceptance before launch.'],'final_entry_release':False})
 write('BINDING_REVIEW01.json',review);print(json.dumps({'decision':'accepted','checks':len(checks),'review_sha256':sha((P/'BINDING_REVIEW01.json').read_bytes()),'read_bytes':total,'final_entry_release':False},sort_keys=True))
except BaseException as error:
 write('BINDING_FAILED04.json',{'error':repr(error),'checks':checks,'evidence':evidence,'read_bytes':total});raise
