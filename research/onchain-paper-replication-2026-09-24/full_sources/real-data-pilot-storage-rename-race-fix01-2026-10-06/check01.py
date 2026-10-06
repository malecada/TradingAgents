"""Deterministic owned filesystem races only; no native or empirical work."""
import hashlib,importlib.util,json,os,tempfile
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;ROOT=H.parents[3]
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load(ROOT/'tradingagents/research/onchain_replication/workflow_storage.py','baseline_storage')
LIMITS={'max_allocated_bytes':1024**2,'max_logical_bytes':1024,'max_entries':10,'max_depth':3,'max_scan_seconds':1}
def race(module,root,persistent=False):
 watch=module.StorageWatch(root,LIMITS);calls=[];errors=[];original_stat=os.stat;original_scan=watch._scan
 def scan(begin):
  calls.append(1)
  if persistent or len(calls)==1:(root/'.pending-race').write_bytes(b'x')
  return original_scan(begin)
 watch._scan=scan
 def stat(name,*a,**kw):
  if name=='.pending-race' and 'dir_fd' in kw:
   (root/'.pending-race').unlink()
   try:return original_stat(name,*a,**kw)
   except FileNotFoundError as e:errors.append(e);raise
  return original_stat(name,*a,**kw)
 with patch.object(module.os,'stat',stat):
  try:return {'value':watch.check(),'calls':len(calls),'errors':errors}
  except BaseException as e:return {'error':e,'calls':len(calls),'errors':errors}
def main():
 with tempfile.TemporaryDirectory(dir=H) as t:
  root=Path(t);red=race(base,root);assert type(red['error']) is FileNotFoundError and red['calls']==1 and red['error'] is red['errors'][0]
 result={'baseline_red':True,'actual_list_to_stat_disappearance':True}
 candidate=H/'workflow_storage.py'
 if not candidate.exists():print(json.dumps(result));return
 new=load(candidate,'candidate_storage')
 with tempfile.TemporaryDirectory(dir=H) as t:
  root=Path(t);green=race(new,root);assert green['calls']==2 and green['value']['scan_attempts']==2 and green['value']['regular_files']==0
  exhausted=race(new,root,True);assert exhausted['calls']==3 and type(exhausted['error']) is FileNotFoundError and exhausted['error'] is exhausted['errors'][-1]
 with tempfile.TemporaryDirectory(dir=H) as t:
  root=Path(t);sub=root/'owned';sub.mkdir();w=new.StorageWatch(sub,LIMITS);sub.rmdir()
  try:w.check()
  except FileNotFoundError as e:assert not hasattr(e,'storage_entry_disappearance')
  else:raise AssertionError('missing root accepted')
  sub.mkdir();w=new.StorageWatch(sub,LIMITS);(sub/'link').symlink_to(root)
  try:w.check()
  except ValueError as e:assert 'symbolic link' in str(e)
  else:raise AssertionError('symlink accepted')
 with tempfile.TemporaryDirectory(dir=H) as t:
  root=Path(t);(root/'oversize').write_bytes(b'X'*1025)
  try:new.StorageWatch(root,LIMITS).check()
  except new.StorageLimit as e:assert e.reason=='logical'
  else:raise AssertionError('observed limit lost')
 for boundary in ('open','rejoin'):
  with tempfile.TemporaryDirectory(dir=H) as t:
   root=Path(t);(root/'child').mkdir();watch=new.StorageWatch(root,LIMITS);real_open=os.open;real_stat=os.stat;seen=[]
   def opened(name,*a,**kw):
    if boundary=='open' and name=='child' and 'dir_fd' in kw and not seen:
     seen.append(1);(root/'child').rmdir()
    return real_open(name,*a,**kw)
   def stated(name,*a,**kw):
    if boundary=='rejoin' and name=='child' and 'dir_fd' in kw:
     seen.append(1)
     if len(seen)==2:(root/'child').rmdir()
    return real_stat(name,*a,**kw)
   with patch.object(new.os,'open',opened),patch.object(new.os,'stat',stated):value=watch.check()
   assert value['scan_attempts']==2 and value['directories']==1
 with tempfile.TemporaryDirectory(dir=H) as t:
  root=Path(t);child=root/'owned';child.mkdir();watch=new.StorageWatch(child,LIMITS);child.rename(root/'old');child.mkdir()
  try:watch.check()
  except ValueError as e:assert 'root replaced' in str(e)
  else:raise AssertionError('root rebirth accepted')
 with tempfile.TemporaryDirectory(dir=H) as t:
  root=Path(t);watch=new.StorageWatch(root,LIMITS);clock=[0.];original=watch._scan;calls=[]
  def slow(begin):
   calls.append(1);clock[0]=2.;return original(begin)
  watch._scan=slow
  with patch.object(new.time,'monotonic',lambda:clock[0]):
   try:watch.check()
   except new.StorageLimit as e:assert e.reason=='time' and len(calls)==1
   else:raise AssertionError('shared time bound bypassed')
 inverse=json.loads((H/'INVERSE01.json').read_text());body=(H/'workflow_storage.py').read_text()
 for edit in reversed(inverse['literal_edits']):assert body.count(edit['after'])==1;body=body.replace(edit['after'],edit['before'])
 assert hashlib.sha256(body.encode()).hexdigest()==inverse['baseline_sha256']
 result.update(directory_open_and_rejoin_retry=True,root_rebirth_strict=True,shared_time_limit_strict=True,exact_literal_inverse=True)
 result.update(candidate_green=True,persistent_disappearance_attempts=3,original_exhaustion_exception_preserved=True,missing_root_strict=True,symlink_strict=True,logical_limit_strict=True)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
