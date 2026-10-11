"""Finite independent source/command joins; never import the reviewed modules."""
import ast,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
HERE=Path(__file__).resolve().parent;F=HERE.parent;R=F.parents[2]
Q=F/'pilot34-native-owner-qualification03-2026-10-11';OLD=F/'pilot34-native-owner-qualification02-2026-10-11'
checks=[];refs={}
def read(p):
 p=Path(p);raw=p.read_bytes();assert len(raw)<2*1024**2
 refs[str(p.relative_to(R))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};return raw
def obj(p):return json.loads(read(p))
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)});assert v,n
def pinned(ref):
 p=Path(ref['path']);raw=read(p);ck(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'actual bytes: '+p.name);return raw
manifest=obj(Q/'MANIFEST03.json');command=obj(Q/'COMMAND03.json')
ck(refs[str((Q/'MANIFEST03.json').relative_to(R))]['sha256']=='1075a8aab7fcc90f606a8dc8cf90ba95165e22d4cdd67172ce3b68880d91ab0f','exact frozen Q03 manifest')
ck(refs[str((Q/'COMMAND03.json').relative_to(R))]['sha256']=='0efabea315da864d19829e1f3658edbe1c3e970e78a3043b6d1b9fb722a0869f','exact frozen command')
for ref in manifest['bodies'].values():pinned(ref)
old=pinned(manifest['predecessor_script']).decode();new=pinned(command['script']).decode()
ck(old.replace('edge-owner-and-kernel-qualification-20261011-02','edge-owner-and-kernel-qualification-20261011-03')==new and old.count('edge-owner-and-kernel-qualification-20261011-02')==1,'sole exact identity-string replacement; full numerical/reporting/resource body unchanged')
ck(ast.dump(ast.parse(new.replace('edge-owner-and-kernel-qualification-20261011-03','edge-owner-and-kernel-qualification-20261011-02')))==ast.dump(ast.parse(old)),'full AST inverse')
previous=json.loads(pinned(command['predecessor_command']))
ck(command['maximum_attempts']==previous['maximum_attempts']==1 and command['outer_timeout_seconds']==previous['outer_timeout_seconds']==60,'unchanged one attempt and outer60s')
ck(command['cwd']==str(R) and command['argv'][:3]==[str(R/'.venv/bin/python'),'-B',str(Q/'qualify03.py')],'exact interpreter cwd script')
a=command['argv'];opts=dict(zip(a[3::2],a[4::2]));ck(len(a)==17 and set(opts)=={'--owner','--owner-sha256','--kernel','--kernel-sha256','--baseline-sha256','--policy','--policy-sha256'},'exact seven argument pairs')
C=F/'matching-compiled-two-attribute-caller-candidate03-2026-10-11';cm=json.loads(pinned(command['candidate_manifest']))
ck(command['candidate_manifest']['sha256']=='fafd78521d0576756018c3b73c1f1adf809490fa3220112b54f3a3b2075a8b4a','selected caller03 manifest')
for flag,name in [('owner','compiled_edge_owner.py'),('kernel','matching_annealing.py')]:
 raw=read(C/name);ck(opts['--'+flag]==str(C/name) and hashlib.sha256(raw).hexdigest()==opts['--'+flag+'-sha256']==cm['files'][name]['sha256'] and len(raw)==cm['files'][name]['bytes'],'exact '+flag+' selected source')
base=read(R/'tradingagents/research/onchain_replication/matching_annealing.py');ck(hashlib.sha256(base).hexdigest()==opts['--baseline-sha256']=='eb509ecf5c9ed7d28783b1a4230013ddcba8036a0fb5174d3aaa60307fc63b43','unchanged actual reference kernel')
policy=obj(Q/'POLICY_ROLE03.json');ck(opts['--policy']==str(Q/'POLICY_ROLE03.json') and refs[str((Q/'POLICY_ROLE03.json').relative_to(R))]['sha256']==opts['--policy-sha256'],'exact policy argument')
roles=command['role_references'];ck(set(roles)=={'source','adapter','library','runtime','abi'},'exact five role denominator')
for role,ref in roles.items():
 pinned(ref);ck(policy[role+'_path']==ref['path'] and policy[role+'_sha256']==ref['sha256'],'policy joins '+role)
for role in ('runtime','abi'):ck(policy[role+'_bytes']==roles[role]['bytes'],'metadata extent '+role)
owner=ast.parse(read(C/'compiled_edge_owner.py'));constants={}
for n in owner.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  try:constants[n.targets[0].id]=ast.literal_eval(n.value)
  except ValueError:pass
ck(set(policy)==constants['FIELDS'] and policy['format']==constants['FORMAT'],'actual owner exact policy fields and format')
ck(all(policy[r+'_sha256']==constants[r.upper()] for r in ('source','adapter','library')),'actual owner compiled role constants')
runtime=json.loads(read(roles['runtime']['path']));abi=json.loads(read(roles['abi']['path']))
ck(runtime['executable']==a[0] and runtime['python']=='3.13.13' and abi['cache_tag']=='cpython-313' and runtime['platform']=='linux','declared runtime/ABI/interpreter join, not observed native proof')
ck(new.index("out.mkdir(mode=0o700, exist_ok=False)")<new.index('import numpy as np') and "result_path.open('xb')" in new,'exclusive attempt before numerical imports and exclusive result')
ck(not (Q/'attempt01').exists(),'attempt absent at read-only review time')
ck(command['actual_native_execution'] is False and command['status']=='QUEUED_UNRELEASED' and any('increment28' in x for x in command['required_before_launch']),'prospective conditional launch and recovery prerequisite')
reuse=F/'matching-compiled-two-attribute-qualification-source-review03-2026-10-11/REVIEW01.json';read(reuse)
ck(refs[str(reuse.relative_to(R))]['sha256']=='dcf05fea48f4ffd4b2a99cdf91fe951b92f77bac399a3cdef70a30e0093cce3d','accepted02 source/reporting/resource evidence reused')
result={'status':'PASS_SOURCE_AND_ENTRY_JOINS_ONLY','checks':checks,'references':refs,'native_scientific_or_harness_execution':False,'library_handling':'hash and extent only; no decode or load','fresh_eligibility_observed':False}
with (HERE/'CHECK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'checks':len(checks)}))
