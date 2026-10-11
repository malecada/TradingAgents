import ast,copy,difflib,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent;O=F/'real-data-pilot-full34-binding-preparation01-2026-10-11';checks=[]
def ck(v,n):assert v,n;checks.append(n)
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=(P/'build_public01.py').read_text();tree=ast.parse(source);wrapper=(P/'bind_actual01.py').read_text();ast.parse(wrapper)
ck(wrapper==(O/'bind_actual01.py').read_text().replace('20261011-34','20261011-35').replace('len(refs)==67','len(refs)==72'),'wrapper exact two-literal inverse retains original binder and all one-use guards')
ck("EXPECTED='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'" in wrapper,'immutable binder02 hash unchanged')
ck("HERE.name=='real-data-pilot-full35-binding-preparation01-2026-10-11'" in source and 'anchor==EXPECTED_ANCHOR' in source,'candidate refuses execution outside actual fresh35 route or wrong source anchor')
ns={'ROOT':R};assigns=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('EXPECTED_ANCHOR','PRIOR_MANIFEST','JOIN_PINS','JOIN_REFS','EDGE_REFS')];exec(compile(ast.Module(body=assigns,type_ignores=[]),'literal-pins-only','exec'),ns)
ck(sha(O/'MANIFEST01.json')==ns['PRIOR_MANIFEST'],'prior34 frozen manifest pinned')
for path,digest in ns['JOIN_PINS'].items():ck(sha(R/path)==digest,'accepted join reference '+Path(path).name)
joins=json.loads(ns['JOIN_REFS'].read_bytes());docs={p.stem:json.loads(p.read_bytes()) for p in (O/'public01').glob('*.json')};base=copy.deepcopy(docs)
for role,pin in joins.items():ck(sha(R/pin['path'])==pin['sha256'],'committed body '+role);docs[role]=json.loads((R/pin['path']).read_bytes())
ck(docs['pair_policy']['numerical_source']['commit']==ns['EXPECTED_ANCHOR'] and len(docs['pair_policy']['numerical_source']['files'])==200,'actual53b889200 source closure')
ck(all(sha(R/path)==digest for path,digest in docs['pair_policy']['numerical_source']['files'].items()),'all200 current body joins without Git execution')
edge=json.loads(ns['EDGE_REFS'].read_bytes());refs=json.loads((O/'PUBLIC_INPUT_REFS_DRAFT01.json').read_bytes());ck(len(refs)==66 and not set(refs)&set(edge) and len(edge)==5,'five new distinct roles and66old draft references');refs.update({role:{**pin,'dataset':'eth'} for role,pin in edge.items()});ck(len(refs)==71 and len(refs)+1==72,'71draft72bound role counts')
for role,pin in edge.items():ck(sha(R/pin['path'])==pin['sha256'],'actual installed backend role '+role)
# Execute only exact existing storage/descriptor rebase loops against copied public metadata.
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
loops=[n for n in main.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id in ('policy','item')]
env={'docs':docs,'ROOT':R,'PRIOR':'eth-paper-real-data-end-to-end-resource-20261011-34','NAME':'eth-paper-real-data-end-to-end-resource-20261011-35','hashlib':hashlib,'raw':raw}
docs['archive_policy']['remote_namespace']='ethpilot-20261011-35';docs['archive_transport']['namespace']='ethpilot-20261011-35';exec(compile(ast.Module(body=loops,type_ignores=[]),'public-storage-and-descriptor-loops-only','exec'),env)
ck(docs['execution_job']['resources']==docs['pilot']['resource_policy'],'job and pilot resource policies remain identical')
for role in ('pair_policy','archive_policy'):
 key='pair_execution' if role=='pair_policy' else 'compact_archive_execution';digest=hashlib.sha256(raw(docs[role])).hexdigest()
 ck(all(d['descriptor'][key]['policy_sha256']==digest for d in (docs['producer_plan']['producers']['original32'],docs['execution_job']['payload']['representation_jobs']['original32'])),'both genuine descriptor joins '+role)
for name in ('compact_policy','mcm_output_policy','original_import','resource_population_plan','typed_payload'):ck(docs[name]==base[name],'unchanged scientific policy '+name)
ck(docs['mcm_policy']==json.loads((R/joins['mcm_policy']['path']).read_bytes()),'exact accepted selected mcm body retained')
# New routes mentioned explicitly; no binder/sourcebuilder invocation in this checker.
ck("'research_artifacts/archive-dispatch-ethpilot-20261011-35'" in source and "pilot-transport-20261011-35-01" in source,'fresh archive and private parent paths')
forward=[];inverse=[]
for name in ('build_public01.py','bind_actual01.py'):
 a=(O/name).read_text();b=(P/name).read_text();forward.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name));inverse.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile=name,tofile=name))
(P/'FORWARD.patch').write_text(''.join(forward));(P/'INVERSE.patch').write_text(''.join(inverse))
(P/'SOURCE_CHECK01.json').write_text(json.dumps({'status':'PASS_BOUNDED_SOURCE_AND_PUBLIC_METADATA_ONLY','checks':checks,'builder_executed':False,'binder_executed':False,'git_executed':False,'numerical_imports':False,'registration_or_admission':False},indent=2)+'\n');print(len(checks),'checks')
