import dataclasses,hashlib,importlib,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;old=sys.argv[1]=='old';tag='old' if old else 'new';A=H.parent/('financial-batch-output-transport-spool-preparation02-2026-10-04' if old else 'financial-batch-output-transport-spool-preparation03-2026-10-04');sys.path.insert(0,str(A));S=importlib.import_module('spool04' if old else 'spool05');out=[]
p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,a=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=a)
for mode in ('check','transfer'):
 parent=H/(tag+'-'+mode);parent.mkdir();r=parent/'root';r.mkdir(mode=0o700);s=S.Spool(r,p);consumed=s.consumed
 real_close=os.close;events=[];calls=[];moved=H/(tag+'-'+mode+'-moved')
 def close(fd):
  real_close(fd);events.append(fd)
  if len(events)==1:parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
 def send(i,m,b):calls.append('send');return S.Ack(i,m.page,m.chunk,m.size,m.sha256,'a'*64)
 def recover(a):calls.append('recover');return S.Recovery(a,b'x')
 try:
  os.close=close
  try:
   if mode=='check':s.check()
   else:s.transfer(b'x',send,recover)
   refused=False
  except (ValueError,OSError):refused=True
 finally:os.close=real_close
 # Original check accepts; original transfer's later check detects the stable
 # alias. New transfer refuses at its FIRST check, before callbacks or _next.
 if mode=='check':assert refused is (not old)
 else:assert refused and not calls and s.failed
 assert s.root.resolve()!=s.root and s.consumed==consumed
 if not old:assert s._next==0 and not calls
 out.append({'mode':mode,'refused':refused,'failed':s.failed,'states':s.states,'walk_closes':len(events),'callbacks':calls,'attempted_prefix':s._next,'consumed_unchanged':True,'original_root':str(s.root),'resolved_root':str(s.root.resolve()),'continuous_race_claim':False});s.close()
(H/('SP4_'+tag+'.json')).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
