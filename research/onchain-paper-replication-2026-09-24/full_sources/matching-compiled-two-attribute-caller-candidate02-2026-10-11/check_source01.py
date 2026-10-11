"""Actual extracted validators with immutable byte transport doubles, no Admission/Owner."""
import ast,copy,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];O=F/'matching-compiled-two-attribute-caller-candidate01-2026-10-11';checks=[]
def ck(v,n):assert v,n;checks.append(n)
def require(v,n):
 if not v:raise ValueError(n)
owner_source=(P/'compiled_edge_owner.py').read_text();tree=ast.parse(owner_source);ns={'Path':Path,'json':json}
nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in ('require','freeze','abi_metadata')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-policy-parser','exec'),ns)
policy=json.loads((P/'POLICY_TEMPLATE01.json').read_text());roles={k:'edge_'+k for k in ('source','adapter','library','runtime','abi')};body_by_path={}
for k in roles:
 path=Path(policy[k+'_path']);body=(P/'edge_chunk_adapter.py').read_bytes() if k=='adapter' else path.read_bytes();assert hashlib.sha256(body).hexdigest()==policy[k+'_sha256'];body_by_path[path]=body
runtime=json.loads(body_by_path[Path(policy['runtime_path'])]);environment_path=F/'real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/environment.json';body_by_path[environment_path]=environment_path.read_bytes();assert hashlib.sha256(body_by_path[environment_path]).hexdigest()==runtime['runtime_inventory_sha256']
inputs={roles[k]:{'path':str(Path(policy[k+'_path']).relative_to(R)),'sha256':policy[k+'_sha256']} for k in roles};inputs['environment']={'path':str(environment_path.relative_to(R)),'sha256':runtime['runtime_inventory_sha256']}
def run_validator(directory,body_override=None,execution_override=None,input_override=None,source_override=None,genuine_override=None):
 bodies=dict(body_by_path);bodies.update(body_override or {});calls=[]
 def read_reference(path,digest,limit,size=None,owned=False):
  body=bodies[Path(path)];calls.append((Path(path),size,owned))
  require(len(body)<=limit and (size is None or len(body)==size),'extent mismatch')
  require(hashlib.sha256(body).hexdigest()==digest,'hash mismatch');return body
 edge=types.SimpleNamespace(freeze=ns['freeze'],abi_metadata=ns['abi_metadata'],read_reference=read_reference)
 metadata=copy.deepcopy(inputs);metadata.update(input_override or {})
 source_files={'tradingagents/research/onchain_replication/edge_chunk_adapter.py':policy['adapter_sha256']};source_files.update(source_override or {})
 # Plain transport doubles only: no actual admission or research authority construction.
 ad=types.SimpleNamespace(root=R,inputs=metadata,experiment={'source_files':source_files})
 reads=[]
 def read_input(role):
  reads.append(role)
  if genuine_override and role in genuine_override:return genuine_override[role]
  return bodies[R/metadata[role]['path']]
 run=types.SimpleNamespace(admission=ad,read_input=read_input)
 env={'require':require,'compiled_edge_owner':edge,'compiled_normalization_policy':types.SimpleNamespace(runtime_metadata=json.loads)}
 tree=ast.parse((directory/'compact_mcm_batched.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_edge_policy','_edge_inputs')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-five-role-validator','exec'),env)
 execution={'compiled_edge_policy':dict(policy),'compiled_edge_inputs':roles} if execution_override is None else execution_override
 try:return env['_edge_inputs'](execution,run),None,calls,reads
 except ValueError as error:return None,str(error),calls,reads
v,error,calls,reads=run_validator(O);ck(error=='extent mismatch' and calls[-1][1]==17072,'predecessor RED21920 rejected by hardcoded17072')
v,error,calls,reads=run_validator(P);ck(error is None and dict(v)==policy,'successor GREEN21920 genuine helper accepts exact roles')
ck([r for r in reads]==list(roles.values())+['environment'] and len(calls)==6,'all five role reads and environment read preserved')
ck(next(c[1:] for c in calls if c[0]==Path(policy['library_path']))==(21920,True),'library extent and owned flag exact')
for size in (17072,21919,21921):
 v,error,*_=run_validator(P,{Path(policy['library_path']):bytes(size)});ck(error=='extent mismatch','new policy refuses library extent '+str(size))
legacy=json.loads((F/'pilot34-native-owner-qualification01-2026-10-11/POLICY_ROLE01.json').read_text())
v,error,calls,reads=run_validator(P,execution_override={'compiled_edge_policy':legacy,'compiled_edge_inputs':roles});ck(error=='unsupported edge bodies' and not calls,'legacy policy remains refused before reads')
v,error,calls,reads=run_validator(P,execution_override={});ck(v is None and error is None and not calls and not reads,'default None still performs zero role reads')
for kwargs,label in [({'genuine_override':{'edge_source':b'bad'}},'genuine source body'),({'source_override':{'tradingagents/research/onchain_replication/edge_chunk_adapter.py':'0'*64}},'adapter source join'),({'input_override':{'edge_library':dict(inputs['edge_library'],sha256='0'*64)}},'registered library hash')]:
 v,error,*_=run_validator(P,**kwargs);ck(error is not None,'unchanged refusal '+label)
old=(O/'compact_mcm_batched.py').read_text();new=(P/'compact_mcm_batched.py').read_text();change=json.loads((P/'CHANGE01.json').read_text());ck(new.replace(change['after'],change['before'])==old,'entire compact inverse only extent expression')
for a,b,n in ((old,new,'FORWARD.patch'),(new,old,'INVERSE.patch')):ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='compact_mcm_batched.py',tofile='compact_mcm_batched.py'))==(P/n).read_text(),'literal '+n)
req=json.loads((P/'SOURCE_REQUIREMENTS01.json').read_text());changed=[]
for rel,row in req.items():
 n=Path(rel).name;body=(P/n).read_bytes();ast.parse(body);ck(hashlib.sha256(body).hexdigest()==row['sha256'] and len(body)==row['bytes'],'exact source requirement '+n)
 if body!=(O/n).read_bytes():changed.append(n)
 ck(change['old_compact_hash'] not in body.decode(),'no stale embedded compact hash '+n)
ck(changed==['compact_mcm_batched.py'],'nine route/helper bodies unchanged')
ck((P/'POLICY_TEMPLATE01.json').read_bytes()==(O/'POLICY_TEMPLATE01.json').read_bytes(),'template exact unchanged new-format references')
ck("admission.experiment['source_files'].get(relative)==file_hash(root/relative)" in new and "own_source='tradingagents/research/onchain_replication/compact_mcm_batched.py'" in new,'compact self-source uses genuine dynamic registered roster')
(P/'SOURCE_RESULT01.json').write_text(json.dumps({'status':'PASS_FOCUSED_ACTUAL_AST_RED_TO_GREEN','checks':checks,'native_loaded':False,'scientific_imports':False,'actual_admission_or_owner':False,'numeric_execution':False},indent=2)+'\n');print(len(checks),'checks')
