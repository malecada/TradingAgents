import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04';s=importlib.util.spec_from_file_location('m',A/'workflow_storage.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));p=H/'cleanup-probe';(p/'d').mkdir(parents=True);(p/'d'/'f').write_bytes(b'x');first=KeyboardInterrupt('body');seen=[]
def st(path,*a,**kw):
 if path=='f':raise first
 return os.stat(path,*a,**kw)
def close(fd):
 os.close(fd);e=RuntimeError('close-'+str(fd));seen.append(e);raise e
m.os.stat=st;m.os.close=close
try:m.StorageWatch(p,dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)).check()
except BaseException as e:
 q=[e];visited=[]
 while q:
  x=q.pop()
  if any(x is z for z in visited):continue
  visited.append(x);q.extend(y for y in (x.__cause__,x.__context__) if y is not None);q.extend(getattr(x,'storage_cleanup_errors',()));q.extend(getattr(x,'exceptions',()))
 out={'original_selected':e is first,'all_seen':[str(x) for x in seen],'reachable_exception_graph':[str(x) for x in visited],'first_close_reachable':any(seen[0] is x for x in visited),'last_close_reachable':any(seen[1] is x for x in visited),'fds':{x:os.readlink('/proc/self/fd/'+x) for x in os.listdir('/proc/self/fd') if os.path.exists('/proc/self/fd/'+x)}}
 (H/'CLEANUP_PROBE01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
