from pathlib import Path
import ast,json,hashlib
D=Path(__file__).resolve().parent;p=D/'chunk_archive01.py';s=p.read_text();baseline=s;edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1;s=s.replace(old,new);edits.append({'old':old,'new':new})
a=s.index('def fresh(');b=s.index('def read_record(',a)
replace(s[a:b],'''def fresh(parent,target):
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
''')
a=s.index('def validate_archive(');b=s.index('def restore(',a)
replace(s[a:b],'''def _hash(value):require(type(value)is str and len(value)==64 and all(c in '0123456789abcdef' for c in value),'SHA256 descriptor required')
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

''')
a=s.index('def verify_flat(')
replace(s[a:],'''def verify_flat(directory,index_hash):
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
  bounds.check(root);filename='body-%08d.bin'%i;require(mapping=={'root':row['root'],'path':row['path'],'body':filename,'mode':row['mode'],'bytes':row['bytes'],'sha256':row['sha256']},'flat logical identity differs');raw=R.read(root,filename);require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'flat body hash/extent');total+=len(raw);expected.add(filename)
 require(total==index['logical_bytes'],'flat total differs');require(set(p.name for p in root.iterdir())==expected,'flat unexpected/missing body');return receipt
''')
p.write_text(s);ast.parse(s);back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==baseline
(D/'INVERSE02.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(baseline.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'edits':edits,'full_byte_inverse':True,'full_ast_inverse':ast.dump(ast.parse(back))==ast.dump(ast.parse(baseline))},indent=2)+'\n')
