"""Read-only Main baselines and extracted public metadata joins; no Git/native/science."""
import ast,copy,difflib,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent;checks=[]
def ck(v,n):assert v,n;checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
plan=json.loads((P/'INSTALLATION_PLAN01.json').read_bytes());requirements=json.loads((P/'SOURCE_REQUIREMENTS01.json').read_bytes());files=json.loads((P/'PROSPECTIVE_NUMERICAL_FILES01.json').read_bytes());patch=[];inverse=[]
for item in plan['modules']:
 target=R/item['destination'];source=R/item['bundle_source'];body=source.read_bytes();old=target.read_bytes() if target.exists() else b'';baseline=item['required_base']
 ck((not target.exists()) if baseline.get('absent') else sha(old)==baseline['sha256'] and len(old)==baseline['bytes'],'actual baseline '+target.name)
 ck(sha(body)==item['result_sha256']==requirements[item['destination']]['sha256'] and body==(R/item['accepted_source']['path']).read_bytes(),'exact accepted installation body '+target.name);ast.parse(body)
 a=''.join(difflib.unified_diff(old.decode().splitlines(True),body.decode().splitlines(True),fromfile=item['destination'] if target.exists() else '/dev/null',tofile=item['destination']));b=''.join(difflib.unified_diff(body.decode().splitlines(True),old.decode().splitlines(True),fromfile=item['destination'],tofile=item['destination'] if target.exists() else '/dev/null'))
 ck(a==(P/(target.name+'.patch')).read_text() and b==(P/(target.name+'.inverse.patch')).read_text(),'literal inverse '+target.name);patch.append(a);inverse.append(b)
ck(''.join(patch)==(P/'BUNDLE.patch').read_text() and ''.join(inverse)==(P/'BUNDLE.inverse.patch').read_text(),'combined patches exact')
job=R/plan['source_enumerator']['path'];tree=ast.parse(job.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');ns={'Path':Path,'__file__':str(job)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'source-enumerator-only','exec'),ns)
ck(set(files)==ns['required_sources']()|set(requirements) and len(files)==200,'genuine conservative source enumeration198 plus2helpers')
ck(all(digest==requirements[name]['sha256'] if name in requirements else digest==sha((R/name).read_bytes()) for name,digest in files.items()),'all prospective200 source hashes are actual body joins')
# Trace the real module aliases from retained import declarations/checkpoint dependencies.
aliases={'compiled_normalization_policy':'compiled_normalization_policy.py','adaptive_edge_policy':'adaptive_edge_policy.py','accepted':'batched_pair_executor.py','engine':'matching_checkpoint.py','engine.ann':'matching_annealing.py','engine.hard':'matching_hardening.py','engine.sparse':'matching_sparse.py','engine.ann.typed_identity':'matching_identity.py','pair':'matching_pair.py','reference':'matching_reference.py','contracts':'contracts.py','immutable_session':'matching_immutable_session.py'}
memo=ast.parse((P/'batched_numeric_reuse.py').read_bytes());pins=next(n.value for n in memo.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_PINS' for t in n.targets))
for entry in pins.elts:
 alias=ast.unparse(entry.elts[0]);digest=ast.literal_eval(entry.elts[1]);ck(files['tradingagents/research/onchain_replication/'+aliases[alias]]==digest,'actual memo source dependency '+alias)
policy=json.loads((P/'POLICY_TEMPLATE01.json').read_bytes());roles=json.loads((P/'ROLE_INPUT_REFS_TEMPLATE01.json').read_bytes());ck(len(roles)==5 and len(set(roles))==5,'five distinct typed roles')
for key in ('source','adapter','library','runtime','abi'):
 role='compiled_edge_'+key;row=roles[role];ck(str(R/row['path'])==policy[key+'_path'] and row['sha256']==policy[key+'_sha256'],'role policy join '+key)
 if key=='adapter':ck(files[row['path']]==row['sha256'],'adapter registered source/input join')
 else:ck(sha((R/row['path']).read_bytes())==row['sha256'],'immutable external role '+key)
old_docs={Path(name).stem:json.loads((R/ref['path']).read_bytes()) for name,ref in plan['public_metadata_baselines'].items()};mcm=json.loads((P/'MCM_POLICY_TEMPLATE01.json').read_bytes());without=copy.deepcopy(mcm);del without['batched']['execution']['compiled_edge_policy'];del without['batched']['execution']['compiled_edge_inputs'];ck(without==old_docs['mcm_policy'],'all original solver numeric neural caps and policy preserved outside two edge selection keys')
source=(P/'prepare_public_joins01.py').read_text();tree=ast.parse(source);functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('raw','updated_documents')];ns={'hashlib':hashlib,'json':json};exec(compile(ast.Module(body=functions,type_ignores=[]),'metadata-joins-only','exec'),ns)
updated=ns['updated_documents'](copy.deepcopy(old_docs),mcm,files,'0'*40) # explicit synthetic anchor; never emitted as a real policy/claim
ck(updated['pair_policy']['numerical_source']=={'commit':'0'*40,'files':files},'future committed closure inserted at exact pair seam')
pair_restore=copy.deepcopy(updated['pair_policy']);pair_restore['numerical_source']=old_docs['pair_policy']['numerical_source'];ck(pair_restore==old_docs['pair_policy'],'pair numerical configuration preserved')
oldhash=sha(ns['raw'](old_docs['pair_policy']));newhash=sha(ns['raw'](updated['pair_policy']))
for name in ('producer_plan','execution_job'):
 restored=json.loads(json.dumps(updated[name]).replace(newhash,oldhash));ck(restored==old_docs[name],'genuine '+name+' descriptor policy hash only changed')
ck(not (P/'committed-public-joins01').exists(),'actual postcommit generator unexecuted')
(P/'ASSEMBLY_CHECK01.json').write_text(json.dumps({'status':'PASS_SOURCE_AND_PUBLIC_METADATA_ONLY','checks':checks,'git_executed':False,'actual_authority':False,'native_or_numeric_execution':False,'installed':False},indent=2)+'\n');print(len(checks),'checks')
