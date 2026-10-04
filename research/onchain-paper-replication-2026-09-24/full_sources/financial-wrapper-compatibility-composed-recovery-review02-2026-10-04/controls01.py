from pathlib import Path
import ast,hashlib,importlib.util,json,os,stat,types
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-compatibility-composed-recovery-correction02-2026-10-04';O=B/'financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04'
checks=[];rows=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(O/'verify01.py').read_bytes();new=(A/'verify02.py').read_bytes();ok(sha(old)=='14145d47b0df54c4234c4c029a1108ce8b3e7a9d4638f92b9475d99eb3f7c52f','original source');ok(sha(new)=='421cc50f32b1bf1d6a483991deea0fa6700aeb4d165ddc1cecf64dacc08dc4a2','corrected source')
inv=json.loads((A/'INVERSE01.json').read_bytes());restored=new.decode()
for e in reversed(inv['literal_edits']):ok(restored.count(e['new'])==1,'unique declared replacement');restored=restored.replace(e['new'],e['old'],1)
ok(restored.encode()==old,'full literal inverse');ok(ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'full AST inverse')
def load(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
N=load(A/'verify02.py','review_new');P=load(O/'verify01.py','review_old');ok(N.OWNED_IO_BYTES==(A/'owned_io.py').read_bytes() and sha(N.OWNED_IO_BYTES)=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','embedded exact owned IO')
def defs(source):
 t=ast.parse(source);out={}
 for n in t.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):out[n.name]=ast.dump(n)
  if isinstance(n,ast.ClassDef):
   for f in n.body:
    if isinstance(f,ast.FunctionDef):out[n.name+'.'+f.name]=ast.dump(f)
 return out
od,nd=defs(old),defs(new)
for name,body in od.items():
 if name not in ['Reader.read','Reader.tree']:ok(nd[name]==body,'unchanged AST '+name)
p=H/'opaque';p.write_bytes(b'opaque source-only control');p.chmod(0o600)
classes=[ValueError,OSError,MemoryError,KeyboardInterrupt,SystemExit]
fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
def retained(actual,target):
 todo=[actual];seen=set()
 while todo:
  e=todo.pop()
  if e is target:return True
  if id(e) in seen:continue
  seen.add(id(e))
  d=BaseException.__dict__['__dict__'].__get__(e)
  todo.extend(x for x in d.get('composed_failures',()) if isinstance(x,BaseException))
  todo.extend(x for x in d.get('failures',()) if isinstance(x,BaseException))
  for k in ['__cause__','__context__']:
   v=BaseException.__dict__[k].__get__(e)
   if v is not None:todo.append(v)
  if isinstance(e,BaseExceptionGroup):todo.extend(e.exceptions)
 return False
for pc in classes:
 for sc in classes:
  primary=pc('read');secondary=sc('close');fds=[];proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)})
  def read(fd,n):fds.append(fd);raise primary
  def close(fd):os.close(fd);raise secondary
  proxy.read=read;proxy.close=close;real=N.os;N.os=proxy
  try:
   try:N.Reader().read(p)
   except BaseException as actual:
    want=primary if fatal(primary) else secondary if fatal(secondary) else None
    ok((actual is want) if want else isinstance(actual,N.IO.CleanupFailure),'read first fatal '+pc.__name__+'/'+sc.__name__)
    ok(retained(actual,primary) and retained(actual,secondary),'read both actual objects retained')
   else:raise AssertionError('read escaped success')
  finally:N.os=real
  for fd in fds:
   try:os.fstat(fd)
   except OSError:ok(True,'actual fd closed')
   else:raise AssertionError('FD leaked')
  rows.append({'control':'read-close','primary':pc.__name__,'secondary':sc.__name__,'passed':True})
# Independent real scandir close plus real iteration failure across all error pairs.
root=H/'tiny-tree';root.mkdir(mode=0o700);(root/'leaf').write_bytes(b'x')
for pc in classes:
 for sc in classes:
  primary=pc('iteration');secondary=sc('iterator close');closed=[]
  class It:
   def __init__(self,path):self.it=os.scandir(path)
   def __iter__(self):return self
   def __next__(self):next(self.it);raise primary
   def close(self):self.it.close();closed.append(True);raise secondary
   def __enter__(self):return self
   def __exit__(self,*args):self.close()
  proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.scandir=It;real=N.os;N.os=proxy
  try:
   try:N.Reader().tree(root)
   except BaseException as actual:
    want=primary if fatal(primary) else secondary if fatal(secondary) else None
    ok((actual is want) if want else isinstance(actual,N.IO.CleanupFailure),'iteration first fatal '+pc.__name__+'/'+sc.__name__)
    ok(retained(actual,primary) and retained(actual,secondary),'iteration both actual objects retained');ok(closed==[True],'iterator closed once')
   else:raise AssertionError('iterator escaped success')
  finally:N.os=real
  rows.append({'control':'iterator-close','primary':pc.__name__,'secondary':sc.__name__,'passed':True})
# Real original REDs, exact old body remains byte-pinned.
for pc,sc,kind in [(ValueError,MemoryError,'read'),(ValueError,SystemExit,'read'),(KeyboardInterrupt,SystemExit,'tree'),(MemoryError,ValueError,'tree')]:
 primary=pc();secondary=sc();proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});closed=[]
 def read(fd,n):raise primary
 def close(fd):os.close(fd);closed.append(True);raise secondary
 class It:
  def __init__(self,path):self.it=os.scandir(path)
  def __enter__(self):return self
  def __iter__(self):return self
  def __next__(self):next(self.it);raise primary
  def __exit__(self,*args):self.it.close();closed.append(True);raise secondary
 proxy.read=read;proxy.close=close;proxy.scandir=It;real=P.os;P.os=proxy
 try:
  try:getattr(P.Reader(),kind)(p if kind=='read' else root)
  except BaseException as actual:ok(actual is (primary if kind=='read' else secondary),'genuine original RED '+kind);ok(closed==[True],'original descriptor closed')
  else:raise AssertionError('old witness missing')
 finally:P.os=real
 rows.append({'control':'original RED','kind':kind,'primary':pc.__name__,'secondary':sc.__name__})
# Extract actual handlers, never execute main or run.
def handler(source):
 main=next(n for n in ast.parse(source).body if isinstance(n,ast.If));tr=next(n for n in main.body if isinstance(n,ast.Try));return compile(ast.Module(body=tr.handlers[0].body,type_ignores=[]),'actual handler only','exec')
for label,M,src in [('old',P,old),('new',N,new)]:
 for pc in classes:
  for sc in classes:
   primary=pc('body');secondary=sc('diagnostic')
   def output(*a,**kw):raise secondary
   ns=dict(M.__dict__);ns['print']=output
   try:
    try:raise primary
    except BaseException as e:ns['error']=e;exec(handler(src),ns)
   except BaseException as actual:
    if label=='old':ok(actual is secondary,'original diagnostic RED')
    else:
     want=primary if fatal(primary) else secondary if fatal(secondary) else None
     ok((actual is want) if want else isinstance(actual,N.IO.CleanupFailure),'new diagnostic firstfatal');ok(retained(actual,primary) and retained(actual,secondary),'diagnostic actual object retention')
   else:raise AssertionError('handler noerror')
class Hostile(KeyboardInterrupt):
 def __str__(self):raise SystemExit('string')
 @property
 def __cause__(self):raise MemoryError('cause hook')
 def __setattr__(self,n,v):raise SystemExit('attribute hook')
for label,M,src in [('old',P,old),('new',N,new)]:
 e=Hostile();ns=dict(M.__dict__);ns['error']=e
 try:
  try:raise e
  except BaseException:exec(handler(src),ns)
 except BaseException as actual:ok(actual is e if label=='new' else actual is not e,'hostile diagnostic '+label)
# Normal actual file and full-tree reads + retained fingerprint failure.
r=N.Reader();ok(r.read(p)==p.read_bytes(),'normal bounded read');r.tree(root);r.finish();p.write_bytes(b'changed')
try:r.finish()
except ValueError:ok(True,'actual retained body drift refusal')
else:raise AssertionError('drift accepted')
result={'assertions':len(checks),'cases':len(rows)+52,'rows':rows,'checks':checks,'source_sha256':sha(new),'public_run_or_entry_executed':False,'numeric_imports':False,'scope':'actual methods, real owned fd/iterator, exact extracted exception handlers; no authority objects'}
(H/'CONTROLS01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['rows','checks']}))
