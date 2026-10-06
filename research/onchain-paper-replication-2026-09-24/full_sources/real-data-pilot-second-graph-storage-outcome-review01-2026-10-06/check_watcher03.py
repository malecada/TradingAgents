import hashlib,importlib.util,json,os,tempfile
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).parent;F=H.parent;M=F.parents[2];C=F/'real-data-pilot-storage-rename-race-fix01-2026-10-06'
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
for name,value in json.loads((C/'MANIFEST01.json').read_text()).items():assert sh(C/name)==value
inv=json.loads((C/'INVERSE01.json').read_text());s=(C/'workflow_storage.py').read_text()
for e in reversed(inv['literal_edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'])
base=M/'tradingagents/research/onchain_replication/workflow_storage.py';assert s==base.read_text() and sh(base)==inv['baseline_sha256']
a=load(base,'old_storage_independent');b=load(C/'workflow_storage.py','new_storage_independent')
limits={'max_allocated_bytes':2**20,'max_logical_bytes':1024,'max_entries':8,'max_depth':3,'max_scan_seconds':1}
results={}
# Actual local filesystem disappearing descendant at each of the three changed calls.
for which in ('stat','open','rejoin'):
 for label,mod in [('old',a),('new',b)]:
  with tempfile.TemporaryDirectory(dir=H) as tmp:
   root=Path(tmp);victim=root/'pending';victim.write_bytes(b'z') if which=='stat' else victim.mkdir()
   w=mod.StorageWatch(root,limits);realstat=os.stat;realopen=os.open;seen=0
   def hookstat(name,*args,**kw):
    global seen
    if name=='pending' and 'dir_fd' in kw:
     seen+=1
     if (which=='stat' and seen==1) or (which=='rejoin' and seen==2):
      victim.unlink() if which=='stat' else victim.rmdir()
    return realstat(name,*args,**kw)
   def hookopen(name,*args,**kw):
    if name=='pending' and 'dir_fd' in kw and which=='open':victim.rmdir()
    return realopen(name,*args,**kw)
   with patch.object(mod.os,'stat',hookstat),patch.object(mod.os,'open',hookopen):
    try:value=w.check()
    except FileNotFoundError:assert label=='old';results[which+'_'+label]='original ENOENT'
    else:assert label=='new' and value['scan_attempts']==2 and value['regular_files']==0 and value['directories']==1;results[which+'_'+label]='fresh complete second scan'
# Three repeatedly disappearing real files preserve exact last OSError; no fourth scan.
with tempfile.TemporaryDirectory(dir=H) as tmp:
 root=Path(tmp);w=b.StorageWatch(root,limits);original=w._scan;calls=[];errors=[];realstat=os.stat
 def scan(begin):calls.append(1);(root/'pending').write_bytes(b'x');return original(begin)
 def missing(name,*args,**kw):
  if name=='pending' and 'dir_fd' in kw:
   (root/'pending').unlink()
   try:return realstat(name,*args,**kw)
   except FileNotFoundError as error:errors.append(error);raise
  return realstat(name,*args,**kw)
 w._scan=scan
 with patch.object(b.os,'stat',missing):
  try:w.check()
  except FileNotFoundError as error:assert len(calls)==3 and error is errors[-1] and error.filename=='pending' and error.errno==2 and error.observation['entries']==1
  else:raise AssertionError('persistent missing sample accepted')
# Root absence is not a descendant retry. An observed entry breach precedes stat.
with tempfile.TemporaryDirectory(dir=H) as tmp:
 parent=Path(tmp);root=parent/'owned';root.mkdir();w=b.StorageWatch(root,limits);root.rmdir()
 try:w.check()
 except FileNotFoundError as error:assert not hasattr(error,'storage_entry_disappearance')
 else:raise AssertionError('missing root accepted')
 root.mkdir();(root/'one').write_bytes(b'x');(root/'two').write_bytes(b'x')
 try:b.StorageWatch(root,{**limits,'max_entries':1}).check()
 except b.StorageLimit as error:assert error.reason=='entries'
 else:raise AssertionError('entry bound lost')
# Shared time is not reset after eligible missing observation.
with tempfile.TemporaryDirectory(dir=H) as tmp:
 root=Path(tmp);(root/'pending').write_bytes(b'x');w=b.StorageWatch(root,limits);clock=[0.];realstat=os.stat
 def expire(name,*args,**kw):
  if name=='pending' and 'dir_fd' in kw:(root/'pending').unlink();clock[0]=2.
  return realstat(name,*args,**kw)
 with patch.object(b.time,'monotonic',lambda:clock[0]),patch.object(b.os,'stat',expire):
  try:w.check()
  except b.StorageLimit as error:assert error.reason=='time' and isinstance(error.__cause__,FileNotFoundError)
  else:raise AssertionError('time reset')
result={'decision':'accepted-source-only','candidate_sha256':sh(C/'workflow_storage.py'),'candidate_manifest_sha256':sh(C/'MANIFEST01.json'),'literal_inverse':True,'changed_seams':results,'persistent_enoent_max_attempts':3,'actual_original_last_oserror_retained':True,'missing_root_not_retried':True,'observed_entry_bound_preserved':True,'shared_time_not_reset':True,'native_network_payload_operations':False,'qualification':'Actual owned filesystem witnesses reproduce the failure class, not the unrecorded original interleaving. No incomplete sample is accepted; original failed backup remains failed.'}
(H/'WATCHER_CHECK03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
