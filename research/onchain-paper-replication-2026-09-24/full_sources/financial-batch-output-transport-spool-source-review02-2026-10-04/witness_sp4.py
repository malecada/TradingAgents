import dataclasses,hashlib,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-transport-spool-preparation02-2026-10-04';sys.path.insert(0,str(A));import spool04 as S
assert hashlib.sha256((A/'spool04.py').read_bytes()).hexdigest()=='c6604ec50a26e639b14cebeb17a89304986b5cf178b9958993d674120d10ef06'
p=S.Plan((S.Member(0,0,1,S.digest(b'x')),),1,0,0);l,a=p.required();p=dataclasses.replace(p,logical_reservation=l,allocated_reservation=a)
parent=H/'parent';parent.mkdir();r=parent/'root';r.mkdir(mode=0o700);s=S.Spool(r,p)
real_close=os.close;events=[];moved=H/'parent-moved'
def close(fd):
 real_close(fd);events.append(fd)
 if len(events)==1:
  parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
try:
 os.close=close;s.check()
finally:os.close=real_close
assert s.root.resolve()!=s.root
result={'source_sha256':hashlib.sha256((A/'spool04.py').read_bytes()).hexdigest(),'exact_real_close_then_owned_parent_change':True,'closed_walk_descriptors':len(events),'check_returned_success':True,'failed':s.failed,'declared_root':str(s.root),'resolved_root':str(s.root.resolve()),'literal_link':os.readlink(parent),'not_a_timed_race_claim':True,'no_research_or_transport':True}
s.close();(H/'SP4_WITNESS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
