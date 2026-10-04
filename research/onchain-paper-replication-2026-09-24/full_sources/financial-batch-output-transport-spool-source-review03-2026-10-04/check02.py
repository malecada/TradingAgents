import ast,dataclasses,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-transport-spool-preparation03-2026-10-04';sys.path.insert(0,str(A));import spool05 as S
count=0;notes=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v):
 global count
 assert v;count+=1
def refuse(fn,typ=ValueError):
 try:fn()
 except typ as e:ok(True);return e
 raise AssertionError('missing refusal')
def plan(bs,window=None):
 w=len(bs) if window is None else window;ms=tuple(S.Member(i//w,i%w,len(b),sha(b)) for i,b in enumerate(bs));p=S.Plan(ms,w,0,0);l,a=p.required();return dataclasses.replace(p,logical_reservation=l,allocated_reservation=a)
def root(n):r=H/n;r.mkdir(mode=0o700);return r
def ack(i,m,b):return S.Ack(i,m.page,m.chunk,m.size,m.sha256,'a'*64)
bs=(b'first',b'second');p=plan(bs);p.validate()
for name,values in [('window',[False,0,33,2.0]),('logical_reservation',[False,p.logical_reservation-1]),('allocated_reservation',[False,p.allocated_reservation-1]),('allocation_quantum',[False,0,2048,4097,S.FILE+4096]),('members',[[],(),p.members[::-1],(S.Member(1,0,1,'a'*64),)])]:
 for v in values:refuse(lambda n=name,v=v:dataclasses.replace(p,**{n:v}).validate())
for field,values in [('page',[False,1,0.0]),('chunk',[False,1,0.0]),('size',[False,0,-1,S.FILE+1,1.0]),('sha256',[None,'A'*64,'a'*63])]:
 for v in values:
  ms=(dataclasses.replace(p.members[0],**{field:v}),)+p.members[1:]
  refuse(lambda ms=ms:dataclasses.replace(p,members=ms).validate())
# Full requested denominator: metadata only, no 9GB allocation.
n=(S.NON_TAIL+S.FILE-1)//S.FILE;ms=tuple(S.Member(i//32,i%32,min(S.FILE,S.NON_TAIL-i*S.FILE),'0'*64) for i in range(n));pfull=S.Plan(ms,32,0,0);l,a=pfull.required();pfull=dataclasses.replace(pfull,logical_reservation=l,allocated_reservation=a);pfull.validate()
ok((n,(n+31)//32,sum(m.size for m in ms),l,a)==(2203,69,9239969792,9285103616,9339269120));notes.append({'full_metadata_only':{'chunks':n,'pages':69,'bytes':S.NON_TAIL,'logical':l,'allocated':a},'actual_capacity':False})
# Ordered complete tiny run, padded slots all actually private/regular/bounded.
s=S.Spool(root('ordered'),p)
for b in bs:s.transfer(b,ack,lambda ac,b=b:S.Recovery(ac,b))
ok(s.states==('ELIGIBLE','ELIGIBLE') and s.calls==4 and s.consumed==p.required());ok(len(s.events)==8)
for path in s.root.iterdir():st=path.stat();ok(stat.S_IMODE(st.st_mode)==0o600 and st.st_size<=S.FILE and st.st_nlink==1)
refuse(s.release,RuntimeError);refuse(S.production,RuntimeError);s.close();before=s.root.stat().st_mtime_ns
refuse(lambda:s.transfer(b'first',lambda *x:(_ for _ in ()).throw(AssertionError('no callback')),None));ok(s.root.stat().st_mtime_ns==before)
# Malformed acknowledgement and raw-body/identity/recovery rejection. Use NEW
# tiny owned tree for each attempted identity; all real partials are retained.
mutations=[('plan','b'*64),('page',1),('chunk',1),('size',6),('sha256','b'*64),('receipt_sha256','bad')]
for number,(k,v) in enumerate(mutations):
 s=S.Spool(root('ack-bad-%02d'%number),p)
 def send(i,m,b):return dataclasses.replace(ack(i,m,b),**{k:v})
 refuse(lambda:s.transfer(bs[0],send,lambda a:S.Recovery(a,bs[0])));ok(s.failed and s.states==('PENDING','ABSENT') and s.consumed==p.required());ok('terminal' in s._sealed);refuse(lambda:s.transfer(bs[0],ack,None));s.close()
for number,(send,recover,body) in enumerate([(lambda *a:{},None,bs[0]),(ack,lambda a:S.Recovery(a,b'wrong'),bs[0]),(ack,lambda a:None,bs[0]),(ack,lambda a:S.Recovery(dataclasses.replace(a,receipt_sha256='b'*64),bs[0]),bs[0]),(ack,None,b'wrong')]):
 s=S.Spool(root('invalid-%02d'%number),p);refuse(lambda:s.transfer(body,send,recover));ok(s.failed and s.consumed==p.required());refuse(lambda:s.transfer(bs[0],ack,None));s.close()
# Retained-window exhaustion cannot recycle eligible members or finish target.
s=S.Spool(root('window'),plan(bs,1));s.transfer(bs[0],ack,lambda a:S.Recovery(a,bs[0]));kept=(s.root/'body-0000').read_bytes();refuse(lambda:s.transfer(bs[1],ack,lambda a:S.Recovery(a,bs[1])));ok(s.failed and s.states==('ELIGIBLE','ABSENT') and (s.root/'body-0000').read_bytes()==kept);s.close()
# Replay of actual earlier opaque ack cannot acknowledge a distinct member.
s=S.Spool(root('replay'),p);first=ack(s.identity,p.members[0],bs[0]);s.transfer(bs[0],lambda *args:first,lambda a:S.Recovery(a,bs[0]));refuse(lambda:s.transfer(bs[1],lambda *args:first,lambda a:S.Recovery(a,bs[1])));ok(s.failed);s.close()
# First actual fatal wins, every supplied cleanup runs once, real descriptors
# drain, and callback observations never become real external receipts.
for i,primary in enumerate((MemoryError('primary'),KeyboardInterrupt('primary'),SystemExit('primary'))):
 for j,secondary in enumerate((OSError('cleanup'),MemoryError('cleanup'),KeyboardInterrupt('cleanup'))):
  s=S.Spool(root('fatal-%d-%d'%(i,j)),p);fds=list(s._fds.values())+[s.fd];seen=[]
  def send(*args):raise primary
  def cleanup():seen.append('cleanup');raise secondary
  try:s.transfer(bs[0],send,None,cleanup)
  except BaseException as e:ok(e is primary)
  else:raise AssertionError('fatal missing')
  ok(s.failed and seen==['cleanup'] and 'terminal' in s._sealed);s.close()
  for fd in fds:
   try:os.fstat(fd)
   except OSError:ok(True)
   else:raise AssertionError('fd leaked')
# Missing/extra/root leaf/mode/body mutations detected by normal boundaries.
for k in ('extra','mode','body','symlink'):
 s=S.Spool(root('ownership-'+k),p)
 if k=='extra':(s.root/'extra').write_bytes(b'preserved')
 elif k=='mode':os.chmod(s.root/'body-0000',0o644)
 elif k=='body':os.pwrite(s._fds['body-0000'],b'X',0)
 else:
  (s.root/'body-0000').rename(s.root/'old-body');(s.root/'body-0000').symlink_to('old-body')
 refuse(lambda:s.transfer(bs[0],ack,None));ok(s.failed);s.close()
# Readbacks below are tiny owned filesystem observations, not production release.
notes.append({'literal_witnesses':json.loads((H/'SP4_new.json').read_text()),'production_refused':True,'deletion_refused':True})
(H/'CHECKS01.json').write_text(json.dumps({'checks':count,'notes':notes,'no_numerical_or_network_work':True},sort_keys=True,indent=2)+'\n');print(count,'checks passed')
