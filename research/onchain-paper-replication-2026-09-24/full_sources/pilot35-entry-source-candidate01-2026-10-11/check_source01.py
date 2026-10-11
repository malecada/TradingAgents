"""Bounded stdlib source and in-memory template checks; never run either builder."""
import ast,difflib,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];O=F/'real-data-pilot-full34-entry-preparation01-2026-10-11';checks=[];refs={}
def read(p):
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
def assign(tree,name):return next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
def fun(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
source=read(P/'prepare_source01.py');registration=read(P/'prepare_registration01.py');st=ast.parse(source);rt=ast.parse(registration)
original=read(O/'preflight34_01.py');changes=ast.literal_eval(assign(st,'changes'));added=ast.literal_eval(assign(st,'added'));out=original
for a,b in changes:ck(a in out,'literal changed seam present '+a);out=out.replace(a,b)
oldline=next(s for s in original.splitlines() if s.startswith('FROZEN_PREPARATION='));moved=oldline.replace('20261011-34','20261011-35')
placeholder='FROZEN_PREPARATION='+repr({'pending_actual_root_preparation':True})
out=out.replace(moved,placeholder)
policy=json.loads(read(F/'pilot34-two-attribute-main-integration-bundle01-2026-10-11/committed-public-joins01/mcm_policy.json'))['batched']['execution'];edge=policy['compiled_edge_policy'];roles=policy['compiled_edge_inputs']
line=next(s for s in out.splitlines() if s.startswith('COMPILED_INPUTS='));insert='\nEDGE_POLICY='+repr(edge)+'\nEDGE_INPUTS='+repr(roles);out=out.replace(line,line+insert)
seam=ast.literal_eval(assign(st,'seam'));out=out.replace(seam,added+seam);ast.parse(out)
inverse=out.replace(added,'').replace(insert,'').replace(placeholder,moved)
for a,b in reversed(changes):inverse=inverse.replace(b,a)
ck(inverse==original,'complete emitted preflight literal inverse including five-role seam')
ck(ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original)),'complete preflight AST inverse')
oldtree=ast.parse(original);newtree=ast.parse(out)
for name in ('reference','read_path','read','authenticate_committed','committed_refs','validate_opaque','inverse_binding','_encoded','_path_envelope','projected'):
 ck(ast.dump(fun(oldtree,name))==ast.dump(fun(newtree,name)),'unchanged actual helper API '+name)
resources=ast.literal_eval(assign(oldtree,'EXPECTED_RESOURCES'));rebased=json.loads(json.dumps(resources).replace('20261011-34','20261011-35'))
ck(ast.literal_eval(assign(newtree,'EXPECTED_RESOURCES'))==rebased,'only identity changes in exact native resource controls')
oldio=read(O/'root_io34_01.py');newio=oldio.replace('from preflight34_01 import check','from preflight35_01 import check')
ck(oldio.count('from preflight34_01 import check')==1 and newio.replace('from preflight35_01 import check','from preflight34_01 import check')==oldio,'RootIO exact import-only inverse')
ck(set(roles)=={'source','adapter','library','runtime','abi'} and roles=={k:'compiled_edge_'+k for k in roles} and edge['format']=='cpython-two-attribute-edge-owner-v1','actual selected five-role policy schema')
oldmap=json.loads(read(O/'CAPACITY_SOURCE_MAP01.json'))['source_files'];serializer=json.loads(read(F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json'));native=json.loads(read(F/'pilot34-two-attribute-main-adoption01-2026-10-11/INTEGRATION01.json'))
expected={m['destination']['path']:m['destination']['sha256'] for m in serializer['modules']};expected.update({m['destination']:m['installed_sha256'] for m in native['modules']});added_paths=set(expected)-set(oldmap)
ck(len(oldmap)==421 and len(expected)==15 and len(set(oldmap)&set(expected))==13 and added_paths=={'tradingagents/research/onchain_replication/compiled_edge_owner.py','tradingagents/research/onchain_replication/edge_chunk_adapter.py'},'actual five plus ten adoption denominator gives thirteen updates two additions and423')
ck(all(oldmap[p]!=h for p,h in expected.items() if p in oldmap),'all thirteen old421 pins actually differ from accepted adoption')
ck("capacity['source_body_pins']==pins" in source and "ref(capacity_path)['sha256']==CAPACITY_SHA" in source and "save(HERE/'CAPACITY_DECLARATION_ROOT01.json'" not in source,'requires actual Root capacity and does not synthesize accepted declaration')
ck("len(numerical['files'])==200" in source and "len(load(T/'PUBLIC_INPUT_REFS_DRAFT01.json'))==71" in source,'exact200 source and71 public draft requirements')
ck("current['batched']['execution'].pop('compiled_edge_policy')" in source and "current['batched']['execution'].pop('compiled_edge_inputs')" in source and "assert current==original" in source,'four original core policies inverse removes only two native selection fields')
ck("assert len(refs)==72" not in registration and "len(refs)==72" in registration and "'all_input_roles':72" in registration and "'input_roles':72" in registration,'actual bound72 and published72 closure')
ck("review['decision']=='accepted'" in registration and "review['extension_sha256']=='e0a1e3f89926094373e6c58022627e5861cda03064657e88a245129756810b9a'" in registration and "ref(review_path)['sha256']==REVIEW_SHA" in registration,'genuine exact106 machine review required before draft writes')
ck("scratch['installed_source']['sha256']=ref(ROOT/kernel)['sha256']" in registration and "86ccc3a471827bdce7784145914240d04416d2cc0023e8acb77fb26ae473df57" in registration,'fresh scratch exact current kernel86ccc')
for s in (source,registration):ck("assert HERE==EXPECTED_HERE" in s and "not (ROOT/'research_runs'/NAME).exists()" in s and "p.open('xb')" in s,'exact Root directory fresh identity exclusive metadata writes')
oldregistration=read(O/'prepare_registration01.py');ort=ast.parse(oldregistration)
for name in ('load','ref','save'):ck(ast.dump(fun(ort,name))==ast.dump(fun(rt,name)),'unchanged registration helper '+name)
patch=[];inversepatch=[]
for n in ('prepare_source01.py','prepare_registration01.py'):
 a=read(O/n);b=read(P/n);patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='full34/'+n,tofile='candidate35/'+n));inversepatch.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='candidate35/'+n,tofile='full34/'+n))
for n,t in [('FORWARD.patch',''.join(patch)),('INVERSE.patch',''.join(inversepatch))]:
 with (P/n).open('x') as f:f.write(t)
result={'status':'PASS_SOURCE_ONLY_NOT_EXECUTED','checks':checks,'references':refs,'builders_executed':False,'emitted_preflight_fixture':'in-memory only; pending-preparation sentinel was not saved or used as evidence','actual_Git_source_join_or_capacity_or_binding_or_admission_or_claim':False,'limits':['Actual Root106 review, capacity declaration SHA and completed public binding remain execution prerequisites.','Git/local423 and numerical200 joins are source-declared, not executed by this checker.','New Source/Entry independent review required; no numerical/scientific/private bodies read or imported.']}
with (P/'SOURCE_CHECK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'builders_executed':False}))
