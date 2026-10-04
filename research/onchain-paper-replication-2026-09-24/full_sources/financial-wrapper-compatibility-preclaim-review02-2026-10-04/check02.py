from pathlib import Path
import json,hashlib,stat,os,ast,importlib.util,types,time
O=Path(__file__).resolve().parent;F=O.parent;T=F/'financial-wrapper-compatibility-preclaim-correction02-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());checks=[]
def ck(n,v):assert v,n;checks.append(n)
m=J(T/'MANIFEST01.json');ck('seal',h((T/'MANIFEST01.json').read_bytes())=='4212eb865b78b944c92385023d1c91b232998ae53e6cc7335dce52dbf4e16cd1')
for x in m['members']:
 p=T/x['path'];s=p.lstat();ck('mode:'+x['path'],stat.S_IMODE(s.st_mode)==x['mode'])
 if x['kind']=='file':ck('body:'+x['path'],stat.S_ISREG(s.st_mode) and len(p.read_bytes())==x['bytes'] and h(p.read_bytes())==x['sha256'])
 elif x['kind']=='directory':ck('dir:'+x['path'],stat.S_ISDIR(s.st_mode))
 elif x['kind']=='symlink':ck('link:'+x['path'],stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'])
 elif x['kind']=='fifo':ck('fifo:'+x['path'],stat.S_ISFIFO(s.st_mode))
 else:raise AssertionError(x['kind'])
ck('complete-author-tree',{p.relative_to(T).as_posix() for p in T.rglob('*')}=={x['path'] for x in m['members']}|set(m['excluded']))
old=(T/'ORIGINAL_preclaim01.py').read_text();new=(T/'preclaim01.py').read_text();ck('sourcepin',h(new.encode())=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16')
a=ast.parse(old);b=ast.parse(new);methods={}
for label,tree in [('old',a),('new',b)]:
 cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Reader');methods[label]={x.name:ast.dump(x,include_attributes=False) for x in cls.body if isinstance(x,ast.FunctionDef)};cls.body=[x for x in cls.body if not isinstance(x,ast.FunctionDef) or x.name not in ['__init__','_physical','finish']]
ck('outside-reader3-identical',ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False));ck('three-readerchanges',sorted(n for n in methods['old'] if methods['old'][n]!=methods['new'][n])==['__init__','_physical','finish'])
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(s);s.loader.exec_module(module);return module
oldm=load('oldpreclaim',T/'ORIGINAL_preclaim01.py');newm=load('newpreclaim',T/'preclaim01.py');witness=[]
for kind in ['extent','mode','replace','redirect','missing']:
 for label,M in [('old',oldm),('new',newm)]:
  d=O/(kind+'-'+label);d.mkdir(mode=0o700);p=d/'earlier';later=d/'later';p.write_bytes(b'original');later.write_bytes(b'last');reader=M.Reader();reader.read(p);reader.read(later);pin=(later.stat().st_dev,later.stat().st_ino);real=M.os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});mutated=[False];closed=[]
  def close(fd):
   s=os.fstat(fd);os.close(fd);closed.append(fd)
   if not mutated[0] and (s.st_dev,s.st_ino)==pin:
    mutated[0]=True
    if kind=='extent':p.write_bytes(b'changed-extent')
    elif kind=='mode':p.chmod(0o600 if stat.S_IMODE(p.stat().st_mode)!=0o600 else 0o644)
    elif kind=='replace':p.rename(d/'original-retained');p.write_bytes(b'original')
    elif kind=='redirect':p.rename(d/'original-retained');p.symlink_to(d/'original-retained')
    else:p.rename(d/'original-retained')
  proxy.close=close;M.os=proxy;error=None
  try:reader.finish()
  except BaseException as e:error=e
  finally:M.os=real
  ck(kind+'mutation'+label,mutated[0]);ck(kind+'disposition'+label,error is None if label=='old' else isinstance(error,(ValueError,OSError)))
  witness.append({'kind':kind,'version':label,'accepted':error is None,'error':None if error is None else type(error).__name__,'cached_bytes_hex':reader.cache[p].hex(),'actual_later_inode':list(pin),'real_close_count':len(closed),'signature_reset_used':False})
  for fd in closed:
   try:os.fstat(fd)
   except OSError:continue
   else:raise AssertionError('fd leak')
d=O/'intact';d.mkdir(mode=0o700);p=d/'opaque';p.write_bytes(b'opaque');r=newm.Reader();ck('intactread',r.read(p)==b'opaque');r.finish();ck('double-read-count',r.total==12)
r.deadline=time.monotonic()-1
try:r.finish()
except newm.Unavailable:checks.append('deadline')
else:raise AssertionError('deadline')
# Real FD _close firstfatal retention, independent of public/genuine API.
for i,a in enumerate([ValueError('body'),MemoryError('body'),SystemExit('body')]):
 for j,b in enumerate([ValueError('close'),MemoryError('close'),SystemExit('close')]):
  fd=os.open(d/f'fatal-{i}-{j}',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});real=newm.os
  def close(fd,e=b):os.close(fd);raise e
  proxy.close=close;newm.os=proxy
  try:
   try:newm._close(fd,a)
   except BaseException as e:
    exp=next((v for v in [a,b] if isinstance(v,MemoryError) or not isinstance(v,Exception)),None);ck(f'fatal{i}{j}',e is exp if exp is not None else isinstance(e,newm.CleanupFailure))
   else:raise AssertionError('cleanup accepted')
  finally:newm.os=real
ck('fixedcaps',(newm.FILE,newm.TOTAL,newm.SECONDS)==(4194304,8388608,120))
(O/'WITNESSES01.json').write_text(json.dumps(witness,indent=2)+'\n');(O/'READBACK01.json').write_text(json.dumps({'schema_version':1,'checks':len(checks),'names':checks,'actual_genuine_public_success':False,'source_sha256':h(new.encode()),'manifest_sha256':h((T/'MANIFEST01.json').read_bytes()),'scope':'Source+real Reader opaque IO only; no genuine Admission/Owner/Run constructed or imported.'},indent=2)+'\n');print('PASS',len(checks),'complete seal/inverse/five actual lateclose oldRED-newREFUSAL/ninefatal controls')
