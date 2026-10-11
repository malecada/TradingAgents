"""Independent runtime02 parser/environment join and fresh-public binding02 review."""
import ast,copy,datetime,difflib,hashlib,json,os,resource,shlex,signal,stat,sys
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];C=F/'real-data-pilot-full30-binding-preparation02-2026-10-11';O=F/'real-data-pilot-full30-binding-preparation01-2026-10-11';U=F/'matching-compiled-runtime-input02-2026-10-11';U0=F/'matching-compiled-runtime-input01-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(20,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(25)
checks=[];refs={};total=0
def ck(v,n):assert v,n;checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    global total
    p=Path(p);assert not {'real_pilot_runtime','keys','apis','.git','.venv'}&set(p.parts) and p.name not in {'connection.json','.env','hf_token.txt'}
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2;b=p.read_bytes();total+=len(b);assert total<12*1024**2
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
for root,h in [(U,'f03573b89b9657dd7a6bfe0c14d90bdc8133cc51c378aa013afec8331b393945'),(C,'dfb3b1a89e7317fe8588c6e95e602fe664d4545b0b846c95689d08e5d2f37f82')]:
    mb=read(root/'MANIFEST01.json');ck(sha(mb)==h,'external frozen manifest '+root.name)
    for name,pin in json.loads(mb)['files'].items():
        b=read(root/name);ck({'bytes':len(b),'sha256':sha(b)}==pin,'frozen artifact '+root.name+'/'+name)
ck(sha(read(F/'real-data-pilot-full30-binding-review01-2026-10-11/REVIEW01.json'))=='7bd51953fabb0d2484355743b60ec3320644a790392da11b1c5504c57d20f4a9','accepted01 wrapper/binder review anchor')
ck(sha(read(O/'BOUND01.json'))=='ed988bd2e19eb7e4dfacb98e73aca41fef825c389eeca0018a59a8353a35e3fa','old01 actual PUBLIC binding retained')
lineage=js(U/'LINEAGE01.json')
for name in ('caller','environment','original_inventory','original_runtime','parser'):
    pin=lineage[name];b=read(R/pin['path']);ck({'bytes':len(b),'sha256':sha(b),'path':pin['path']}==pin,'public lineage '+name)
oldruntime=js(U0/'RUNTIME_REFERENCE01.json');runtimeb=read(U/'RUNTIME_REFERENCE01.json');runtime=json.loads(runtimeb);inventory=js(U0/'INVENTORY01.json');envb=read(R/lineage['environment']['path']);envhash=sha(envb)
ck(len(runtimeb)==345 and sha(runtimeb)=='8135e84845eae061bfbb68c22fc825fd5614d9b6dc313e8b39a5a0d1f0df97fb' and runtimeb==raw(runtime),'actual canonical345B runtime02')
restored=dict(runtime);restored['runtime_inventory_sha256']=oldruntime['runtime_inventory_sha256'];ck(restored==oldruntime,'only semantic runtime inventory field changed')
ck(oldruntime['runtime_inventory_sha256']==sha(read(U0/'INVENTORY01.json')) and runtime['runtime_inventory_sha256']==envhash=='3a97a20ba8058cac81c8c62a7ba3596aac2fe4deb17627d0aa57bf53a93b86dc','old aggregate versus actual environment body join')
envrows=[x for x in inventory['references'] if x['path']==str(R/lineage['environment']['path'])];ck(len(envrows)==1 and envrows[0]['sha256']==envhash and envrows[0]['bytes']==len(envb) and len(inventory['references'])==6,'six-body historical inventory contains exact environment reference')
ck({k:runtime[k] for k in inventory['metadata']}==inventory['metadata'],'historical platform/version/executable fields preserved')
parser=ast.parse(read(R/lineage['parser']['path']));ns={'Path':Path,'json':json}
for n in parser.body:
    if isinstance(n,ast.Assign):
        for target in n.targets:
            if isinstance(target,ast.Name):ns[target.id]=ast.literal_eval(n.value)
nodes=[n for n in parser.body if isinstance(n,ast.FunctionDef) and n.name in {'require','digest','freeze','runtime_metadata'}]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-stdlib-parser-only>','exec'),ns)
ck(ns['runtime_metadata'](runtimeb)==runtime,'actual installed parser accepts corrected runtime metadata')
policy=js(U/'POLICY01.json');oldpolicy=js(U0/'POLICY01.json');ck(dict(ns['freeze'](policy))==policy,'actual installed freeze accepts corrected selection metadata')
for bad in [{**runtime,'python':'0'},{**runtime,'runtime_inventory_sha256':'G'*64},{**runtime,'extra':'value'},{**runtime,'numpy':None}]:
    try:ns['runtime_metadata'](raw(bad))
    except ValueError:checks.append('actual parser refuses malformed typed/runtime/digest/extra metadata')
    else:raise AssertionError('malformed runtime accepted')
caller=read(R/lineage['caller']['path']).decode();ck("runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256']" in caller,'genuinecaller environment predicate remains unchanged')
try:ns['require'](oldruntime['runtime_inventory_sha256']==envhash,'normalization inventory not joined to genuine environment input')
except ValueError:checks.append('actual require refuses old environment-join operands')
else:raise AssertionError('old join unexpectedly passed')
ns['require'](runtime['runtime_inventory_sha256']==envhash,'normalization inventory not joined to genuine environment input');checks.append('actual require accepts corrected environment-join operands; no Admission fabricated')
restored=dict(policy)
for field in ('runtime_path','runtime_sha256','runtime_bytes'):restored[field]=oldpolicy[field]
ck(restored==oldpolicy and policy['runtime_path']==str(U/'RUNTIME_REFERENCE01.json') and policy['runtime_sha256']==sha(runtimeb) and policy['runtime_bytes']==345,'only exact runtime path/hash/extent selection changes')
docs={p.stem:js(p) for p in sorted((C/'public01').glob('*.json'))};prior={p.stem:js(p) for p in sorted((O/'public01').glob('*.json'))};ck(set(docs)==set(prior),'same12 public template roles')
for role,doc in docs.items():
    restored=copy.deepcopy(doc)
    if role=='mcm_policy':restored['batched']['execution']['compiled_normalization_policy']=prior[role]['batched']['execution']['compiled_normalization_policy']
    if role=='archive_transport':ck(restored['connection'] is None and restored['namespace']=='ethpilot-20261011-30v2','new unbound transport namespace');restored['namespace']=prior[role]['namespace']
    if role=='archive_policy':ck(restored['transport_identity'] is None and restored['remote_namespace']=='ethpilot-20261011-30v2','new unbound archive namespace');restored['remote_namespace']=prior[role]['remote_namespace']
    if role=='execution_job':restored['payload']['representation_jobs']['original32']['descriptor']['compact_archive_execution']=prior[role]['payload']['representation_jobs']['original32']['descriptor']['compact_archive_execution']
    if role=='producer_plan':restored['producers']['original32']['descriptor']['compact_archive_execution']=prior[role]['producers']['original32']['descriptor']['compact_archive_execution']
    ck(restored==prior[role],'complete science/caps/public inverse '+role)
ck(read(C/'MATCHING_SCRATCH_RESERVATION01.json')==read(O/'MATCHING_SCRATCH_RESERVATION01.json'),'scratch identity and all cap bytes unchanged')
selected=docs['execution_job']['payload']['representation_jobs']['original32'];producer=docs['producer_plan']['producers']['original32'];ck(selected['descriptor']==producer['descriptor'] and docs['pilot']['resource_policy']==docs['execution_job']['resources'],'both actual descriptors and pilot resources agree')
for key,role in [('compact_archive_execution','archive_policy'),('compact_execution','compact_policy'),('pair_execution','pair_policy')]:ck(selected['descriptor'][key]['policy_sha256']==sha(raw(docs[role])),'canonical policy digest '+role)
public=js(C/'PUBLIC_INPUT_REFS_DRAFT01.json');previous=js(O/'PUBLIC_INPUT_REFS_DRAFT01.json');ck(set(public)==set(previous) and len(public)==66 and 'archive_transport' not in public,'unchanged66public+pendingopaque67role denominator')
ck(public['environment']==previous['environment'] and public['environment']['sha256']==envhash and public['environment']['path']==lineage['environment']['path'],'actual registered environment reference join')
changed=set(docs)-{'archive_transport'}|{'matching_ordered_edge_scratch','compiled_normalization_runtime'}
for role,pin in public.items():
    if role not in changed:ck(pin==previous[role],'unchanged inherited role '+role)
    else:ck(sha(read(R/pin['path']))==pin['sha256'] and pin['dataset']=='eth','actual changed public reference '+role)
execution=docs['mcm_policy']['batched']['execution'];ck(execution['compiled_normalization_policy']==policy,'MCM exactruntime02selection')
for kind,role in execution['compiled_normalization_inputs'].items():ck(str(R/public[role]['path'])==policy[kind+'_path'] and public[role]['sha256']==policy[kind+'_sha256'],'three-role policy reference '+kind)
prepared=js(C/'PREPARED01.json');request=js(C/'REQUEST01.json');ck(prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'},'actual prepared body set')
ck(request['connection']==js(O/'REQUEST01.json')['connection'],'unchanged connection PUBLIC reference only')
ck(request['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-30-02' and request['private_leaf']=='archive_transport01.json','new exact30-02 private route string only')
for name in ('prepared','archive_policy'):
    pin=request[name];b=read(R/pin['path']);ck(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'new request reference '+name)
ck(request['archive_policy']==prepared['builder03_spec']['references']['archive_policy'],'prepared/request archive join')
wrapper=read(C/'bind_actual01.py').decode();oldwrapper=read(O/'bind_actual01.py').decode();ck(wrapper.replace('pilot-transport-20261011-30-02','pilot-transport-20261011-30-01').replace('archive-dispatch-ethpilot-20261011-30v2','archive-dispatch-ethpilot-20261011-30')==oldwrapper,'entire wrapper inverse is only fresh private/namespace strings')
for token in ['not os.path.lexists(p)','parent.mkdir(mode=0o700,exist_ok=False)',"load(HERE/'REQUEST01.json')","save(HERE/'BOUND01.json',bound)",'module.bind(ROOT,request)']:ck(token in wrapper,'accepted one-use seam unchanged '+token)
# Verify each declared patch block by independent difflib reconstruction, never applying it.
for root in (C,U):
    patch=read(root/'LITERAL_PATCH01.diff').decode();lines=patch.splitlines(True);pairs=[]
    for i,line in enumerate(lines):
        if line.startswith('--- '):pairs.append((Path(line[4:].strip()),Path(lines[i+1][4:].strip())))
    rebuilt=[]
    for a,b in pairs:rebuilt.extend(difflib.unified_diff(read(a).decode().splitlines(True),read(b).decode().splitlines(True),fromfile=str(a),tofile=str(b)))
    ck(''.join(rebuilt)==patch,'actual literal patch inverse/reencoding '+root.name)
for name in ('BOUND01.json','inputs01','ALL_INPUT_REFS01.json','BINDING_CHECK01.json'):ck(not os.path.lexists(C/name),'fresh public output absent '+name)
ck(not os.path.lexists(R/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-30') and not os.path.lexists(R/'research_artifacts/archive-dispatch-ethpilot-20261011-30v2'),'fresh empirical30 claim/newdispatch namespace absent (public metadata only)')
command=read(C/'REPORT.md').decode().split('```sh\n',1)[1].split('\n```',1)[0];argv=shlex.split(command)
ck(argv==['taskset','-c','3','nice','-n','10','prlimit','--cpu=30','--as=536870912','--fsize=4194304','--','.venv/bin/python','-B',str((C/'bind_actual01.py').relative_to(R))],'exact Root offline one-use v2 command')
ck(not any(n.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for n in sys.modules),'no native/scientific imports')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'RELEASE_EXACT_RUNTIME02_AND_FULL30V2_OFFLINE_BINDING_ONCE','checks':checks,'references':refs,'read_bytes':total,'cwd':str(R),'argv':argv,'command':command,'old_environment_join':False,'new_environment_join':True,'new_runtime_bytes':345,'private_or_connection_target_reads_hashes_stats':False,'binder_or_authority_execution':False,'old_inventory_exclusions_preserved':inventory['excluded'],'limitations':['Runtime metadata observation age and exclusions persist; no current package/library/loaded runtime proof.','New private parent existence/currentness is intentionally uninspected; actual wrapper must enforce its one-use checks.','Actual v2binding/opaque67th/current gate/source/native/admission/accounting and external recovery remain pending.','No empirical30 claim or allowance101 adoption is made; unchanged input identities do not supply authority.']}
with (P/'CHECKS01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','old_inventory_exclusions_preserved','limitations','argv','command')}));print('checks',len(checks))
