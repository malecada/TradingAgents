import ast,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-recordfix-capture-preparation01-2026-10-04';Q=F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
ck(sha((O/'MANIFEST02.json').read_bytes())=='c83889ab848947f4639c8e96454d316e568de0cc552767c10f6c286f5f91c25a','prior review02 unchanged')
for r in json.loads((O/'MANIFEST02.json').read_bytes())['members']:
 p=O/r['path'];st=p.lstat();ck(stat.S_IMODE(st.st_mode)==r['mode'],'original mode unchanged')
 if r['kind']=='file':ck(st.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'original full review01/02 body unchanged')
 elif r['kind']=='symlink':ck(os.readlink(p)==r['target'],'original symlink text unchanged')
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('actual_capture_review',P/'capture01.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C);a=C.R
read=lambda p:a.read(p.parent,p.name)
def doc(p):return json.loads(read(p))
t=doc(Q/'ACTUAL_TERMINAL02.json');D=Path(t['original_output_root']);q=doc(D/'request.json');m=doc(D/'source-manifest.json');terminal=doc(D/'terminal.json');auth=doc(D/'source-authentication.json')
ck(sha(read(D/'request.json'))=='b6d6486622cea62c40317b1c554451bd01e0d60a55a4a0b4e798939a950bcadf' and C.contract(q)=='5aaf7cda0a06d94164c39b27d49ae2a5c8694d1b7b80f6c39f39704e987c20ce','actual request exact released contract')
ck(q['release']=={'path':str(O/'EXACT_RELEASE02.json'),'sha256':'155193e3e4ac07621fd3de5a69af18ed7666c03c5333fbf0d764e6205fdfdf4a'},'genuine actual release ref')
ck(set(p.name for p in D.iterdir())=={r['path'] for r in t['original_files']} and len(t['original_files'])==5 and stat.S_IMODE(D.stat().st_mode)==0o700,'exact original fivefile private output')
for row in t['original_files']:
 p=D/row['path'];b=read(p);st=p.lstat();ck(stat.S_IMODE(st.st_mode)==row['original_posix_mode']==0o600 and st.st_nlink==1 and len(b)==row['bytes'] and sha(b)==row['sha256'] and b==read(Q/row['path']),'every original0600/Maincopy byte and mode metadata')
ck(m==q['manifest']==a.scan(C.CAP) and a.digest(a.encode(m))==q['manifest_sha256']=='26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53','full actual current986 mode/body manifest')
ck(a.encode(C.authenticate())==a.encode(auth) and sha(read(D/'source-authentication.json'))=='a73865063fc845dd824cb2b8ddaaa0cf8445c216e93674d6b5ca259f55bfe336','complete325 Git324pins8roles194149 current authentication')
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';defs=[n for n in ast.parse(read(prior)).body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')];exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'))
raw=read(D/'source.tar.gz');ck(sha(raw)=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb' and len(raw)==3481434==terminal['archive']['bytes'],'actual archive exact extent/hash')
bodies,framing=decode(raw,m);ck(recode(m,bodies)==raw,'entire canonical compressed archive reconstruction')
for row in m['members']:
 if row['kind']=='file':ck(bodies[row['path']]==read(C.CAP/row['path']),'every actual archived/current opaque body')
ck(len(m['members'])==986 and len(bodies)==713 and sum(len(b) for b in bodies.values())==8642839,'full tree regular and logical extent')
gate=json.loads(bodies[C.GATE]);exp=gate['experiments'][C.IDENTITY]
for n,h in exp['source_files'].items():ck(sha(bodies[n])==h,'all324 recovered source pins')
for role,ref in exp['inputs'].items():ck(sha(bodies[ref['path']])==ref['sha256'],'all8 archived role inputs')
ck(terminal['status']=='COMPLETE_BYTES_ONLY' and terminal['error_type'] is None and terminal['source']==C.SOURCE and terminal['external_recovery'] is False and terminal['runtime_bodies'] is False and terminal['scientific_credit']==0,'actual complete local-only disposition')
ck(len(terminal['observed_free_bytes'])==4 and all(x>=a.FLOOR for x in terminal['observed_free_bytes']),'four genuine sampled10GiB floors')
ck(sha(read(D/'terminal.json'))==t['actual_original_terminal_sha256']=='550554037a4aece6f204fcb94cd7e406c2388ccfd2254df180316271d81257c4','actual original terminal hash')
stdout=read(Q/'ACTUAL_CAPTURE02.out');stderr=read(Q/'ACTUAL_CAPTURE02.err');ck(t['actual_exit']==0 and t['actual_session']==44125 and t['actual_start_tool']=='e91e69' and t['actual_completion_tool']=='d218f1' and sha(stdout)==t['actual_stdout_sha256'] and sha(stderr)==t['actual_stderr_sha256'] and not stderr and json.loads(stdout)==terminal['archive'],'actual parentexit tools stdout stderr')
ck(read(Q/'REQUEST_FINAL02.json')==read(D/'request.json'),'Root final request identical')
ck(all(not os.path.lexists(C.CAP/n) for n in ['research_runs','research_artifacts','fixture_outer']),'current zero claims/native output namespaces')
processes=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:cwd=os.readlink(p/'cwd')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if cwd in [str(C.CAP),str(D)]:processes.append(int(p.name))
ck(not processes,'no observed source/output cwd processes')
ck(a.scan(C.CAP)==m and a.encode(C.authenticate())==a.encode(auth),'final complete actual current source stable')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_ACTUAL_COMPLETE_LOCAL_RECORDFIX_SOURCE_CAPTURE_ONLY','checks':len(checks),'source':C.SOURCE,'request_sha256':sha(read(D/'request.json')),'release_sha256':q['release']['sha256'],'manifest_sha256':q['manifest_sha256'],'archive':terminal['archive'],'original_terminal_sha256':sha(read(D/'terminal.json')),'actual_root_terminal_sha256':sha(read(Q/'ACTUAL_TERMINAL02.json')),'original_output_root':str(D),'typed_members':986,'regular_bodies':713,'logical_bytes':8642839,'framing':framing,'tracked':325,'source_pins':324,'implementation':194,'package':149,'original_file_modes':t['original_files'],'actual_exit':0,'actual_claims':0,'original_capture_PID':None,'PID_qualification':'Original helper/intent/terminal do not record PID; actual tool exit0 authenticated, no current source/output cwd process observed. No invented specific PID/group absence.','current_source_output_cwd_processes':processes,'external_or_flat_recovery':False,'runtime_store_POSIX_capacity_numerical_authority':False}
(O/'ACTUAL_CAPTURE_READBACK03.json').write_bytes(a.encode(out));print(json.dumps(out,indent=2))
