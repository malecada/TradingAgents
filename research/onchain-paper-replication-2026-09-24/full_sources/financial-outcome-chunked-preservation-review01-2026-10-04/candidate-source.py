"""Finite byte-only chunk archive and flat recovery; no research authority.

Raw chunks (not tar/gzip) have exact length/hash framing in paged manifests.
No child process is created. Git is opaque retained bytes, not verified objects.
"""
import hashlib,json,os,shutil,stat,time
from pathlib import Path
import recovery04 as R
from owned_io import _opened,_cleanup
FILE=4*1024**2
CHUNK=1024**2
TOTAL=1024**3
FLOOR=10*1024**3
ENTRIES=32768
PAGE=128
SECONDS=1800
FINAL_REVIEW=None

def require(v,m):
 if not v:raise ValueError(m)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def canonical_root(value):
 p=Path(value);require(type(value)is str and p.is_absolute() and p.resolve()==p and str(p)==value,'canonical absolute root required');R.path_name(value.lstrip('/'));return p
def anchor(path):
 s=path.lstat();require(stat.S_ISDIR(s.st_mode) and not path.is_symlink(),'regular directory anchor required');return {'device':s.st_dev,'inode':s.st_ino,'mode':stat.S_IMODE(s.st_mode)}
def check_anchor(path,want):require(anchor(path)==want,'root directory anchor changed')
def disjoint(paths):
 for i,p in enumerate(paths):
  for q in paths[i+1:]:require(p!=q and not p.is_relative_to(q) and not q.is_relative_to(p),'source/output scope overlaps')
def name(value):R.path_name(value);require('/' not in value,'one relative component required');return value
class Bounds:
 def __init__(self):self.deadline=time.monotonic()+SECONDS;self.anchors={}
 def check(self,path):
  require(time.monotonic()<self.deadline,'finite archive time expired');require(shutil.disk_usage(path).free>=FLOOR,'10GiB disk floor')

def scan(root,bounds):
 """Complete sorted inventory including dot/Git bodies; original roots unchanged."""
 root=canonical_root(str(root));root_anchor=anchor(root);rows=[];logical=allocated=root.stat().st_blocks*512
 def visit(relative):
  nonlocal logical,allocated
  path=root/relative;fd=None;it=None
  try:
   fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);before=R.sig(os.fstat(fd));it=os.scandir(fd);names=[]
   for entry in it:
    require(len(rows)+len(names)<ENTRIES,'entry bound');names.append(entry.name)
   for leaf in sorted(names):
    bounds.check(root);rel=leaf if not relative else relative+'/'+leaf;R.path_name(rel);p=root/rel;s=p.lstat();require(p.resolve()==p and s.st_dev==root_anchor['device'],'redirect/device boundary')
    row={'path':rel,'mode':stat.S_IMODE(s.st_mode)};allocated+=s.st_blocks*512
    if stat.S_ISDIR(s.st_mode):row['kind']='directory';rows.append(row);visit(rel)
    else:
     raw=R.read(root,rel);require(R.sig(p.lstat())==R.sig(s),'source changed during inventory');logical+=len(raw);row.update(kind='file',bytes=len(raw),sha256=sha(raw));rows.append(row)
    require(len(rows)<=ENTRIES and logical<=TOTAL and allocated<=TOTAL,'whole source bound')
   require(before==R.sig(path.lstat())==R.sig(os.fstat(fd)),'directory changed during scan')
  finally:_cleanup((() if it is None else (it.close,))+(() if fd is None else (lambda:os.close(fd),)))
 visit('');check_anchor(root,root_anchor)
 require(not (root/'.git').is_file(),'external Git worktree pointer not complete Git')
 for rel in ('.git/objects/info/alternates','objects/info/alternates'):
  if (root/rel).exists():require(R.read(root,rel).strip()==b'','external Git alternates not a complete opaque root')
 return {'anchor':root_anchor,'members':sorted(rows,key=lambda r:r['path']),'logical':logical,'allocated':allocated}

def _write(directory,filename,raw,bounds):
 name(filename);require(type(raw)is bytes and len(raw)<=FILE,'4MiB output extent');bounds.check(directory)
 require(shutil.disk_usage(directory).free-len(raw)>=FLOOR,'prospective disk floor')
 # Open every ancestor without following links, then bind the actual output inode
 # before creating any file. A renamed/replaced target cannot redirect writes.
 fds=[];child=None
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(fd)
  for part in directory.parts[1:]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd)
  info=os.fstat(fd);actual={'device':info.st_dev,'inode':info.st_ino,'mode':stat.S_IMODE(info.st_mode)}
  require(actual==bounds.anchors[directory],'owned output anchor differs')
  child=os.open(filename,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
  view=memoryview(raw)
  while view:
   n=os.write(child,view[:65536]);require(type(n)is int and n>0,'short write');view=view[n:]
  os.fsync(child);require(os.fstat(child).st_size==len(raw),'output extent differs');check_anchor(directory,actual)
 finally:_cleanup((() if child is None else (lambda:os.close(child),))+tuple(lambda f=f:os.close(f) for f in reversed(fds)))
 return {'name':filename,'bytes':len(raw),'sha256':sha(raw)}
def _sync(path):
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:_cleanup((lambda:os.close(fd),))
def fresh(parent,target):
 require(target.parent==parent and target.name not in ('','.','..'),'fresh direct output child required');name(target.name);require(parent.resolve()==parent,'redirected parent');a=anchor(parent);target.mkdir();check_anchor(parent,a);_sync(parent);return anchor(target)
def read_record(root,record):
 require(type(record)is dict and set(record)=={'name','bytes','sha256'},'artifact descriptor fields');name(record['name']);require(type(record['bytes'])is int and 0<=record['bytes']<=FILE,'artifact extent')
 raw=R.read(root,record['name']);require(len(raw)==record['bytes'] and sha(raw)==record['sha256'],'artifact hash/length differs');return raw

def capture(roots,destination):
 """Caller owns frozen closed roots and fresh output; no authority inferred."""
 bounds=Bounds();require(type(roots)is dict and 0<len(roots)<=4,'one to four exact closed roots');roots={name(k):canonical_root(v) for k,v in sorted(roots.items())}
 target=canonical_root(str(destination));parent=target.parent;require(not target.exists(),'one-use archive destination');disjoint([*roots.values(),target]);bounds.check(parent)
 inventories={label:scan(root,bounds) for label,root in roots.items()}
 entries=[{'root':label,**row} for label,inv in inventories.items() for row in inv['members']]
 require(len(entries)<=ENTRIES,'aggregate entry bound')
 size=sum(r['bytes'] for r in entries if r['kind']=='file');allocated=sum(v['allocated'] for v in inventories.values())
 # All original + archive + eventual flat bodies, metadata/blocks/inodes reserved.
 reserve=size*3+32*1024**2+len(entries)*16384
 require(reserve<=TOTAL and allocated+size*2+32*1024**2+len(entries)*16384<=TOTAL,'full retained-source/archive/recovery copies exceed fixed1GiB watch')
 ta=fresh(parent,target);bounds.anchors[target]=ta;written=[];pages=[];page=[];chunks=[];ordinal=0
 try:
  intent={'schema_version':1,'kind':'opaque-chunk-capture-intent','roots':{k:{'path':str(roots[k]),'anchor':v['anchor']} for k,v in inventories.items()},'member_count':len(entries),'file_count':sum(r['kind']=='file' for r in entries),'logical_bytes':size,'reserved_whole_bytes':max(reserve,allocated+size*2+32*1024**2+len(entries)*16384),'native_or_research_authority':False}
  _write(target,'intent.json',encode(intent),bounds);written.append('intent.json')
  for row in entries:
   check_anchor(target,ta);out=dict(row)
   if row['kind']=='file':
    raw=R.read(roots[row['root']],row['path']);require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'source body changed after inventory');out['chunks']=[]
    for start in range(0,len(raw),CHUNK):
     filename='chunk-%08d.bin'%ordinal;ordinal+=1;record=_write(target,filename,raw[start:start+CHUNK],bounds);chunks.append(record);out['chunks'].append(record);written.append(filename)
   page.append(out)
   if len(page)==PAGE:
    filename='page-%05d.json'%len(pages);pages.append(_write(target,filename,encode(page),bounds));written.append(filename);page=[]
  if page:
   filename='page-%05d.json'%len(pages);pages.append(_write(target,filename,encode(page),bounds));written.append(filename)
  require({k:scan(root,bounds) for k,root in roots.items()}==inventories,'source inventory changed before completion')
  index={**intent,'kind':'opaque-chunk-complete-index','pages':pages,'chunk_count':len(chunks),'chunk_bytes':sum(r['bytes'] for r in chunks),'member_manifest_sha256':sha(encode(entries)),'git_qualification':'all declared Git bytes retained as opaque paths/modes/content; no Git OID/object/ancestry verification performed','flat_qualification':'logical modes/directories preserved as metadata; no POSIX restoration claim'}
  _write(target,'index.json',encode(index),bounds);written.append('index.json');_sync(target)
  require(set(p.name for p in target.iterdir())==set(written),'unexpected archive member');return {'index_sha256':sha(encode(index)),'directory':str(target),'members':len(entries),'chunks':len(chunks),'logical_bytes':size}
 except BaseException as primary:
  # All completed/partial artifacts remain; failure receipt is best effort only.
  try:_write(target,'capture-failure.json',encode({'status':'failed','error_type':type(primary).__name__,'completed_artifacts':written,'qualification':'partial bodies retained; no complete recovery authority'}),bounds)
  except BaseException as cleanup:
   _cleanup((lambda:(_ for _ in ()).throw(cleanup),),primary=primary)
  raise

def validate_archive(directory,index_hash,bounds):
 root=canonical_root(str(directory));raw=R.read(root,'index.json');require(sha(raw)==index_hash,'exact complete index pin required');index=json.loads(raw);require(encode(index)==raw,'canonical index framing')
 required={'schema_version','kind','roots','member_count','file_count','logical_bytes','reserved_whole_bytes','native_or_research_authority','pages','chunk_count','chunk_bytes','member_manifest_sha256','git_qualification','flat_qualification'}
 require(set(index)==required and type(index['schema_version'])is int and index['schema_version']==1 and index['kind']=='opaque-chunk-complete-index' and index['native_or_research_authority'] is False,'complete index schema')
 require(type(index['pages'])is list and len(index['pages'])<=ENTRIES//PAGE+1 and type(index['member_count'])is int and 0<=index['member_count']<=ENTRIES,'finite page/entry count')
 require(type(index['reserved_whole_bytes'])is int and index['reserved_whole_bytes']<=TOTAL,'fixed writable cap');require(type(index['roots'])is dict and 0<len(index['roots'])<=4,'finite roots')
 for label,ref in index['roots'].items():
  name(label);require(set(ref)=={'path','anchor'},'root fields');canonical_root(ref['path']);require(set(ref['anchor'])=={'device','inode','mode'} and all(type(v)is int and v>=0 for v in ref['anchor'].values()) and ref['anchor']['mode']<=0o7777,'root anchor fields')
 members=[];chunks=[];seen=set();expected={'intent.json','index.json'};directories=set();logical=0
 for i,page in enumerate(index['pages']):
  bounds.check(root);require(page['name']=='page-%05d.json'%i,'canonical page sequence');body=read_record(root,page);rows=json.loads(body);require(encode(rows)==body and type(rows)is list and 0<len(rows)<=PAGE,'page framing');expected.add(page['name'])
  for row in rows:
   bounds.check(root)
   require(type(row)is dict and row.get('kind') in ('file','directory'),'typed member');require(set(row)==({'root','path','mode','kind'}|({'bytes','sha256','chunks'} if row['kind']=='file' else set())),'member fields')
   name(row['root']);require(row['root'] in index['roots'],'unknown root');R.path_name(row['path']);key=(row['root'],row['path']);require(key not in seen,'duplicate member');seen.add(key);parent=str(Path(row['path']).parent);require(parent=='.' or (row['root'],parent) in directories,'missing directory parent');require(type(row['mode'])is int and 0<=row['mode']<=0o7777,'mode')
   bare={k:v for k,v in row.items() if k!='chunks'};members.append(bare)
   if row['kind']=='directory':directories.add(key)
   else:
    require(type(row['bytes'])is int and 0<=row['bytes']<=FILE and type(row['chunks'])is list and len(row['chunks'])<=4,'file extent/fragments');h=hashlib.sha256();count=0
    for record in row['chunks']:
     require(record['name']=='chunk-%08d.bin'%len(chunks),'unique contiguous chunk sequence');part=read_record(root,record);require(len(part)==min(CHUNK,row['bytes']-count) and len(part)>0,'canonical chunk extent');h.update(part);count+=len(part);chunks.append(record);expected.add(record['name'])
    require(count==row['bytes'] and h.hexdigest()==row['sha256'],'complete file fragment hash/length');logical+=count
  require(len(members)<=ENTRIES and logical<=TOTAL,'aggregate bound')
 require([(r['root'],r['path']) for r in members]==sorted(seen),'exact sorted membership')
 require(len(members)==index['member_count'] and sum(r['kind']=='file' for r in members)==index['file_count'] and logical==index['logical_bytes']==index['chunk_bytes'] and len(chunks)==index['chunk_count'] and sha(encode(members))==index['member_manifest_sha256'],'complete index denominator differs')
 require(logical*3+32*1024**2+len(members)*16384<=index['reserved_whole_bytes']<=TOTAL,'declared simultaneous capacity invalid')
 intent=json.loads(R.read(root,'intent.json'));require(intent=={k:v for k,v in index.items() if k not in {'pages','chunk_count','chunk_bytes','member_manifest_sha256','git_qualification','flat_qualification'}}|{'kind':'opaque-chunk-capture-intent'},'intent/index roots differ')
 require(set(p.name for p in root.iterdir())==expected,'missing/extra archive bodies');return index,members

def restore(directory,index_hash,destination):
 bounds=Bounds();archive=canonical_root(str(directory));index,members=validate_archive(archive,index_hash,bounds);target=canonical_root(str(destination));disjoint([archive,target,*[Path(v['path']) for v in index['roots'].values()]]);require(not target.exists(),'one-use restore destination');bounds.check(target.parent);ta=fresh(target.parent,target);bounds.anchors[target]=ta
 # Flat body names avoid interpreting logical Git/member paths as host paths.
 mapping=[];ordinal=0;written=[];page_rows=[]
 try:
  for page in index['pages']:
   for row in json.loads(read_record(archive,page)):
    bounds.check(target);check_anchor(target,ta)
    if row['kind']=='file':
     raw=b''.join(read_record(archive,c) for c in row['chunks']);require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'body changed during flat recovery')
     filename='body-%08d.bin'%ordinal;ordinal+=1;_write(target,filename,raw,bounds);written.append(filename);mapping.append({'root':row['root'],'path':row['path'],'body':filename,'mode':row['mode'],'bytes':len(raw),'sha256':sha(raw)})
  # Paged flat index avoids recreating the original single-metadata-file limit.
  pages=[]
  for start in range(0,len(mapping),PAGE):
   filename='mapping-%05d.json'%len(pages);pages.append(_write(target,filename,encode(mapping[start:start+PAGE]),bounds));written.append(filename)
  validate_archive(archive,index_hash,bounds)
  for row in mapping:require(sha(R.read(target,row['body']))==row['sha256'],'flat retained body differs')
  for page in index['pages']:
   _write(target,page['name'],read_record(archive,page),bounds);written.append(page['name'])
  _write(target,'index.json',R.read(archive,'index.json'),bounds);written.append('index.json')
  receipt={'schema_version':1,'status':'complete-flat-byte-recovery','source_index_sha256':index_hash,'mapping_pages':pages,'file_count':len(mapping),'member_count':len(members),'logical_bytes':index['logical_bytes'],'member_manifest_sha256':index['member_manifest_sha256'],'roots':index['roots'],'qualification':'complete logical directory/mode manifest and Git bytes retained in this flat tree; no POSIX/Git object instantiation or scientific authority'}
  _write(target,'recovery.json',encode(receipt),bounds);written.append('recovery.json');_sync(target);require(set(p.name for p in target.iterdir())==set(written),'unexpected flat output');return receipt
 except BaseException as primary:
  try:_write(target,'restore-failure.json',encode({'status':'failed','error_type':type(primary).__name__,'completed_artifacts':written,'qualification':'partial flat bodies preserved; no complete recovery'}),bounds)
  except BaseException as cleanup:_cleanup((lambda:(_ for _ in ()).throw(cleanup),),primary=primary)
  raise


def verify_flat(directory,index_hash):
 """Verify fresh flat bodies and complete copied manifest without source trees."""
 bounds=Bounds();root=canonical_root(str(directory));raw=R.read(root,'index.json');require(sha(raw)==index_hash,'flat complete index differs');index=json.loads(raw);require(encode(index)==raw,'flat index framing')
 require(type(index['pages'])is list and len(index['pages'])<=ENTRIES//PAGE+1 and 0<=index['member_count']<=ENTRIES,'flat finite denominator')
 receipt=json.loads(R.read(root,'recovery.json'));require(receipt['status']=='complete-flat-byte-recovery' and receipt['source_index_sha256']==index_hash and receipt['roots']==index['roots'],'flat receipt ancestry')
 members=[];expected={'index.json','recovery.json'}
 for i,page in enumerate(index['pages']):
  require(page['name']=='page-%05d.json'%i,'flat page sequence');raw=read_record(root,page);rows=json.loads(raw);require(encode(rows)==raw and type(rows)is list and len(rows)<=PAGE,'flat member page framing');expected.add(page['name']);members.extend({k:v for k,v in r.items() if k!='chunks'} for r in rows)
 require(len(members)==index['member_count'] and sha(encode(members))==index['member_manifest_sha256']==receipt['member_manifest_sha256'],'flat full member manifest differs')
 keys=[(r['root'],r['path']) for r in members];require(keys==sorted(set(keys)),'flat duplicate/missing membership');dirs=set();files=[]
 for row in members:
  R.path_name(row['path']);require(row['root'] in index['roots'],'flat root differs');parent=str(Path(row['path']).parent);require(parent=='.' or (row['root'],parent) in dirs,'flat missing directory');require(type(row['mode'])is int and 0<=row['mode']<=0o7777,'flat mode')
  if row['kind']=='directory':dirs.add((row['root'],row['path']))
  else:require(row['kind']=='file','flat member kind');files.append(row)
 mappings=[];require(type(receipt['mapping_pages'])is list and len(receipt['mapping_pages'])<=ENTRIES//PAGE+1,'flat mapping bound')
 for i,page in enumerate(receipt['mapping_pages']):
  require(page['name']=='mapping-%05d.json'%i,'flat mapping sequence');raw=read_record(root,page);rows=json.loads(raw);require(encode(rows)==raw and type(rows)is list and len(rows)<=PAGE,'flat mapping framing');mappings.extend(rows);expected.add(page['name'])
 require(len(mappings)==len(files)==index['file_count']==receipt['file_count'],'flat file denominator')
 total=0
 for i,(row,mapping) in enumerate(zip(files,mappings,strict=True)):
  bounds.check(root);filename='body-%08d.bin'%i;require(mapping=={'root':row['root'],'path':row['path'],'body':filename,'mode':row['mode'],'bytes':row['bytes'],'sha256':row['sha256']},'flat logical identity differs');raw=R.read(root,filename);require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'flat body hash/extent');total+=len(raw);expected.add(filename)
 require(total==index['logical_bytes']==receipt['logical_bytes'] and receipt['member_count']==len(members),'flat total differs');require(set(p.name for p in root.iterdir())==expected,'flat unexpected/missing body');return receipt
