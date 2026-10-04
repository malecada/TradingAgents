import importlib.util,os,json,hashlib
from pathlib import Path
P=Path(__file__).absolute().parent
spec=importlib.util.spec_from_file_location('preclaim_review',P/'CANDIDATE_preclaim01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
O=P/'owned-witness01';O.mkdir(mode=0o700)
a=O/'earlier';b=O/'later';a.write_bytes(b'original');b.write_bytes(b'later')
r=m.Reader();r.read(a);r.read(b)
orig=m.os.close;mutated=False;closes=[]
def close(fd):
 global mutated
 s=os.fstat(fd);original_later=s.st_ino==b.stat().st_ino
 orig(fd);closes.append(fd)
 if original_later and not mutated:
  mutated=True;a.write_bytes(b'changed!')
  st=a.stat();os.utime(a,ns=(st.st_atime_ns,st.st_mtime_ns+1000000000))
m.os.close=close
error=None
try:r.finish()
except BaseException as e:error=e
finally:m.os.close=orig
result={'helper_sha256':hashlib.sha256((P/'CANDIDATE_preclaim01.py').read_bytes()).hexdigest(),'operation':'Reader.finish after cache reads of two owned files','later_real_descriptor_closed':mutated,'returned_without_error':error is None,'earlier_cached_hex':r.cache[a].hex(),'earlier_current_hex':a.read_bytes().hex(),'explicit_mtime_change':True,'closed_descriptor_count':len(closes),'qualification':'Mutation occurs inside actual owned IO cleanup before finish returns; no public Admission/Run/success constructed, no live file changed. This is not proof of post-return or continuous writer exclusion.'}
(P/'WITNESS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
