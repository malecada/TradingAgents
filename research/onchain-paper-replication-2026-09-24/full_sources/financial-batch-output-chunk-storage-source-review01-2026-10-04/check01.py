import ast,copy,hashlib,io,json,os,stat,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-chunk-storage-preparation01-2026-10-04';sys.path.insert(0,str(A));import codec01 as C;import local_store01 as L
checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def refuses(call,n,types=(ValueError,KeyError,FileNotFoundError,TypeError)):
 try:call()
 except types:ok(True,n)
 else:raise AssertionError(n)
# Authenticate complete author evidence, including failure outputs and literal links.
manifest=(A/'MANIFEST01.json').read_bytes();ok(sha(manifest)=='1181852868d880e624caf3e4a3982f6bd27301983cc3fe2e7a2a0c92f6e3ef8d','author manifest exact');m=json.loads(manifest);rows=[]
def walk(p,rel):
 st=p.lstat();r={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
 if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(st.st_mode):
  r['kind']='directory'
  for q in sorted(p.iterdir()):walk(q,rel+'/'+q.name)
 else:
  ok(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=4194304,'author bounded regular');b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
for p in sorted(A.iterdir()):
 if p.name!='MANIFEST01.json':walk(p,p.name)
ok(sorted(rows,key=lambda r:r['path'])==m['members'],'whole author typed members')
refs=json.loads((A/'SOURCE_READBACK01.json').read_bytes())
for row in refs['read_only_sources']:
 p=Path(row['path']);b=p.read_bytes();ok(len(b)==row['bytes'] and sha(b)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],'genuine actual source ref '+p.name);ast.parse(b)
for row in refs['unchanged_copied_dependencies']:
 b=(A/row['copy']).read_bytes();ok(b==Path(row['source']).read_bytes() and sha(b)==row['sha256'],'unchanged primitive '+row['copy'])
# Complete two-role multi-page opaque roundtrips and individual corruption/refusal controls.
base={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[17,32],'order':'C','scope':{k:'a'*64 for k in C.SCOPE},'motifs':32,'spent_samples':512}
fixtures=[]
for role,dtype in [('score-batches','<f8'),('mcm-output','<f4')]:
 d=copy.deepcopy(base);d.update(role=role,dtype=dtype);raw=bytes((i%251 for i in range(C.descriptor(d))));files={};pin=C.encode_stream(io.BytesIO(raw),d,lambda n,b:files.setdefault(n,b),chunk_bytes=32);out=[];got=C.verify_stream(files.__getitem__,pin,d,out.append);ok(b''.join(out)==raw and got['raw_sha256']==sha(raw) and got['members']==sorted(files),'ordered whole opaque bytes '+role);ok(got['authority'] is None and got['representation_complete'] is False,'not scientific complete '+role);fixtures.append((d,raw,files,pin))
 for name in files:
  for kind in ['missing','truncated','flipped','extra']:
   mutated=dict(files)
   if kind=='missing':del mutated[name]
   elif kind=='truncated':mutated[name]=mutated[name][:-1]
   elif kind=='flipped':mutated[name]=bytes([mutated[name][0]^1])+mutated[name][1:]
   else:mutated[name]+=b'x'
   refuses(lambda:C.verify_stream(mutated.__getitem__,pin,d),'individual '+role+' '+kind+' '+name)
 for k,v in [('dtype','>f8'),('order','F'),('shape',[17,31]),('shape',[True,32]),('motifs',True),('spent_samples',511),('schema_version',True)]:
  bad=copy.deepcopy(d);bad[k]=v;refuses(lambda:C.verify_stream(files.__getitem__,pin,bad),'descriptor '+k+str(v))
 for k in C.SCOPE:
  bad=copy.deepcopy(d);bad['scope'][k]='b'*64;refuses(lambda:C.verify_stream(files.__getitem__,pin,bad),'independent scope '+k)
 for extension in [raw[:-1],raw+b'x']:
  saved={};refuses(lambda:C.encode_stream(io.BytesIO(extension),d,lambda n,b:saved.setdefault(n,b),chunk_bytes=32),'exact encoder total');ok('terminal.json' not in saved,'no completed terminal on incomplete source')
# Malformed rows/pages/headers under freshly recomputed metadata pins, not just stale outer hashes.
d,raw,files,pin=fixtures[0]
def repin(f,page=None):
 t=json.loads(f['terminal.json'])
 if page is not None:
  f['page-0000.json']=C.canonical(page);t['pages'][0]['sha256']=sha(f['page-0000.json'])
 f['terminal.json']=C.canonical(t);return sha(f['terminal.json'])
for label,mutate in [('offset',lambda p:p['rows'][0].update(offset=1)),('duplicate',lambda p:p['rows'].__setitem__(1,copy.deepcopy(p['rows'][0]))),('reorder',lambda p:p['rows'].reverse()),('rowextra',lambda p:p['rows'][0].update(extra=True)),('boolindex',lambda p:p.update(index=False))]:
 f=dict(files);page=json.loads(f['page-0000.json']);mutate(page);p=repin(f,page);refuses(lambda:C.verify_stream(f.__getitem__,p,d),'rehashed page '+label)
for label in ['magic','index','offset','length','start','chain','footer']:
 f=dict(files);frame=bytearray(f['chunk-00000.bin']);positions={'magic':0,'index':8,'offset':16,'length':24,'start':32,'chain':64,'footer':len(frame)-1};frame[positions[label]]^=1
 if label!='footer':frame[-32:]=hashlib.sha256(frame[:-32]).digest()
 f['chunk-00000.bin']=bytes(frame);page=json.loads(f['page-0000.json']);page['rows'][0]['frame_sha256']=sha(bytes(frame));p=repin(f,page);refuses(lambda:C.verify_stream(f.__getitem__,p,d),'rehashed frame '+label)
for k,v in [('head','b'*64),('raw_sha256','b'*64),('logical_bytes',1),('chunks',False),('pages',[])]:
 f=dict(files);t=json.loads(f['terminal.json']);t[k]=v;f['terminal.json']=C.canonical(t);refuses(lambda:C.verify_stream(f.__getitem__,sha(f['terminal.json']),d),'rehashed terminal '+k)
# Actual byte-read bounded callbacks and no live publication.
class ShortReader:
 def __init__(self,b):self.b=b;self.calls=[]
 def read(self,n):self.calls.append(n);b=self.b[:min(n,7)];self.b=self.b[len(b):];return b
reader=ShortReader(raw);saved={};p=C.encode_stream(reader,d,lambda n,b:saved.setdefault(n,b),chunk_bytes=32);ok(max(reader.calls)<=32 and saved==files and p==pin,'short real byte reader bounded/exact')
refuses(lambda:C.publish_live(None,None,None),'live publication always unavailable')
# Actual private roots, retained mode/hardlink/redirect errors, and unchanged first-fatal IO method.
for variant in ['hardlink','symlink','foreign','mode']:
 root=H/('ownership-'+variant);root.mkdir(mode=0o700)
 with L.LocalStore(root) as store:
  store.put('start.json',b'opaque')
  if variant=='hardlink':os.link(root/'start.json',root/'page-0000.json')
  elif variant=='symlink':(root/'page-0000.json').symlink_to('absent')
  elif variant=='foreign':(root/'foreign').write_bytes(b'opaque')
  else:(root/'start.json').chmod(0o644)
  refuses(lambda:store.put('terminal.json',b'never accepted'),'actual owned '+variant);ok(store.poisoned,'put failure poisoned '+variant)
original_os=L.os
for primary_type in [MemoryError,KeyboardInterrupt,SystemExit]:
 for secondary_type in [OSError,MemoryError,KeyboardInterrupt]:
  root=H/('fatal-'+primary_type.__name__+'-'+secondary_type.__name__);root.mkdir(mode=0o700);store=L.LocalStore(root);primary=primary_type('actual write');secondary=secondary_type('actual close');fds=[]
  def write(fd,b):fds.append(fd);raise primary
  def close(fd):os.close(fd);raise secondary
  L.os=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});L.os.write=write;L.os.close=close
  try:
   try:store.put('start.json',b'opaque')
   except BaseException as e:ok(e is primary,'actual put firstfatal original');ok(store.poisoned,'fatal sink poisoned');ok(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in fds),'actual put fd closed')
   else:raise AssertionError('fatal swallowed')
  finally:L.os=original_os;store.close()
# Actual output-root replacement after descriptor creation is detected; both owned trees retained.
root=H/'namespace-race';root.mkdir(mode=0o700);store=L.LocalStore(root);retained=H/'namespace-retained';once=[]
def rename_write(fd,b):
 if not once:root.rename(retained);root.mkdir(mode=0o700);once.append(True)
 return os.write(fd,b)
L.os=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});L.os.write=rename_write
try:
 refuses(lambda:store.put('start.json',b'opaque'),'actual namespace replacement refuses');ok(store.poisoned and (retained/'start.json').read_bytes()==b'opaque' and not list(root.iterdir()),'actual retained descriptor child not fake zero-sideeffect')
finally:L.os=original_os;store.close()
for n in ['codec01.py','local_store01.py','owned_io.py','recovery04.py','bounded_git01.py','PROTOCOL01.md','SOURCE_READBACK01.json','MACHINE01.json','MANIFEST01.json','RED01.out']:
 if (A/n).exists():
  with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((A/n).read_bytes())
result={'checks':len(checks),'check_names':checks,'author_members':len(m['members']),'copied_dependencies_exact':True,'read_only_scientific_source_refs':refs['read_only_sources'],'numerical_imports_or_arrays':False,'real_production_or_capacity_test':False}
with (H/'CHECKS01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'author_members':len(m['members']),'sha256':sha((H/'CHECKS01.json').read_bytes())}))
