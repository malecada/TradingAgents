from pathlib import Path
import sys,json,os
H=Path(__file__).resolve().parent;A=H.with_name('financial-batch-output-genuine-storage-lease-preparation01-2026-10-04');sys.path.insert(0,str(A));import storage_lease01 as L
root=H/'late-close';root.mkdir(mode=0o700);roles={r:r for r in L.ROLES}
for p in roles.values():(root/p).mkdir(mode=0o700)
a=root/'diagnostic/a';z=root/'diagnostic/z';a.write_bytes(b'original');z.write_bytes(b'last');lease=L.OwnedLease(root,'lease',roles,64*L.MIB,64*L.MIB,lambda:None);before=a.stat();target=z.stat();realclose=os.close;events=[]
def close(fd):
 s=os.fstat(fd);match=(s.st_dev,s.st_ino)==(target.st_dev,target.st_ino);realclose(fd)
 if match and not events:
  events.append(fd);a.write_bytes(b'changed!');os.utime(a,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
os.close=close
try:sample=lease.check()
finally:os.close=realclose
assert events and not lease.failed and a.read_bytes()==b'changed!';error=None
try:lease.check()
except ValueError as e:error=str(e)
assert error=='unreserved existing file mutation';(H/'WITNESS02.json').write_text(json.dumps({'finding':'SL2_CENSUS_LATE_CLEANUP_STALE_EARLIER_SIGNATURE','first_sample_accepted':True,'next_refusal':error,'sample':sample,'original_sig':L.sig(before),'current_sig':L.sig(a.stat()),'real_closed_fd':events,'genuine_handles':False},indent=2)+'\n')
