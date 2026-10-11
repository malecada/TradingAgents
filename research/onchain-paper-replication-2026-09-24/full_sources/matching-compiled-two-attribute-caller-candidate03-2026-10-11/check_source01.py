"""Actual allocation/seal/cleanup prefix AST; inert stdlib stand-ins, no ctypes import."""
import ast,copy,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;O=P.parent/'matching-compiled-two-attribute-caller-candidate02-2026-10-11';checks=[]
def ck(v,n):assert v,n;checks.append(n)
def require(v,n):
 if not v:raise ValueError(n)
source=(P/'compiled_edge_owner.py').read_text();tree=ast.parse(source)
def find(name):return copy.deepcopy(next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name))
acquire=find('acquire');prefix=next(n for n in acquire.body if isinstance(n,ast.Try));end=next(i for i,n in enumerate(prefix.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='info');prefix.body=prefix.body[:end];prefix.body=[ast.Pass() if isinstance(n,ast.Import) else n for n in prefix.body]
def exercise(platform='linux',allocated=7,write_error=None,seals=15,close_error_value=None):
 events=[];raw=b'bounded mock body'
 class Create:
  def __call__(self,name,flags):events.append(('create',name,flags));return allocated
 create=Create()
 def library(path,**kwargs):events.append(('libc',path,kwargs));return types.SimpleNamespace(memfd_create=create)
 ctypes_mock=types.SimpleNamespace(CDLL=library,c_char_p=object(),c_uint=object(),c_int=object(),get_errno=lambda:38)
 def write(fd,view):
  events.append(('write',fd))
  if write_error:raise write_error
  return len(view)
 def closefd(fd):
  events.append(('close',fd))
  if close_error_value:raise close_error_value
 def fcntl(fd,command,*args):events.append(('fcntl',fd,command,args));return seals if command==1034 else 0
 env={'require':require,'sys':types.SimpleNamespace(platform=platform),'ctypes':ctypes_mock,'fcntl':types.SimpleNamespace(fcntl=fcntl),'os':types.SimpleNamespace(write=write,pread=lambda *args:raw,strerror=lambda n:'mock errno'),'raw':raw,'close_fd':closefd}
 exec(compile(ast.Module(body=[find('_note')],type_ignores=[]),'actual-note','exec'),env)
 fn=ast.parse('def run():\n fd=None\n closed=False\n close_error=None\n active=None\n').body[0];fn.body.extend([find('close'),copy.deepcopy(prefix),ast.Return(ast.Name('fd',ast.Load()))]);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'actual-allocation-prefix','exec'),env)
 try:return env['run'](),None,events,create,ctypes_mock
 except BaseException as error:return None,error,events,create,ctypes_mock
fd,error,events,create,c=exercise();ck(fd==7 and error is None,'valid descriptor retained and actual prefix completes');ck(create.argtypes==(c.c_char_p,c.c_uint) and create.restype is c.c_int,'exact typed libc declaration');ck(events[:2]==[('libc',None,{'use_errno':True}),('create',b'uncached-edge',3)],'exact probed lookup flags and name');ck([e for e in events if e[0]=='fcntl']==[('fcntl',7,1033,(15,)),('fcntl',7,1034,())],'ADD1033 GET1034 fullmask15 kernel readback')
fd,error,events,*_=exercise(allocated=-1);ck(isinstance(error,OSError) and error.errno==38 and not any(e[0] in ('close','write','fcntl') for e in events),'negative errno refusal before fd publication or write')
primary=KeyboardInterrupt('postallocation write failure');cleanup=OSError('ambiguous close')
fd,error,events,*_=exercise(write_error=primary,close_error_value=cleanup);ck(error is primary and events.count(('close',7))==1,'valid fd acquired before fallible write; fatal preserved and cleanup once')
fd,error,events,*_=exercise(seals=7);ck(isinstance(error,ValueError) and events.count(('close',7))==1,'kernel seal mismatch refuses and closes descriptor')
fd,error,events,*_=exercise(platform='other');ck(isinstance(error,ValueError) and events==[],'strict Linux refusal before libc lookup')
req=json.loads((P/'SOURCE_REQUIREMENTS01.json').read_text());changed=[];forward=[];inverse=[]
for rel,row in req.items():
 n=Path(rel).name;body=(P/n).read_bytes();ast.parse(body);ck(hashlib.sha256(body).hexdigest()==row['sha256'] and len(body)==row['bytes'],'source requirement '+n)
 a=(O/n).read_text();b=body.decode()
 if a!=b:changed.append(n);forward.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=n,tofile=n));inverse.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile=n,tofile=n))
ck(set(changed)=={'compiled_edge_owner.py','batched_numeric_reuse.py'},'all numerical and eight other route bodies unchanged')
ck(''.join(forward)==(P/'FORWARD.patch').read_text() and ''.join(inverse)==(P/'INVERSE.patch').read_text(),'full literal forward/inverse')
a=hashlib.sha256((P/'compiled_edge_owner.py').read_bytes()).hexdigest();b=hashlib.sha256((O/'compiled_edge_owner.py').read_bytes()).hexdigest();ck((P/'batched_numeric_reuse.py').read_text().replace(a,b)==(O/'batched_numeric_reuse.py').read_text(),'memo exact sole owner pin update')
ck((P/'POLICY_TEMPLATE01.json').read_bytes()==(O/'POLICY_TEMPLATE01.json').read_bytes(),'new backend policy unchanged')
ck('fcntl.fcntl(fd,1034)==seals' in source and 'os.memfd_create' not in source and 'fcntl.F_' not in source,'currentness GET and all unavailable primitive sites repaired')
(P/'SOURCE_RESULT01.json').write_text(json.dumps({'status':'PASS_SOURCE_ONLY_LINUX_PREFIX','checks':checks,'native_or_kernel_execution':False,'scientific_imports':False,'actual_authority':False},indent=2)+'\n');print(len(checks),'checks')
