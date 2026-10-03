"""Read-only original local byte members. Content evidence, never admission.

No Owner/Target/Binding/cold capability is made here. The eventual actual typed
caller supplies its independently trusted original terminal/manifest hash, and
must retain its own scientific and lease checks. No remote/missing fallback.
"""
import ast,hashlib,json,os,re,stat,struct
from contextlib import contextmanager
from pathlib import Path
from types import MappingProxyType
from owned_io import _cleanup
SCOPES=('graph','node_order','dictionary','ordered_motifs','matching','workflow')
META=8192;PART=1048576;ENTRIES=65536;MAX_BYTES=64*1024**3

def require(v,m):
 if not v:raise ValueError(m)
def sha(v):return type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None
def member_name(name):
 require(type(name) is str and name not in ('','.','..') and '/' not in name and '\\' not in name and '\0' not in name and len(name)<=128,'one original member name required');return name
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def parse(raw,*,compact=True):
 def pairs(items):
  d={}
  for k,v in items:require(k not in d,'duplicate metadata key');d[k]=v
  return d
 value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite metadata')))
 expected=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=compact,allow_nan=False).encode()+(b'\n' if compact else b'')
 require(expected==raw,'original canonical metadata required');return value
def integer(v,lo,hi):return type(v) is int and lo<=v<=hi
def scope(v):require(type(v) is dict and set(v)==set(SCOPES) and all(sha(x) for x in v.values()),'scientific scope fields differ')
def npy_header(raw,expected):
 require(raw[:6]==b'\x93NUMPY' and raw[6:8] in (b'\x01\x00',b'\x02\x00'),'supported original NPY header required')
 width=2 if raw[6]==1 else 4;start=8+width;require(len(raw)>=start,'short NPY header')
 length=int.from_bytes(raw[8:start],'little');end=start+length;require(0<length<=65536-start and len(raw)>=end,'NPY header bound differs')
 value=ast.literal_eval(raw[start:end].decode('latin1'));require(type(value) is dict and set(value)=={'descr','fortran_order','shape'} and value['fortran_order'] is False,'NPY order/header schema differs')
 dtype,shape=expected;require(value['descr']==dtype and type(value['shape']) is tuple and list(value['shape'])==list(shape) and all(type(n) is int and n>=0 for n in value['shape']),'NPY shape/dtype differs')
 count=1
 for n in shape:count*=n
 return end+count*(4 if dtype=='<f4' else 8)

class LocalContent:
 __slots__=('root','fd','kind','reference','closed','_root_sig','_files','_payload','_pin','_frozen')
 def __setattr__(self,name,value):
  if getattr(self,'_frozen',False):raise AttributeError('content snapshot cannot be rebound')
  object.__setattr__(self,name,value)
 def __delattr__(self,name):
  raise AttributeError('content snapshot attributes cannot be deleted')
 def __init__(self,root,fd,kind,reference):
  self.root=root;self.fd=fd;self.kind=kind;self.reference=reference;self.closed=False;self._root_sig=signature(os.fstat(fd));self._files={};self._payload={}
  require(stat.S_ISDIR(os.fstat(fd).st_mode),'source directory required');self._root()
  if kind=='score-batches':self._batches()
  elif kind=='mcm-output':self._output()
  elif kind=='graph-artifact':self._graph()
  else:raise ValueError('explicit local original format required')
  self._inventory();self._pin=tuple(sorted(self._files.items()));self._payload=MappingProxyType(self._payload);self._files=MappingProxyType(self._files);self._frozen=True
 def _root(self):
  require(not self.closed and self.root.resolve()==self.root,'closed or redirected reader')
  a=self.root.lstat();b=os.fstat(self.fd);require(stat.S_ISDIR(a.st_mode) and (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)==self._root_sig[:2],'original root inode changed')
 def _inventory(self):
  self._root();seen=set();iterator=os.scandir(self.fd)
  try:
   for entry in iterator:
    require(len(seen)<ENTRIES,'member inventory cap exceeded');member_name(entry.name)
    require(entry.name in self._files and entry.name not in seen,'unexpected original member');seen.add(entry.name)
  finally:_cleanup((iterator.close,))
  require(seen==set(self._files),'missing original member');self._root()
 def _read(self,name,limit,*,expected=None,extent=None,npy=None,capture=False):
  member_name(name);self._root();fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=self.fd)
  try:
   before=os.fstat(fd);sig=signature(before)
   require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<=limit and (extent is None or before.st_size==extent),'single-link member extent differs')
   require(sig==signature(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),'member path/FD differs')
   digest=hashlib.sha256();pieces=[];prefix=bytearray();count=0
   while True:
    block=os.read(fd,min(65536,limit-count+1))
    if not block:break
    count+=len(block);require(count<=limit,'member grew beyond bound');digest.update(block)
    if capture:pieces.append(block)
    if npy is not None and len(prefix)<65536:prefix.extend(block[:65536-len(prefix)])
   require(count==before.st_size and signature(os.fstat(fd))==signature(os.stat(name,dir_fd=self.fd,follow_symlinks=False))==sig,'member changed while reading')
   actual=digest.hexdigest();require(expected is None or actual==expected,'original member SHA differs')
   if npy is not None:require(npy_header(prefix,npy)==count,'NPY body extent differs')
   self._root();return (sig,actual,count,npy),b''.join(pieces) if capture else None
  finally:_cleanup((lambda:os.close(fd),))
 def _doc(self,name,expected=None,limit=META):
  record,raw=self._read(name,limit,expected=expected,capture=True);self._files[name]=record;return parse(raw,compact=self.kind!='graph-artifact'),record[1]
 def _member(self,name,size,digest,npy=None):
  require(integer(size,0,MAX_BYTES) and sha(digest),'member descriptor differs')
  record,_=self._read(name,size,expected=digest,extent=size,npy=npy);self._files[name]=record;self._payload[name]=(size,digest,npy)
 def _batches(self):
  terminal,_=self._doc('terminal.json',self.reference);start,head=self._doc('start.json')
  require(set(start)=={'schema_version','scope','owner','rows','motifs','chunk_cells','dtype','order'} and type(start['schema_version']) is int and start['schema_version']==1,'batch start schema differs')
  scope(start['scope']);require(sha(start['owner']) and integer(start['rows'],1,2**40) and start['motifs']==32 and type(start['motifs']) is int and integer(start['chunk_cells'],1,1048576) and start['dtype']=='<f8' and start['order']=='row-major','batch semantics differ')
  cells=start['rows']*32;chunks=(cells+start['chunk_cells']-1)//start['chunk_cells'];require(2+2*chunks<=ENTRIES,'batch inventory bound')
  require(set(terminal)=={'schema_version','start_sha256','head','status','cells','chunks','reason','pending'} and type(terminal['schema_version']) is int and terminal['schema_version']==1 and terminal['start_sha256']==head and terminal['status']=='complete' and type(terminal['cells']) is int and terminal['cells']==cells and type(terminal['chunks']) is int and terminal['chunks']==chunks and terminal['reason']=='' and terminal['pending']==[],'complete original batch terminal required')
  initial=head
  for index in range(chunks):
   name=f'chunk-{index:012d}';offset=index*start['chunk_cells'];count=min(start['chunk_cells'],cells-offset)
   header,h=self._doc(name+'.json')
   require(set(header)=={'schema_version','start_sha256','previous','index','start_cell','cells','payload_sha256'} and all(type(header[k]) is int for k in ('schema_version','index','start_cell','cells')) and header=={'schema_version':1,'start_sha256':initial,'previous':head,'index':index,'start_cell':offset,'cells':count,'payload_sha256':header['payload_sha256']} and sha(header['payload_sha256']),'batch chain/order differs')
   self._member(name+'.bin',8*count,header['payload_sha256']);head=h
  require(head==terminal['head'],'batch terminal head differs')
 def _output(self):
  value,_=self._doc('manifest.json',self.reference)
  fields={'schema_version','kind','stage_sha256','contract_sha256','stage_directory','scope','owner','rows','motifs','dtype','order','array_bytes','array_sha256','execution_admitted'}
  require(set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='compact-mcm-output' and all(sha(value[k]) for k in ('stage_sha256','contract_sha256','owner')),'output original schema differs')
  scope(value['scope']);require(type(value['stage_directory']) is str and Path(value['stage_directory']).is_absolute() and integer(value['rows'],1,2**40) and type(value['motifs']) is int and value['motifs']==32 and value['dtype']=='<f4' and value['order']=='row-major' and value['execution_admitted'] is False and type(value['array_bytes']) is int and value['array_bytes']==4*value['rows']*32,'output original dimensions differ')
  self._member('matrix.f32',value['array_bytes'],value['array_sha256'])
 def _graph(self):
  value,_=self._doc('manifest.json',self.reference,4*1024**2)
  require(set(value)=={'schema_version','context','tree','arrays'} and type(value['schema_version']) is int and value['schema_version']==1 and type(value['context']) is dict,'component schema differs')
  def scalar(v):return {'kind':'scalar','value':v}
  tree={'kind':'dict','items':[[scalar('feature'),{'kind':'dict','items':[[scalar('mcm'),{'kind':'array','member':'array-000000.npy'}],[scalar('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[scalar('aligned_vectors'),scalar(None)]]}
  require(value['tree']==tree and set(value['arrays'])=={'array-000000.npy','array-000001.npy'},'original graph membership/tree differs')
  for name,dtype in [('array-000000.npy','float32'),('array-000001.npy','int64')]:
   d=value['arrays'][name];require(set(d)=={'sha256','bytes','shape','dtype'} and d['dtype']==dtype and type(d['shape']) is list and len(d['shape'])==2 and all(integer(n,0,2**40) for n in d['shape']),'component descriptor differs')
   require((d['shape'][0]>0 and d['shape'][1]==32) if dtype=='float32' else d['shape'][0]==2,'graph full shape differs')
   self._member(name,d['bytes'],d['sha256'],('<f4' if dtype=='float32' else '<i8',tuple(d['shape'])))
 @property
 def members(self):return tuple(self._payload)
 def check(self):
  self._inventory()
  for name,prior in self._pin:
   record,_=self._read(name,prior[2],expected=prior[1],extent=prior[2],npy=prior[3]);require(record==prior,'original member identity changed')
  self._inventory()
 def read_part(self,name,offset,count):
  require(name in self._payload and integer(offset,0,MAX_BYTES) and integer(count,1,PART) and offset+count<=self._payload[name][0],'exact original payload range required')
  self._inventory();self._root();fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=self.fd)
  try:
   require(signature(os.fstat(fd))==self._files[name][0]==signature(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),'payload replaced before range read')
   parts=[];seen=0
   while seen<count:
    b=os.pread(fd,count-seen,offset+seen);require(bool(b),'short member range');parts.append(b);seen+=len(b)
   require(signature(os.fstat(fd))==self._files[name][0]==signature(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),'payload mutated during range read');self._root();return b''.join(parts)
  finally:_cleanup((lambda:os.close(fd),))

@contextmanager
def open_local(root,*,kind,document_sha256):
 require(sha(document_sha256),'independently pinned original document SHA required');root=Path(root)
 require(root.is_absolute() and root.resolve()==root,'canonical original directory required')
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);reader=None
 try:
  reader=LocalContent(root,fd,kind,document_sha256)
  yield reader
  reader.check()
 finally:
  if reader is not None:object.__setattr__(reader,'closed',True)
  _cleanup((lambda:os.close(fd),))
