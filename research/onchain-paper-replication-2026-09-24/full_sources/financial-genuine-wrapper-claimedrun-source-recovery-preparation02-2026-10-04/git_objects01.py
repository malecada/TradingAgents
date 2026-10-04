"""Finite recovered loose-object commit ancestry/tree/blob authentication."""
import hashlib,re,time,zlib

def require(v,m):
 if not v:raise ValueError(m)

class RecoveredGit:
 def __init__(self,raw,paths,limit=4*1024**2):
  self.raw=raw;self.paths=paths;self.limit=limit;self.objects={};self.commits={};self.state={};self.total=0;self.tree_visits=0;self.tree_entries=0;self.start=time.monotonic()
  require(not any(n in paths for n in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow')) and not any(n.startswith(('.git/objects/pack/','.git/refs/replace/')) for n in paths),'self-contained loose Git scope')
 def obj(self,oid,kind):
  require(time.monotonic()-self.start<120,'Git verification deadline');require(type(oid)is str and re.fullmatch('[0-9a-f]{40}',oid) is not None,'object identity')
  if oid in self.objects:
   k,b=self.objects[oid];require(k==kind,'cached object type');return b
  require(len(self.objects)<4096,'finite object count');name='.git/objects/'+oid[:2]+'/'+oid[2:];require(name in self.paths,'missing original object');compressed=self.raw(name);require(len(compressed)<=self.limit,'compressed bound');d=zlib.decompressobj();body=d.decompress(compressed,self.limit+129)
  require(d.eof and not d.unused_data and not d.unconsumed_tail and len(body)<=self.limit+128,'object inflate/framing');head,sep,value=body.partition(b'\0');require(sep and head==kind.encode()+b' '+str(len(value)).encode() and len(value)<=self.limit and hashlib.sha1(body).hexdigest()==oid,'Git object type/hash')
  self.total+=len(value);require(self.total<=64*1024**2,'aggregate object bound');self.objects[oid]=(kind,value);return value
 def tree(self,oid,prefix='',depth=0,active=None):
  self.tree_visits+=1;require(self.tree_visits<=32768,'aggregate tree visits');require(depth<=32,'tree depth');active=set() if active is None else active;require(oid not in active,'tree cycle');active=active|{oid};body=self.obj(oid,'tree');at=0;names=set();last=None;result={}
  while at<len(body):
   self.tree_entries+=1;require(self.tree_entries<=65536,'aggregate tree entries');space=body.index(b' ',at);end=body.index(b'\0',space);mode=body[at:space].decode('ascii');namebytes=body[space+1:end];name=namebytes.decode('utf-8');require(name not in ('','.','..') and '/' not in name and name not in names,'tree path');names.add(name)
   require(mode in ('40000','100644','100755'),'canonical regular/directory mode');key=namebytes+(b'/' if mode=='40000' else b'\0');require(last is None or last<key,'canonical Git tree order');last=key
   require(end+21<=len(body),'tree oid framing');child=body[end+1:end+21].hex();at=end+21;path=prefix+name
   if mode=='40000':result.update(self.tree(child,path+'/',depth+1,active))
   else:self.obj(child,'blob');result[path]=(mode,child)
   require(len(result)<=32768,'finite tree population')
  return result
 def ancestry(self,oid,depth=0):
  require(depth<=128 and len(self.state)<=1024,'finite ancestry');require(self.state.get(oid)!=1,'commit cycle')
  if self.state.get(oid)==2:return self.commits[oid]
  self.state[oid]=1;value=self.obj(oid,'commit');headers,sep,message=value.partition(b'\n\n');require(sep,'commit header boundary');lines=headers.split(b'\n');require(lines[0].startswith(b'tree ') and len(lines[0])==45,'commit first tree');tree=lines[0][5:].decode('ascii');parents=[];other=False
  for line in lines[1:]:
   if line.startswith(b'parent '):
    require(not other and len(line)==47,'canonical parent header');parent=line[7:].decode('ascii');require(parent not in parents,'duplicate parent');parents.append(parent)
   else:other=True;require(not line.startswith(b'tree '),'duplicate tree header')
  entries=self.tree(tree)
  for parent in parents:self.ancestry(parent,depth+1)
  self.commits[oid]={'tree':tree,'parents':parents,'entries':entries};self.state[oid]=2;return self.commits[oid]

def tree_join(raw,paths,commit,expected_count,limit=4*1024**2,manifest_modes=None):
 repo=RecoveredGit(raw,paths,limit);current=repo.ancestry(commit);entries=current['entries'];require(len(entries)==expected_count,'complete tracked denominator')
 for path,(mode,oid) in entries.items():
  require(path in paths and raw(path)==repo.obj(oid,'blob'),'recovered committed body')
  if manifest_modes is not None:require(path in manifest_modes and bool(manifest_modes[path]&0o111)==(mode=='100755'),'manifest versus Git executable mode')
 return repo,entries

def claim_join(repo,claim):
 source=claim['source'];design=claim['design_source'];require(source in repo.commits and design in repo.commits,'original claim source/design outside recovered ancestry');require(source==design and claim['bindings'] is None and claim['bindings_sha256'] is None,'original fixed no-binding claim')
 entries=repo.commits[source]['entries'];regpath=claim['registration'];require(regpath in entries,'historical registration absent');raw=repo.obj(entries[regpath][1],'blob');require(hashlib.sha256(raw).hexdigest()==claim['registration_sha256'],'original registration hash')
 import json
 reg=json.loads(raw);exp=reg['experiments'][claim['experiment_id']];require(exp==claim['experiment'] and reg['program_id']==claim['program_id'] and reg['families'][exp['family']]==claim['family'],'genuine claimed registration definition')
 pins=exp['source_files'];require(len(entries)==325 and len(pins)==324 and set(pins)|{regpath}==set(entries),'original325/324 source closure')
 for path,pin in pins.items():require(hashlib.sha256(repo.obj(entries[path][1],'blob')).hexdigest()==pin,'original claimed source body')
 require(claim['inputs']==exp['inputs'] and len(claim['inputs'])==8,'original actual input role mapping')
 for ref in claim['inputs'].values():require(hashlib.sha256(repo.obj(entries[ref['path']][1],'blob')).hexdigest()==ref['sha256'],'original claimed input bytes')
 require(claim['effective_attempt_budget']==18,'historical highest18 preserved');return {'source':source,'design_source':design,'tracked':325,'pins':324,'inputs':8,'budget':18}
