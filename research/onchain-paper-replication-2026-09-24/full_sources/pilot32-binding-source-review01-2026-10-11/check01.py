"""Exact public32 rebasing and offline caller review. No private body or binder execution."""
import ast,copy,hashlib,json,os,resource,signal,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));signal.alarm(40)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full32-binding-preparation01-2026-10-11';O=F/'real-data-pilot-full31-binding-preparation03-2026-10-11';ANCHOR='3d07e4cc06cd37352ac633d69ab781a7955b656b';N='eth-paper-real-data-end-to-end-resource-20261011-32';OLD=N.replace('-32','-31');checks={};evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def rb(p):
 assert not ({'.git','.venv','keys','apis','research_artifacts','research_runs'}&set(p.parts));assert p.name not in {'connection.json','archive_transport01.json'}
 b=p.read_bytes();assert len(b)<2*1024**2;evidence[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def j(p):return json.loads(rb(p))
def ref(p):
 b=rb(p);return {'path':str(p.relative_to(R)),'bytes':len(b),'sha256':sha(b)}
def ck(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def encode(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def save(name,v):
 with (P/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
try:
 prior=j(F/'pilot31-binding-source-entry-review03-2026-10-11/REVIEW01.json');ck(prior['decision']=='RELEASE_EXACT_PILOT31_BINDER03_ONCE','accepted predecessor exact source and caller')
 ck(ref(O/'MANIFEST01.json')==prior['manifest'] and ref(O/'PREPARED01.json')==prior['prepared'] and ref(O/'REQUEST01.json')==prior['request'] and ref(O/'bind_actual01.py')==prior['wrapper'],'authenticated predecessor anchors')
 m=j(D/'MANIFEST01.json');ck(m['status']=='DRAFT_NOT_RELEASED','current preparation remains draft')
 for name,row in m['files'].items():ck(ref(D/name)==row,'exact frozen member '+name)
 olddocs={p.stem:j(p) for p in sorted((O/'public01').glob('*.json'))};docs={p.stem:j(p) for p in sorted((D/'public01').glob('*.json'))};ck(set(docs)==set(olddocs) and len(docs)==12,'exact12public roster')
 numeric=docs['pair_policy']['numerical_source'];oldnumeric=olddocs['pair_policy']['numerical_source'];pins=numeric['files'];changed=[p for p in pins if pins[p]!=oldnumeric['files'].get(p)]
 ck(numeric['commit']==ANCHOR and len(pins)==198 and set(pins)==set(oldnumeric['files']) and changed==['tradingagents/research/onchain_replication/real_pilot_import_caller.py'],'198complete numerical closure with sole caller change')
 ck(pins[changed[0]]=='f65ff353315bfb9e4db80d326170e02e5b2ebc6da1e5d59e5a8e9243b4afd11a','exact reviewed preload installed pin')
 source_review=j(F/'pilot31-loaded-identity-correction-review01-2026-10-11/REVIEW01.json');ck(source_review['candidate']['sha256']==pins[changed[0]] and source_review['decision']=='ACCEPT_EXACT_PREACTIVATION_HELPER_PRELOAD_SOURCE','accepted preload review joins')
 required_tree=ast.parse(rb(R/'tradingagents/research/onchain_replication/job.py'));function=next(n for n in required_tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');scope={'Path':Path,'__file__':str(R/'tradingagents/research/onchain_replication/job.py')};exec(compile(ast.Module(body=[function],type_ignores=[]),'actual-source-roster-only','exec'),scope)
 ck(set(scope['required_sources']())==set(pins),'actual required_sources complete198 denominator')
 local={p:rb(R/p) for p in pins};ck(all(sha(b)==pins[p] for p,b in local.items()),'all198 actual current bodies authenticate')
 command=['git','-c','core.packedGitWindowSize=16m','-c','core.packedGitLimit=64m','cat-file','--batch'];query=('\n'.join(ANCHOR+':'+p for p in pins)+'\n').encode();proc=subprocess.run(command,cwd=R,input=query,capture_output=True,timeout=20);(P/'git-batch.stderr').write_bytes(proc.stderr);ck(proc.returncode==0 and proc.stderr==b'','independent actual readonly Git batch exit0')
 pos=0;joined=[]
 for p,b in local.items():
  end=proc.stdout.index(b'\n',pos);head=proc.stdout[pos:end].split();pos=end+1;size=int(head[2]);assert len(head)==3 and head[1]==b'blob' and size==len(b);assert proc.stdout[pos:pos+size]==b and proc.stdout[pos+size:pos+size+1]==b'\n';pos+=size+1;joined.append({'path':p,'bytes':size,'sha256':sha(b),'git_oid':head[0].decode()})
 ck(pos==len(proc.stdout) and len(joined)==198,'independent all198 exact Git/current body joins with no batch suffix')
 actualgit={'argv':command,'source':ANCHOR,'exit_code':proc.returncode,'stderr_bytes':len(proc.stderr),'stdout_bytes':len(proc.stdout),'stdout_sha256':sha(proc.stdout),'query_sha256':sha(query),'files':joined};save('ACTUAL_GIT_JOIN01.json',actualgit)
 rootjoin=j(D/'CURRENT_NUMERICAL_GIT_JOIN01.json');ck(rootjoin['source']==ANCHOR and rootjoin['count']==198 and rootjoin['files']==joined and rootjoin['actual_git_batch_stdout_sha256']==actualgit['stdout_sha256'],'Root original Git receipt independently reproduced')
 # Reconstruct predecessor documents by reversing only exact selected changes.
 inverse=copy.deepcopy(docs);inverse['pair_policy']['numerical_source']=oldnumeric
 ck(docs['archive_policy']['remote_namespace']==docs['archive_transport']['namespace']=='ethpilot-20261011-32' and docs['archive_policy']['transport_identity'] is None and docs['archive_transport']['connection'] is None,'fresh32 public namespace and unbound opaque placeholder')
 inverse['archive_policy']['remote_namespace']=olddocs['archive_policy']['remote_namespace'];inverse['archive_transport']['namespace']=olddocs['archive_transport']['namespace']
 for role,key in [('execution_job','resources'),('pilot','resource_policy')]:
  budget=inverse[role][key]['storage_budget'];ck(budget['experiment']==N and budget['roots'][1]==str(R/'research_runs'/N),'fresh32 storage scope '+role);budget['experiment']=OLD;budget['roots'][1]=str(R/'research_runs'/OLD)
 ck(docs['execution_job']['resources']==docs['pilot']['resource_policy'],'exact two resource policies equal')
 for role,branch in [('execution_job',('payload','representation_jobs')),('producer_plan',('producers',))]:
  parent=docs[role];invparent=inverse[role];oldparent=olddocs[role]
  for key in branch:parent=parent[key];invparent=invparent[key];oldparent=oldparent[key]
  ck(set(parent)=={'original32'},'single original32 descriptor '+role)
  for policy,key in [('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')]:
   ck(parent['original32']['descriptor'][key]['policy_sha256']==sha(encode(docs[policy])),'actual canonical '+policy+' digest in '+role)
   invparent['original32']['descriptor'][key]['policy_sha256']=oldparent['original32']['descriptor'][key]['policy_sha256']
 ck(inverse==olddocs,'full12 JSON inverse preserves every scientific method cell policy cap and old sample identity')
 prepared=j(D/'PREPARED01.json');oldprepared=j(O/'PREPARED01.json');ck(prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'} and len(prepared['builder03_result']['inputs'])==11,'exact11 preparedroles exclude archive policy collision')
 inv=copy.deepcopy(prepared);inv['builder03_result']['inputs']=oldprepared['builder03_result']['inputs'];ck(prepared['builder03_spec']['references']['archive_policy']==ref(D/'public01/archive_policy.json'),'prepared correct archive reference');inv['builder03_spec']['references']['archive_policy']=oldprepared['builder03_spec']['references']['archive_policy'];ck(inv==oldprepared,'whole prepared JSON inverse')
 request=j(D/'REQUEST01.json');oldrequest=j(O/'REQUEST01.json');ck(set(request)==set(oldrequest) and request['prepared']==ref(D/'PREPARED01.json') and request['archive_policy']==ref(D/'public01/archive_policy.json'),'exact request shape and public pins');ck(request['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-32-01' and request['private_leaf']==oldrequest['private_leaf']=='archive_transport01.json' and request['connection']==oldrequest['connection'],'fresh private32 literal and unchanged opaque connection ref only')
 references=j(D/'PUBLIC_INPUT_REFS_DRAFT01.json');oldrefs=j(O/'PUBLIC_INPUT_REFS_DRAFT01.json');ck(len(references)==66 and set(references)==set(oldrefs) and 'archive_transport' not in references,'exact66draft public roles no opaque role')
 expected=copy.deepcopy(oldrefs)
 for role in docs:
  if role!='archive_transport':row=ref(D/'public01'/(role+'.json'));expected[role].update(path=row['path'],sha256=row['sha256'])
 ck(expected==references,'exact all66 ref inverse no unrelated input change')
 wrapper=rb(D/'bind_actual01.py');oldwrapper=rb(O/'bind_actual01.py');ck(wrapper==oldwrapper.replace(b'pilot-transport-20261011-31-03',b'pilot-transport-20261011-32-01').replace(b'20261011-31',b'20261011-32'),'literal wrapper only fresh identity and private route changed')
 ck(ref(R/prior['binder']['path'])==prior['binder'],'unchanged accepted original binder02 bytes')
 public_fresh=[D/'BOUND01.json',D/'inputs01',D/'ALL_INPUT_REFS01.json',D/'BINDING_CHECK01.json',R/'research_runs'/N,R/'research_artifacts/archive-dispatch-ethpilot-20261011-32'];ck(all(not os.path.lexists(p) for p in public_fresh),'actual current public output and claim/archive paths unused')
 argv=prior['argv'][:-1]+[str((D/'bind_actual01.py').relative_to(R))]
 result={'schema_version':1,'decision':'RELEASE_EXACT_PILOT32_BINDER01_ONCE','identity':N,'reviewer':'independent outcome16_release_review','cwd':str(R),'argv':argv,'command':' '.join(argv),'source_anchor':ANCHOR,'manifest':ref(D/'MANIFEST01.json'),'prepared':ref(D/'PREPARED01.json'),'request':ref(D/'REQUEST01.json'),'wrapper':ref(D/'bind_actual01.py'),'binder':prior['binder'],'checks':checks,'evidence':evidence,'actual_git_join':ref(P/'ACTUAL_GIT_JOIN01.json'),'scope':'One-use offline fresh32 binding source/caller only. Exact198 actual Git/current source join, installed f65 caller and literal/full JSON inverse against accepted31prep03.','conditions':['Root executes exact argv once with original one-use/private ownership/freshness/current body checks. Private parent/connection/key/body were not inspected by reviewer.','Preserve partial/failed output and refuse retry under same namespace.','Independently authenticate actual returned public67/opaque ref; regenerate full exact source/numerical/gate/admission/current-entry and preservation before any fresh attempt.'],'limits':['No binder/private/connection/credential execution or inspection; no native/arrays/science/Owner/admission/claim.','Read-only Git batch authenticated only the finite declared198 source bodies; no Git writes or network.','Original scientific cells/caps/sample identities preserved, not revalidated numerically. No budget extension, new exposure, capacity or financial/speed claim.']}
 save('REVIEW01.json',result);print(json.dumps({'decision':result['decision'],'checks':len(checks),'review_sha256':sha((P/'REVIEW01.json').read_bytes()),'manifest_sha256':result['manifest']['sha256'],'wrapper_sha256':result['wrapper']['sha256']},sort_keys=True))
except BaseException as e:
 save('FAILED_CHECK01.json',{'error':repr(e),'checks':checks,'evidence':evidence});raise
