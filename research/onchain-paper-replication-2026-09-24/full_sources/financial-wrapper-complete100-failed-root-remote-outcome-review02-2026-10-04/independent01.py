from pathlib import Path
from unittest.mock import patch
import importlib.util,os,json
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('watchreview',H/'watch01.py');W=importlib.util.module_from_spec(s);s.loader.exec_module(W)
original=Path.lstat;rows=[]
for action in ('grow','shrink','replace','mode','link','file-limit','logical-limit'):
 p=H/'own'/action;p.mkdir(parents=True);f=p/'opaque';f.write_bytes(b'x'*8192);calls=0;policy=dict(W.POLICY)
 if action=='file-limit':W.POLICY['file']=8200
 if action=='logical-limit':W.POLICY['logical']=8200
 def sample(path,*a,**kw):
  global calls
  if path==f:
   calls+=1
   if calls==2:
    if action in ('grow','file-limit','logical-limit'):
     fd=os.open(f,os.O_WRONLY|os.O_APPEND)
     try:os.write(fd,b'y'*128);os.fsync(fd)
     finally:os.close(fd)
    elif action=='shrink':
     fd=os.open(f,os.O_WRONLY)
     try:os.ftruncate(fd,1);os.fsync(fd)
     finally:os.close(fd)
    elif action=='replace':os.rename(f,p.parent/'retained');f.write_bytes(b'z')
    elif action=='mode':os.chmod(f,0o600)
    elif action=='link':os.link(f,p/'second')
  return original(path,*a,**kw)
 try:
  with patch.object(Path,'lstat',sample):r=W._sample(p)
 except (ValueError,W.ChangingTree) as e:
  assert action not in ('grow','shrink');rows.append({'case':action,'refused':type(e).__name__,'message':str(e),'lstat_calls':calls})
 else:
  assert action in ('grow','shrink');assert r['logical_bytes']==(8320 if action=='grow' else 8192);assert r['regular_extent_changes']==1
  rows.append({'case':action,'observed':r,'current_bytes':f.stat().st_size,'lstat_calls':calls})
 finally:W.POLICY.clear();W.POLICY.update(policy)
# Whole census retry is only for transient namespace incompleteness, not limits/fatals.
prior=W._sample
for error in (W.ChangingTree('changed'),FileNotFoundError('gone'),ValueError('cap'),MemoryError('first')):
 calls=0
 def fail(root):
  global calls
  calls+=1;raise error
 W._sample=fail
 try:
  try:W.census(H/'own')
  except BaseException as e:
   transient=isinstance(error,(W.ChangingTree,FileNotFoundError));assert calls==(3 if transient else 1)
   if not transient:assert e is error
   rows.append({'case':'retry-domain','type':type(error).__name__,'attempts':calls})
  else:raise AssertionError('accepted')
 finally:W._sample=prior
# Real iterator-close failure remains attached to the selected fatal; no fake FD.
prior=W.os.scandir;first=KeyboardInterrupt('original');later=SystemExit('secondary');events=[]
class It:
 def __init__(self,p):self.actual=prior(p)
 def __iter__(self):return self
 def __next__(self):raise first
 def close(self):self.actual.close();events.append('actual close');raise later
W.os.scandir=It
try:
 try:W.census(H/'own')
 except BaseException as e:assert e is first and events==['actual close'];rows.append({'case':'iterator-firstfatal','first_identity':True,'close_events':events})
 else:raise AssertionError('accepted')
finally:W.os.scandir=prior
print(json.dumps({'cases':len(rows),'rows':rows,'sampled_not_atomic':True},indent=2))
