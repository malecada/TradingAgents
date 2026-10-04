import gzip,hashlib,io,json,os,stat,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04';UNION=ROOT/'union-bytes01'
checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def read(p):
 s=p.lstat();check(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded regular '+str(p));b=p.read_bytes();check((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(p.lstat().st_dev,p.lstat().st_ino,p.lstat().st_size,p.lstat().st_mtime_ns,p.lstat().st_ctime_ns),'stable read '+str(p));return b
mappingraw=read(UNION/'ORIGINAL_TREES01.json');mapping=json.loads(mappingraw);manifestraw=read(ROOT/'union-manifest.json');manifest=json.loads(manifestraw);authraw=read(ROOT/'UNION_AUTHENTICATION01.json');auth=json.loads(authraw);archive=read(ROOT/'union.tar.gz')
check(mappingraw==encoded(mapping) and manifestraw==encoded(manifest) and authraw==encoded(auth),'canonical metadata encoding')
pre=json.loads((HERE/'SCOPE_CHECK01.json').read_bytes());expected={(r['scope'],r['path']):r for r in pre['actual_original_rows']}
check(len(mapping['scope_trees'])==11,'eleven actual whole originals');observed={};originalbytes=0;linkcount=0
for tree in mapping['scope_trees']:
 scope=tree['scope'];root=Path(tree['original_root']);check(root.resolve()==root and root.is_absolute(),'actual canonical original '+scope)
 actual=[]
 def visit(p,rel):
  s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory';actual.append(r)
   for q in sorted(p.iterdir()):visit(q,q.name if rel=='.' else rel+'/'+q.name)
   return
  else:
   b=read(p);r.update(kind='file',bytes=len(b),sha256=sha(b),union_path=scope+'/'+rel)
  actual.append(r)
 visit(root,'.');check(sorted(actual,key=lambda r:r['path'])==tree['members'],'fresh complete original '+scope)
 for r in tree['members']:
  joined=dict(scope=scope,**{k:v for k,v in r.items() if k!='union_path'});check(joined==expected[(scope,r['path'])],'preflight exact member '+scope+'/'+r['path']);observed[scope,r['path']]=r
  if r['kind']=='file':
   b=read(UNION/r['union_path']);check(len(b)==r['bytes'] and sha(b)==r['sha256'],'ordinary mapped body '+r['union_path']);originalbytes+=len(b)
  elif r['kind']=='lexical-symlink':linkcount+=1;check(not os.path.lexists(UNION/scope/r['path']),'literal link never instantiated')
check(set(expected)==set(observed),'complete original set');check(originalbytes==mapping['original_regular_logical_bytes'],'original logical byte total')
actualrows=[]
def unionwalk(root):
 for p in sorted(root.iterdir()):
  s=p.lstat();rel=str(p.relative_to(UNION));row={'path':rel,'mode':stat.S_IMODE(s.st_mode)};check(not stat.S_ISLNK(s.st_mode),'ordinary union no links '+rel)
  if stat.S_ISDIR(s.st_mode):row['kind']='directory';actualrows.append(row);unionwalk(p)
  else:b=read(p);row.update(kind='file',bytes=len(b),sha256=sha(b));actualrows.append(row)
unionwalk(UNION);check(sorted(actualrows,key=lambda r:r['path'])==manifest['members'],'actual complete ordinary manifest');check(stat.S_IMODE(UNION.stat().st_mode)==manifest['root_mode'],'ordinary root mode')
check(sum(r.get('bytes',0) for r in actualrows)<=64*1024**2,'whole mapping inclusive64MiB');check(len(archive)<=4*1024**2,'whole archive4MiB')
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
 members=tf.getmembers();check(len(members)==len(manifest['members']),'archive complete count')
 for t,r in zip(members,manifest['members']):
  check(t.name==r['path'] and t.mode==r['mode'] and t.uid==0 and t.gid==0 and t.uname=='' and t.gname=='' and t.mtime==0,'canonical header '+t.name)
  check(t.isdir() if r['kind']=='directory' else t.isfile(),'archive type '+t.name)
  if t.isfile():b=tf.extractfile(t).read();check(len(b)==r['bytes'] and sha(b)==r['sha256'],'archive body '+t.name)
  else:check(t.size==0,'empty directory payload '+t.name)
# Independently rebuild canonical tar/gzip stream from observed actual union bytes.
sink=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
  for r in manifest['members']:
   t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
   if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tf.addfile(t)
   else:b=read(UNION/r['path']);t.size=len(b);tf.addfile(t,io.BytesIO(b))
check(sink.getvalue()==archive,'independent full canonical recompression')
check(auth['archive']==dict(bytes=len(archive),sha256=sha(archive),manifest_sha256=sha(manifestraw)),'actual archive authentication')
check(auth['union_mapping_sha256']==sha(mappingraw),'mapping authentication');check(auth['original_typed_members']==len(observed) and auth['original_regular_members']==275 and auth['original_trees']==11 and auth['original_lexical_links']==linkcount and auth['ordinary_members']==len(actualrows),'all counts')
check(auth['free_bytes']>=10*1024**3,'recorded final floor');check(auth['genuine_native_or_numerical_started'] is False and mapping['native_or_numerical_started'] is False and mapping['runtime_bodies_or_empirical_stores_recovered'] is False and mapping['links_followed_or_extracted'] is False,'no invented authority')
result=dict(decision='ACTUAL_FULL_UNION_BYTE_CAPTURE_ACCEPTED',checks=len(checks),check_names=checks,archive_sha256=sha(archive),archive_bytes=len(archive),manifest_sha256=sha(manifestraw),mapping_sha256=sha(mappingraw),authentication_sha256=sha(authraw),original_trees=11,original_members=len(observed),original_files=275,original_bytes=originalbytes,ordinary_members=len(actualrows),ordinary_files=sum(r['kind']=='file' for r in actualrows),ordinary_bytes=sum(r.get('bytes',0) for r in actualrows),lexical_links=linkcount,actual_remote=None,actual_flat=None,native_eligibility=False,scientific_authority=False)
with (HERE/'ACTUAL_CHECK02.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='check_names'}))
