import pathlib,os,stat,json,hashlib,ast,importlib.util,types,copy,time
H=pathlib.Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-compatibility-operational-delta-flat-source-mode-successor04-2026-10-04';D=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';checks=[];cases=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(v,s):
 if not v:raise AssertionError(s)
 checks.append(s)
def refuse(f,s):
 try:f()
 except (ValueError,OSError) as e:cases.append({'name':s,'refused':True,'error_type':type(e).__name__,'message':str(e)});ok(True,s)
 else:raise AssertionError('accepted '+s)
def auth(root,pin):
 raw=(root/'MANIFEST01.json').read_bytes();ok(sha(raw)==pin,'manifest pin '+root.name);m=json.loads(raw);rows=m['members']
 for r in rows:
  p=root/r['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'],'mode '+str(p))
  if r['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+str(p))
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'directory '+str(p))
  elif r['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal symlink '+str(p))
  else:raise AssertionError(r)
 return len(rows)
auth(A,'29db85f0e660532afd721f6889c3b34322737ab3c4a9739a37bf2bf6e292225a')
for z in json.loads((A/'AUTHENTICATION01.json').read_bytes())['lineages']:auth(pathlib.Path(z['root']),z['manifest_sha256'])
old=(A/'ORIGINAL_restore01.py').read_bytes();new=(A/'restore01.py').read_bytes();inv=json.loads((A/'SOURCE_INVERSE01.json').read_bytes());rest=new.decode()
for e in reversed(inv['edits']):ok(rest.count(e['new'])==1,'unique inverse replacement');rest=rest.replace(e['new'],e['old'],1)
ok(rest.encode()==old and ast.dump(ast.parse(rest))==ast.dump(ast.parse(old)),'full literal/AST inverse');ok(sha(new)=='17f4ee85d2408cdc1b678e107e82b6e19b674b4b941f1fa51f40f17bbedef282','candidate exact')
def nodes(b):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
u,v=nodes(old),nodes(new);ok(set(u)==set(v) and {n for n in u if u[n]!=v[n]}=={'VerifiedCohort','authenticate_selected','run'},'all other definition AST identical')
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('review_new',A/'restore01.py');O=load('review_old',A/'ORIGINAL_restore01.py')
for n,p in M.PINS.items():ok(sha((A/n).read_bytes())==p,'exact metadata/helper '+n)
for n in O.PINS:ok(M.PINS[n]==O.PINS[n],'unchanged utility '+n)
remote=json.loads((D/'REMOTE_RECOVERY01.json').read_bytes());selection=json.loads((D/'SELECTED_BODIES01.json').read_bytes());sp=sha((D/'SELECTED_BODIES01.json').read_bytes())
def actual_snapshot():
 return {str(p):((p.lstat().st_dev,p.lstat().st_ino,p.lstat().st_mode,p.lstat().st_uid,p.lstat().st_size,p.lstat().st_mtime_ns,p.lstat().st_ctime_ns),sha(p.read_bytes()) if p.is_file() else None) for p in [D/'selected',*(D/'selected').rglob('*'),D/'REMOTE_RECOVERY01.json',D/'SELECTED_BODIES01.json',D/'ROOT_REMOTE03_EXIT01.json']}
before=actual_snapshot();refuse(lambda:O.authenticate_selected(D,remote,selection,sp),'actual original03 RM1')
c=M.VerifiedCohort();got=M.authenticate_selected(D,remote,selection,sp,c);c.check();ok(len(got)==15 and sum(x['bytes'] for x in got)==507946,'actual completed input accepted exactly15/507946');ok(len(c.selected_profile['directory_modes'])==7 and len(c.byte_proofs)==21,'exact modes and complete prerequisite byte cohort')
for root in [H,H/'unrelated',D.parent]:refuse(lambda root=root:M.authenticate_selected(root,remote,selection,sp),'wrong fixed receiver '+str(root))
for field,value in [('remote_commit','0'*40),('selected_count',14),('status','COMPLETE'),('genuine_run_or_native_started',True)]:
 r=copy.deepcopy(remote);r[field]=value;refuse(lambda r=r:M.authenticate_selected(D,r,selection,sp),'remote argument mutation '+field)
refuse(lambda:M.authenticate_selected(D,remote,selection,'0'*64),'wrong selection hash')
# Alter only returned read bytes, never original receipt/profile/source files.
for name in ['COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json','COMPLETED_REMOTE_REVIEW_MACHINE01.json','COMPLETED_REMOTE_REVIEW_MANIFEST01.json','ROOT_REMOTE03_EXIT01.json']:
 original=M.R.read
 def altered(root,n,limit=M.R.FILE):
  b=original(root,n,limit)
  return b+b' ' if n==name else b
 M.R.read=altered
 try:refuse(lambda:M.authenticate_selected(D,remote,selection,sp),'dependency byte substitution '+name)
 finally:M.R.read=original
# Profile does not widen genuinely owned output roots or unlisted children.
for mode in [0o775,0o755,0o777]:
 p=H/('output-mode-'+oct(mode));p.mkdir(mode=0o700);p.chmod(mode);refuse(lambda p=p:c.anchor(p),'unrelated nonprivate output '+oct(mode))
for case in ['file-mode','extra','symlink','hardlink','child-mode']:
 p=H/('output-'+case);p.mkdir(mode=0o700);f=p/'a';f.write_bytes(b'opaque');f.chmod(0o600)
 if case=='file-mode':f.chmod(0o644)
 if case=='extra':(p/'extra').write_bytes(b'x')
 if case=='symlink':(p/'link').symlink_to('a')
 if case=='hardlink':os.link(f,p/'alias')
 if case=='child-mode':(p/'dir').mkdir(mode=0o755)
 refuse(lambda p=p:c.tree(p,{'a'}),'private output '+case)
# Real later descriptor-close mutates an earlier proven body/mode/name/metadata/cross-scope.
for label,Mx in [('old03',O),('new04',M)]:
 for kind in ['bytes','mode','foreign','metadata','cross-scope']:
  p=H/(label+'-'+kind);p.mkdir(mode=0o700);p2=p/'other';p2.mkdir(mode=0o700)
  first=p/'metadata' if kind=='metadata' else p/'first';last=p2/'last';first.write_bytes(b'opaque-first');last.write_bytes(b'opaque-last');first.chmod(0o600);last.chmod(0o600)
  co=Mx.VerifiedCohort();co.read(p,first.name);co.tree(p,{first.name,'other/last'});trigger=last.stat();real=Mx.R.os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});did=[]
  def close(fd):
   s=os.fstat(fd);os.close(fd)
   if not did and (s.st_dev,s.st_ino)==(trigger.st_dev,trigger.st_ino):
    did.append(True)
    if kind=='mode':first.chmod(0o644)
    elif kind=='foreign':(p/'foreign').write_bytes(b'x')
    else:
     first.write_bytes(b'changed-first');s=first.stat();os.utime(first,ns=(s.st_atime_ns,s.st_mtime_ns+1000000))
  proxy.close=close;Mx.R.os=proxy
  try:co.read(p2,'last');refuse(co.check,label+' later real close '+kind)
  finally:Mx.R.os=real
  ok(bool(did),'actual descriptor trigger '+label+kind)
# Retained-profile final check still includes reads from earlier scopes after later callback.
p=H/'final-callback';p.mkdir(mode=0o700);f=p/'body';f.write_bytes(b'x');f.chmod(0o600);co=M.VerifiedCohort();M.authenticate_selected(D,remote,selection,sp,co);co.read(p,'body');co.tree(p,{'body'});f.write_bytes(b'y');s=f.stat();os.utime(f,ns=(s.st_atime_ns,s.st_mtime_ns+1000000));refuse(co.check,'final boundary changes earlier own body with inputprofile retained')
# Direct deadline/finite limits and original fatal propagation do not acquire retry semantics.
co=M.VerifiedCohort();co.deadline=time.monotonic()-1;refuse(co.check,'expired final cohort deadline');co=M.VerifiedCohort();co.pins={str(i):None for i in range(32769)};refuse(co.tick,'member cap unchanged')
for primary in [KeyboardInterrupt(),SystemExit(9),MemoryError()]:
 secondary=OSError('close');seen=[]
 try:M.R._cleanup((lambda:seen.append(1),lambda:(_ for _ in ()).throw(secondary)),primary=primary)
 except BaseException as e:ok(e is primary and seen==[1],'first fatal unchanged '+type(primary).__name__)
 else:raise AssertionError('fatal swallowed')
ok(actual_snapshot()==before,'all actual completed input signatures/modes/bytes remain unchanged')
run=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='run');calls=[ast.unparse(n) for n in run.body];ok(sum('cohort.check()'==x for x in calls)==2 and calls[-2]=='cohort.check()','cohort after final sidecar boundary retained')
ok('cohort.read(HERE, \'FLAT_RECOVERY01.json\')' in ast.unparse(run),'published receipt byte read remains');ok(not any(isinstance(n,ast.Call) and ast.unparse(n.func)=='cohort.read' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='FLAT_POSTWRITE_OBSERVATION01.json' for n in ast.walk(run)),'sidecar remains explicit outside byte cohort')
result={'status':'PASS_SOURCE_ONLY_FIXED_COMPLETED_INPUT_PROFILE','assertions':len(checks),'checks':checks,'cases':cases,'actual_records':len(got),'actual_bytes':sum(x['bytes'] for x in got),'actual_profile':c.selected_profile,'actual_unchanged':True,'public_run_or_entry':False,'actual_restoration':None,'numerical_authority':False,'sidecar_byte_cohort':False}
(H/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':result['status'],'assertions':len(checks),'cases':len(cases)}))
