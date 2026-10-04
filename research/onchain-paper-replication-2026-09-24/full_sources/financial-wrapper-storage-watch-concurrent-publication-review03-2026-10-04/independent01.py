import importlib.util,json,os,stat
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent
L=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
rows=[]
def load():
 s=importlib.util.spec_from_file_location('reviewwatch',H/'workflow_storage.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));return m
def root(label):
 p=H/'independent-fixtures'/label;p.mkdir(parents=True,mode=0o700);return p
before=len(os.listdir('/proc/self/fd'))
# A genuine link+directory fsync+unlink event occurs in the first file stat.
for limited in (False,True):
 m=load();p=root('publication-'+str(limited));(p/'.pending').write_bytes(b'opaque');w=m.StorageWatch(p,{**L,'max_logical_bytes':5} if limited else L);events=[]
 def st(path,*a,**kw):
  if path=='.pending' and not events:
   os.link(p/'.pending',p/'complete');fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
   try:os.fsync(fd)
   finally:os.close(fd)
   os.unlink(p/'.pending');events.append('link-fsync-unlink')
  return os.stat(path,*a,**kw)
 m.os.stat=st
 try:r=w.check()
 except m.StorageLimit as e:
  assert limited and e.reason=='logical';rows.append({'case':'publication-limit','terminal':True,'reason':e.reason,'events':events})
 else:
  assert not limited and r['logical_file_bytes']==6 and r['scan_attempts']==2 and r['regular_files']==1
  rows.append({'case':'publication-retry','observation':r,'events':events})
# Three real owned descriptors drain exactly once, with hostile diagnostics and
# actual nested close secondaries. No counter is accepted instead of FD readback.
for base in (KeyboardInterrupt,MemoryError,SystemExit):
 for secondary in (None,RuntimeError,SystemExit):
  m=load();p=root(base.__name__+'-'+str(secondary));(p/'a'/'b').mkdir(parents=True);(p/'a'/'b'/'opaque').write_bytes(b'z');closed=[];errors=[];hooks=[]
  def bad(self):hooks.append('diagnostic');raise RuntimeError('diagnostic must not replace first')
  First=type('First',(base,),{'__cause__':property(bad),'__context__':property(bad)})
  first=First('original selected fatal');attempts=[]
  def st(path,*a,**kw):
   if path=='opaque':attempts.append(path);raise first
   return os.stat(path,*a,**kw)
  def close(fd):
   identity=os.fstat(fd);os.close(fd);closed.append((fd,identity.st_ino))
   if secondary:
    e=secondary('after actual close');errors.append(e);raise e
  m.os.stat=st;m.os.close=close
  try:m.StorageWatch(p,L).check()
  except BaseException as e:
   assert e is first and not hooks and len(attempts)==1 and len(closed)==3 and len(set(fd for fd,_ in closed))==3
   state=BaseException.__dict__['__dict__'].__get__(e);assert state.get('storage_cleanup_errors',())==tuple(errors)
   for fd,_ in closed:
    try:os.fstat(fd)
    except OSError:pass
    else:raise AssertionError('FD open')
   rows.append({'case':'nested-first-fatal','primary':base.__name__,'secondary':secondary.__name__ if secondary else None,'closes':closed,'selected_original':True,'all_secondary_objects_retained':True,'attempts':1})
  else:raise AssertionError('fatal swallowed')
# Strict policy primitives reject boolean, floating, missing and excess fields.
for i,bad in enumerate(({**L,'max_entries':True},{**L,'max_entries':100.0},{**L,'extra':1},{k:v for k,v in L.items() if k!='max_depth'})):
 m=load();p=root('schema-'+str(i))
 try:m.StorageWatch(p,bad)
 except ValueError:rows.append({'case':'strict-policy','index':i,'refused':True})
 else:raise AssertionError('bad limits accepted')
# Fixed metadata caps remain no-retry, and sparse logical bytes count in full.
for key,value,reason in [('max_logical_bytes',1,'logical'),('max_allocated_bytes',1,'allocated'),('max_entries',1,'entries'),('max_depth',1,'depth')]:
 m=load();p=root('cap-'+reason);(p/'a'/'b').mkdir(parents=True);(p/'opaque').write_bytes(b'ab');calls=[];original=m.StorageWatch._scan
 def scan(self,begin):calls.append(1);return original(self,begin)
 m.StorageWatch._scan=scan
 try:m.StorageWatch(p,{**L,key:value}).check()
 except m.StorageLimit as e:assert e.reason==reason and len(calls)==1;rows.append({'case':'terminal-cap','reason':reason,'scan_calls':len(calls)})
 else:raise AssertionError('cap passed')
assert len(os.listdir('/proc/self/fd'))==before
rows.append({'case':'final-fd-census','before':before,'after':len(os.listdir('/proc/self/fd'))})
print(json.dumps({'cases':len(rows),'rows':rows,'scope':'fresh opaque engineering controls only'},indent=2))
