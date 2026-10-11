"""Preliminary changed-source/capacity check only; final gate/binding pending."""
import ast,copy,hashlib,json,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(15,15));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(25)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full31-entry-preparation02-2026-10-11';O=F/'real-data-pilot-full30-entry-preparation01-2026-10-11';checks=[];refs={};count=0
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
    checks.append({'name':n,'pass':bool(v)})
    if not v:raise AssertionError(n)
def read(p):
    global count
    p=Path(p);assert not ({'.git','.venv','keys','apis','research_artifacts','research_runs'}&set(p.parts))
    b=p.read_bytes();assert len(b)<4*1024**2;count+=len(b);assert count<32*1024**2
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
m=js(D/'SOURCE_MANIFEST01.json')
for name,row in m['files'].items():
    b=read(D/name);ck(row['path']==str((D/name).relative_to(R)) and len(b)==row['bytes'] and sha(b)==row['sha256'],'source manifest '+name)
oldreview=read(F/'real-data-pilot-full30-final-entry-review04-2026-10-11/RELEASE_REVIEW03.json');ck(sha(oldreview)=='e2caccb74715c41dfb6a38051d1da3c7f58360a70d0b9ca4ff44731d364b344b','accepted full30 entry release')
oldrelease=json.loads(oldreview)
before=read(O/'preflight30_05.py').decode();after=read(D/'preflight31_01.py').decode();expected=before
changes=[('20261011-30','20261011-31'),('gate03.json','gate01.json'),('BINDING03.json','BINDING01.json'),('RELEASE_REVIEW03.json','RELEASE_REVIEW01.json'),('effective_attempt_budget!=101','effective_attempt_budget!=102'),("'effective_attempt_budget':101","'effective_attempt_budget':102"),('genuine budget101','genuine budget102'),('exact reviewed full30','exact reviewed full31')]
for left,right in changes:ck(left in expected,'literal original seam '+left);expected=expected.replace(left,right)
oldline=next(x for x in before.splitlines() if x.startswith('FROZEN_PREPARATION='));newline=next(x for x in after.splitlines() if x.startswith('FROZEN_PREPARATION='))
expected=expected.replace(oldline.replace('20261011-30','20261011-31'),newline)
ck(expected==after,'preflight exact allowed substitutions only')
frozen=ast.literal_eval(newline.split('=',1)[1]);body=read(R/frozen['path']);ck(len(body)==frozen['bytes'] and sha(body)==frozen['sha256']=='38e44a08c8b9f94123e9f1dd862beb3d0054edd8c6f62515eaaa5f8b4616bfb9','exact public31prepared pin')
ck(read(D/'root_io31_01.py')==read(O/'root_io30_05.py').replace(b'from preflight30_05 import check',b'from preflight31_01 import check'),'RootIO exact import-only inverse')
mapping=js(D/'CAPACITY_SOURCE_MAP01.json');oldmapping=js(O/'CAPACITY_SOURCE_MAP01.json');pins=mapping['source_files'];oldpins=oldmapping['source_files']
ck(len(pins)==421 and set(pins)==set(oldpins) and [p for p in pins if pins[p]!=oldpins[p]]==['tradingagents/research/onchain_replication/compact_mcm_batched.py'],'only compact source changed in421')
for path,digest in pins.items():ck(sha(read(R/path))==digest,'actual local source body '+path)
for name in ['preflight30_05.py','root_io30_05.py','CAPACITY_SOURCE_MAP01.json','CORE_MANIFEST02.json']:
    path=str((O/name).relative_to(R));ck(sha(read(O/name))==oldrelease['evidence'][path],'accepted predecessor body '+name)
integration=js(F/'pilot31-source-integration01-2026-10-11/ROOT_INTEGRATION01.json')
for role in ['source_review','actual_prior_recovery_review','candidate','installed']:
    row=integration[role];b=read(R/row['path']);ck(len(b)==row['bytes'] and sha(b)==row['sha256'],'accepted integration anchor '+role)
ck(integration['source_review']['sha256']=='76b23f26a27d149446137474d66f030ea7bae4a8c688d06b603a1c53b1a503cf' and integration['installed']['sha256']==pins[integration['installed']['path']]=='e93d3b7073c8de5d1c3e7f5f30b55ba613b47a014f8fe449a0fe7e8a746941dd','exact reviewed three-boundary correction installed')
capacity=js(D/'CAPACITY_DECLARATION_ROOT01.json');oldcap_path=F/'real-data-pilot-full30-preparation01-2026-10-11/CAPACITY_DECLARATION_ROOT01.json';oldcap=js(oldcap_path)
ck(sha(read(oldcap_path))==oldrelease['evidence'][str(oldcap_path.relative_to(R))],'accepted prior prospective capacity declaration')
changed={'at','identity','owned_paths','qualification','source_anchor','source_body_pins'}
ck(set(capacity)==set(oldcap) and {k for k in capacity if capacity[k]!=oldcap[k]}==changed,'only declared capacity lineage fields changed')
ck(capacity['source_body_pins']==pins and capacity['source_anchor']==mapping['source_anchor']=='b87a3c226ea5af74fab37c48e3884340b11d2458' and capacity['owned_paths']==[x.replace('20261011-30','20261011-31') for x in oldcap['owned_paths']],'capacity source and owned path identity joins')
inverse=copy.deepcopy(capacity)
for key in changed:inverse[key]=oldcap[key]
ck(inverse==oldcap,'whole capacity inverse retains all growth/headroom terms')
core=js(D/'CORE_MANIFEST01.json');oldcore=js(O/'CORE_MANIFEST02.json')
ck(set(core)==set(oldcore) and core['builder_sha256']==oldcore['builder_sha256'],'same scientific capacity builder provenance')
for role,row in core['inputs'].items():
    b=read(R/row['path']);ck(sha(b)==row['sha256']==oldcore['inputs'][role]['sha256'] and len(b)==row['bytes'],'unchanged scientific policy '+role)
ck(set(core['source'])==set(oldcore['source']) and [p for p in core['source'] if core['source'][p]!=oldcore['source'][p]]==['tradingagents/research/onchain_replication/compact_mcm_batched.py'],'unchanged reservation source except accepted correction')
scope={};tree=ast.parse(after)
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_RESOURCES' for t in node.targets):scope['resources']=ast.literal_eval(node.value)
sourcepath=R/integration['installed']['path'];ck(all(not sourcepath.is_relative_to(Path(root)) for root in scope['resources']['storage_budget']['roots']) and integration['candidate']['bytes']-45525==659,'additional659 readonlysource bytes outside writable roots')
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'need','projected'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-pure-capacity-functions','exec'),scope)
limits=scope['resources']['storage_budget']['limits'];fields=[('logical_file_bytes','new_logical_growth_bytes','max_logical_bytes'),('allocated_bytes','new_allocated_growth_bytes','max_allocated_bytes'),('entries','new_entries','max_entries')]
at_limit={observed:limits[limit]-capacity[growth] for observed,growth,limit in fields};scope['projected'](capacity,at_limit,limits);ck(True,'actual projection accepts exact remaining headroom')
for observed,_,limit in fields:
    v=dict(at_limit);v[observed]+=1
    try:scope['projected'](capacity,v,limits)
    except ValueError as e:ck(limit in str(e),'actual projection refuses one-unit excess '+limit)
    else:raise AssertionError('missing bound refusal '+limit)
out={'decision':'PRELIMINARY_SOURCE_CAPACITY_CHECKS_PASS_FINAL_ENTRY_WITHHELD','checks':checks,'references':refs,'read_bytes':count,'scope':'Exact31 entry substitution, current421local source hashes, accepted source correction/recovery anchors, unchanged prospective capacity terms and actual pure projection guard boundaries. Concrete gate/binding/release evidence and Root exact command still pending.','not_proved':['Independent current Git object joins (Root preparation reports421joins; genuine Root entry will authenticate committed refs)','actual live storage/RAM/runtime/native eligibility','final gate/input/binding joins','claim/admission/launch','performance or whole-job capacity'],'final_release':False}
with (P/'SOURCE_CHECK01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks),'read_bytes':count},sort_keys=True))
