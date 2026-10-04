import dataclasses,json,os
from pathlib import Path
import spool04 as S
P=Path(__file__).resolve().parent;rows=[]
for a,A in enumerate((MemoryError,KeyboardInterrupt,SystemExit)):
 for b,B in enumerate((OSError,MemoryError,SystemExit)):
  root=P/('fatal-%s-%s'%(a,b));root.mkdir(mode=0o700)
  p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,r=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=r)
  s=S.Spool(root,p);fds=tuple(s._fds.values())+(s.fd,);first=A('first');later=B('later');seen=[]
  def send(*args):raise first
  def cleanup():seen.append(1);raise later
  try:s.transfer(b'x',send,None,cleanup)
  except BaseException as e:assert e is first
  else:raise AssertionError('lost fatal')
  assert s.failed and seen==[1] and s.consumed==p.required();s.close()
  for fd in fds:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('fd remains open')
  rows.append({'primary':A.__name__,'cleanup':B.__name__,'identity_preserved':True,'cleanup_calls':1,'fds_closed':len(fds)})
(P/'FATAL01.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'passed')
