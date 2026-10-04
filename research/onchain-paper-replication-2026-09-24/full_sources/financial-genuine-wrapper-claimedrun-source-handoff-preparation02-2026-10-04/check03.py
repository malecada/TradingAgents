import ast,copy,hashlib,io,json,os,stat,types
from pathlib import Path
import generate01 as G
import owned_io as O
H=G.H;checks=[]
def ok(x,n):assert x,n;checks.append(n)
old=(H/'predecessor01/generate01.py').read_text();new=(H/'generate01.py').read_text()
def function(s,n):return next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name==n)
def segment(s,n):a=function(s,n);return '\n'.join(s.splitlines()[a.lineno-1:a.end_lineno])
inverse=new.replace(segment(new,'read'),segment(old,'read')).replace('from owned_io import _cleanup,_opened','from owned_io import _cleanup').replace("with _opened(output/n,'xb') as f:f.write(b)","with (output/n).open('xb') as f:f.write(b)")
inverse=inverse.replace('genuine-financial-wrapper-claimedrun-native-20261004-02/source','genuine-financial-wrapper-claimedrun-native-20261004-01/source')
ok(inverse==old,'exact full byte inverse');ok(ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)),'full AST inverse')
for name in ('old','new'):
 root=H/('reader-root02-'+name);root.mkdir();folder=root/'original';folder.mkdir();leaf=folder/'body';leaf.write_bytes(b'opaque');moved=root/'retained';done=[]
 def read(fd,n):
  b=os.read(fd,n)
  if not done:done.append(True);folder.rename(moved);folder.symlink_to(moved,target_is_directory=True)
  return b
 proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});proxy.read=read
 ns={'FILE':G.FILE,'os':proxy,'stat':stat,'Path':Path,'require':G.require,'_cleanup':O._cleanup}
 exec(compile(ast.Module(body=[function(old if name=='old' else new,'read')],type_ignores=[]),'<exact reader>','exec'),ns)
 try:result=ns['read'](leaf)
 except ValueError:ok(name=='new','SH1 new refuses actual redirected parent')
 else:ok(name=='old' and result==b'opaque','SH1 old accepts actual redirected parent')
# Exact output loops; real owned fd closed before fatal write.
for name in ('old','new'):
 first=MemoryError('primary');fds=[];path=H/('writer-root02-'+name)
 class Stream(io.BufferedWriter):
  def write(self,b):fds.append(self.raw.fileno());os.close(self.raw.fileno());raise first
 class Leaf:
  def open(self,mode):return Stream(io.FileIO(path,mode))
 class Output:
  def __truediv__(self,n):return Leaf() if name=='old' else path
 loop=next(n for n in function(old if name=='old' else new,'main').body if isinstance(n,ast.For))
 ns={'output':Output(),'bodies':{'tiny':b'opaque'},'_opened':O._opened}
 original=O.os.fdopen
 def fdopen(fd,mode,closefd):return Stream(io.FileIO(fd,mode,closefd=False))
 try:
  if name=='new':O.os.fdopen=fdopen
  try:exec(compile(ast.Module(body=[loop],type_ignores=[]),'<exact output loop>','exec'),ns)
  except BaseException as e:ok((name=='old' and isinstance(e,OSError)) or (name=='new' and e is first),'SH2 '+name+' actual close disposition')
  else:raise AssertionError('missing fatal')
 finally:O.os.fdopen=original
 ok(not Path('/proc/self/fd/'+str(fds[0])).exists(),'actual fd absent '+name)
for n in (H/'generated01').iterdir():
 if n.name=='HANDOFF01.json':
  q=json.loads(n.read_bytes());prior=json.loads((H/'predecessor01/generated01'/n.name).read_bytes());q['proposed_root']=prior['proposed_root'];q['input_roles']['execution_job']['sha256']=prior['input_roles']['execution_job']['sha256'];ok(q==prior,'handoff exact root and job hash inverse');continueok(n.read_bytes().replace(b'genuine-financial-wrapper-claimedrun-native-20261004-02/source',b'genuine-financial-wrapper-claimedrun-native-20261004-01/source')==(H/'predecessor01/generated01'/n.name).read_bytes(),'generated root inverse '+n.name)
for t1 in (ValueError,MemoryError,KeyboardInterrupt):
 for t2 in (OSError,MemoryError,KeyboardInterrupt):
  first=t1('primary');second=t2('secondary');done=[]
  def fail():done.append(1);raise second
  try:
   try:raise first
   finally:O._cleanup((fail,lambda:done.append(2)))
  except BaseException as e:
   expected=first if O._fatal(first) else second if O._fatal(second) else None
   ok(e is expected if expected else isinstance(e,O.CleanupFailure),'firstfatal '+t1.__name__+t2.__name__)
  ok(done==[1,2],'all cleanup '+t1.__name__+t2.__name__)
(H/'CHECKS03.json').write_bytes(G.enc({'count':len(checks),'checks':checks,'actual_target_created':False,'claims':0}))
print(json.dumps({'checks':len(checks),'status':'passed'}))
