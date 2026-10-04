import importlib.util,json,os,hashlib,stat,time
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def load(path,n):
 spec=importlib.util.spec_from_file_location(n,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
new=load(HERE/'watch01.py','newwatch03')
old=load(HERE/'ORIGINAL_watch01.py','oldwatch02')
rows=[];original=Path.lstat

def extent(module,label,growth,policy=None):
 root=HERE/'owned'/label;root.mkdir(parents=True);f=root/'opaque';f.write_bytes(b'12345678');calls=0;prior=dict(module.POLICY)
 if policy:module.POLICY.update(policy)
 def lstat(path,*a,**k):
  nonlocal calls
  if path==f:
   calls+=1
   if calls%2==0:
    fd=os.open(f,os.O_WRONLY|os.O_APPEND);os.write(fd,b'x'*growth);os.fsync(fd);os.close(fd)
  return original(path,*a,**k)
 result=None;error=None
 try:
  with patch.object(Path,'lstat',lstat):result=module.census(root.resolve())
 except BaseException as e:error=type(e).__name__+':'+str(e)
 finally:module.POLICY.clear();module.POLICY.update(prior)
 rows.append({'label':label,'result':result,'error':error,'actual_bytes':f.stat().st_size,'lstat_calls':calls})
 return result,error
r,e=extent(old,'original-red',128);assert r is None and 'no complete census' in e
r,e=extent(new,'new-green',128);assert e is None and r['logical_bytes']==136 and r['regular_extent_changes']==1 and r['complete_attempts']==1
r,e=extent(new,'file-limit-refusal',128,{'file':64});assert r is None and 'per-file' in e
r,e=extent(new,'whole-logical-refusal',128,{'logical':64});assert r is None and 'whole rejoin' in e
# Scaled allocation refusal includes directory blocks and both regular samples.
r,e=extent(new,'allocated-refusal',4096,{'allocated':8192});assert r is None and 'allocated' in e
root=HERE/'owned'/'unmodified';root.mkdir();(root/'a').write_bytes(b'abc');r=new.census(root.resolve());assert r['logical_bytes']==3 and r['regular_extent_changes']==0;rows.append({'label':'unmodified','result':r})
for label,make in [('symlink',lambda root:(root/'bad').symlink_to('/proc')),('hardlink',lambda root:(os.link(root/'a',root/'bad')) )]:
 root=HERE/'owned'/label;root.mkdir();(root/'a').write_bytes(b'abc');make(root)
 try:new.census(root.resolve())
 except ValueError as e:rows.append({'label':label,'error':str(e)})
 else:raise AssertionError(label)
# Fatal census and caps never repeat metadata or a child.
root=HERE/'owned'/'fatal';root.mkdir();(root/'a').write_bytes(b'abc');calls=0;fatal=KeyboardInterrupt()
def boom(path,*a,**k):
 global calls
 if path==root/'a':calls+=1;raise fatal
 return original(path,*a,**k)
try:
 with patch.object(Path,'lstat',boom):new.census(root.resolve())
except BaseException as e:assert e is fatal and calls==1;rows.append({'label':'fatal-no-retry','calls':calls,'identity':True})
else:raise AssertionError('fatal')
(HERE/'CONTROLS01.json').write_text(json.dumps({'rows':rows,'checks':20,'actual_OS_extents':True,'new_claim_or_network':False},sort_keys=True,indent=2)+'\n')
print('PASS',len(rows))
