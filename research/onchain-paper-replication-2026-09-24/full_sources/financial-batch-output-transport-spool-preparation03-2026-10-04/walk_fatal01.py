import dataclasses,json,os
from pathlib import Path
import spool05 as S
P=Path(__file__).resolve().parent;root=P/'walk-fatal';root.mkdir(mode=0o700)
p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,a=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=a);s=S.Spool(root,p)
realopen=os.open;realclose=os.close;opened=[];closed=[];first=KeyboardInterrupt('original walk fatal')
def opening(*args,**kwargs):
 if len(opened)==3:raise first
 fd=realopen(*args,**kwargs);opened.append(fd);return fd
def closing(fd):
 realclose(fd);closed.append(fd);raise OSError('post-close uncertainty')
try:
 os.open=opening;os.close=closing
 try:s.transfer(b'x',None,None)
 except BaseException as e:assert e is first
 else:raise AssertionError('walk fatal lost')
finally:os.open=realopen;os.close=realclose
assert s.failed and set(opened)==set(closed) and len(closed)==3 and s.consumed==p.required()
for fd in opened:
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('leaked walk fd')
s.close();(P/'WALK_FATAL01.json').write_text(json.dumps({'first_fatal_identity':True,'opened':opened,'closed':closed,'consumed_unchanged':True,'failed':True},indent=2)+'\n');print('walk fatal passed')
