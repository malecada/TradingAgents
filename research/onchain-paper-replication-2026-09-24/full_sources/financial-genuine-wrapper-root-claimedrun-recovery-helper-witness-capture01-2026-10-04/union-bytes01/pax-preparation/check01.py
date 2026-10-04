import ast,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sys.path.insert(0,str(H));import recovery_pax01 as N
sp=importlib.util.spec_from_file_location('original_r4',H/'original-recovery04.py');O=importlib.util.module_from_spec(sp);sp.loader.exec_module(O)
checks=[];witness=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(fn,n):
 try:fn()
 except (ValueError,KeyError,TypeError,tarfile.TarError,OSError,EOFError):ok(True,n)
 else:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
s=(H/'recovery_pax01.py').read_text();o=(H/'original-recovery04.py').read_text();e=json.loads((H/'INVERSE01.json').read_bytes());ok(s.count(e['new'])==1 and s.replace(e['new'],e['old'])==o,'exact full byte inverse');ok(ast.dump(ast.parse(s.replace(e['new'],e['old'])))==ast.dump(ast.parse(o)),'exact full AST inverse');ok(sha(o.encode())=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','actual original source pin')
a={n.name:ast.get_source_segment(o,n) for n in ast.parse(o).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};b={n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name in a:
 if name!='framed_members':ok(a[name]==b[name],'unchanged '+name)
for name,pin in [('owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'),('bounded_git01.py','db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f')]:ok(sha((H/name).read_bytes())==pin,'unchanged primitive '+name)
# Genuine original archives: framing/hash/member/reencoding only; NO restoration or Root write.
root=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04'
for number,pin in [(35,'55a2e77d065cbf98370dd8e50bb8133a3737a8f910bb8ac89e426b2efb25feb9'),(49,'5dd2114ccc90ad36af91c85ca286a6e13ea8164a334e05599bc487389af20962')]:
 name='shards/shard-%04d.tar.gz'%number;raw=N.read(root,name);ok(sha(raw)==pin,'actual archive unchanged '+str(number));refuse(lambda:list(O.framed_members(raw)),'original actual RED '+str(number));frames=list(N.framed_members(raw));m=json.loads(N.read(root,'shards/shard-%04d-manifest.json'%number));N.validate(m);ok(len(frames)==len(m['members']),'actual whole member count')
 for (path,t,body),r in zip(frames,m['members']):
  ok(path==r['path'] and t.mode==r['mode'],'actual path/order/mode')
  if r['kind']=='directory':ok(t.isdir() and not body and t.size==0,'actual directory bound')
  else:ok(t.isfile() and len(body)==r['bytes'] and sha(body)==r['sha256'],'actual opaque body pin')
 sink=N.ExactSink(raw);N.tar_stream(root/('shard-trees/shard-%04d'%number),m,sink);ok(sink.count==len(raw) and sink.hash.hexdigest()==sha(raw),'actual original canonical complete bytes')
 witness.append({'archive':name,'sha256':pin,'members':len(frames),'original_refuses':True,'new_frames_and_canonical_bytes_pass':True,'actual_restore':False})
# Real tiny owned path with canonical truncated raw slash.
tiny=H/'tiny';tiny.mkdir(mode=0o700);long='a'*99;(tiny/long).mkdir(mode=0o700);(tiny/long/'file').write_bytes(b'x');(tiny/long/'file').chmod(0o600);m=N.scan(tiny);archive=H/'tiny.tar.gz';info=N.pack(tiny,m,archive);raw=archive.read_bytes();refuse(lambda:list(O.framed_members(raw)),'owned old RED');ok(len(list(N.framed_members(raw)))==2,'owned successor GREEN');flat=H/'flat';flat.mkdir(mode=0o700);res=N.restore(archive,info,m,flat);ok(res['regular_bodies']==1 and not res['research_authority'],'real tiny canonical fresh flat')
# Finite malformed headers / PAX payloads. Framing controls never imply authority.
def tar_raw(name='file',body=b'x',kind=tarfile.REGTYPE,pax=None):
 out=io.BytesIO()
 with gzip.GzipFile(filename='',mtime=0,fileobj=out,mode='wb') as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   t=tarfile.TarInfo(name);t.mode=384;t.size=len(body);t.type=kind
   if pax is not None:t.pax_headers=pax
   tf.addfile(t,io.BytesIO(body))
 return out.getvalue()
for name in ('bad/','bad//','../bad','/absolute','','a/../b','keys/secret','a//b'):
 refuse(lambda name=name:list(N.framed_members(tar_raw(name))), 'nonPAX bad path '+repr(name))
for name in ('bad/','bad//','../bad','/absolute','','a/../b','keys/secret','a//b'):
 refuse(lambda name=name:list(N.framed_members(tar_raw('safe',pax={'path':name}))), 'effective PAX bad path '+repr(name))
for kind in (tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.CHRTYPE,tarfile.BLKTYPE,tarfile.FIFOTYPE):refuse(lambda kind=kind:list(N.framed_members(tar_raw(kind=kind))),'wrong raw type '+repr(kind))
for pax in ({'path':'safe','mtime':'0'},{'path':'x'*8200},{'path':'../bad'}):refuse(lambda pax=pax:list(N.framed_members(tar_raw(pax=pax))),'PAX semantic/extent')
refuse(lambda:list(N.framed_members(tar_raw('dir/',body=b'x',kind=tarfile.DIRTYPE))),'nonempty directory')
# Full original restore still rejects altered order/extra/missing/mode/footer and canonical compression.
mutations=[]
plain=gzip.decompress(raw)
mutations.append(('footer',gzip.compress(plain+b'bad',mtime=0)))
mutations.append(('corrupt-gzip',raw[:-8]+b'badbytes'))
mutations.append(('truncated',raw[:len(raw)//2]))
mutations.append(('extra',tar_raw('extra')))
mutations.append(('missing',tar_raw(long,body=b'',kind=tarfile.DIRTYPE)))
mutations.append(('canonical-header',gzip.compress(plain,mtime=1)))
for label,mutated in mutations:
 p=H/(label+'.gz');p.write_bytes(mutated);out=H/('refused-'+label);out.mkdir(mode=0o700);ii={'bytes':len(mutated),'sha256':sha(mutated),'manifest_sha256':sha(N.encode(m))}
 refuse(lambda:N.restore(p,ii,m,out),'full restore '+label)
for firstcls in (MemoryError,KeyboardInterrupt):
 for secondcls in (OSError,MemoryError,KeyboardInterrupt):
  fd=os.open(H/'fd-witness',os.O_CREAT|os.O_WRONLY,0o600);first=firstcls('primary');second=secondcls('secondary');events=[]
  def close():os.close(fd);events.append(1);raise second
  def done():events.append(2)
  try:
   try:raise first
   finally:N._cleanup((close,done))
  except BaseException as err:ok(err is first,'original firstfatal retained')
  ok(events==[1,2] and not Path('/proc/self/fd/'+str(fd)).exists(),'real fd closed allcallbacks')
ok(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'no numerical imports')
(H/'ACTUAL_RED_GREEN01.json').write_text(json.dumps(witness,indent=2)+'\n');(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'actual_root_restore':False},indent=2)+'\n');print('PASS',len(checks))
