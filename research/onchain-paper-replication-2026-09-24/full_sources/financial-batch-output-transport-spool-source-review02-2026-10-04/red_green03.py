import dataclasses,importlib,json,os,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;old=sys.argv[1]=='old';A=H.parent/('financial-batch-output-transport-spool-preparation01-2026-10-04' if old else 'financial-batch-output-transport-spool-preparation02-2026-10-04');sys.path.insert(0,str(A));S=importlib.import_module('spool02' if old else 'spool04');tag='old' if old else 'new';result={}
p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,a=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=a)
def ack(i,m,b):return S.Ack(i,m.page,m.chunk,m.size,m.sha256,'a'*64)
parent=H/(tag+'-parent');parent.mkdir();r=parent/'root';r.mkdir(mode=0o700);s=S.Spool(r,p);moved=H/(tag+'-moved');parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
try:s.transfer(b'x',ack,lambda a:S.Recovery(a,b'x'));refused=False
except (ValueError,OSError):refused=True
assert refused is (not old);result['SP1']={'refused':refused,'failed':s.failed,'canonical':s.root.resolve()==s.root};s.close()
r=H/(tag+'-bool');r.mkdir(mode=0o700);s=S.Spool(r,p)
try:s.transfer(b'x',lambda i,m,b:S.Ack(i,False,False,True,m.sha256,'a'*64),lambda a:S.Recovery(a,b'x'));refused=False
except ValueError:refused=True
assert refused is (not old);result['SP2']={'refused':refused,'failed':s.failed,'states':s.states};s.close()
r=H/(tag+'-late');r.mkdir(mode=0o700);s=S.Spool(r,p,seconds=1)
def cleanup():time.sleep(max(0,s.deadline-time.monotonic())+.025)
try:s.transfer(b'x',ack,lambda a:S.Recovery(a,b'x'),cleanup);refused=False
except ValueError:refused=True
assert refused is (not old);result['SP3']={'refused':refused,'failed':s.failed,'states':s.states,'terminal':'terminal' in s._sealed};s.close()
(H/('RED_GREEN_'+tag+'.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
