"""Independent real-descriptor stale-earlier-body witness; no actual receipt/entry."""
from pathlib import Path
import os,sys,json,hashlib,importlib.util,time
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));s=importlib.util.spec_from_file_location('review_flat',D/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
B=D.parent/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';c,m=M.load_failed_capture(B);owned=D/'witness-owned01';owned.mkdir(mode=0o700)
boundaries=[]
def boundary():boundaries.append(M.W.census(owned))
r=M.restore_failed_delta(B,c,m,owned,boundary);dest=owned/M.FAILED_OUTPUT;metadata=json.loads((dest/r['metadata_file']).read_bytes());files=[x for x in m['members'] if x['kind']=='file'];first=files[0];last=files[-1];victim=dest/metadata['flat_members'][first['path']];trigger=dest/metadata['flat_members'][last['path']]
H=lambda b:hashlib.sha256(b).hexdigest();original=victim.read_bytes();assert original and victim!=trigger;before=victim.stat();close=os.close;fired=[];fd_before=len(os.listdir('/proc/self/fd'))
def closed(fd):
 try:target=os.readlink('/proc/self/fd/'+str(fd))
 except OSError:target=None
 close(fd)
 if target==str(trigger) and not fired:
  with victim.open('r+b') as f:f.write(bytes([original[0]^1]));f.flush();os.fsync(f.fileno())
  os.utime(victim,ns=(before.st_atime_ns,before.st_mtime_ns+1000000000))
  fired.append({'real_closed_fd':fd,'trigger':str(trigger),'victim':str(victim),'before_mtime_ns':before.st_mtime_ns,'after_mtime_ns':victim.stat().st_mtime_ns})
os.close=closed
try:result=M.verify_flat(dest,r,c,m,boundary)
finally:os.close=close
actual=H(victim.read_bytes());assert fired and actual!=first['sha256'] and result==metadata and len(os.listdir('/proc/self/fd'))==fd_before
out={'decision':'COUNTEREXAMPLE_REPRODUCED','source_sha256':H((D/'restore01.py').read_bytes()),'function_returned_success':True,'expected_sha256':first['sha256'],'actual_sha256':actual,'changed_fingerprint_observable':M.R.sig(before)!=M.R.sig(victim.stat()),'events':fired,'fd_before':fd_before,'fd_after':len(os.listdir('/proc/self/fd')),'boundaries':boundaries,'actual_remote_receipt':None,'run_or_entry_executed':False,'qualification':'Later genuine owned descriptor close changed earlier already-hashed body with explicit mtime change. Final full-tree resource census sees stable new metadata and accepts it; no terminal body-fingerprint cohort rejoin.'}
(D/'WITNESS01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('decision','expected_sha256','actual_sha256','function_returned_success')}))
