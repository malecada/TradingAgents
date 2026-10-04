import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-preparation01-2026-10-04';ROOT=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';sys.path.insert(0,str(A));import recovery_pax01 as N
sp=importlib.util.spec_from_file_location('original',B/'held-consumer-final-recovery-preparation04-2026-10-03/recovery04.py');O=importlib.util.module_from_spec(sp);sp.loader.exec_module(O)
count=0;events=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 global count
 assert v,n;count+=1
def refuse(fn,n):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError,EOFError,tarfile.TarError) as e:events.append({'control':n,'exception':type(e).__name__,'message':str(e)});ck(True,n)
 else:raise AssertionError('not refused '+n)
def scan(root):
 rows=[]
 def walk(p,name):
  st=p.lstat();r={'path':name,'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(st.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):walk(c,name+'/'+c.name if name else c.name)
   return
  else:ck(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'typed singlelink');b=N.read(root,name);r.update(kind='file',bytes=len(b),sha256=sha(b))
  rows.append(r)
 for p in sorted(root.iterdir()):walk(p,p.name)
 return rows
manifest=N.read(A,'MANIFEST01.json');ck(sha(manifest)=='27abd99dc0dfe68de28e78cb6d1923dd8616aed38f10df20a0590b92906c0035','candidate seal');actual=scan(A);declared=json.loads(manifest)['members'];ck([r for r in actual if r['path']!='MANIFEST01.json']==declared,'all frozen author members')
s=N.read(A,'recovery_pax01.py');o=N.read(B/'held-consumer-final-recovery-preparation04-2026-10-03','recovery04.py');ck(sha(s)=='a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2' and sha(o)=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','exact source pins');change=json.loads(N.read(A,'INVERSE01.json'));text=s.decode();ck(text.count(change['new'])==1 and text.replace(change['new'],change['old']).encode()==o,'complete byte inverse');ck(ast.dump(ast.parse(text.replace(change['new'],change['old'])))==ast.dump(ast.parse(o)),'complete AST inverse')
for name,pin in [('owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'),('bounded_git01.py','db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f')]:ck(sha(N.read(A,name))==pin,'primitive unchanged')
# Exact actual archive framing and full canonical bytes, no actual flat recovery.
archive_results=[]
for i in (35,49):
 name='shards/shard-%04d.tar.gz'%i;raw=N.read(ROOT,name);m=json.loads(N.read(ROOT,'shards/shard-%04d-manifest.json'%i));refuse(lambda:list(O.framed_members(raw)),'original actual RED '+str(i));frames=list(N.framed_members(raw));ck(len(frames)==len(m['members']),'new complete actual frame count');bodies={}
 for (path,t,b),r in zip(frames,m['members']):
  ck(path==r['path'] and t.mode==r['mode'],'actual effective name/mode');ck((t.isdir() and not b) if r['kind']=='directory' else (t.isfile() and len(b)==r['bytes'] and sha(b)==r['sha256']),'actual complete body/type');bodies[path]=b
 sink=N.ExactSink(raw);N.tar_stream(ROOT/('shard-trees/shard-%04d'%i),m,sink);ck(sink.count==len(raw),'actual whole canonical inverse');archive_results.append({'path':name,'sha256':sha(raw),'members':len(frames),'actual_restore':False})
# Fresh canonical owned path precisely recreates slash-truncated raw name.
root=H/'tiny';root.mkdir(mode=0o700);directory='r'*99;(root/directory).mkdir(mode=0o700);(root/directory/'body').write_bytes(b'\x00opaque\xff');(root/directory/'body').chmod(0o600);m=N.scan(root);archive=H/'tiny.tar.gz';info=N.pack(root,m,archive);raw=archive.read_bytes();refuse(lambda:list(O.framed_members(raw)),'original tiny RED');flat=H/'flat';flat.mkdir(mode=0o700);receipt=N.restore(archive,info,m,flat);meta=json.loads(N.read(flat,receipt['metadata_file']));ck(N.read(flat,meta['flat_members'][directory+'/body'])==b'\x00opaque\xff','fresh tiny body restored');ck(receipt['research_authority'] is False and receipt['instantiated_posix_tree'] is False,'original no-authority fields')
for p in flat.iterdir():ck(stat.S_IMODE(p.lstat().st_mode)==384 and p.lstat().st_nlink==1,'private original FD output')
def make(name='safe',kind=tarfile.REGTYPE,pax=None,body=b'x',size=None):
 out=io.BytesIO()
 with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   t=tarfile.TarInfo(name);t.type=kind;t.mode=384;t.size=len(body) if size is None else size
   if pax is not None:t.pax_headers=pax
   tf.addfile(t,io.BytesIO(body))
 return out.getvalue()
for p in ('bad/','bad//','../x','/absolute','a/../x','a//x','', 'a\x00b','keys/file'):
 refuse(lambda p=p:list(N.framed_members(make(p))),'bad nonPAX '+repr(p));refuse(lambda p=p:list(N.framed_members(make(pax={'path':p}))),'bad effective PAX '+repr(p))
for kind in (tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.FIFOTYPE,tarfile.CHRTYPE,tarfile.BLKTYPE,tarfile.GNUTYPE_SPARSE):refuse(lambda kind=kind:list(N.framed_members(make(kind=kind,pax={'path':'safe'}))),'bad raw type '+repr(kind))
for ext in ({'path':'safe','mtime':'1'},{'path':'x'*8200},{'path':'../bad'}):refuse(lambda ext=ext:list(N.framed_members(make(pax=ext))),'bad PAX schema/bound')
refuse(lambda:list(N.framed_members(make('dir/',tarfile.DIRTYPE,body=b'x'))),'nonempty directory')
# Header-only extent refusal occurs before oversized payload allocation.
t=tarfile.TarInfo('oversized');t.size=N.FILE+1;t.mode=384;huge=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT)+bytes(1024),mtime=0);refuse(lambda:list(N.framed_members(huge)),'4MiB member extent before body')
# Full restore always binds canonical archive, manifest membership/order/modes and footer.
plain=gzip.decompress(raw);mutations={'nonzero-footer':gzip.compress(plain+b'X',mtime=0),'missing-footer':gzip.compress(plain[:-10240],mtime=0),'gzip-corruption':raw[:-8]+b'badbytes','truncated':raw[:len(raw)//2],'canonical-header':gzip.compress(plain,mtime=1),'extra':make('extra'),'semantic-pax-slash':make(pax={'path':'safe/'})}
# Directly reverse or duplicate valid frame records for canonical/order/cardinality refusals.
parts=[];off=0;pending=b''
while plain[off:off+512]!=bytes(512):
 h=plain[off:off+512];ti=tarfile.TarInfo.frombuf(h,'utf-8','strict');length=512+((ti.size+511)//512)*512;block=plain[off:off+length];off+=length
 if ti.type==tarfile.XHDTYPE:pending=block
 else:parts.append(pending+block);pending=b''
def packparts(p):
 b=b''.join(p)+bytes(1024);b+=bytes((-len(b))%10240);return gzip.compress(b,mtime=0)
mutations['duplicate']=packparts(parts+[parts[-1]]);mutations['order']=packparts(list(reversed(parts)));mutations['missing']=packparts(parts[:-1])
for label,b in mutations.items():
 p=H/(label+'.gz');p.write_bytes(b);out=H/('refused-'+label);out.mkdir(mode=0o700);inf={'bytes':len(b),'sha256':sha(b),'manifest_sha256':sha(N.encode(m))};refuse(lambda:N.restore(p,inf,m,out),'full restore '+label)
# Wrong original mode remains refused independently of byte/name correction.
bad=copy.deepcopy(m);bad['members'][-1]['mode']^=1;out=H/'refused-mode';out.mkdir(mode=0o700);inf=dict(info,manifest_sha256=sha(N.encode(bad)));refuse(lambda:N.restore(archive,inf,bad,out),'full manifest mode')
# Actual output cleanup on body-write fatal: restore uses original owned IO reducer.
for i,typ in enumerate((MemoryError,KeyboardInterrupt,SystemExit)):
 out=H/('fatal-'+str(i));out.mkdir(mode=0o700);primary=typ('original body fatal');write=os.write;close=os.close;closed=[]
 def failwrite(fd,data):raise primary
 def failclose(fd):close(fd);closed.append(fd);raise OSError('close diagnostic')
 os.write=failwrite;os.close=failclose
 try:
  try:N.restore(archive,info,m,out)
  except BaseException as e:ck(e is primary,'actual restore first fatal identity')
  else:raise AssertionError('fatal not raised')
 finally:os.write=write;os.close=close
 ck(len(closed)>=2 and all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in closed),'actual failed restore owned descriptors closed')
ck(not any(k in sys.modules for k in ('numpy','torch','scipy','pandas')),'stdlib-only')
q={'schema_version':1,'decision':'accepted-source-only-witness-pax-framer-correction','source_sha256':sha(s),'original_sha256':sha(o),'author_manifest_sha256':sha(manifest),'checks':count,'refusals':events,'actual_archive_red_green':archive_results,'actual_Root_restore':False,'numerical_or_research_authority':False,'scope':'Only witness archive framing; source/final caller recovery primitives remain immutable; actual integration/release and restored union verification remain separate.'}
(H/'READBACK01.json').write_text(json.dumps(q,sort_keys=True,indent=2)+'\n');print('PASS',count)
