from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys,time,types
O=Path(__file__).resolve().parent;F=O.parent;D=F/'financial-wrapper-compatibility-complete100-outcome-capture-preparation03-2026-10-05';OLD=F/'financial-wrapper-compatibility-complete100-outcome-capture-preparation02-2026-10-05';H=lambda b:hashlib.sha256(b).hexdigest();spec=importlib.util.spec_from_file_location('candidate02',D/'capture01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
assert H((D/'capture01.py').read_bytes())=='d8b61b8bc45e69da0df50bfa4694c0c0d103aaa5dce6668fccd0686c275958bb'
inv=json.loads((D/'INVERSE01.json').read_bytes());s=(OLD/'capture01.py').read_text()
for a,b in inv['changes']:assert s.count(a)==1;s=s.replace(a,b)
assert s==(D/'capture01.py').read_text()
old={n.name:ast.dump(n)for n in ast.parse((OLD/'capture01.py').read_bytes()).body if isinstance(n,ast.FunctionDef)};new={n.name:ast.dump(n)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
assert all(old[n]==new[n]for n in old if n not in {'run','capture','ref_read'})
results=[]
for case in ('healthy','late_archive_mutation','late_expired_deadline'):
 root=O/case;root.mkdir(mode=0o700);cap=root/'capsule';parent=root/'parent';cap.mkdir(mode=0o700);parent.mkdir(mode=0o700);(cap/'one.body').write_bytes(b'opaque complete original\0');(parent/'two.body').write_bytes(b'opaque Parent\0');out=root/'output'
 close0=os.close;clock=time.monotonic;offset=[0.];M.time=types.SimpleNamespace(monotonic=lambda:clock()+offset[0]);closed=[]
 def close(fd):
  try:target=os.readlink('/proc/self/fd/'+str(fd))
  except OSError:target=''
  close0(fd)
  if target==str(out/'CAPTURE01.json') and not closed:
   closed.append(fd)
   if case=='late_archive_mutation':
    p=out/'piece-000.tar.gz';b=p.read_bytes();p.write_bytes(bytes([b[0]^1])+b[1:])
   elif case=='late_expired_deadline':offset[0]=121.
 os.close=close
 try:
  try:M.capture({'capsule':cap,'parent':parent},out,M.time.monotonic());status='accepted';reason=None
  except ValueError as e:status='refused';reason=str(e)
 finally:os.close=close0
 assert len(closed)==1 and (status=='accepted')==(case=='healthy');results.append({'case':case,'status':status,'reason':reason,'real_final_fd_closed':True})
# New public evidence merge must retain an earlier authenticated Parent-body pin.
root=O/'evidence_overlap';root.mkdir(mode=0o700);cap=root/'capsule';parent=root/'parent';cap.mkdir(mode=0o700);parent.mkdir(mode=0o700);p=parent/'REQUEST_FINAL.json';p.write_bytes(b'original authorized opaque metadata');(cap/'body').write_bytes(b'opaque source');trigger=root/'later-source-read';trigger.write_bytes(b'actual owned later read');pins={};original=p.read_bytes();M.ref_read({'path':str(p),'sha256':H(original)},pins);pin_before=pins[str(p)];close0=os.close;closed=[]
def close(fd):
 try:target=os.readlink('/proc/self/fd/'+str(fd))
 except OSError:target=''
 close0(fd)
 if target==str(trigger):p.write_bytes(b'changed unapproved opaque metadata');closed.append(fd)
os.close=close
try:M.R.read(root,trigger.name)
finally:os.close=close0
assert len(closed)==1 and M.R.sig(p.lstat())!=pin_before
M.time=types.SimpleNamespace(monotonic=time.monotonic)
try:M.capture({'capsule':cap,'parent':parent},root/'output',time.monotonic(),pins)
except ValueError as e:
 assert str(e)=='earlier authenticated evidence changed';results.append({'case':'earlier_authenticated_parent_pin_conflict','status':'refused','reason':str(e),'actual_later_fd_closed_once':True})
else:raise AssertionError('changed evidence accepted')
(O/'CHECKS01.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
