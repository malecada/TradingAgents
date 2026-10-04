from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,stat,sys,subprocess,types,time
H=Path(__file__).resolve().parent;B=H.parent;N=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01');O=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');checks=[];readback=[];begun=time.monotonic()
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,pin=None):
 s=p.lstat();ok(p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded regular '+str(p));b=p.read_bytes();sg=lambda t:(t.st_dev,t.st_ino,t.st_mode,t.st_nlink,t.st_size,t.st_mtime_ns,t.st_ctime_ns);ok(sg(s)==sg(p.lstat()) and (pin is None or sha(b)==pin),'literal pin/signature '+str(p));readback.append({'path':str(p),'sha256':sha(b),'bytes':len(b),'mode':stat.S_IMODE(s.st_mode)});return b
src=read(N/'parent01.py','424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0');old=read(O/'parent01.py','7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3');qraw=read(N/'REQUEST_DRAFT01.json','e7579251741a865a2955917a3a9dc346ed6710ffc08388f1907c727e95d0a721');q=json.loads(qraw);inv=json.loads(read(N/'SOURCE_INVERSE01.json'));x=src.decode()
for e in reversed(inv['literal_changes']):ok(x.count(e['new'])==1,'exact unique inverse');x=x.replace(e['new'],e['old'],1)
ok(len(inv['literal_changes'])==22 and x.encode()==old,'22 full literal inverse');ok(ast.dump(ast.parse(x))==ast.dump(ast.parse(old)),'full AST inverse')
nt=ast.parse(src);ot=ast.parse(old);nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)};of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)}
for name in ['sha','require','reference','contract','stream_hash','memory','child_cleanup']:ok(ast.dump(nf[name])==ast.dump(of[name]),'unchanged function '+name)
for n in ['supervisor01.py','descendants01.py','owned_io.py','bounded_git01.py','recovery04.py','PROTOCOL_PINS01.json']:ok(read(N/n,q['helper_hashes'][n])==read(O/n),'unchanged original helper '+n)
pre=read(N/'preclaim01.py','557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16');ok(pre==read(B/'financial-wrapper-compatibility-preclaim-correction02-2026-10-04/preclaim01.py'),'accepted preclaim exact')
CAP=Path(q['capsule_root']);ok(q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None and set(q['proofs'])=={'cumulative','full_recovery','independent_source_input_runtime'} and q['proofs']['full_recovery'] is None and q['proofs']['independent_source_input_runtime'] is None,'real missing release fields');ok(len(q['helper_hashes'])==7 and q['caller_sha256']==sha(src),'sevenhelper/caller join')
env=dict(os.environ);env.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='');head=subprocess.run(['git','-C',str(CAP),'rev-parse','HEAD'],check=True,capture_output=True,env=env,timeout=10).stdout.decode().strip();ok(head==q['source']==q['design_source']=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','actual current source/design')
raw=subprocess.run(['git','-C',str(CAP),'ls-tree','-rz',head],check=True,capture_output=True,env=env,timeout=10).stdout;tree={}
for record in raw.split(b'\0'):
 if not record:continue
 meta,path=record.split(b'\t',1);mode,typ,oid=meta.decode().split();ok(typ=='blob' and mode in ('100644','100755'),'genuine tree type');tree[path.decode()]=(mode,oid)
ok(len(tree)==355 and set(tree)==set(q['source_files'])|{q['registration']},'complete355/354 source closure')
for n,(mode,oid) in tree.items():
 b=read(CAP/n,q['source_files'].get(n,q['registration_sha256']));ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'every committed blob current body');ok(bool((CAP/n).stat().st_mode&0o111)==(mode=='100755'),'Git executable class')
g=json.loads(read(CAP/q['registration'],q['registration_sha256']));e=g['experiments'][q['identity']];ok(e['parent'] is None and len(g['experiments'])==13 and e['source_files']==q['source_files'] and len(e['inputs'])==11,'genuine registration/reference topology');oldg=json.loads(read(CAP/'fixture_inputs/financial_wrapper_claimedrun01/gates.json'));ok(all(g['experiments'][k]==v for k,v in oldg['experiments'].items()),'all12 prior definitions identical')
for role,v in e['inputs'].items():read(CAP/v['path'],v['sha256']);ok(q['input_hashes'][role]==v['sha256'],'all11 input pins')
job=json.loads(read(CAP/e['inputs']['execution_job']['path']));plan=json.loads(read(CAP/e['inputs']['wrapper_plan']['path']));ok(plan['phase']=='complete100' and plan['experiment']==q['identity'] and plan['cell_id']=='financial-wrapper-classification-eager-reference-compatibility-20261004-01' and plan['prior_input'] is None and plan['reference_input'] is None,'independent100 fresh cell/prior/reference')
history=[]
for p in sorted((CAP/'research_runs').iterdir()):
 if p.name=='.lock':continue
 c=json.loads(read(p/'claim.json'));f=json.loads(read(p/'failed.json'));ok(not (p/'complete.json').exists() and f['claim_sha256']==sha((p/'claim.json').read_bytes()),'actual originalFAILED joins');history.append({'identity':p.name,'claim_sha256':sha((p/'claim.json').read_bytes()),'failed_sha256':sha((p/'failed.json').read_bytes()),'budget':c.get('effective_attempt_budget',c['family']['attempt_budget'])})
ok(len(history)==3 and max(x['budget'] for x in history)==19,'spent3 actualhigh19 remains')
ok(not os.path.lexists(N/'attempt') and not os.path.lexists(CAP/'research_runs'/q['identity']),'fresh prospective namespaces')
# Import ONLY the external stdlib parent/helper definitions, not project admission.
sys.path.insert(0,str(N));sp=importlib.util.spec_from_file_location('parent_review_only',N/'parent01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
ok(not any(x.split('.')[0] in ('numpy','torch','scipy','pandas','tradingagents') for x in sys.modules),'no scientific/project import')
ref={'path':str(N/'REQUEST_DRAFT01.json'),'sha256':sha(qraw)}
for name,call in [('validate',lambda:M.validate_release(copy.deepcopy(q))),('preflight',lambda:M.preflight(copy.deepcopy(q),ref))]:
 try:call()
 except ValueError as err:ok(str(err)=='no draft release','real draft early refusal '+name)
 else:raise AssertionError('draft accepted')
# A released status label alone cannot override the actual NULL release body.
for field in ['source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review']:
 z=copy.deepcopy(q);z['status']='RELEASED_ONE_USE_FINANCIAL_PARENT';z[field]=None
 try:M.validate_release(z)
 except ValueError:ok(True,'missing field refusal '+field)
 else:raise AssertionError('unresolved accepted')
# Inspect preflight AST: source metadata path has no direct creation/spawn/start.
for node in ast.walk(nf['preflight']):
 if isinstance(node,ast.Call):
  name=ast.unparse(node.func);ok(not name.endswith(('.mkdir','.start','.put','.Popen','.supervise')) and name not in ('supervise','launch'),'preflight no direct mutation/spawn '+name)
calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(nf['preflight']) if isinstance(n,ast.Call)];ok(any(n=='job._admitted' for _,n in calls) and any(n=='PRECLAIM.validate_preclaim' for _,n in calls),'genuine public prerequisite calls');ok(min(l for l,n in calls if n=='job._admitted')<min(l for l,n in calls if n=='PRECLAIM.validate_preclaim'),'admission then exact preclaim');ok('ResearchRun' not in src.decode(),'no artificial Run construction')
# unchanged real descriptor stream_hash and cleanup pair controls in reviewer-owned files.
p=H/'opaque02';p.write_bytes(b'opaque');ok(M.stream_hash(p,64)==sha(b'opaque'),'real bounded stream')
for limit in [0,5]:
 try:M.stream_hash(p,limit)
 except ValueError:ok(True,'extent refusal')
 else:raise AssertionError('extent accepted')
classes=[ValueError,MemoryError,KeyboardInterrupt,SystemExit];fatal=lambda v:isinstance(v,MemoryError) or not isinstance(v,Exception);fdcases=[]
for pc in classes:
 for sc in classes:
  primary=pc('read');secondary=sc('close');fds=[];proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});real=M.os
  def rd(fd,n):fds.append(fd);raise primary
  def cl(fd):os.close(fd);raise secondary
  proxy.read=rd;proxy.close=cl;M.os=proxy
  try:
   try:M.stream_hash(p,64)
   except BaseException as err:
    expected=primary if fatal(primary) else secondary if fatal(secondary) else None
    ok(err is expected if expected else isinstance(err,sys.modules['owned_io'].CleanupFailure),'original real cleanup firstfatal')
   else:raise AssertionError('fatal missing')
  finally:M.os=real
  for fd in fds:
   try:os.fstat(fd)
   except OSError:ok(True,'real owned descriptor absent')
   else:raise AssertionError('FD leaked')
  fdcases.append([pc.__name__,sc.__name__])
ok(not os.path.lexists(N/'attempt') and not os.path.lexists(CAP/'research_runs'/q['identity']) and not any(x.split('.')[0] in ('numpy','torch','scipy','pandas','tradingagents') for x in sys.modules),'no actual attempt/newclaim/project imports')
(H/'READBACK02.json').write_text(json.dumps({'assertions':len(checks),'checks':checks,'sources':readback,'history':history,'source':head,'typed_git_count':len(tree),'source_pins':354,'inputs':11,'fd_pairs':fdcases,'actual_draft_bytes':len(qraw),'caller_bytes':len(src),'full_preclaim_success':False,'actual_native_or_claim':False,'elapsed_seconds':time.monotonic()-begun},sort_keys=True,indent=2)+'\n');print(json.dumps({'assertions':len(checks),'source':head,'fd_pairs':len(fdcases),'native_or_claim':False}))
