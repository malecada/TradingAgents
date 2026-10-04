import ast,copy,hashlib,io,json,os,stat,sys
from pathlib import Path
import codec01 as C
import local_store01 as L
H=Path(__file__).resolve().parent
D=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[1,32],order='C',scope={k:'a'*64 for k in C.SCOPE},motifs=32,spent_samples=512)
checks=0;records=[]
def check(v):
 global checks
 assert v;checks+=1
def refuse(call,types=(ValueError,)):
 try:call()
 except types:check(True)
 else:raise AssertionError('expected refusal')
def fixture(d=D):
 raw=bytes(range(128))*(C.descriptor(d)//128);f={};pin=C.encode_stream(io.BytesIO(raw),d,lambda n,b:f.setdefault(n,b),chunk_bytes=32);return raw,f,pin
raw,files,pin=fixture()
# Every scope field, plus shape/order/type/provenance callback mutation.
for field in sorted(C.SCOPE):
 expected=copy.deepcopy(D);expected['scope'][field]='b'*64
 def reader(n):expected['scope'][field]='a'*64;return files[n]
 refuse(lambda:C.verify_stream(reader,pin,expected))
 expected=copy.deepcopy(D)
 def reader(n):expected['scope'][field]='b'*64;return files[n]
 check(C.verify_stream(reader,pin,expected)['status']=='complete-byte-proof-only')
for field,value in [('shape',[999,32]),('order','F'),('dtype','<f8'),('motifs',12),('spent_samples',0)]:
 expected=copy.deepcopy(D)
 def reader(n):expected[field]=value;return files[n]
 check(C.verify_stream(reader,pin,expected)['logical_bytes']==128)
# Reference byte outputs unchanged for both dtype roles and split chunk boundaries.
import importlib.util
spec=importlib.util.spec_from_file_location('original_codec',H/'ORIGINAL_codec01.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
for role,dtype in [('score-batches','<f8'),('mcm-output','<f4')]:
 d=copy.deepcopy(D);d.update(role=role,dtype=dtype)
 for chunk in (8,32,128,C.CHUNK):
  raw=bytes(range(128))*(C.descriptor(d)//128);a={};b={}
  pa=old.encode_stream(io.BytesIO(raw),d,lambda n,x:a.setdefault(n,x),chunk_bytes=chunk)
  pb=C.encode_stream(io.BytesIO(raw),d,lambda n,x:b.setdefault(n,x),chunk_bytes=chunk)
  check(pa==pb and a==b);out=[];C.verify_stream(b.__getitem__,pb,d,out.append);check(b''.join(out)==raw)
# Actual pre-write reservation exhausts BEFORE second file creation, with scaled
# threshold for one tiny reservation. This is not actual 64MiB capacity.
r=H/'reservation-one03';r.mkdir(mode=0o700);oldlimit=L.LIMIT
initial=r.stat().st_blocks*512+L.DIRECTORY_HEADROOM+L.SCRATCH_HEADROOM
L.LIMIT=initial+2*L.BLOCK
try:
 with L.LocalStore(r) as store:
  check(store.reserved==initial);store.put('start.json',b'x');reserved=store.reserved
  refuse(lambda:store.put('terminal.json',b'y'))
  check(store.poisoned and store.reserved==reserved and not os.path.lexists(r/'terminal.json'))
  actual=r.stat().st_blocks*512+sum(p.stat().st_blocks*512 for p in r.iterdir())
  check(actual<=L.LIMIT);records.append({'scaled_limit':L.LIMIT,'actual_allocated':actual,'reserved_before_refused_write':reserved,'root':str(r),'not_64MiB_capacity':True})
finally:L.LIMIT=oldlimit
# Exact formula boundaries including overflow/negative/bool and all byte sizes.
for size in (1,4095,4096,65535,65536,65537,C.FILE):
 cost=((size+L.BLOCK-1)//L.BLOCK)*L.BLOCK+L.ENTRY_HEADROOM
 check(L.project(123,45,size,123+cost)==(123+cost,45+size))
 refuse(lambda:L.project(123,45,size,123+cost-1))
for args in [(True,0,1),(0,0,False),(-1,0,1),(0,-1,1),(0,0,0),(0,0,C.FILE+1)]:refuse(lambda:L.project(*args))
# Genuine owned descriptor closes: fatal verify then real close secondary.
for primary_type in (KeyboardInterrupt,MemoryError,SystemExit,ValueError):
 for close_type in (OSError,MemoryError,KeyboardInterrupt):
  r=H/('fatal-'+primary_type.__name__+'-'+close_type.__name__);r.mkdir(mode=0o700);s=L.LocalStore(r)
  pin=C.encode_stream(io.BytesIO(bytes(range(128))),D,s.put,chunk_bytes=32);fd=s.fd
  primary=primary_type('actual provisional primary');secondary=close_type('after real owned close');real_close=os.close;closed=[]
  def close(n):real_close(n);closed.append(n);raise secondary
  def provisional(b):os.close=close;raise primary
  try:
   try:
    try:s.verify(pin,D,provisional)
    finally:s.close()
   except BaseException as error:
    expected=primary if primary_type in (KeyboardInterrupt,MemoryError,SystemExit) else secondary if close_type in (MemoryError,KeyboardInterrupt) else None
    if expected is not None:check(error is expected)
    else:check(type(error).__name__=='CleanupFailure')
    check(s.poisoned and s.closed and closed==[fd])
   else:raise AssertionError('missing error')
  finally:os.close=real_close
  try:os.fstat(fd)
  except OSError:check(True)
  else:raise AssertionError('owned fd leaked')
  records.append({'primary':primary_type.__name__,'secondary':close_type.__name__,'fd_closed':True,'poisoned':s.poisoned,'retained_files':len(list(r.iterdir()))})
# Write failure retains its reservation and actual incomplete file, no refund.
r=H/'partial-write03';r.mkdir(mode=0o700)
with L.LocalStore(r) as store:
 before=store.reserved;real_write=os.write;failure=MemoryError('actual pre-write fatal')
 def bad_write(fd,b):raise failure
 try:
  os.write=bad_write
  try:store.put('start.json',b'x')
  except MemoryError as e:check(e is failure)
  else:raise AssertionError('missing original fatal')
 finally:os.write=real_write
 check(store.poisoned and store.reserved>before and store.reserved_logical==1 and (r/'start.json').stat().st_size==0)
 refuse(lambda:store.put('terminal.json',b'y'))
# Exact inverse and immutable dependencies/source scopes.
inverse=json.loads((H/'INVERSE01.json').read_text())
for n,v in inverse.items():
 new=(H/n).read_text();back=new
 for e in reversed(v['edits']):check(back.count(e['after'])==1);back=back.replace(e['after'],e['before'])
 check(back==(H/('ORIGINAL_'+n)).read_text());check(ast.dump(ast.parse(back))==ast.dump(ast.parse((H/('ORIGINAL_'+n)).read_text())))
for n in ('owned_io.py','recovery04.py','bounded_git01.py'):check((H/n).read_bytes()==(H/('ORIGINAL_'+n)).read_bytes())
fs=os.statvfs(H);s=H.stat();records.append({'kind':'actual-local-filesystem-readback','f_bsize':fs.f_bsize,'f_frsize':fs.f_frsize,'st_blksize':s.st_blksize,'free_bytes':fs.f_bavail*fs.f_frsize,'allocation_bound_verified':False,'kernel_quota_installed':False})
(H/'CHECKS03.json').write_text(json.dumps({'checks':checks,'observations':records,'live_publication':'UNAVAILABLE','actual_64MiB_capacity':False},sort_keys=True,indent=2)+'\n')
print(json.dumps({'checks':checks,'result':'passed'},sort_keys=True))
