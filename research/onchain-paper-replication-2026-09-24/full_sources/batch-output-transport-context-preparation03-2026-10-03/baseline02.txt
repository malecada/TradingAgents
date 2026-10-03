"""Unadmitted local non-tail transport preparation, no subprocess/network/delete.

Local content is evidence of bytes, never a ResearchRun/Owner/transport capability.
Reservation counters are local engineering proposal counters, not research spend.
"""
import hashlib,importlib.util,json,sys,time,os,stat
from threading import current_thread
from contextlib import contextmanager
from pathlib import Path
from types import MappingProxyType
D=Path(__file__).resolve().parent.parent/'batch-output-exact-member-reader-candidate02-2026-10-03'
PINS={'owned_io':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','exact_members02':'ea1ffcef833344ff1a5fbd89bc2f79ade1414c90a3159329c1f3bdee86bfe0cb'}
def require(v,m):
 if not v:raise ValueError(m)
class BootstrapCleanupFailure(BaseException):pass

def bootstrap_read(path):
 """Bound before read; original descriptor/path and first fatal survive close."""
 require(type(path) is Path or isinstance(path,Path),'dependency path required')
 require(path.resolve()==path,'canonical dependency path required')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
 primary=None;result=None
 try:
  before=os.fstat(fd)
  signature=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=1048576,'bounded regular dependency required')
  require(signature(before)==signature(path.lstat()),'dependency path/FD differs')
  parts=[];count=0
  while count<=before.st_size:
   block=os.read(fd,min(65536,before.st_size-count+1))
   if not block:break
   count+=len(block);require(count<=before.st_size,'dependency grew');parts.append(block)
  require(count==before.st_size and signature(before)==signature(os.fstat(fd))==signature(path.lstat()),'dependency changed')
  result=b''.join(parts)
 except BaseException as error:primary=error
 try:os.close(fd)
 except BaseException as later:
  primary_fatal=primary is not None and (isinstance(primary,MemoryError) or not isinstance(primary,Exception))
  later_fatal=isinstance(later,MemoryError) or not isinstance(later,Exception)
  if not primary_fatal:primary=later if later_fatal else BootstrapCleanupFailure('dependency close uncertain; no retry')
 if primary is not None:raise primary
 return result

def load(name):
 p=D/(name+'.py');b=bootstrap_read(p);require(hashlib.sha256(b).hexdigest()==PINS[name],'accepted local dependency differs')
 if name in sys.modules:
  m=sys.modules[name];require(Path(m.__file__).resolve()==p.resolve(),'dependency alias differs');return m
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 try:exec(compile(b,str(p),'exec'),m.__dict__)
 except BaseException:
  del sys.modules[name];raise
 return m
io=load('owned_io');reader=load('exact_members02')
BLOCK=32768;MAX_MEMBERS=4096
class CleanupFailure(BaseException):pass
def fatal(e):return isinstance(e,MemoryError) or (not isinstance(e,Exception) and not isinstance(e,(CleanupFailure,io.CleanupFailure)))
def select(first,later):
 if first is None:return later
 if fatal(first):return first
 if fatal(later):return later
 if isinstance(later,(CleanupFailure,io.CleanupFailure)):return later
 return first
def finish(actions,primary=None):
 selected=primary;uncertain=False
 for action in actions:
  try:action()
  except BaseException as error:selected=select(selected,error);uncertain=True
 if uncertain and not fatal(selected) and not isinstance(selected,(CleanupFailure,io.CleanupFailure)):selected=CleanupFailure('local cleanup uncertain')
 if selected is not None:raise selected
class Frozen:
 __slots__=()
 def __setattr__(self,n,v):raise AttributeError('immutable local context')
 def __delattr__(self,n):raise AttributeError('immutable local context')
class Reservations(Frozen):
 __slots__=('_policy','_spent','_start','_revoked','_thread','_reserving')
 def __init__(self,value):
  fields={'max_rounded_bytes','max_commands','max_parts','part_bytes','deadline_seconds'}
  require(type(value) is dict and set(value)==fields,'exact finite local reservation policy')
  require(all(type(v) is int and v>0 for v in value.values()),'positive strict integer limits')
  require(value['max_rounded_bytes']<=2**40 and value['max_commands']<=131072 and value['max_parts']<=65536 and value['part_bytes']<=1048576 and value['deadline_seconds']<=1800,'local preparation ceilings exceeded')
  object.__setattr__(self,'_policy',MappingProxyType(dict(value)));object.__setattr__(self,'_spent',(0,0,0));object.__setattr__(self,'_start',time.monotonic());object.__setattr__(self,'_revoked',False);object.__setattr__(self,'_thread',current_thread());object.__setattr__(self,'_reserving',False)
 @property
 def policy(self):return self._policy
 @property
 def spent(self):return MappingProxyType(dict(zip(('rounded_bytes','commands','parts'),self._spent)))
 @property
 def revoked(self):return self._revoked
 def revoke(self):object.__setattr__(self,'_revoked',True)
 def check(self):
  require(current_thread() is self._thread,'reservation context thread differs')
  require(not self.revoked,'reservation context revoked')
  if time.monotonic()-self._start>=self.policy['deadline_seconds']:self.revoke();raise TimeoutError('whole local preparation deadline')
 def reserve(self,size):
  entered=False
  try:
   self.check();require(not self._reserving,'reentrant reservation refused')
   object.__setattr__(self,'_reserving',True);entered=True
   require(type(size) is int and 0<size<=1048576,'finite positive part bytes')
   b,c,p=self._spent
   # Conservative actual archive_transport.get bound includes an extra block
   # at exact multiples; proposal only, not SSH framing or wire metering.
   new=(b+(size//BLOCK+1)*BLOCK,c+1,p+1)
   require(new[0]<=self.policy['max_rounded_bytes'] and new[1]<=self.policy['max_commands'] and new[2]<=self.policy['max_parts'],'cumulative reservation exhausted')
   self.check();object.__setattr__(self,'_spent',new);return self.spent
  except BaseException:self.revoke();raise
  finally:
   if entered:object.__setattr__(self,'_reserving',False)

class Context(Frozen):
 __slots__=('_reader','_budget','_inventory','_members','_metadata','_position','_recovered','_revoked')
 def __init__(self,content,limits):
  if type(content) is not reader.LocalContent:raise TypeError('actual accepted LocalContent required; not Owner authority')
  content.check();require(len(content._pin)<=MAX_MEMBERS,'complete container exceeds local member ceiling')
  object.__setattr__(self,'_reader',content);object.__setattr__(self,'_budget',limits if type(limits) is Reservations else Reservations(limits));object.__setattr__(self,'_revoked',False)
  inventory=tuple((n,p[1],p[2],p[3]) for n,p in content._pin)
  object.__setattr__(self,'_inventory',inventory);object.__setattr__(self,'_members',tuple(n for n,p in content._pin));object.__setattr__(self,'_position',(0,0));object.__setattr__(self,'_recovered',False)
  # Capture original metadata only; all fields derive from verified on-disk members.
  require(sum(p[2] for n,p in content._pin if n.endswith('.json'))<=4194304,'complete metadata extent exceeds preparation bound')
  docs=[]
  for n,p in content._pin:
   if n.endswith('.json'):
    _,raw=content._read(n,p[2],expected=p[1],extent=p[2],capture=True)
    docs.append((n,raw))
  require(sum(len(b) for _,b in docs)<=4194304,'complete metadata extent exceeds preparation bound')
  object.__setattr__(self,'_metadata',tuple(docs));self.check()
 @property
 def policy(self):return self._budget.policy
 @property
 def spent(self):return self._budget.spent
 @property
 def revoked(self):return self._revoked or self._budget.revoked
 @property
 def members(self):return self._members
 @property
 def inventory(self):return self._inventory
 def revoke(self):object.__setattr__(self,'_revoked',True);self._budget.revoke()
 def check(self):
  try:
   require(not self.revoked,'local content context revoked');self._budget.check();self._reader.check()
   require(tuple((n,p[1],p[2],p[3]) for n,p in self._reader._pin)==self.inventory,'original complete inventory changed')
  except BaseException:self.revoke();raise
 def description(self):
  self.check()
  return {'kind':'unadmitted-original-content-context-v1','container_kind':self._reader.kind,'container_sha256':self._reader.reference,'original_root':str(self._reader.root),'original_metadata_sha256':[(n,hashlib.sha256(b).hexdigest()) for n,b in self._metadata],'members':[{'path':n,'sha256':h,'bytes':b,'npy':s} for n,h,b,s in self.inventory],'source_pins':dict(PINS),'ancestry_qualification':'original metadata retained exactly; owner/stage fields are content, not verified live authority','execution_admitted':False,'transport_authority':False}
 def _part(self,content,name,offset,count):
  if name in content.members:return content.read_part(name,offset,count)
  prior=content._files[name];_,raw=content._read(name,prior[2],expected=prior[1],extent=prior[2],capture=True)
  return raw[offset:offset+count]
 def ranges(self,name):
  reader.member_name(name);require(name in self.members,'original payload only');size=self._reader._files[name][2]
  require((size+self.policy['part_bytes']-1)//self.policy['part_bytes']<=self.policy['max_parts'],'member part denominator exceeds policy')
  return ((i,min(self.policy['part_bytes'],size-i)) for i in range(0,size,self.policy['part_bytes']))
 def read_original(self,name,offset,count):
  try:
   self.check();reader.member_name(name);index,position=self._position
   require(index<len(self.members) and name==self.members[index] and offset==position,'exact original member order required')
   size=self._reader._files[name][2];require(type(count) is int and count==min(self.policy['part_bytes'],size-position),'exact original part denominator')
   self._budget.reserve(count);raw=self._part(self._reader,name,offset,count);self.check()
   position+=count;object.__setattr__(self,'_position',(index+1,0) if position==size else (index,position));return raw
  except BaseException:self.revoke();raise
 def verify_recovery(self,root):
  """Local complete-copy byte proof only, not a remote or disposal receipt."""
  try:
   self.check();require(not self._recovered and self._position==(len(self.members),0),'complete original stream required once before recovery')
   root=Path(root);require(root!=self._reader.root and root.resolve()!=self._reader.root,'distinct retained recovery root required')
   with reader.open_local(root,kind=self._reader.kind,document_sha256=self._reader.reference) as recovered:
    actual=tuple((n,p[1],p[2],p[3]) for n,p in recovered._pin);require(actual==self.inventory,'complete original membership/hash/header differs')
    for name in self.members:
     expected=self._reader._files[name][1];h=hashlib.sha256()
     for offset,count in self.ranges(name):
      self.check();self._budget.reserve(count);h.update(self._part(recovered,name,offset,count));self.check()
     require(h.hexdigest()==expected,'whole recovered member hash differs')
    recovered.check();self.check()
   self.check();object.__setattr__(self,'_recovered',True)
   return {'kind':'unadmitted-complete-local-recovery-observation','container_sha256':self._reader.reference,'complete_original_members':len(self.inventory),'spent':dict(self.spent),'recovery_authority':False,'remote_verified':False,'local_bytes_retired':0}
  except BaseException:self.revoke();raise
 def activate_transport(self,*args,**kwargs):
  self.check()
  raise NotImplementedError('non-tail population absent from genuine archive_dispatch preflight/Context and typed Ledger; actual registered held/cold authority and durable no-refund original Context required')
@contextmanager
def open_context(root,*,kind,document_sha256,limits):
 cm=reader.open_local(root,kind=kind,document_sha256=document_sha256)
 shared=limits if type(limits) is Reservations else None
 c=None;primary=None;entered=False
 try:
  content=cm.__enter__();entered=True
  c=Context(content,limits);yield c;c.check()
 except BaseException as error:
  primary=error
  if shared is not None:shared.revoke()
 def close():
  if not entered:return
  try:cm.__exit__(type(primary) if primary is not None else None,primary,primary.__traceback__ if primary is not None else None)
  except BaseException as error:
   if shared is not None:shared.revoke()
   if c is not None:c.revoke()
   if error is not primary:raise
 actions=[close]
 if c is not None:actions.append(c.revoke if primary is not None else lambda:object.__setattr__(c,'_revoked',True))
 finish(actions,primary)
