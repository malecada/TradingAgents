"""Pure deterministic greedy full-body partition; no IO or authority."""
import tarfile
LOGICAL=2*1024**2
MEMBERS=256
ARCHIVE=4*1024**2

def require(v,m):
 if not v:raise ValueError(m)

def tar_bound(rows):
 total=0
 for r in rows:
  t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0;t.size=r['bytes'] if r['kind']=='file' else 0
  if r['kind']=='directory':t.type=tarfile.DIRTYPE
  header=t.tobuf(format=tarfile.PAX_FORMAT,encoding='utf-8',errors='strict')
  if header[156:157]==b'x':require(int(header[124:136].strip(b'\0 '),8)<=8192,'bounded original PAX record')
  total+=len(header)+((t.size+511)//512)*512
 # tarfile closes with two zero blocks and pads to RECORDSIZE=10240.
 return ((total+1024+10239)//10240)*10240

def gzip_bound(n):return n+(n>>12)+(n>>14)+(n>>25)+64

def partition(m):
 rows=m['members'];by={r['path']:r for r in rows};require(len(by)==len(rows),'duplicate virtual path');files=sorted(r['path'] for r in rows if r['kind']=='file');require(files,'nonempty body union');groups=[];current=[]
 def group(names):
  paths=set(names)
  for name in names:
   pieces=name.split('/')
   for i in range(1,len(pieces)):
    parent='/'.join(pieces[:i]);require(parent in by and by[parent]['kind']=='directory','virtual parent');paths.add(parent)
  members=[by[n] for n in sorted(paths)];logical=sum(by[n]['bytes'] for n in names);bound=tar_bound(members)
  return {'regular_paths':list(names),'manifest':{'schema_version':m['schema_version'],'root_mode':m['root_mode'],'members':members},'members':len(members),'regular_bodies':len(names),'logical_bytes':logical,'tar_bytes_bound':bound}
 def fits(g):return g['logical_bytes']<=LOGICAL and g['members']<=MEMBERS and gzip_bound(g['tar_bytes_bound'])<=ARCHIVE
 for name in files:
  trial=group(current+[name])
  if not fits(trial):
   require(current,'single body/parent/PAX bound unavailable');groups.append(group(current));current=[name];require(fits(group(current)),'single body/parent/PAX bound unavailable')
  else:current.append(name)
 if current:groups.append(group(current))
 require([n for g in groups for n in g['regular_paths']]==files,'complete sorted disjoint body cover');return groups
