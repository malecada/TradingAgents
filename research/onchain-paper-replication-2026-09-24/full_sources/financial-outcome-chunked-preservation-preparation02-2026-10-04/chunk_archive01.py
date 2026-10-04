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
 require(target.parent==parent and target.name not in ('','.','..'),'fresh direct output child required');name(target.name);require(parent.is_absolute() and parent.resolve()==parent,'redirected parent');a=anchor(parent)
 fds=[];child=None
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(fd)
  for part in parent.parts[1:]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd)
  parent_fd=fd
  info=os.fstat(parent_fd);actual={'device':info.st_dev,'inode':info.st_ino,'mode':stat.S_IMODE(info.st_mode)}
  require(actual==a,'opened parent differs from owned anchor');check_anchor(parent,a)
  # Creation is relative to the verified owned descriptor, never a redirected path.
  os.mkdir(target.name,dir_fd=parent_fd)
  child=os.open(target.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent_fd)
  info=os.fstat(child);result={'device':info.st_dev,'inode':info.st_ino,'mode':stat.S_IMODE(info.st_mode)}
  os.fsync(parent_fd);check_anchor(parent,a);require(target.resolve()==target and anchor(target)==result,'created child namespace changed');return result
 finally:_cleanup((() if child is None else (lambda:os.close(child),))+tuple(lambda f=f:os.close(f) for f in reversed(fds)))
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

def _hash(value):require(type(value)is str and len(value)==64 and all(c in '0123456789abcdef' for c in value),'SHA256 descriptor required')
def _descriptor(record,filename):
 require(type(record)is dict and set(record)=={'name','bytes','sha256'} and record['name']==filename,'canonical descriptor required');name(record['name']);require(type(record['bytes'])is int and 0<=record['bytes']<=FILE,'artifact extent');_hash(record['sha256'])
def _index(index,raw):
 """Shared exact envelope policy: neither archive nor flat path may weaken it."""
 required={'schema_version','kind','roots','member_count','file_count','logical_bytes','reserved_whole_bytes','native_or_research_authority','pages','chunk_count','chunk_bytes','member_manifest_sha256','git_qualification','flat_qualification'}
 require(type(index)is dict and set(index)==required and encode(index)==raw,'canonical complete index fields')
 require(type(index['schema_version'])is int and index['schema_version']==1 and index['kind']=='opaque-chunk-complete-index' and index['native_or_research_authority'] is False,'complete index kind/authority')
 for key in ('member_count','file_count','logical_bytes','reserved_whole_bytes','chunk_count','chunk_bytes'):require(type(index[key])is int and index[key]>=0,'integer denominator required')
 require(index['file_count']<=index['member_count']<=ENTRIES and index['chunk_count']<=4*index['file_count'] and index['logical_bytes']==index['chunk_bytes']<=TOTAL,'finite member/file/chunk count')
 require(index['logical_bytes']*3+32*1024**2+index['member_count']*16384<=index['reserved_whole_bytes']<=TOTAL,'fixed simultaneous writable reservation')
 require(index['git_qualification']=='all declared Git bytes retained as opaque paths/modes/content; no Git OID/object/ancestry verification performed' and index['flat_qualification']=='logical modes/directories preserved as metadata; no POSIX restoration claim','opaque qualification differs')
 require(type(index['pages'])is list and len(index['pages'])==(index['member_count']+PAGE-1)//PAGE,'exact finite page denominator')
 for i,page in enumerate(index['pages']):_descriptor(page,'page-%05d.json'%i)
 require(type(index['roots'])is dict and 0<len(index['roots'])<=4,'finite roots')
 paths=[]
 for label,ref in index['roots'].items():
  name(label);require(type(ref)is dict and set(ref)=={'path','anchor'},'root fields');paths.append(canonical_root(ref['path']))
  require(type(ref['anchor'])is dict and set(ref['anchor'])=={'device','inode','mode'} and all(type(v)is int and v>=0 for v in ref['anchor'].values()) and ref['anchor']['mode']<=0o7777,'root anchor fields')
 disjoint(paths);_hash(index['member_manifest_sha256']);return index

def _members(index,pages):
 """Shared pure framing/denominator/parent validator, with no body authority."""
 require(type(pages)is list and len(pages)==len(index['pages']),'complete pages required');members=[];rows=[];seen=set();directories=set();chunks=[];logical=0;files=0
 for i,page in enumerate(pages):
  require(type(page)is list and len(page)==min(PAGE,index['member_count']-len(rows)),'canonical member page length')
  for row in page:
   require(type(row)is dict and row.get('kind') in ('file','directory'),'typed member');require(set(row)==({'root','path','mode','kind'}|({'bytes','sha256','chunks'} if row['kind']=='file' else set())),'member fields')
   name(row['root']);require(row['root'] in index['roots'],'unknown root');R.path_name(row['path']);key=(row['root'],row['path']);require(key not in seen,'duplicate member');seen.add(key)
   parent=str(Path(row['path']).parent);require(parent=='.' or (row['root'],parent) in directories,'missing directory parent');require(type(row['mode'])is int and 0<=row['mode']<=0o7777,'mode')
   rows.append(row);members.append({k:v for k,v in row.items() if k!='chunks'})
   if row['kind']=='directory':directories.add(key)
   else:
    files+=1;require(type(row['bytes'])is int and 0<=row['bytes']<=FILE and type(row['chunks'])is list and len(row['chunks'])==(row['bytes']+CHUNK-1)//CHUNK,'file extent/fragments');_hash(row['sha256']);count=0
    for record in row['chunks']:
     _descriptor(record,'chunk-%08d.bin'%len(chunks));require(record['bytes']==min(CHUNK,row['bytes']-count) and record['bytes']>0,'canonical chunk extent');count+=record['bytes'];chunks.append(record)
    require(count==row['bytes'],'complete fragment extent');logical+=count
 require([(r['root'],r['path']) for r in members]==sorted(seen),'exact sorted membership')
 require(len(members)==index['member_count'] and files==index['file_count'] and logical==index['logical_bytes']==index['chunk_bytes'] and len(chunks)==index['chunk_count'] and sha(encode(members))==index['member_manifest_sha256'],'complete index denominator differs')
 return members,rows,chunks

def _pages(root,index,bounds):
 pages=[]
 for page in index['pages']:
  bounds.check(root);raw=read_record(root,page);rows=json.loads(raw);require(encode(rows)==raw,'canonical page framing');pages.append(rows)
 return pages

def validate_archive(directory,index_hash,bounds):
 root=canonical_root(str(directory));raw=R.read(root,'index.json');_hash(index_hash);require(sha(raw)==index_hash,'exact complete index pin required');index=_index(json.loads(raw),raw)
 members,rows,chunks=_members(index,_pages(root,index,bounds));expected={'intent.json','index.json'}|{p['name'] for p in index['pages']}
 for row in rows:
  bounds.check(root)
  if row['kind']=='file':
   h=hashlib.sha256();count=0
   for record in row['chunks']:
    part=read_record(root,record);h.update(part);count+=len(part);expected.add(record['name'])
   require(count==row['bytes'] and h.hexdigest()==row['sha256'],'complete file fragment hash/length')
 intent_raw=R.read(root,'intent.json');intent=json.loads(intent_raw);require(encode(intent)==intent_raw and intent=={k:v for k,v in index.items() if k not in {'pages','chunk_count','chunk_bytes','member_manifest_sha256','git_qualification','flat_qualification'}}|{'kind':'opaque-chunk-capture-intent'},'intent/index roots differ')
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
 """Same strict source index/member policy as archive, plus exact flat bodies."""
 bounds=Bounds();root=canonical_root(str(directory));raw=R.read(root,'index.json');_hash(index_hash);require(sha(raw)==index_hash,'flat complete index differs');index=_index(json.loads(raw),raw)
 members,rows,chunks=_members(index,_pages(root,index,bounds));rraw=R.read(root,'recovery.json');receipt=json.loads(rraw)
 required={'schema_version','status','source_index_sha256','mapping_pages','file_count','member_count','logical_bytes','member_manifest_sha256','roots','qualification'}
 require(type(receipt)is dict and set(receipt)==required and encode(receipt)==rraw and type(receipt['schema_version'])is int and receipt['schema_version']==1,'flat receipt fields/framing')
 require(receipt['status']=='complete-flat-byte-recovery' and receipt['source_index_sha256']==index_hash and receipt['roots']==index['roots'],'flat receipt ancestry')
 require(receipt['qualification']=='complete logical directory/mode manifest and Git bytes retained in this flat tree; no POSIX/Git object instantiation or scientific authority','flat qualification differs')
 for key in ('file_count','member_count','logical_bytes'):require(type(receipt[key])is int and receipt[key]==index[key],'flat complete denominator differs')
 require(receipt['member_manifest_sha256']==index['member_manifest_sha256'],'flat full member manifest differs')
 files=[r for r in rows if r['kind']=='file'];expected={'index.json','recovery.json'}|{p['name'] for p in index['pages']};mappings=[]
 require(type(receipt['mapping_pages'])is list and len(receipt['mapping_pages'])==(len(files)+PAGE-1)//PAGE,'flat mapping page denominator')
 for i,page in enumerate(receipt['mapping_pages']):
  _descriptor(page,'mapping-%05d.json'%i);raw=read_record(root,page);page_rows=json.loads(raw);require(type(page_rows)is list and len(page_rows)==min(PAGE,len(files)-len(mappings)) and encode(page_rows)==raw,'flat mapping framing');mappings.extend(page_rows);expected.add(page['name'])
 require(len(mappings)==len(files),'flat exact file denominator');total=0
 for i,(row,mapping) in enumerate(zip(files,mappings,strict=True)):
  bounds.check(root);filename='body-%08d.bin'%i;require(mapping=={'root':row['root'],'path':row['path'],'body':filename,'mode':row['mode'],'bytes':row['bytes'],'sha256':row['sha256']},'flat logical identity differs');raw=R.read(root,filename);require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'flat body hash/extent')
  offset=0
  for fragment in row['chunks']:
   part=raw[offset:offset+fragment['bytes']];require(len(part)==fragment['bytes'] and sha(part)==fragment['sha256'],'flat body chunk framing/hash differs');offset+=len(part)
  require(offset==len(raw),'flat body chunk denominator');total+=len(raw);expected.add(filename)
 require(total==index['logical_bytes'],'flat total differs');require(set(p.name for p in root.iterdir())==expected,'flat unexpected/missing body');return receipt
