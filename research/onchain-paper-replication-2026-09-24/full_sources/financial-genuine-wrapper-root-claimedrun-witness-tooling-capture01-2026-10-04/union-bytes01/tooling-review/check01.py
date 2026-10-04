import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile,time,types
from pathlib import Path
H=Path(__file__).resolve().parent; B=H.parent; A=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-preparation02-2026-10-04'
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
checks=[]
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,q):p.write_text(json.dumps(q,sort_keys=True,indent=2)+'\n')
def refuse(fn,n):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError) as e:checks.append(n+': '+type(e).__name__+': '+str(e));return
 raise AssertionError('not refused '+n)
def rows(root):
 out=[]
 def walk(p,name):
  t=p.lstat();r={'path':name,'mode':stat.S_IMODE(t.st_mode)}
  if stat.S_ISLNK(t.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(t.st_mode):
   r['kind']='directory';out.append(r)
   for child in sorted(p.iterdir()):walk(child,child.name if name=='.' else name+'/'+child.name)
   return
  else:
   ck(stat.S_ISREG(t.st_mode) and t.st_nlink==1,'regular singlelink '+name);body=R.read(root,name);r.update(kind='file',bytes=len(body),sha256=sha(body))
  out.append(r)
 walk(root,'.');return sorted(out,key=lambda r:r['path'])
def seal(root,name,pin):
 body=R.read(root,name);ck(sha(body)==pin,'seal pin '+str(root.name));q=json.loads(body);actual=rows(root);by={r['path']:r for r in actual}
 for r in q['members']:
  ck(r==by[r['path']],'full sealed typed member '+root.name+'/'+r['path'])
 ck(set(by)=={r['path'] for r in q['members']}|{'.',name},'full frozen membership '+root.name)
 return actual
seal(A,'MANIFEST01.json','97e91712054ba8af26302606e70c40577fc8059b8b10a1966d865d1806afe359')
s=R.read(A,'capture_witness02.py').decode();ck(sha(s.encode())=='b275af0c30a4f19227cff1cccbc19c01d7548b3b218e43f78a3be493bfe05ae6','candidate pin')
ns={'__name__':'read_only_review','__file__':str(A/'capture_witness02.py')};exec(compile(s,str(A/'capture_witness02.py'),'exec'),ns)
for n,p in ns['PINS'].items():ck(sha(R.read(ns['PRIMITIVES'],n))==p,'original primitive '+n)
ck(sha(R.read(A,'shards01.py'))=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba','unchanged planner')
x=s
for e in reversed(json.loads(R.read(A,'INVERSE01.json'))['edits']):ck(x.count(e['new'])==1,'unique inverse');x=x.replace(e['new'],e['old'])
old=R.read(A,'original-capture_witness01.py').decode();ck(x==old and ast.dump(ast.parse(x))==ast.dump(ast.parse(old)),'complete byte+AST inverse')
refuse(ns['main'],'uninstalled fixed Root refusal')
census=[]
for label,root in sorted(ns['SCOPES'].items()):
 rr=seal(root,'MANIFEST02.json' if label=='actual-capture-review' else 'MANIFEST01.json',ns['SEALS'][label]);census.append({'scope':label,'original_root':str(root),'members':rr})
expected=json.loads(R.read(A,'CURRENT_SCOPE01.json'))['original_trees'];ck(census==expected,'independent entire current census equals frozen author observation')
allr=[r for t in census for r in t['members']];files=[r for r in allr if r['kind']=='file'];ck(len(files)==2302 and sum(r['bytes'] for r in files)==61971030 and sum(r['kind']=='lexical-symlink' for r in allr)==59,'actual five full roots')
d=ns['DIRECT'];db=R.read(ns['MAIN'],d['source_path']);ck(len(db)==2532973 and sha(db)==d['sha256'],'actual raw direct bytes');ck(stat.S_IMODE((ns['MAIN']/d['source_path']).lstat().st_mode)==384,'actual direct mode')
ck([r['bytes'] for r in files if r['bytes']>2*1024**2]==[2532973],'exact sole greater-than2MiB body')
# Independently construct the virtual copy metadata without performing the real capture.
virtual=[];inv=copy.deepcopy(census)
for t in inv:
 virtual.append({'path':t['scope'],'kind':'directory','mode':448})
 for r in t['members']:
  if r['path']=='.':continue
  name=t['scope']+'/'+r['path']
  if r['kind']=='directory':virtual.append({'path':name,'kind':'directory','mode':448})
  elif r['kind']=='file':
   ns['bind_member'](t['scope'],r['path'],r,d)
   if 'union_path' in r:virtual.append(dict(path=name,kind='file',mode=384,bytes=r['bytes'],sha256=r['sha256']))
# Use the literal mapping assignment from the exact source, not an invented receipt.
main=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main')
mapassign=next(n for n in main.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='mapping' for v in n.targets))
mns=dict(ns,inventory=inv,total=61971030);exec(compile(ast.Module(body=[mapassign],type_ignores=[]),'exact mapping','exec'),mns);mb=ns['encoded'](mns['mapping']);ck(61971030+len(mb)<=64*1024**2,'64MiB includes direct+mapping')
virtual.append(dict(path='ORIGINAL_TREES01.json',kind='file',mode=384,bytes=len(mb),sha256=sha(mb)));vm={'schema_version':1,'root_mode':448,'members':sorted(virtual,key=lambda r:r['path'])};R.validate(vm);ns['partition_join'](inv,vm,d)
spec=importlib.util.spec_from_file_location('review_planner',A/'shards01.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);groups=P.partition(vm)
ck(sorted(p for g in groups for p in g['regular_paths'])==sorted(r['path'] for r in virtual if r['kind']=='file'),'actual projected exact shard cover')
for g in groups:ck(len(g['manifest']['members'])<=256 and sum(r.get('bytes',0) for r in g['manifest']['members'])<=2*1024**2,'projected finite parent-inclusive shard')
R.same(ns['SOURCE'],json.loads(R.read(ns['SOURCE_CAPTURE'],'source-manifest.json')))
ck(sha(R.read(ns['PARENT'],'REQUEST_FINAL03.json'))=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8','current final request')
ck(sha(R.read(ns['PARENT'],'proofs/FULL_SOURCE_RECOVERY01.json'))=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825','current Source full recovery proof')
ck(not os.path.lexists(ns['PARENT']/'attempt'),'no Parent attempt')
# Exact main suffix executed only on explicitly owned opaque projections.
pos=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in n.targets));fn=ast.FunctionDef(name='projection',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=main.body[pos:],decorator_list=[]);ast.fix_missing_locations(fn)
for case in ('valid','direct-body','direct-mode','late-extra','literal-change','missing-direct'):
 h=H/case;h.mkdir(mode=0o700);roots={}
 for i in range(5):
  p=h/('original'+str(i));p.mkdir(mode=0o700);(p/'empty').mkdir(mode=0o700);(p/'link').symlink_to('../not-followed');(p/'small').write_bytes(b'opaque');roots[str(i)]=p
 p=roots['0']/'direct';p.write_bytes(db if case=='valid' else b'direct opaque');p.chmod(0o600);body=p.read_bytes();desc=dict(scope='0',path='direct',source_path=p.relative_to(H).as_posix(),bytes=len(body),sha256=sha(body),mode=384)
 if case=='valid':
  for i in range(3):q=roots['1']/('chunk'+str(i));q.write_bytes(bytes([17+i])*1100000);q.chmod(0o600)
 source=h/'source';source.mkdir(mode=0o700);(source/'opaque').write_bytes(b'unrelated projection');sm=R.scan(source)
 local={'__name__':'owned_projection','__file__':str(A/'capture_witness02.py')};exec(compile(s,'exact exporter definitions','exec'),local);local.update(HERE=h,MAIN=H,SCOPES=roots,DIRECT=desc,SOURCE=source,source_manifest=sm,start=time.monotonic(),planner=P)
 proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)});fired=[]
 def pack(root,m,out):
  result=R.pack(root,m,out)
  if not fired:
   fired.append(True)
   if case=='direct-body':p.write_bytes(b'changed')
   elif case=='direct-mode':p.chmod(0o644)
   elif case=='late-extra':(roots['2']/'extra').write_bytes(b'extra')
   elif case=='literal-change':(roots['2']/'link').unlink();(roots['2']/'link').symlink_to('different')
  return result
 proxy.pack=pack;exec(compile(ast.Module(body=[fn],type_ignores=[]),'exact owned suffix','exec'),local)
 if case=='missing-direct':p.unlink()
 if case!='valid':refuse(lambda:local['projection'](proxy),'actual pipeline '+case);ck(not (h/'UNION_AUTHENTICATION01.json').exists(),'no false auth '+case);continue
 local['projection'](proxy);idx=json.loads(R.read(h,'SHARD_INDEX01.json'));mapping=json.loads(R.read(h/'union-bytes01','ORIGINAL_TREES01.json'));manifest=json.loads(R.read(h,'union-manifest.json'));auth=json.loads(R.read(h,'UNION_AUTHENTICATION01.json'))
 ck(idx['kind']=='complete-witness-shards-plus-direct-v1' and idx['direct_bodies']==[desc] and len(idx['shards'])>=3,'actual current index kind and full direct descriptor')
 recovered={}
 for j,g in enumerate(idx['shards']):
  mm=json.loads(R.read(h,g['manifest']['path']));archive=R.read(h,g['archive']['path']);flat=h/('flat'+str(j));flat.mkdir(mode=0o700);out=R.restore(h/g['archive']['path'],{k:v for k,v in g['archive'].items() if k!='path'},mm,flat);meta=json.loads(R.read(flat,out['metadata_file']))
  for name,leaf in meta['flat_members'].items():ck(name not in recovered,'unique flat path');recovered[name]=R.read(flat,leaf)
  buf=io.BytesIO()
  with gzip.GzipFile(fileobj=buf,mode='wb',filename='',mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
    for row in mm['members']:
     ti=tarfile.TarInfo(row['path']);ti.mode=row['mode'];ti.uid=ti.gid=ti.mtime=0;ti.uname=ti.gname=''
     if row['kind']=='directory':ti.type=tarfile.DIRTYPE;tf.addfile(ti)
     else:bb=recovered[row['path']];ti.size=len(bb);tf.addfile(ti,io.BytesIO(bb))
  ck(buf.getvalue()==archive,'independent complete canonical recompression')
 original_files=[r for t in mapping['scope_trees'] for r in t['members'] if r['kind']=='file']
 for row in original_files:
  bb=R.read(H,desc['source_path']) if 'direct_source_path' in row else recovered[row['union_path']];ck(len(bb)==row['bytes'] and sha(bb)==row['sha256'],'all original reconstruction including actual2532973 raw')
 ck(auth['direct_regular_members']==1 and auth['original_lexical_links']==5,'literal metadata retained')
 for mutation in ('missing','duplicate','hash','mode','path','extra-archive','missing-archive'):
  trees=copy.deepcopy(mapping['scope_trees']);mm=copy.deepcopy(manifest);rr=next(r for t in trees for r in t['members'] if 'direct_source_path' in r)
  if mutation=='missing':next(t for t in trees if rr in t['members'])['members'].remove(rr)
  elif mutation=='duplicate':trees[0]['members'].append(copy.deepcopy(rr))
  elif mutation=='hash':rr['sha256']='0'*64
  elif mutation=='mode':rr['mode']=420
  elif mutation=='path':rr['direct_source_path']+='bad'
  elif mutation=='extra-archive':mm['members'].append(dict(path='extra',kind='file',mode=384,bytes=0,sha256=sha(b'')))
  else:mm['members'].remove(next(r for r in mm['members'] if r['kind']=='file' and r['path']!='ORIGINAL_TREES01.json'))
  refuse(lambda:local['partition_join'](trees,mm,desc),'partition '+mutation)
 # Reusing a projected namespace must refuse mkdir; no real Root reuse.
 refuse(lambda:local['projection'](R),'one-use owned projection')
# Real original IO reducer with real held descriptors, no stand-in cleanup.
for i,firstclass in enumerate((MemoryError,KeyboardInterrupt,SystemExit)):
 for j,secondclass in enumerate((OSError,MemoryError,SystemExit)):
  first=firstclass('original fatal');second=secondclass('close diagnostic');fd=os.open(H/('fd-%d-%d'%(i,j)),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);events=[]
  def close():os.close(fd);events.append('close');raise second
  def tail():events.append('tail')
  try:
   try:raise first
   finally:R._cleanup((close,tail))
  except BaseException as e:ck(e is first,'exact real first fatal identity')
  ck(events==['close','tail'] and not Path('/proc/self/fd/'+str(fd)).exists(),'independent cleanup closed real FD')
ck(not any(k in sys.modules for k in ('numpy','torch','scipy','pandas')),'no numerical imports')
# Final current membership re-read independently, no write outside this review.
for t in census:ck(rows(Path(t['original_root']))==t['members'],'final unchanged original '+t['scope'])
save(H/'READBACK01.json',{'schema_version':1,'decision':'accepted-source-only-sharded-witness-capture-plus-exact-direct','source_sha256':sha(s.encode()),'author_manifest_sha256':'97e91712054ba8af26302606e70c40577fc8059b8b10a1966d865d1806afe359','checks':checks,'count':len(checks),'original_regular_bodies':2302,'original_logical_bytes':61971030,'literal_links':59,'direct_body':d,'mapping_bytes':len(mb),'whole_logical_including_mapping':61971030+len(mb),'projected_shards':len(groups),'index_kind':'complete-witness-shards-plus-direct-v1','actual_root_capture':False,'actual_external_recovery':False,'shards_alone_complete':False,'numerical_authority':False})
save(H/'ACTUAL_CENSUS01.json',{'scope_trees':census});print('PASS',len(checks), 'projected shards',len(groups),'mapping',len(mb))
