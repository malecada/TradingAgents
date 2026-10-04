import copy,hashlib,io,json,os,stat,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-batch-output-chunk-storage-preparation02-2026-10-04';OLD=B/'financial-batch-output-chunk-storage-preparation01-2026-10-04';sys.path.insert(0,str(A));import codec01 as C;import local_store01 as L
checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
refs=json.loads((OLD/'SOURCE_READBACK01.json').read_bytes())
for row in refs['read_only_sources']:
 p=Path(row['path']);b=p.read_bytes();ok(len(b)==row['bytes'] and sha(b)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],'genuine source unchanged '+p.name)
for row in refs['unchanged_copied_dependencies']:ok((A/row['copy']).read_bytes()==Path(row['source']).read_bytes() and sha((A/row['copy']).read_bytes())==row['sha256'],'actual IO original exact')
d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:'a'*64 for k in C.SCOPE},'motifs':32,'spent_samples':512};raw=bytes(range(128));files={};pin=C.encode_stream(io.BytesIO(raw),d,lambda n,b:files.setdefault(n,b),chunk_bytes=32);terminal=json.loads(files['terminal.json']);terminal['raw_sha256']='b'*64;files['terminal.json']=C.canonical(terminal);badpin=sha(files['terminal.json']);root=H/'late-whole-footer';root.mkdir(mode=0o700);prefix=[]
with L.LocalStore(root) as store:
 for n,b in files.items():store.put(n,b)
 try:store.verify(badpin,d,prefix.append)
 except ValueError as e:ok(str(e)=='whole payload footer','rehashed terminal wholefooter refusal');ok(store.poisoned and b''.join(prefix)==raw,'entire delivered prefix remains unsuccessful and store poisoned')
 else:raise AssertionError('bad footer accepted')
# Unsupported filesystem block sizing: scalar guard injection only, real owned FD closes.
root=H/'unsupported-block';root.mkdir(mode=0o700);original=L.os;fds=[]
def open_fd(*args,**kwargs):fd=os.open(*args,**kwargs);fds.append(fd);return fd
L.os=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});L.os.open=open_fd;L.os.fstatvfs=lambda fd:types.SimpleNamespace(f_bsize=L.BLOCK+1,f_frsize=4096)
try:
 try:L.LocalStore(root)
 except ValueError as e:ok(str(e)=='unsupported filesystem block size','unsupported blockguard refusal');ok(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in fds),'initial refusal actualfd closed');ok(not list(root.iterdir()),'initial refusal creates nofiles')
 else:raise AssertionError('unsupported block accepted')
finally:L.os=original
# Namespace replacement after real descriptor creation: retain written old directory and reject.
root=H/'namespace';root.mkdir(mode=0o700);retained=H/'namespace-retained';store=L.LocalStore(root);once=[]
def write_fd(fd,b):
 if not once:root.rename(retained);root.mkdir(mode=0o700);once.append(True)
 return os.write(fd,b)
L.os=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});L.os.write=write_fd
try:
 try:store.put('start.json',b'opaque')
 except ValueError as e:ok(str(e)=='root changed','namespace race refused');ok(store.poisoned and (retained/'start.json').read_bytes()==b'opaque' and not list(root.iterdir()),'retained descriptor-bound child explicit')
 else:raise AssertionError('namespace race accepted')
finally:L.os=original;store.close()
ok(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numerical package imports')
with (H/'CHECKS02.json').open('x') as f:json.dump({'checks':len(checks),'check_names':checks,'source_refs':refs['read_only_sources'],'unsupported_filesystem_test_is_scalar_injection':True,'actual_capacity_measured':False},f,sort_keys=True,indent=2);f.write('\n')
print(len(checks))
