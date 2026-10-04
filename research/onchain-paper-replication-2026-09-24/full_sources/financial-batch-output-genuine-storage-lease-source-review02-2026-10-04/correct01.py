import ast,difflib,hashlib,importlib.util,json,os,stat,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import storage_lease01 as N
spec=importlib.util.spec_from_file_location('original_lease',H/'storage_lease01.original.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
checks=[];witnesses=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refusal(f,n):
 try:f()
 except BaseException as e:checks.append(n+':'+type(e).__name__);return e
 raise AssertionError(n)
def fresh(name,L,callback):
 root=H/name;root.mkdir(mode=0o700);roles={r:r for r in L.ROLES}
 for p in roles.values():(root/p).mkdir(mode=0o700)
 return root,L.OwnedLease(root,'lease',roles,64*L.MIB,64*L.MIB,callback)
# Exact frozen SL1 mechanism, same two actual callback invocations.
for label,L in [('old',O),('new',N)]:
 state={'armed':False,'calls':0};slot={}
 def callback():
  if state['armed']:
   state['calls']+=1
   if state['calls']==2:(slot['root']/'diagnostic/unreserved').write_bytes(b'actual callback addition')
 root,x=fresh(label+'-late-callback',L,callback);slot['root']=root;state['armed']=True;fds=(x.fd,x.ledger_fd)
 if label=='old':
  sample=x.check();ok(not x.failed and (root/'diagnostic/unreserved').exists(),'SL1 exact old RED first check accepted');refusal(x.check,'SL1 old nextcheck refusal')
 else:
  e=refusal(x.check,'SL1 successor GREEN same first check');ok(x.failed and x.fd is None and x.ledger_fd is None,'SL1 failure all descriptors closed');sample=None
 ok(state['calls']==2 if label=='new' else state['calls']>=2,'actual callback sequence '+label)
 witnesses.append({'id':'SL1','version':label,'first_returned_sample':sample,'unreserved_retained':(root/'diagnostic/unreserved').exists(),'failed':x.failed})
# Exact frozen SL2 later real descriptor-close mutation with explicit mtime.
for label,L in [('old',O),('new',N)]:
 root=H/(label+'-late-close');root.mkdir(mode=0o700);roles={r:r for r in L.ROLES}
 for p in roles.values():(root/p).mkdir(mode=0o700)
 a=root/'diagnostic/a';z=root/'diagnostic/z';a.write_bytes(b'original');z.write_bytes(b'last')
 x=L.OwnedLease(root,'lease',roles,64*L.MIB,64*L.MIB,lambda:None);before=a.stat();target=z.stat();realclose=os.close;events=[]
 def close(fd):
  s=os.fstat(fd);match=(s.st_dev,s.st_ino)==(target.st_dev,target.st_ino);realclose(fd)
  if match and not events:
   events.append(fd);a.write_bytes(b'changed!');os.utime(a,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
 os.close=close
 try:
  if label=='old':sample=x.check();ok(not x.failed,'SL2 exact old RED first check accepted')
  else:e=refusal(x.check,'SL2 successor GREEN same first check');sample=None
 finally:os.close=realclose
 if label=='old':refusal(x.check,'SL2 old nextcheck refusal')
 ok(bool(events) and a.read_bytes()==b'changed!','SL2 actual later close and retained earlier change '+label)
 ok(x.failed and x.fd is None and x.ledger_fd is None,'SL2 terminal resources '+label)
 witnesses.append({'id':'SL2','version':label,'first_returned_sample':sample,'actual_closed_fd':events,'original_signature':L.sig(before),'current_signature':L.sig(a.stat())})
# Trailing callback may lawfully materialize reserved bytes. Return final actual
# counters, not the earlier pre-callback sample.
state={'armed':False,'calls':0};slot={}
def callback():
 if state['armed']:
  state['calls']+=1
  if state['calls']==2:(slot['root']/'codec/promised').write_bytes(b'opaque')
r,x=fresh('final-current-result',N,callback);slot['root']=r;x.reserve('codec',[('codec/promised','file',6)]);state['armed']=True
s=x.check();state['armed']=False
actual=[r]+list(r.rglob('*'));ok(s['logical_bytes']==sum(p.lstat().st_size for p in actual),'returned final logical measurement');ok(s['allocated_bytes']==sum(p.lstat().st_blocks*512 for p in actual),'returned final allocated measurement');x.close()
# Resource query itself is IO; mutation before its return must precede finaljoin.
r,x=fresh('resource-io',N,lambda:None);real=N.os.fstatvfs;events=[]
def changed(fd):
 v=real(fd)
 if not events:events.append(fd);(r/'diagnostic/new').write_bytes(b'late statvfs')
 return v
try:
 N.os.fstatvfs=changed;refusal(x.check,'resource IO followed by finaljoin')
finally:N.os.fstatvfs=real
ok(x.failed and x.fd is None,'resource IO mutation terminal')
# Explicit floor refusal remains whole committed-headroom, no refund.
r,x=fresh('floor',N,lambda:None);reserved=(x.logical_reserved,x.allocated_reserved);real=N.os.fstatvfs
class V:f_bavail=N.FLOOR;f_frsize=1
try:
 N.os.fstatvfs=lambda fd:V();refusal(x.check,'actual floor predicate injected bound')
finally:N.os.fstatvfs=real
ok((x.logical_reserved,x.allocated_reserved)==reserved and x.failed,'floor no refund')
# Genuine finaljoin resource accounting remains bounded. Tiny scaled allocation
# injection is not an actual64MiB/whole-fit outcome.
r,x=fresh('allocated',N,lambda:None);snapshot=x._sample();real=N.census
try:
 def allocated(*a,**k):
  rows=real(*a,**k);rows['']['allocated']=x.allocated_reserved+1;return rows
 N.census=allocated;refusal(x.check,'allocated over reservation refusal')
finally:N.census=real
ok(x.failed and x.fd is None,'allocated refusal cleanup')
# The final rejoin creates no new descriptor/iterator/callback/cleanup gap.
tree=ast.parse((H/'storage_lease01.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_rejoin')
for forbidden in ('open','scandir','close','_cleanup','_callback','_boundary','census'):
 ok(not any(isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id==forbidden) or (isinstance(n.func,ast.Attribute) and n.func.attr==forbidden)) for n in ast.walk(f)),'descriptor-free bounded rejoin excludes '+forbidden)
# First fatal and actual closure remain after final fingerprint refusal.
for i,error in enumerate((KeyboardInterrupt(),MemoryError(),SystemExit(3),ValueError('ordinary'))):
 r,x=fresh('fatal-'+str(i),N,lambda:None);rejoin=N._rejoin;close=N.os.close;fds=(x.fd,x.ledger_fd);seen=[]
 def fail(*a,**k):raise error
 def closing(fd):
  close(fd)
  if fd in fds:seen.append(fd)
 try:
  N._rejoin=fail;N.os.close=closing;e=refusal(x.check,'finaljoin failure '+str(i))
 finally:N._rejoin=rejoin;N.os.close=close
 ok(e is error and set(seen)==set(fds),'original primary/all cleanup '+str(i));ok(x.failed,'never retry '+str(i));refusal(x.check,'terminal '+str(i))
# Complete declared literal inverse including only one origin string and new final
# rejoin/sample placement. No genuine class method/guard change.
old=(H/'storage_lease01.original.py').read_text();new=(H/'storage_lease01.py').read_text();reversed_source=new
edits=[]
for before,after in [
 ('financial-batch-output-genuine-storage-lease-preparation01-2026-10-04','financial-batch-output-genuine-storage-lease-preparation02-2026-10-04'),
 ("require(len(rows)<=ENTRIES,'finite total tree')\n    return rows","require(len(rows)<=ENTRIES,'finite total tree')\n    _rejoin(root,fd,root_id,rows,deadline)\n    return rows"),
 ("self.seen=rows;self._stamp=self._state()\n        return {'logical_bytes'","# Floor/statvfs and census descriptor cleanup precede this final sweep.\n        _rejoin(self.root,self.fd,self.root_id,rows,min(self.deadline,time.monotonic()+5))\n        self.seen=rows;self._stamp=self._state()\n        return {'logical_bytes'"),
 ("self._boundary();yield;self._boundary()","self._boundary();final={};yield final;self._boundary()\n            # Exactly one final census after the actual trailing callback.\n            # Its cleanup/floor IO is followed by a descriptor-free rejoin.\n            final['sample']=self._sample()"),
 ("with self._operation():return self._sample()","with self._operation() as final:self._sample()\n        return final['sample']"),
 ("with self._operation():\n            self._sample();require(role","with self._operation() as final:\n            self._sample();require(role"),
 ("result=self._sample();return result","self._sample()\n        return final['sample']")]:
 ok(reversed_source.count(after)==1,'single literal corrected seam '+str(len(edits)));reversed_source=reversed_source.replace(after,before);edits.append({'before':before,'after':after})
start=reversed_source.index('def _rejoin(');end=reversed_source.index('def census(',start);addition=reversed_source[start:end];reversed_source=reversed_source[:start]+reversed_source[end:]
ok(reversed_source==old,'full exact byte inverse');ok(ast.dump(ast.parse(reversed_source),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'full AST inverse')
a=next(n for n in ast.parse(old).body if isinstance(n,ast.ClassDef) and n.name=='GenuineLease');b=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GenuineLease');ok(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'all genuine ancestry/class/grant refusals AST unchanged')
ok(hashlib.sha256((H/'owned_io.py').read_bytes()).hexdigest()==N.IO_SHA,'original reducer unchanged')
(H/'INVERSE01.json').write_text(json.dumps({'edits':edits,'added_function':addition,'full_literal_inverse':True,'full_AST_inverse':True},indent=2,sort_keys=True)+'\n');(H/'SOURCE01.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original92e5',tofile='successor02')))
(H/'WITNESSES01.json').write_text(json.dumps(witnesses,indent=2,sort_keys=True)+'\n');(H/'CHECKS01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'source_sha256':hashlib.sha256(new.encode()).hexdigest(),'scientific_handles_executed':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'status':'PASS'}))
