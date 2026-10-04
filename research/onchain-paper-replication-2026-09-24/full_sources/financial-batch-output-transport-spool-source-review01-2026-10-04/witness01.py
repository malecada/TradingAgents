import dataclasses,hashlib,json,os,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-transport-spool-preparation01-2026-10-04';sys.path.insert(0,str(A));import spool02 as S
assert hashlib.sha256((A/'spool02.py').read_bytes()).hexdigest()=='fcd2f425ac03028a8aa82e2d3e148543acb93746282a3f50f3cc248f789c2245'
def plan(b=b'x'):
 p=S.Plan((S.Member(0,0,len(b),S.digest(b)),),1,0,0);l,a=p.required();return dataclasses.replace(p,logical_reservation=l,allocated_reservation=a)
def ack(i,m,b):return S.Ack(i,m.page,m.chunk,m.size,m.sha256,'a'*64)
results={}
# Ordinary owned directory rename and literal symlink alias, without replacing
# a descriptor or mocking any source operation. Root inode is unchanged.
parent=H/'parent-before';parent.mkdir();r=parent/'root';r.mkdir(mode=0o700);s=S.Spool(r,plan())
oldroot=str(s.root);moved=H/'parent-after';parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
assert s.root.resolve()!=s.root
s.check();s.transfer(b'x',ack,lambda a:S.Recovery(a,b'x'))
results['SP1']={'declared_root':oldroot,'resolved_root':str(s.root.resolve()),'check_accepted':True,'transfer_states':list(s.states),'failed':s.failed,'same_original_root_inode':list(s._root),'literal_link':os.readlink(parent)};s.close()
# Equality accepts booleans for integer identity fields. No mutable or fake
# empirical object is created; these are exact public opaque Ack dataclasses.
r=H/'typed-ack';r.mkdir(mode=0o700);s=S.Spool(r,plan())
def badack(i,m,b):return S.Ack(i,False,False,True,m.sha256,'a'*64)
s.transfer(b'x',badack,lambda a:S.Recovery(a,b'x'))
results['SP2']={'ack_types':['bool','bool','bool'],'accepted_states':list(s.states),'failed':s.failed,'ack_event':json.loads(s.events[1][2])};s.close()
# A finite cleanup callback crosses the deadline. No clock mocking; the source
# checks the deadline before and after send/recover, but never after cleanup.
r=H/'late-cleanup';r.mkdir(mode=0o700);s=S.Spool(r,plan(),seconds=1)
def cleanup():time.sleep(max(0,s.deadline-time.monotonic())+.025)
s.transfer(b'x',ack,lambda a:S.Recovery(a,b'x'),cleanup)
results['SP3']={'deadline_exceeded':time.monotonic()>s.deadline,'returned_without_failure':not s.failed,'states':list(s.states),'sealed_terminal':'terminal' in s._sealed}
assert results['SP3']['deadline_exceeded'] and not s.failed
s.close()
(H/'WITNESSES01.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
