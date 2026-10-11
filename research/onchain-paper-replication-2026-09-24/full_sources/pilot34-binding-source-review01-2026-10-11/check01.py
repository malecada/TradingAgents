import ast,copy,difflib,hashlib,json,os,re,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=Path(__file__).resolve().parent;D=F/'real-data-pilot-full34-binding-preparation01-2026-10-11';O=F/'real-data-pilot-full33-binding-preparation01-2026-10-11';checks=[];refs={};ANCHOR='d8c878e9a81e32c2fc98894f74acece465078f82'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def ck(v,n):assert v,n;checks.append(n)
def ref(p):return {'path':str(p.relative_to(R)),**refs.get(str(p.relative_to(R)),{})}
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
for mn in ['SOURCE_MANIFEST01.json','MANIFEST01.json']:
 m=js(D/mn)
 for name,pin in m['files'].items():b=read(D/name);ck(sha(b)==pin['sha256'] and len(b)==pin['bytes'],'manifest '+mn+' '+name)
ck(sha(read(O/'MANIFEST01.json'))=='29e15f65c52c91456a4830ba83e698abcfea3e55fe9757b5be4e07e3183c0145','accepted33 template manifest')
for name,pin in js(O/'MANIFEST01.json')['files'].items():ck(sha(read(O/name))==pin['sha256'],'unchanged accepted33 '+name)
oldwrap=read(O/'bind_actual01.py').decode();wrapper=read(D/'bind_actual01.py').decode();expected=oldwrap.replace('20261011-33','20261011-34');ck(wrapper==expected and ast.dump(ast.parse(wrapper.replace('20261011-34','20261011-33')))==ast.dump(ast.parse(oldwrap)),'wrapper exact literal and AST inverse')
for name,old,new in [('GENERATOR_LITERAL_PATCH01.diff',O/'build_public01.py',D/'build_public01.py'),('GENERATOR_LITERAL_INVERSE01.diff',D/'build_public01.py',O/'build_public01.py')]:
 text=''.join(difflib.unified_diff(read(old).decode().splitlines(True),read(new).decode().splitlines(True),fromfile=str(old.relative_to(R)),tofile=str(new.relative_to(R))))
 ck(text==read(D/name).decode(),'exact '+name)
gen=ast.parse(read(D/'build_public01.py'));fn=next(n for n in gen.body if isinstance(n,ast.FunctionDef) and n.name=='main');first=fn.body[0]
for bad in [None,'','pending','0'*39,'G'*40,12,True]:
 try:exec(compile(ast.Module(body=[first],type_ignores=[]),'anchor-guard','exec'),{'anchor':bad,'re':re})
 except AssertionError:pass
 else:raise AssertionError('invalid anchor accepted')
checks.append('actual first anchor assertion rejects invalid before writes/Git')
docs={p.stem:js(p) for p in sorted((D/'public01').glob('*.json'))};prior={p.stem:js(p) for p in sorted((O/'public01').glob('*.json'))};ck(set(docs)==set(prior) and len(docs)==12,'exact12 public roles')
num=docs['pair_policy']['numerical_source'];ck(num['commit']==ANCHOR and len(num['files'])==198,'actual198 commit')
job=R/'tradingagents/research/onchain_replication/job.py';tree=ast.parse(read(job));required=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');ns={'Path':Path,'__file__':str(job)};exec(compile(ast.Module(body=[required],type_ignores=[]),'actual-required-source-function','exec'),ns);ck(set(num['files'])==ns['required_sources'](),'genuine required198 exact')
ck([p for p,h in num['files'].items() if prior['pair_policy']['numerical_source']['files'][p]!=h]==['tradingagents/research/onchain_replication/compact_mcm.py'] and num['files']['tradingagents/research/onchain_replication/compact_mcm.py']=='abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8','sole cadence source difference')
paths=sorted(num['files']);out=subprocess.check_output(['git','-c','core.packedGitWindowSize=16m','-c','core.packedGitLimit=64m','cat-file','--batch'],input=''.join(ANCHOR+':'+p+'\n' for p in paths).encode(),cwd=R,timeout=30);pos=0
for path in paths:
 end=out.index(b'\n',pos);oid,kind,size=out[pos:end].split();assert kind==b'blob';pos=end+1;size=int(size);body=out[pos:pos+size];pos+=size;assert out[pos:pos+1]==b'\n';pos+=1
 ck(body==read(R/path) and sha(body)==num['files'][path],'actual committed/current source '+path)
ck(pos==len(out),'finite Git batch framing consumed')
back=copy.deepcopy(docs);back['pair_policy']['numerical_source']=prior['pair_policy']['numerical_source'];back['archive_policy']['remote_namespace']=prior['archive_policy']['remote_namespace'];back['archive_transport']['namespace']=prior['archive_transport']['namespace']
for role,key in [('execution_job','resources'),('pilot','resource_policy')]:
 budget=docs[role][key]['storage_budget'];ck(budget['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-34' and budget['roots'][1]==str(R/'research_runs'/budget['experiment']),'fresh storage '+role)
 back[role][key]['storage_budget']['experiment']=prior[role][key]['storage_budget']['experiment'];back[role][key]['storage_budget']['roots'][1]=prior[role][key]['storage_budget']['roots'][1]
for role,route in [('execution_job',('payload','representation_jobs')),('producer_plan',('producers',))]:
 a=docs[role];b=back[role];o=prior[role]
 for k in route:a=a[k];b=b[k];o=o[k]
 for policy,key in [('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')]:
  ck(a['original32']['descriptor'][key]['policy_sha256']==sha(raw(docs[policy])),'actual descriptor '+role+' '+key);b['original32']['descriptor'][key]['policy_sha256']=o['original32']['descriptor'][key]['policy_sha256']
ck(back==prior,'full12 document inverse proves unchanged scientific/model/motif/sample/caps policies')
ck(docs['archive_policy']['remote_namespace']==docs['archive_transport']['namespace']=='ethpilot-20261011-34' and docs['archive_policy']['transport_identity'] is None and docs['archive_transport']['connection'] is None,'exact unbound namespace')
prepared=js(D/'PREPARED01.json');oldprepared=js(O/'PREPARED01.json');ck(prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'} and len(prepared['builder03_result']['inputs'])==11,'11prepared excluding archive policy')
for pin in [prepared['builder03_spec']['references']['archive_policy']]:ck(pin==ref(D/'public01/archive_policy.json'),'archive public prepared ref')
req=js(D/'REQUEST01.json');oldreq=js(O/'REQUEST01.json');ck(req['prepared']==ref(D/'PREPARED01.json') and req['archive_policy']==ref(D/'public01/archive_policy.json') and req['connection']==oldreq['connection'] and req['private_leaf']==oldreq['private_leaf'] and req['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-34-01','request public/opaque-reference joins; no target read')
inputs=js(D/'PUBLIC_INPUT_REFS_DRAFT01.json');oldinputs=js(O/'PUBLIC_INPUT_REFS_DRAFT01.json');ck(len(inputs)==66 and set(inputs)==set(oldinputs) and 'archive_transport' not in inputs,'66draft add one opaque only through binder')
for role,pin in inputs.items():
 if role in docs:ck(pin=={**oldinputs[role],'path':str((D/'public01'/(role+'.json')).relative_to(R)),'sha256':sha(raw(docs[role]))},'rebased public input '+role)
 else:ck(pin==oldinputs[role],'unchanged opaque input reference '+role)
binder=F/'real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py';ck(sha(read(binder))=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb','original binder immutable')
for p in [R/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-34',R/'research_artifacts/archive-dispatch-ethpilot-20261011-34',R/req['private_parent'],D/'BOUND01.json',D/'inputs01',D/'ALL_INPUT_REFS01.json',D/'BINDING_CHECK01.json']:ck(not os.path.lexists(p),'fresh one-use metadata path '+str(p.relative_to(R)))
result={'decision':'ACCEPT_EXACT_ACTUAL34_PUBLIC_SOURCE_AND_OFFLINE_BINDER_COMMAND_ONLY','checks':checks,'references':refs,'source_anchor':ANCHOR,'public_roles':12,'prepared_roles':11,'draft_roles':66,'expected_bound_roles':67,'exact_root_command':'taskset -c 3 nice -n 10 prlimit --cpu=30 --as=536870912 --fsize=4194304 -- .venv/bin/python -B '+str((D/'bind_actual01.py').relative_to(R)),'limitations':['No binder/private body/scientific/native/admission execution.','Read-only finite Git cat-file batch authenticated actual198 bodies; no Git mutation/network.','Source report and ROOT_PREPARATION descriptive Fresh33 wording are inherited stale labels; actual identities/namespace/commit/refs independently authentic34.','Only offline binding command released; actual resulting67refs/source-entry/release/admission remain separate.']}
(P/'REVIEW01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'review_sha256':sha((P/'REVIEW01.json').read_bytes())}))
