import ast,contextlib,hashlib,importlib.util,io,json,os,stat,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-source-handoff-preparation02-2026-10-04';O=H.parent/'financial-genuine-wrapper-claimedrun-source-handoff-preparation01-2026-10-04';checks=[];rows=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def req(v,m):
 if not v:raise ValueError(m)
spec=importlib.util.spec_from_file_location('owned',P/'owned_io.py');oi=importlib.util.module_from_spec(spec);spec.loader.exec_module(oi)
def node(raw,name):return next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==name)
def reader(raw,hook=None,failclose=None):
 fds=[]
 def op(*a,**k):
  fd=os.open(*a,**k);fds.append(fd);return fd
 def cl(fd):
  os.close(fd)
  if failclose:raise failclose
 def rd(fd,n):
  b=os.read(fd,n)
  if hook:hook(fd)
  return b
 proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in ('fstat','stat','O_RDONLY','O_NOFOLLOW','O_NONBLOCK','O_DIRECTORY')},open=op,close=cl,read=rd)
 ns={'os':proxy,'Path':Path,'stat':stat,'require':req,'FILE':4194304,'_cleanup':oi._cleanup}
 exec(compile(ast.Module(body=[node(raw,'read')],type_ignores=[]),'<actual reader>','exec'),ns)
 return ns['read'],fds
old=(O/'generate01.py').read_text();new=(P/'generate01.py').read_text()
# Actual SH1 old acceptance/new refusal with owned directories retained.
for version,raw in [('old',old),('new',new)]:
 root=H/('redirect02-'+version);root.mkdir();folder=root/'original';folder.mkdir();leaf=folder/'body';leaf.write_bytes(b'opaque');moved=root/'retained';done=[]
 def change(fd):
  if not done:done.append(True);folder.rename(moved);folder.symlink_to(moved,target_is_directory=True)
 read,fds=reader(raw,change)
 try:result=read(leaf);out='accepted'
 except ValueError as e:out=str(e)
 check(out=='accepted' if version=='old' else out=='changed parent','SH1 '+version)
 check(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in fds),'all actual reader descriptors absent '+version)
 rows.append({'case':'SH1','version':version,'result':out,'owned_descriptor_count':len(fds)})
# Fresh opaque cases: stable body, symlink/dir/oversize refusal, parent mutation,
# body mutation, and actual descriptor cleanup under first fatal + close fatal.
root=H/'cases02';root.mkdir();leaf=root/'body';leaf.write_bytes(b'opaque');read,fds=reader(new);check(read(leaf)==b'opaque','stable body')
link=root/'link';link.symlink_to(leaf)
for label,p,cap in [('link',link,100),('directory',root,100),('oversize',leaf,2)]:
 try:reader(new)[0](p,cap)
 except ValueError:check(True,'refusal '+label)
 else:raise AssertionError(label)
for primary_type in (MemoryError,SystemExit,KeyboardInterrupt,ValueError):
 for secondary_type in (MemoryError,SystemExit,OSError):
  first=primary_type('first');second=secondary_type('close');done=[]
  def fatal(fd):raise first
  read,fds=reader(new,fatal,second)
  try:read(leaf)
  except BaseException as e:
   expected=first if oi._fatal(first) else second
   check((e is expected) if oi._fatal(first) or oi._fatal(second) else (isinstance(e,oi.CleanupFailure) and first in e.failures and second in e.failures),'first fatal read '+primary_type.__name__+'/'+secondary_type.__name__)
  else:raise AssertionError('missing reader failure')
  check(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in fds),'all cleanup attempted read '+primary_type.__name__+'/'+secondary_type.__name__)
# Actual SH2 old/new loop. New _opened extracted intact; only its fdopen seam
# routes into concrete owned stream subclass. Real os.close generates EBADF.
for version,raw in [('old',old),('new',new)]:
 first=MemoryError('write first');used=[]
 class Stream(io.BufferedWriter):
  def write(self,b):used.append(self.raw.fileno());os.close(self.raw.fileno());raise first
 class Leaf:
  def open(self,mode):return Stream(io.FileIO(H/('writer02-'+version),'xb'))
 class Output:
  def __truediv__(self,n):return Leaf() if version=='old' else H/('writer02-'+version)
 def fdopen(fd,mode,closefd):return Stream(io.FileIO(fd,mode,closefd=False))
 proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in ('open','close','O_NOFOLLOW','O_CLOEXEC','O_RDONLY','O_NONBLOCK','O_WRONLY','O_CREAT','O_EXCL')},fdopen=fdopen)
 ns={'os':proxy,'_require':req,'_cleanup':oi._cleanup,'contextmanager':contextlib.contextmanager}
 exec(compile(ast.Module(body=[node((P/'owned_io.py').read_text(),'_opened')],type_ignores=[]),'<actual opened>','exec'),ns)
 ns.update(output=Output(),bodies={'tiny':b'opaque'})
 loop=next(n for n in node(raw,'main').body if isinstance(n,ast.For))
 try:exec(compile(ast.Module(body=[loop],type_ignores=[]),'<actual main loop>','exec'),ns)
 except BaseException as e:
  check((isinstance(e,OSError) and e.errno==9 and e.__context__ is first) if version=='old' else e is first,'SH2 '+version)
  rows.append({'case':'SH2','version':version,'raised_type':type(e).__name__,'first_preserved':e is first})
 else:raise AssertionError('missing writer failure')
 check(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in used),'writer fd absent '+version)
# Independent full text and AST inverse: only read/import/output/root allowed.
back=new.replace('from owned_io import _cleanup,_opened','from owned_io import _cleanup').replace("with _opened(output/n,'xb') as f:f.write(b)","with (output/n).open('xb') as f:f.write(b)").replace('genuine-financial-wrapper-claimedrun-native-20261004-02/source','genuine-financial-wrapper-claimedrun-native-20261004-01/source')
bn=node(back,'read');on=node(old,'read');lines=back.splitlines(keepends=True);back=''.join(lines[:bn.lineno-1])+ast.get_source_segment(old,on)+'\n'+''.join(lines[bn.end_lineno:]);check(back==old,'full helper byte inverse only four declared seams');check(ast.dump(ast.parse(back))==ast.dump(ast.parse(old)),'full helper AST inverse')
for name in ('model','training','environment','runtime_mapping','synthetic_recipe','source_closure','wrapper_plan'):
 check((P/'generated01'/f'{name}.json').read_bytes()==(O/'generated01'/f'{name}.json').read_bytes(),'unchanged seven role bytes '+name)
a=json.loads((P/'generated01/execution_job.json').read_bytes());b=json.loads((O/'generated01/execution_job.json').read_bytes());a['resources']['disk_paths']=b['resources']['disk_paths'];a['resources']['storage_budget']['root']=b['resources']['storage_budget']['root'];check(a==b,'job exact root-only delta')
a=json.loads((P/'generated01/HANDOFF01.json').read_bytes());b=json.loads((O/'generated01/HANDOFF01.json').read_bytes());a['proposed_root']=b['proposed_root'];a['input_roles']['execution_job']=b['input_roles']['execution_job'];check(a==b,'handoff exact root+jobhash delta')
check(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'no numerical import')
out={'checks':len(checks),'check_names':checks,'witnesses':rows,'source_only':True,'actual_runtime':False,'future_source':None,'future_admission':None,'future_release':None};(H/'IO_CHECKS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out))
