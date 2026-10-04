from pathlib import Path
import sys,json,os
H=Path(__file__).resolve().parent;A=H.with_name('financial-batch-output-genuine-storage-lease-preparation01-2026-10-04');sys.path.insert(0,str(A));import storage_lease01 as L
root=H/'late-callback';root.mkdir(mode=0o700);roles={r:r for r in L.ROLES}
for p in roles.values():(root/p).mkdir(mode=0o700)
state={'armed':False,'calls':0}
def callback():
 if state['armed']:
  state['calls']+=1
  if state['calls']==2:(root/'diagnostic'/'unreserved').write_bytes(b'actual callback addition')
lease=L.OwnedLease(root,'lease',roles,64*L.MIB,64*L.MIB,callback);state['armed']=True
sample=lease.check();assert state['calls']==2 and (root/'diagnostic'/'unreserved').exists() and not lease.failed
error=None
try:lease.check()
except ValueError as e:error=str(e)
assert error=='unreserved new member' and lease.failed
(H/'WITNESS01.json').write_text(json.dumps({'finding':'SL1_POST_SAMPLE_CALLBACK_MUTATION','first_check_returned':sample,'callback_count_at_first_return':2,'first_return_failed_flag':False,'unreserved_file_present_at_first_return':True,'next_check_refused':error,'genuine_handles':False},indent=2)+'\n');print(error)
