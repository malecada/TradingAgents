import dataclasses
import hashlib
import json
import os
from pathlib import Path
import spool02 as S

HERE=Path(__file__).resolve().parent
checks=[]
def ok(value,label):
    assert value,label
    checks.append(label)
def plan(bodies,window=None):
    window=window or len(bodies)
    members=tuple(S.Member(i//window,i%window,len(b),S.digest(b)) for i,b in enumerate(bodies))
    p=S.Plan(members,window,0,0)
    a,b=p.required()
    return dataclasses.replace(p,logical_reservation=a,allocated_reservation=b)
def root(name):
    p=HERE/('run02-'+name);p.mkdir(mode=0o700);return p
def ack(identity,m,body):
    return S.Ack(identity,m.page,m.chunk,m.size,m.sha256,'a'*64)
def case(name,fn,expected=Exception):
    try:fn()
    except BaseException as e:
        ok(isinstance(e,expected),name+' exact category')
        return e
    raise AssertionError(name+' did not refuse')

bodies=(b'opaque01',b'opaque02')
p=plan(bodies)
s=S.Spool(root('tiny-success'),p)
for b in bodies:s.transfer(b,ack,lambda a,b=b:S.Recovery(a,b))
ok(s.states==('ELIGIBLE','ELIGIBLE'),'complete ordered byte equality')
ok(len(s.events)==8 and s.calls==4,'finite event/callback counts')
ok(s.consumed==p.required(),'whole reservation nonrefundable')
case('release',s.release,RuntimeError)
s.close()
case('closed replay',lambda:s.transfer(bodies[0],ack,None),ValueError)
case('production always closed',lambda:S.production(object()),RuntimeError)
for which in ('logical_reservation','allocated_reservation'):
    bad=dataclasses.replace(p,**{which:getattr(p,which)-1})
    case(which,lambda bad=bad:bad.validate(),ValueError)

for label,send,recover,expected in (
 ('partial',lambda *a:None,lambda a:None,ValueError),
 ('wrong-recovery',ack,lambda a:S.Recovery(a,b'wrong'),ValueError),
 ('mutable-ack',lambda *a:{},lambda a:None,ValueError),
 ('fatal',lambda *a:(_ for _ in ()).throw(MemoryError('original')),lambda a:None,MemoryError)):
    s=S.Spool(root('tiny-'+label),p)
    error=case(label,lambda:s.transfer(bodies[0],send,recover),expected)
    ok(s.failed and s.states[1]=='ABSENT' and s.consumed==p.required(),label+' failed/absent/no refund')
    case(label+' retry',lambda:s.transfer(bodies[0],ack,lambda a:S.Recovery(a,bodies[0])),ValueError)
    s.close()

s=S.Spool(root('tiny-replay'),p)
first=ack(s.identity,p.members[0],bodies[0])
s.transfer(bodies[0],lambda *a:first,lambda a:S.Recovery(a,bodies[0]))
case('replayed ack',lambda:s.transfer(bodies[1],lambda *a:first,lambda a:S.Recovery(a,bodies[1])),ValueError)
ok(s.states==('ELIGIBLE','PENDING'),'old ack does not acknowledge next chunk');s.close()

s=S.Spool(root('tiny-window'),plan(bodies,1))
s.transfer(bodies[0],ack,lambda a:S.Recovery(a,bodies[0]))
case('retained window',lambda:s.transfer(bodies[1],ack,lambda a:S.Recovery(a,bodies[1])),ValueError)
ok(s.states[1]=='ABSENT' and s.failed,'no local retirement credit');s.close()

s=S.Spool(root('tiny-cleanup'),p);primary=MemoryError('first fatal');later=SystemExit('later fatal');seen=[]
def send(*a):raise primary
def cleanup():seen.append('closed');raise later
err=case('fatal cleanup',lambda:s.transfer(bodies[0],send,None,cleanup),MemoryError)
ok(err is primary and seen==['closed'],'first fatal identity plus independent cleanup');s.close()

s=S.Spool(root('tiny-cleanup-only'),p)
def badclose():raise OSError('close uncertainty')
case('cleanup uncertainty',lambda:s.transfer(bodies[0],ack,lambda a:S.Recovery(a,bodies[0]),badclose),S.io.CleanupFailure)
ok(s.failed,'cleanup uncertainty terminal');s.close()

s=S.Spool(root('tiny-mutation'),p)
os.pwrite(s._fds['body-0000'],b'X',0)
case('preallocated mutation',lambda:s.transfer(bodies[0],ack,None),ValueError)
ok(s.failed,'mutation poisons instance');s.close()

full_count=(S.NON_TAIL+S.FILE-1)//S.FILE
members=tuple(S.Member(i//32,i%32,min(S.FILE,S.NON_TAIL-i*S.FILE),'0'*64) for i in range(full_count))
full=S.Plan(members,32,0,0);logical,allocated=full.required()
full=dataclasses.replace(full,logical_reservation=logical,allocated_reservation=allocated);full.validate()
ok(sum(m.size for m in full.members)==9239969792,'exact non-tail finite denominator')
(HERE/'RESULT02.json').write_text(json.dumps({'checks':checks,'count':len(checks),'full_target_metadata_only':{'bytes':S.NON_TAIL,'chunks':full_count,'pages':(full_count+31)//32,'logical_reservation':logical,'allocated_reservation':allocated},'production_available':False,'network_or_numerical_work':False},sort_keys=True,indent=2)+'\n')
print(len(checks),'passed')
