from pathlib import Path
import hashlib,importlib.util,json,os,sys,time,types
D=Path(__file__).resolve().parent;O=D/'old-red';O.mkdir(mode=0o700);P=D.parent/'financial-wrapper-compatibility-complete100-outcome-capture-preparation02-2026-10-05';H=lambda b:hashlib.sha256(b).hexdigest();spec=importlib.util.spec_from_file_location('actual_old02',P/'capture01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);results=[]
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
result=M.capture({'capsule':cap,'parent':parent},root/'output',time.monotonic(),pins)
record=next(row for row in result['originals']['parent']['manifest']['members']if row['path']==p.name)
assert record['sha256']==H(p.read_bytes())!=H(original)
results.append({'case':'earlier_authenticated_parent_pin_overwritten','status':'accepted_changed_evidence','original_sha256':H(original),'captured_sha256':record['sha256'],'actual_later_fd_closed_once':True})
(O/'CHECKS01.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
