"""Bounded immutable loose Git object view over recovered flat bodies."""
import hashlib,re,zlib

def tree_join(raw,paths,commit,expected_count,limit=4*1024**2):
 def require(v,m):
  if not v:raise ValueError(m)
 require(re.fullmatch('[0-9a-f]{40}',commit) is not None,'commit identity')
 require(not any(n in paths for n in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow')) and not any(n.startswith(('.git/objects/pack/','.git/refs/replace/')) for n in paths),'self-contained loose Git scope')
 def obj(oid,kind):
  require(re.fullmatch('[0-9a-f]{40}',oid) is not None,'object identity');name='.git/objects/'+oid[:2]+'/'+oid[2:];require(name in paths,'missing original object');compressed=raw(name);require(len(compressed)<=limit,'compressed bound');d=zlib.decompressobj();body=d.decompress(compressed,limit+129);require(d.eof and not d.unused_data and not d.unconsumed_tail and len(body)<=limit+128,'object inflate/framing');head,sep,value=body.partition(b'\0');require(sep and head==kind.encode()+b' '+str(len(value)).encode() and len(value)<=limit and hashlib.sha1(body).hexdigest()==oid,'Git object type/hash');return value
 c=obj(commit,'commit');line=c.split(b'\n',1)[0];require(line.startswith(b'tree ') and len(line)==45,'commit tree');tree=line[5:].decode();result={};visited=0
 def walk(oid,prefix,depth):
  nonlocal visited
  require(depth<=32,'tree depth');visited+=1;require(visited<=32768,'tree count');body=obj(oid,'tree');at=0;names=set()
  while at<len(body):
   space=body.index(b' ',at);end=body.index(b'\0',space);mode=body[at:space].decode();name=body[space+1:end].decode('utf-8');require(name not in ('','.','..') and '/' not in name and name not in names,'tree path');names.add(name);require(end+21<=len(body),'tree oid framing');child=body[end+1:end+21].hex();at=end+21;path=prefix+name
   if mode=='40000':walk(child,path+'/',depth+1)
   else:
    require(mode in ('100644','100755') and path not in result and len(result)<expected_count,'tracked type/count');b=obj(child,'blob');require(raw(path)==b,'recovered committed body');result[path]=(mode,child)
 walk(tree,'',0);require(len(result)==expected_count,'complete tracked denominator');return result
