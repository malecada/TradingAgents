import ast,hashlib,io,gzip,json,os,stat,sys,tarfile,time,types
from pathlib import Path
H=Path(__file__).resolve().parent; B=H.parent; A=B/'financial-genuine-wrapper-claimedrun-witness-tooling-capture-preparation01-2026-10-04'
checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def save(n,v):
 p=H/n
 with p.open('xb') as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
def census(root):
 rows=[]
 def rec(p,rel):
  s=p.lstat();before=(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns);r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory'
   for c in sorted(p.iterdir()):rec(c,c.name if rel=='.' else rel+'/'+c.name)
  else:
   ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded opaque regular '+str(p.relative_to(B)))
   body=p.read_bytes();r.update(kind='file',bytes=len(body),sha256=sha(body))
  t=p.lstat();ok(before==(t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns),'stable metadata '+str(p.relative_to(B)))
  rows.append(r)
 rec(root,'.');return sorted(rows,key=lambda r:r['path'])
def seal(root,pin):
 raw=(root/'MANIFEST01.json').read_bytes();ok(sha(raw)==pin,'seal '+root.name)
 actual=census(root);expected=json.loads(raw)['members'];observed=[r for r in actual if r['path'] not in ('.','MANIFEST01.json')]
 ok(observed==expected,'complete typed sealed membership '+root.name);return actual
seal(A,'34f28fde09ebce6e586f40555dfbef918a408534ce393e165987c3547085cf7d')
s=(A/'capture_tooling01.py').read_text();old=(A/'original-capture01.py').read_text();ok(sha(s.encode())=='85368444d94a93df1aa4ba8b0f657d2725bc3d4717e9a07beecc3fa59033a167','candidate exact')
inv=s
for e in reversed(json.loads((A/'INVERSE01.json').read_text())['edits']):
 ok(inv.count(e['new'])==e.get('count',1),'inverse unique');inv=inv.replace(e['new'],e['old'])
ok(inv==old,'full byte inverse');ok(ast.dump(ast.parse(inv))==ast.dump(ast.parse(old)),'full AST inverse')
original=B/'financial-genuine-wrapper-claimedrun-final-capture-preparation01-2026-10-04/capture01.py';ok(original.read_bytes()==old.encode(),'actual immutable baseline')
ns={'__name__':'independent_source_only','__file__':str(A/'capture_tooling01.py')};exec(compile(s,str(A/'capture_tooling01.py'),'exec'),ns)
for n,h in ns['PINS'].items():ok(sha((ns['PRIMITIVES']/n).read_bytes())==h,'primitive '+n)
sys.path.insert(0,str(ns['PRIMITIVES']));import recovery04 as R
actual=[];projections=[]
for scope,root in sorted(ns['SCOPES'].items()):
 rows=seal(root,ns['SEALS'][scope]);actual.append({'scope':scope,'root':str(root),'members':rows})
 mapped=[dict(r,union_path=scope+'/'+r['path']) if r['kind']=='file' else r for r in rows]
 metadata=ns['encoded']({'schema_version':1,'original_tree':{'scope':scope,'original_root':str(root),'members':mapped},'source_commit':'0a2e7639b42b9423b90743feadcda4078aa21816','links_followed_or_extracted':False,'research_authority':False})
 virtual=[dict(r,mode=384 if r['kind']=='file' else 448) for r in rows if r['path']!='.' and r['kind']!='lexical-symlink']
 virtual.append({'path':'CAPTURE_ORIGINAL_TREE01.json','kind':'file','mode':384,'bytes':len(metadata),'sha256':sha(metadata)});virtual.sort(key=lambda r:r['path'])
 buf=io.BytesIO();hazards=[]
 with gzip.GzipFile(filename='',mode='wb',fileobj=buf,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for r in virtual:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    body=None
    if r['kind']=='directory':t.type=tarfile.DIRTYPE
    else:
     body=metadata if r['path']=='CAPTURE_ORIGINAL_TREE01.json' else R.read(root,r['path']);ok(len(body)==r['bytes'] and sha(body)==r['sha256'],'projected actual body '+scope+'/'+r['path']);t.size=len(body)
    header=t.tobuf(tarfile.PAX_FORMAT,'utf-8','strict')[-512:];rawname=header[:100].split(b'\0',1)[0].decode()
    if t.isfile() and rawname.endswith('/'):hazards.append({'path':r['path'],'raw_100byte_name':rawname})
    tf.addfile(t,None if body is None else io.BytesIO(body))
 raw=buf.getvalue();ok(len(raw)<=4194304,'projected unchanged archive cap')
 with (H/(scope+'-PROJECTED_ONLY.tar.gz')).open('xb') as f:f.write(raw)
 # Independent complete semantic readback; not original framed decoder.
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:
  members=tf.getmembers();ok([t.name for t in members]==[r['path'] for r in virtual],'projected complete order')
  for t,r in zip(members,virtual):
   ok(t.mode==r['mode'] and t.uid==t.gid==t.mtime==0 and t.uname==t.gname=='','projected exact mode/header')
   if r['kind']=='file':body=tf.extractfile(t).read();ok(len(body)==r['bytes'] and sha(body)==r['sha256'],'projected full body readback')
   else:ok(t.isdir() and t.size==0,'projected empty directory retained')
 count=0;error=None;gen=R.framed_members(raw)
 try:
  for name,t,body in gen:count+=1
 except BaseException as e:error={'type':type(e).__name__,'message':str(e)}
 finally:gen.close()
 projections.append({'scope':scope,'archive_bytes':len(raw),'archive_sha256':sha(raw),'ordinary_members':len(virtual),'original_members':len(rows),'regulars':sum(r['kind']=='file' for r in rows),'original_bytes':sum(r.get('bytes',0) for r in rows),'links':sum(r['kind']=='lexical-symlink' for r in rows),'metadata_bytes':len(metadata),'raw_regular_slash_hazards':hazards,'original_framer_delivered':count,'original_framer_error':error,'actual_Root_capture':False})
 ok(census(root)==rows,'current complete original stable after projection')
save('PROJECTION01.json',projections);save('ORIGINAL_CENSUS01.json',actual)
print(json.dumps(projections))
# Context authenticated without admission, import of packages, or Source mutation.
for p,h in [(ns['SOURCE_CAPTURE']/'source-manifest.json','fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8'),(ns['SOURCE_CAPTURE']/'source.tar.gz','b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24'),(ns['PARENT']/'REQUEST_FINAL03.json','529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8'),(ns['PARENT']/'proofs/FULL_SOURCE_RECOVERY01.json','468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825')]:ok(sha(p.read_bytes())==h,'actual context '+p.name)
R.same(ns['SOURCE'],json.loads((ns['SOURCE_CAPTURE']/'source-manifest.json').read_bytes()));ok(True,'whole actual Source unchanged')
# Exact capture suffix, with tiny roots and explicit post-pack mutation injection only.
node=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name=='main');start=next(i for i,x in enumerate(node.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in x.targets))
fn=ast.FunctionDef(name='tiny_capture',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=node.body[start:],decorator_list=[]);code=compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<exact suffix>','exec')
for variant in ('valid','extra','body','mode','link','remove'):
 here=H/('tiny-'+variant);here.mkdir(mode=0o700);roots={}
 for i in range(2):
  r=here/('original'+str(i));r.mkdir(mode=0o700);(r/'empty').mkdir(mode=0o750);(r/'body').write_bytes(b'opaque-'+str(i).encode());(r/'body').chmod(0o640);(r/'literal').symlink_to('absent');roots[str(i)]=r
 source=here/'source';source.mkdir();(source/'body').write_bytes(b'opaque source');m=R.scan(source)
 local=dict(ns,HERE=here,SCOPES=roots,SOURCE=source,source_manifest=m,start=time.monotonic());exec(code,local);proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)})
 calls=[]
 def pack(r,m,d):
  result=R.pack(r,m,d);calls.append(str(d))
  if len(calls)==2:
   p=roots['0']
   if variant=='extra':(p/'late').write_bytes(b'late')
   elif variant=='body':(p/'body').write_bytes(b'changed')
   elif variant=='mode':(p/'body').chmod(0o600)
   elif variant=='link':(p/'literal').unlink();(p/'literal').symlink_to('other')
   elif variant=='remove':(p/'body').unlink()
  return result
 proxy.pack=pack
 try:local['tiny_capture'](proxy)
 except ValueError as e:ok(variant!='valid' and 'complete original membership' in str(e),'post-pack '+variant+' refuses');ok(not (here/'UNION_AUTHENTICATION01.json').exists(),'no success for '+variant)
 else:
  ok(variant=='valid','valid only succeeds');auth=json.loads((here/'UNION_AUTHENTICATION01.json').read_bytes());ok(auth['original_regular_members']==2 and auth['original_lexical_links']==2,'tiny complete denominators')
  for k,rec in auth['archives'].items():
   raw=(here/rec['archive']['path']).read_bytes();manifest=json.loads((here/rec['manifest']['path']).read_bytes());gen=R.framed_members(raw);got=list(gen);ok([x[0] for x in got]==[r['path'] for r in manifest['members']],'tiny canonical complete framing');ok(any(x[0]=='empty' and x[1].isdir() for x in got),'tiny emptydir retained')
   sink=R.Sink();R.tar_stream(here/'union-bytes01'/k,manifest,sink);ok(sink.hash.hexdigest()==sha(raw),'tiny exact canonical reencoding')
   out=here/('flat'+k);out.mkdir(mode=0o700);R.restore(here/rec['archive']['path'],{x:y for x,y in rec['archive'].items() if x!='path'},manifest,out);ok(True,'tiny genuine flat byte pipeline')
# Actual exact put body failure; real descriptor close under fatal.
for typ in (OSError,MemoryError,KeyboardInterrupt,SystemExit):
 primary=typ('independent write failure');fds=[]
 def failing(fd,b):fds.append(fd);raise primary
 local=dict(ns,os=types.SimpleNamespace(write=failing,fsync=os.fsync));putnode=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name=='put');exec(compile(ast.Module(body=[putnode],type_ignores=[]),'<exact put>','exec'),local)
 try:local['put'](R,H/('put-'+typ.__name__),b'opaque')
 except BaseException as e:ok(e is primary,'exact put retains '+typ.__name__)
 for fd in fds:ok(not Path('/proc/self/fd/'+str(fd)).exists(),'exact put descriptor absent')
for a in (MemoryError,KeyboardInterrupt,SystemExit):
 for b in (OSError,MemoryError,KeyboardInterrupt,SystemExit):
  primary=a('primary');secondary=b('close');fd=os.open(H/('cleanup-'+a.__name__+'-'+b.__name__),os.O_CREAT|os.O_WRONLY|os.O_EXCL,0o600);order=[]
  def close():order.append('close');os.close(fd);raise secondary
  def last():order.append('last')
  try:
   try:raise primary
   finally:R._cleanup((close,last))
  except BaseException as e:ok(e is primary,'first fatal exact object')
  ok(order==['close','last'] and not Path('/proc/self/fd/'+str(fd)).exists(),'all cleanup attempted descriptor absent')
save('CHECKS01.json',{'count':len(checks),'checks':checks,'actual_Root_capture':False,'actual_Root_restore':False});print('INDEPENDENT CHECKS',len(checks))
