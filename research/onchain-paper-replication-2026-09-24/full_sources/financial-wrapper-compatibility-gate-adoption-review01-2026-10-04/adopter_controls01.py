"""Candidate functions and exact predicate slices on owned opaque fixtures only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,stat,types
D=Path(__file__).resolve().parent;F=D.parent;S=F/'heartbeat-root-checkpoint10-2026-10-04/root_compatibility_gate_adopt01.py';source=S.read_bytes();assert hashlib.sha256(source).hexdigest()=='f8aad6a7eab5f484036ae27d8c25ba1620be651c437644fcd8aca218686982c8';(D/'ADOPTER_SOURCE01.py').write_bytes(source)
spec=importlib.util.spec_from_file_location('adopter',S);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');owned=D/'owned-controls01';owned.mkdir(mode=0o700);rows=[]
# Exact trusted Reader/ownedIO prefix, not an automatic acceptance of added writer.
A=F/'financial-wrapper-compatibility-composed-recovery-correction02-2026-10-04/verify02.py';prefix=source.split(b'# Root-owned one-use metadata integration;')[0];original=A.read_bytes().split(b'def seal(')[0];assert prefix==original
rows.append({'case':'full literal accepted dependency prefix','sha256':hashlib.sha256(prefix).hexdigest(),'passed':True})
def fatal(e):return e is not None and (isinstance(e,MemoryError) or not isinstance(e,Exception))
def reaches(root,target):
 todo=[root];seen=set()
 while todo:
  e=todo.pop()
  if e is target:return True
  if id(e) in seen:continue
  seen.add(id(e))
  if isinstance(e,BaseException):
   todo.extend(BaseException.__dict__['__dict__'].__get__(e).values())
   for key in ['__cause__','__context__']:
    v=BaseException.__dict__[key].__get__(e)
    if v is not None:todo.append(v)
   if isinstance(e,BaseExceptionGroup):todo.extend(BaseExceptionGroup.__dict__['exceptions'].__get__(e))
  elif isinstance(e,(tuple,list)):todo.extend(e)
 return False
for ptype in [None,ValueError,MemoryError,KeyboardInterrupt,SystemExit]:
 for stype in [None,OSError,MemoryError,KeyboardInterrupt,SystemExit]:
  p=owned/('write-'+str(len(rows)));real=M.os;proxy=types.SimpleNamespace(**vars(os));fds=[];closed=[];primary=None if ptype is None else ptype('body');secondary=None if stype is None else stype('close');escaped=None
  def open(*a,**k):fd=os.open(*a,**k);fds.append(fd);return fd
  def write(fd,b):
   if primary is not None:
    os.write(fd,b[:1]);raise primary
   return os.write(fd,b)
  def close(fd):
   os.close(fd);closed.append(fd)
   if secondary is not None:raise secondary
  proxy.open=open;proxy.write=write;proxy.close=close;M.os=proxy
  try:
   try:M.put(p,b'opaque-body')
   except BaseException as e:escaped=e
  finally:M.os=real
  assert closed==fds and len(fds)==1
  if fatal(primary):assert escaped is primary
  elif fatal(secondary):assert escaped is secondary
  elif secondary is not None:assert isinstance(escaped,M.IO.CleanupFailure)
  elif primary is not None:assert escaped is primary
  else:assert escaped is None and p.read_bytes()==b'opaque-body'
  for e in (primary,secondary):
   if e is not None:assert reaches(escaped,e)
  for fd in fds:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('FD leak')
  assert p.exists() and stat.S_IMODE(p.lstat().st_mode)==0o600
  if primary is not None:assert p.read_bytes()==b'o'
  rows.append({'case':'real partial write/close precedence','primary':None if ptype is None else ptype.__name__,'secondary':None if stype is None else stype.__name__,'actualFDclosed_once':True,'partial_preserved':primary is not None})
def refused(name,f):
 try:f()
 except BaseException as e:rows.append({'case':name,'refused':True,'type':type(e).__name__});return
 raise AssertionError('accepted '+name)
existing=owned/'existing';existing.write_bytes(b'original');refused('exclusive no overwrite',lambda:M.put(existing,b'changed'));assert existing.read_bytes()==b'original'
link=owned/'symlink';link.symlink_to(existing);refused('exclusive no symlink follow',lambda:M.put(link,b'changed'));assert existing.read_bytes()==b'original'
big=owned/'oversize';refused('4MiB output before open',lambda:M.put(big,b'x'*(M.FILE+1)));assert not big.exists()
zero=owned/'zero-write';real=M.os;proxy=types.SimpleNamespace(**vars(os));proxy.write=lambda fd,b:0;M.os=proxy
try:refused('zero write stops',lambda:M.put(zero,b'opaque'))
finally:M.os=real
assert zero.exists() and zero.read_bytes()==b''
# Pure genuine preview predicates: no accepted release machine is manufactured.
PREVIEW=F/'financial-wrapper-compatibility-gate-preview02-2026-10-04';preview=json.loads((PREVIEW/'PREVIEW01.json').read_bytes());code=compile(ast.Module(body=[n for n in main.body if 154<=n.lineno<=157],type_ignores=[]),'<exact preview predicates>','exec')
def preview_pred(q):
 ns=dict(M.__dict__);ns['preview']=q;exec(code,ns)
preview_pred(preview);rows.append({'case':'actual pinned preview scalar/path predicates','passed':True})
import copy
for field,value in [('status','foreign'),('source_before','0'*40),('root','/foreign'),('identity','foreign'),('parent','foreign'),('roles',10),('source_pins',353),('prospective_tracked',354),('actual_highest',18),('actual_spent_failed',2),('prospective_amendment',21),('old_experiments_preserved',11)]:
 q=copy.deepcopy(preview);q[field]=value;refused('preview inverse '+field,lambda q=q:preview_pred(q))
q=copy.deepcopy(preview);key=next(iter(q['new_file_pins']));q['new_file_pins']['outside/name']=q['new_file_pins'].pop(key);refused('outside destination refuses',lambda:preview_pred(q))
# Complete terminal preservation predicates on a small OWNED opaque population.
terminal=[n for n in main.body if 187<=n.lineno<=196];terminal_code=compile(ast.Module(body=terminal,type_ignores=[]),'<exact terminal slice>','exec')
for failure in [None,'old-body','old-mode','old-inode','new-body','new-mode','extra-member','oldgate','head','newdir-mode']:
 cap=owned/('terminal-'+str(len(rows)));cap.mkdir(mode=0o700);(cap/'.git').mkdir(mode=0o700);(cap/'.git/HEAD').write_bytes(b'opaque-head\n');(cap/'old-dir').mkdir(mode=0o700);oldfile=cap/'old-dir/body';oldfile.write_bytes(b'old body');oldfile.chmod(0o600);oldgate=cap/'old-gate';oldgate.write_bytes(b'old gate');oldgate.chmod(0o600);before_reader=M.Reader();before=before_reader.tree(cap,('.git',));oldrows={'old-dir':{'kind':'directory','mode':0o700},'old-dir/body':{'kind':'file','mode':0o600,'bytes':8,'sha256':M.h(b'old body')},'old-gate':{'kind':'file','mode':0o600,'bytes':8,'sha256':M.h(b'old gate')}};before_reader.read(oldgate);before_reader.finish();newdir='new';(cap/newdir).mkdir(mode=0o700);files={'new/body':b'new body'};M.put(cap/'new/body',b'new body');pins={'new/body':M.h(b'new body')}
 if failure=='old-body':oldfile.write_bytes(b'changed')
 elif failure=='old-mode':oldfile.chmod(0o644)
 elif failure=='old-inode':replacement=cap/'replacement';replacement.write_bytes(b'old body');replacement.chmod(0o600);os.replace(replacement,oldfile)
 elif failure=='new-body':(cap/'new/body').write_bytes(b'changed')
 elif failure=='new-mode':(cap/'new/body').chmod(0o644)
 elif failure=='extra-member':(cap/'foreign').write_bytes(b'foreign')
 elif failure=='oldgate':oldgate.write_bytes(b'bad gate')
 elif failure=='head':(cap/'.git/HEAD').write_bytes(b'changed-head\n')
 elif failure=='newdir-mode':(cap/newdir).chmod(0o755)
 ns=dict(M.__dict__);ns.update(CAP=cap,NEW=newdir,OLD_GATE='old-gate',OLD_GATE_PIN=M.h(b'old gate'),SOURCE='opaque-head',r=before_reader,before=before,oldrows=oldrows,files=files,pins=pins)
 # head is original exact function recompiled with owned globals to keep filesystem ownership bounded.
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='head');exec(compile(ast.Module(body=[fn],type_ignores=[]),'<exact head>','exec'),ns)
 if failure is None:exec(terminal_code,ns);rows.append({'case':'terminal owned exact preserve/add','passed':True})
 else:refused('terminal inverse '+failure,lambda:exec(terminal_code,ns))
# Static mutation surface excludes .git/history/existing bodies and actual public main remains uninvoked.
mutations=[ast.unparse(n) for n in ast.walk(main) if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id=='put') or (isinstance(n.func,ast.Attribute) and n.func.attr in ('mkdir','chmod')))]
assert len(mutations)==6
(D/'ADOPTER_CONTROLS01.json').write_text(json.dumps({'schema_version':1,'source_sha256':hashlib.sha256(source).hexdigest(),'public_main_invoked':False,'accepted_release_fabricated':False,'rows':rows,'mutation_surface':mutations},indent=2)+'\n');print(len(rows))
